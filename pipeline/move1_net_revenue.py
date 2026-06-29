"""Move 1 — Net Revenue Ranking pipeline.

Queries the Cinderhaven Postgres source for trailing-52-week revenue by
retailer.  Computes total trade cost as structural rate-card spend plus
operational deductions (damaged, spoilage, late delivery, etc.) from
retailer_deductions.  Promo billbacks and slotting are excluded from the
deduction add-on because they are already funded by the structural rate.
"""

from __future__ import annotations

import pandas as pd
import psycopg2.extras

from pipeline.db import source_conn, results_conn

_RETAILER_ID_TO_DISPLAY = {
    "RET-WALMART": "Walmart",
    "RET-COSTCO": "Costco",
    "RET-KROGER": "Kroger",
    "RET-WHOLEFOODS": "Whole Foods",
    "RET-SPROUTS": "Sprouts",
    "RET-REGIONAL": "Regional Group",
}

_REVENUE_SQL = """
WITH trailing_bounds AS (
    SELECT MIN(week_ending) AS oldest_week, MAX(week_ending) AS newest_week
    FROM (
        SELECT DISTINCT week_ending
        FROM raw.scan_data
        ORDER BY week_ending DESC
        LIMIT 52
    ) t
),
channel_rates AS (
    SELECT
        AVG(trade_spend_pct_walmart)     AS rate_walmart,
        AVG(trade_spend_pct_costco)      AS rate_costco,
        AVG(trade_spend_pct_kroger)      AS rate_kroger,
        AVG(trade_spend_pct_whole_foods) AS rate_whole_foods,
        AVG(trade_spend_pct_sprouts)     AS rate_sprouts,
        AVG(trade_spend_pct_regional)    AS rate_regional
    FROM raw.sku_costs
),
revenue_by_retailer AS (
    SELECT
        st.chain_name AS retailer,
        SUM(sd.dollars_sold) AS gross_revenue
    FROM raw.scan_data sd
    JOIN raw.stores st ON sd.store_id = st.store_id
    WHERE sd.week_ending >= (SELECT oldest_week FROM trailing_bounds)
    GROUP BY st.chain_name
),
with_rate AS (
    SELECT
        r.retailer,
        r.gross_revenue,
        CASE r.retailer
            WHEN 'Walmart'     THEN cr.rate_walmart
            WHEN 'Costco'      THEN cr.rate_costco
            WHEN 'Kroger'      THEN cr.rate_kroger
            WHEN 'Whole Foods' THEN cr.rate_whole_foods
            WHEN 'Sprouts'     THEN cr.rate_sprouts
            ELSE cr.rate_regional
        END AS structural_rate
    FROM revenue_by_retailer r
    CROSS JOIN channel_rates cr
)
SELECT
    retailer,
    gross_revenue,
    structural_rate,
    gross_revenue * structural_rate AS structural_trade_spend
FROM with_rate
"""

_DEDUCTIONS_SQL = """
WITH trailing_bounds AS (
    SELECT MIN(week_ending) AS oldest_week, MAX(week_ending) AS newest_week
    FROM (
        SELECT DISTINCT week_ending
        FROM raw.scan_data
        ORDER BY week_ending DESC
        LIMIT 52
    ) t
)
SELECT
    d.retailer_id,
    SUM(d.amount) AS operational_deductions
FROM raw.retailer_deductions d, trailing_bounds tb
WHERE d.deduction_date >= tb.oldest_week
  AND d.deduction_date <= tb.newest_week
  AND d.deduction_type NOT IN ('promo_billback', 'slotting')
GROUP BY d.retailer_id
"""


def compute_net_revenue(conn) -> pd.DataFrame:
    """Return per-retailer net revenue after all trade costs.

    Total trade cost = structural rate-card spend + operational deductions.
    Promo billbacks and slotting excluded from deductions (covered by rate card).

    Columns: retailer, gross_revenue, trade_spend, net_revenue, net_to_gross_ratio
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_REVENUE_SQL)
        rev_rows = cur.fetchall()
        cur.execute(_DEDUCTIONS_SQL)
        ded_rows = cur.fetchall()

    if not rev_rows:
        raise ValueError("No rows returned — scan_data or stores may be empty")

    df_rev = pd.DataFrame([dict(r) for r in rev_rows])
    df_ded = pd.DataFrame([dict(r) for r in ded_rows])
    df_ded["retailer"] = df_ded["retailer_id"].map(_RETAILER_ID_TO_DISPLAY)
    df_ded = df_ded.drop(columns=["retailer_id"])

    df = df_rev.merge(df_ded, on="retailer", how="left")
    df["operational_deductions"] = df["operational_deductions"].fillna(0)

    df["trade_spend"] = df["structural_trade_spend"] + df["operational_deductions"]
    df["net_revenue"] = df["gross_revenue"] - df["trade_spend"]
    df["net_to_gross_ratio"] = df["net_revenue"] / df["gross_revenue"]

    df = df[["retailer", "gross_revenue", "trade_spend", "net_revenue", "net_to_gross_ratio"]]
    return df.sort_values("net_revenue", ascending=False).reset_index(drop=True)


def run() -> None:
    """Execute Move 1 and write results_net_revenue to results.db."""
    with source_conn() as conn:
        df = compute_net_revenue(conn)

    numeric_cols = ["gross_revenue", "trade_spend", "net_revenue", "net_to_gross_ratio"]
    for col in numeric_cols:
        df[col] = df[col].astype(float)

    with results_conn() as conn:
        df.to_sql("results_net_revenue", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_net_revenue_retailer "
            "ON results_net_revenue(retailer)"
        )

    print(f"  Move 1 complete — {len(df)} retailers written to results_net_revenue")
