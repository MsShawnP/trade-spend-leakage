"""Move 2 — Trade Spend Efficiency pipeline.

Per retailer, computes:
  (a) structural trade spend as % of gross revenue — from results_net_revenue
      (already written by Move 1)
  (b) revenue per promo dollar — promo-period scan revenue ÷ total promo cost
      from raw.promotions × raw.scan_data. Deduplicates overlapping promo weeks
      so revenue is not double-counted. Retailers with no promo cost data are
      flagged lift_measurable=False.

Writes results_trade_efficiency to results.db.

Note: revenue_per_promo_dollar is the full promo-period scan revenue, not
incremental above baseline. Move 4 (U5) computes the rolling-median-adjusted
incremental lift. This is the simpler ratio for the efficiency comparison.
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import psycopg2.extras

from pipeline.db import source_conn, results_conn

# ---------------------------------------------------------------------------
# retailer_id mapping for raw.promotions (uses RET-* format, unlike deductions)
# ---------------------------------------------------------------------------
# raw.promotions.retailer_id uses 'RET-WALMART' format.
# raw.retailer_deductions.retailer_id uses 'walmart' (lowercase slug) format.
# raw.stores.chain_name uses 'Walmart' (display name) format.
# ---------------------------------------------------------------------------

_SLUG_TO_DISPLAY: dict[str, str] = {
    "RET-WALMART":    "Walmart",
    "RET-COSTCO":     "Costco",
    "RET-KROGER":     "Kroger",
    "RET-WHOLEFOODS": "Whole Foods",
    "RET-SPROUTS":    "Sprouts",
    "RET-REGIONAL":   "Regional Group",
}

# Retailer name → slug (inverse, for joining with results_net_revenue)
_DISPLAY_TO_SLUG: dict[str, str] = {v: k for k, v in _SLUG_TO_DISPLAY.items()}

# ---------------------------------------------------------------------------
# Postgres query — promo cost + deduplicated promo-period scan revenue
# ---------------------------------------------------------------------------
# Uses DISTINCT ON (retailer_id, store_id, week_ending) to avoid
# double-counting scan revenue when multiple promotions overlap for the
# same retailer in the same week.
# ---------------------------------------------------------------------------

_SQL_PROMO_EFFICIENCY = """
WITH slug_map (slug, chain_name) AS (
    VALUES
        ('RET-WALMART',    'Walmart'),
        ('RET-COSTCO',     'Costco'),
        ('RET-KROGER',     'Kroger'),
        ('RET-WHOLEFOODS', 'Whole Foods'),
        ('RET-SPROUTS',    'Sprouts'),
        ('RET-REGIONAL',   'Regional Group')
),
promo_costs AS (
    SELECT
        retailer_id,
        SUM(promo_cost) AS total_promo_cost,
        COUNT(DISTINCT promo_id) AS promo_count
    FROM raw.promotions
    WHERE promo_cost IS NOT NULL AND promo_cost > 0
    GROUP BY retailer_id
),
deduped_promo_weeks AS (
    SELECT DISTINCT ON (p.retailer_id, sd.store_id, sd.week_ending)
        p.retailer_id,
        sd.dollars_sold
    FROM raw.promotions p
    JOIN slug_map sm ON sm.slug = p.retailer_id
    JOIN raw.stores st ON st.chain_name = sm.chain_name
    JOIN raw.scan_data sd
        ON  sd.store_id = st.store_id
        AND sd.week_ending BETWEEN p.start_week AND p.end_week
    WHERE p.promo_cost IS NOT NULL AND p.promo_cost > 0
    ORDER BY p.retailer_id, sd.store_id, sd.week_ending
),
promo_scan AS (
    SELECT
        retailer_id,
        SUM(dollars_sold) AS promo_period_revenue
    FROM deduped_promo_weeks
    GROUP BY retailer_id
)
SELECT
    pc.retailer_id,
    pc.total_promo_cost,
    pc.promo_count,
    ps.promo_period_revenue,
    CASE
        WHEN pc.total_promo_cost > 0 AND ps.promo_period_revenue IS NOT NULL
        THEN ps.promo_period_revenue::float / pc.total_promo_cost
        ELSE NULL
    END AS revenue_per_promo_dollar
FROM promo_costs pc
LEFT JOIN promo_scan ps ON ps.retailer_id = pc.retailer_id
ORDER BY pc.retailer_id
"""


def compute_efficiency(source, results_db_conn: sqlite3.Connection) -> pd.DataFrame:
    """Return per-retailer efficiency DataFrame.

    Joins Postgres promo data with results_net_revenue (already in results.db).

    Columns:
      retailer, trade_spend_pct, trade_spend, gross_revenue,
      total_promo_cost, promo_period_revenue, revenue_per_promo_dollar,
      lift_measurable
    """
    # --- Postgres: promo cost + scan revenue during promo periods ---
    with source.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_SQL_PROMO_EFFICIENCY)
        rows = cur.fetchall()

    df_promo = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame(
        columns=["retailer_id", "total_promo_cost", "promo_count",
                 "promo_period_revenue", "revenue_per_promo_dollar"]
    )

    # Map slug → display name for joining
    if not df_promo.empty:
        df_promo["retailer"] = df_promo["retailer_id"].map(_SLUG_TO_DISPLAY)
        for col in ["total_promo_cost", "promo_period_revenue", "revenue_per_promo_dollar"]:
            df_promo[col] = pd.to_numeric(df_promo[col], errors="coerce").astype(float)

    # --- SQLite: results_net_revenue for trade_spend_pct ---
    df_net = pd.read_sql_query(
        "SELECT retailer, gross_revenue, trade_spend, net_to_gross_ratio "
        "FROM results_net_revenue",
        results_db_conn,
    )
    if df_net.empty:
        raise ValueError(
            "results_net_revenue is empty — run Move 1 before Move 2: "
            "python pipeline/run.py --moves 1"
        )
    df_net["trade_spend_pct"] = df_net["trade_spend"] / df_net["gross_revenue"]

    # --- Join on retailer display name ---
    if not df_promo.empty:
        df = df_net.merge(
            df_promo[["retailer", "total_promo_cost", "promo_period_revenue",
                       "revenue_per_promo_dollar"]],
            on="retailer",
            how="left",
        )
    else:
        df = df_net.copy()
        df["total_promo_cost"] = None
        df["promo_period_revenue"] = None
        df["revenue_per_promo_dollar"] = None

    df["lift_measurable"] = df["revenue_per_promo_dollar"].notna().astype(int)

    return df[[
        "retailer", "trade_spend_pct", "trade_spend", "gross_revenue",
        "total_promo_cost", "promo_period_revenue", "revenue_per_promo_dollar",
        "lift_measurable",
    ]]


def run() -> None:
    """Execute Move 2 and write results_trade_efficiency to results.db."""
    with source_conn() as pg_conn:
        with results_conn() as sq_conn:
            df = compute_efficiency(pg_conn, sq_conn)

    # Cast numerics to float for clean SQLite storage
    for col in ["trade_spend_pct", "trade_spend", "gross_revenue",
                 "total_promo_cost", "promo_period_revenue", "revenue_per_promo_dollar"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
    df["lift_measurable"] = df["lift_measurable"].astype(int)

    with results_conn() as conn:
        df.to_sql("results_trade_efficiency", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_efficiency_retailer "
            "ON results_trade_efficiency(retailer)"
        )

    measurable = df["lift_measurable"].sum()
    print(
        f"  Move 2 complete — {len(df)} retailers written to results_trade_efficiency "
        f"({measurable} with measurable revenue-per-promo-dollar)"
    )
