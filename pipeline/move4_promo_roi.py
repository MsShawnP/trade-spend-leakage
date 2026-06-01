"""Move 4 — Promotional ROI pipeline.

For each of the 75 distinct promotion events in raw.promotions, computes:

  * has_sufficient_baseline — True when ≥8 weeks of pre-promo scan data exist
    for the promoted SKU × retailer. Only 18 of 75 events satisfy this in the
    Cinderhaven dataset (per data_generation_log.md).

  * baseline_weekly_revenue — rolling-median weekly revenue across the 8 weeks
    immediately preceding start_week (None when has_sufficient_baseline=False).

  * incremental_revenue — total promo-period scan revenue minus the expected
    baseline for the same number of weeks. Revenue proxy for gross margin (COGS
    not available in the Cinderhaven schema).

  * is_money_losing — promo_cost > incremental_revenue (None when
    has_sufficient_baseline=False or promo_cost is NULL).

Promotions with NULL promo_cost (7 rows in the data) are included in the output
but excluded from ROI classification (is_money_losing=None).

Writes results_promo_roi to results.db.

Note: DISTINCT ON (promo_id) is applied at the SQL layer — the promotions table
has 188 rows but 75 distinct promo events. We pick the row with the highest
promo_cost for each event (most informative single-row representative).
"""

from __future__ import annotations

import sqlite3
from statistics import median

import pandas as pd
import psycopg2.extras

from pipeline.db import source_conn, results_conn

# ---------------------------------------------------------------------------
# Retailer slug map — same as move2_efficiency
# ---------------------------------------------------------------------------

_SLUG_TO_DISPLAY: dict[str, str] = {
    "RET-WALMART":    "Walmart",
    "RET-COSTCO":     "Costco",
    "RET-KROGER":     "Kroger",
    "RET-WHOLEFOODS": "Whole Foods",
    "RET-SPROUTS":    "Sprouts",
    "RET-REGIONAL":   "Regional Group",
}

# ---------------------------------------------------------------------------
# Baseline window
# ---------------------------------------------------------------------------

_BASELINE_WEEKS = 8
_MIN_BASELINE_WEEKS = 8  # must have this many weeks to flag has_sufficient_baseline

# ---------------------------------------------------------------------------
# SQL — one row per promo event (DISTINCT ON promo_id) with promo attributes
# ---------------------------------------------------------------------------

_SQL_PROMOS = """
SELECT DISTINCT ON (promo_id)
    promo_id,
    sku          AS sku_id,
    retailer_id,
    start_week,
    end_week,
    promo_cost,
    promo_type,
    funding_mechanism
FROM raw.promotions
ORDER BY promo_id, promo_cost DESC NULLS LAST
"""

# ---------------------------------------------------------------------------
# SQL — pre-promo weekly revenue for all promos in one fetch
#   8 weeks before start_week, for the promoted SKU × retailer's stores.
# ---------------------------------------------------------------------------

_SQL_PRE_PROMO_WEEKLY = """
WITH slug_map (slug, chain_name) AS (
    VALUES
        ('RET-WALMART',    'Walmart'),
        ('RET-COSTCO',     'Costco'),
        ('RET-KROGER',     'Kroger'),
        ('RET-WHOLEFOODS', 'Whole Foods'),
        ('RET-SPROUTS',    'Sprouts'),
        ('RET-REGIONAL',   'Regional Group')
),
promo_list AS (
    SELECT DISTINCT ON (promo_id)
        promo_id,
        sku          AS sku_id,
        retailer_id,
        start_week
    FROM raw.promotions
    ORDER BY promo_id, promo_cost DESC NULLS LAST
)
SELECT
    p.promo_id,
    sd.week_ending,
    SUM(sd.dollars_sold) AS weekly_revenue
FROM promo_list p
JOIN slug_map sm ON sm.slug = p.retailer_id
JOIN raw.stores st ON st.chain_name = sm.chain_name
JOIN raw.scan_data sd
    ON  sd.store_id = st.store_id
    AND sd.sku      = p.sku_id
    AND sd.week_ending >= p.start_week - INTERVAL '8 weeks'
    AND sd.week_ending <  p.start_week
GROUP BY p.promo_id, sd.week_ending
ORDER BY p.promo_id, sd.week_ending
"""

# ---------------------------------------------------------------------------
# SQL — promo-period revenue (sum of dollars_sold during promo window)
# ---------------------------------------------------------------------------

_SQL_PROMO_PERIOD = """
WITH slug_map (slug, chain_name) AS (
    VALUES
        ('RET-WALMART',    'Walmart'),
        ('RET-COSTCO',     'Costco'),
        ('RET-KROGER',     'Kroger'),
        ('RET-WHOLEFOODS', 'Whole Foods'),
        ('RET-SPROUTS',    'Sprouts'),
        ('RET-REGIONAL',   'Regional Group')
),
promo_list AS (
    SELECT DISTINCT ON (promo_id)
        promo_id,
        sku          AS sku_id,
        retailer_id,
        start_week,
        end_week
    FROM raw.promotions
    ORDER BY promo_id, promo_cost DESC NULLS LAST
)
SELECT
    p.promo_id,
    SUM(sd.dollars_sold)         AS promo_revenue,
    COUNT(DISTINCT sd.week_ending) AS promo_weeks
FROM promo_list p
JOIN slug_map sm ON sm.slug = p.retailer_id
JOIN raw.stores st ON st.chain_name = sm.chain_name
JOIN raw.scan_data sd
    ON  sd.store_id  = st.store_id
    AND sd.sku       = p.sku_id
    AND sd.week_ending BETWEEN p.start_week AND p.end_week
GROUP BY p.promo_id
"""


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_promo_roi(source) -> pd.DataFrame:
    """Return per-promo-event ROI DataFrame (75 rows).

    Columns:
      promo_id, sku_id, retailer_id, retailer, start_week, end_week,
      promo_cost, promo_type, has_sufficient_baseline,
      baseline_weekly_revenue, incremental_revenue,
      promo_weeks, is_money_losing
    """
    with source.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_SQL_PROMOS)
        promo_rows = [dict(r) for r in cur.fetchall()]

        cur.execute(_SQL_PRE_PROMO_WEEKLY)
        pre_rows = [dict(r) for r in cur.fetchall()]

        cur.execute(_SQL_PROMO_PERIOD)
        period_rows = [dict(r) for r in cur.fetchall()]

    if not promo_rows:
        return _empty_result()

    df_promos = pd.DataFrame(promo_rows)
    for col in ["promo_cost"]:
        df_promos[col] = pd.to_numeric(df_promos[col], errors="coerce")

    # Pre-promo weekly data grouped by promo_id
    pre_by_promo: dict[str, list[float]] = {}
    for row in pre_rows:
        pid = str(row["promo_id"])
        rev = float(row["weekly_revenue"]) if row["weekly_revenue"] is not None else 0.0
        pre_by_promo.setdefault(pid, []).append(rev)

    # Promo-period totals by promo_id
    period_by_promo: dict[str, dict] = {}
    for row in period_rows:
        pid = str(row["promo_id"])
        period_by_promo[pid] = {
            "promo_revenue": float(row["promo_revenue"]) if row["promo_revenue"] else 0.0,
            "promo_weeks": int(row["promo_weeks"]) if row["promo_weeks"] else 0,
        }

    # Build result rows
    results = []
    for _, promo in df_promos.iterrows():
        pid = str(promo["promo_id"])
        pre_weeks = pre_by_promo.get(pid, [])
        period = period_by_promo.get(pid, {"promo_revenue": 0.0, "promo_weeks": 0})

        has_baseline = len(pre_weeks) >= _MIN_BASELINE_WEEKS
        baseline_weekly = float(median(pre_weeks)) if has_baseline else None
        promo_rev = period["promo_revenue"]
        promo_wks = period["promo_weeks"]

        if has_baseline and baseline_weekly is not None and promo_wks > 0:
            incremental = promo_rev - (baseline_weekly * promo_wks)
        else:
            incremental = None

        promo_cost = float(promo["promo_cost"]) if pd.notna(promo["promo_cost"]) else None

        if has_baseline and incremental is not None and promo_cost is not None:
            is_money_losing = promo_cost > incremental
        else:
            is_money_losing = None

        results.append({
            "promo_id":                 pid,
            "sku_id":                   str(promo["sku_id"]) if promo["sku_id"] else None,
            "retailer_id":              str(promo["retailer_id"]),
            "retailer":                 _SLUG_TO_DISPLAY.get(str(promo["retailer_id"]), str(promo["retailer_id"])),
            "start_week":               str(promo["start_week"]),
            "end_week":                 str(promo["end_week"]),
            "promo_cost":               promo_cost,
            "promo_type":               str(promo["promo_type"]) if promo["promo_type"] else None,
            "has_sufficient_baseline":  int(has_baseline),
            "baseline_weekly_revenue":  baseline_weekly,
            "promo_revenue":            promo_rev if promo_wks > 0 else None,
            "promo_weeks":              promo_wks if promo_wks > 0 else None,
            "incremental_revenue":      incremental,
            "is_money_losing":          int(is_money_losing) if is_money_losing is not None else None,
        })

    return pd.DataFrame(results)


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "promo_id", "sku_id", "retailer_id", "retailer",
        "start_week", "end_week", "promo_cost", "promo_type",
        "has_sufficient_baseline", "baseline_weekly_revenue",
        "promo_revenue", "promo_weeks", "incremental_revenue",
        "is_money_losing",
    ])


def run() -> None:
    """Execute Move 4 and write results_promo_roi to results.db."""
    with source_conn() as pg_conn:
        df = compute_promo_roi(pg_conn)

    if df.empty:
        print("  Move 4 — no promotion data found; results_promo_roi not written")
        return

    # Float casts for clean SQLite storage
    for col in ["promo_cost", "baseline_weekly_revenue", "promo_revenue",
                "incremental_revenue"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

    for col in ["has_sufficient_baseline", "promo_weeks"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # is_money_losing: keep as nullable int (None → NULL in SQLite)
    df["is_money_losing"] = df["is_money_losing"].where(df["is_money_losing"].notna(), other=None)

    with results_conn() as conn:
        df.to_sql("results_promo_roi", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_promo_roi_promo_id "
            "ON results_promo_roi(promo_id)"
        )

    total = len(df)
    measurable = int(df["has_sufficient_baseline"].sum())
    money_losing = int((df["is_money_losing"] == 1).sum())
    print(
        f"  Move 4 complete — {total} promo events written to results_promo_roi "
        f"({measurable} with sufficient baseline, {money_losing} money-losing)"
    )
