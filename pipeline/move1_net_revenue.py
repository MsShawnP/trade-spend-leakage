"""Move 1 — Net Revenue Ranking pipeline.

Queries the Cinderhaven Postgres source for trailing-52-week revenue by
retailer, applies structural trade spend rates from sku_costs, and writes
results_net_revenue to results.db.
"""

from __future__ import annotations

import pandas as pd
import psycopg2.extras

from pipeline.db import source_conn, results_conn

# Postgres query — adapts all_in_trade_rate.sql pattern from trade-spend-data-diagnostic.
# Uses a subquery CTE to capture the trailing-52-week floor, then joins scan_data
# to stores for the retailer name, CROSS JOINs channel_rates from sku_costs, and
# applies a CASE to assign each retailer its structural trade rate.
_SQL = """
WITH trailing_bounds AS (
    SELECT MIN(week_ending) AS oldest_week
    FROM (
        SELECT DISTINCT week_ending
        FROM scan_data
        ORDER BY week_ending DESC
        LIMIT 52
    ) t
),
channel_rates AS (
    SELECT
        AVG(trade_spend_pct_walmart)     AS rate_walmart,
        AVG(trade_spend_pct_costco)      AS rate_costco,
        AVG(trade_spend_pct_whole_foods) AS rate_whole_foods,
        AVG(trade_spend_pct_unfi)        AS rate_unfi,
        AVG(trade_spend_pct_dtc)         AS rate_dtc,
        AVG(trade_spend_pct_kehe)        AS rate_kehe,
        AVG(trade_spend_pct_regional)    AS rate_regional
    FROM sku_costs
),
revenue_by_retailer AS (
    SELECT
        st.retailer,
        SUM(sd.dollars_sold) AS gross_revenue
    FROM scan_data sd
    JOIN stores st ON sd.store_id = st.store_id
    WHERE sd.week_ending >= (SELECT oldest_week FROM trailing_bounds)
    GROUP BY st.retailer
),
with_rate AS (
    SELECT
        r.retailer,
        r.gross_revenue,
        CASE r.retailer
            WHEN 'Walmart'     THEN cr.rate_walmart
            WHEN 'Costco'      THEN cr.rate_costco
            WHEN 'Whole Foods' THEN cr.rate_whole_foods
            WHEN 'UNFI'        THEN cr.rate_unfi
            WHEN 'DTC'         THEN cr.rate_dtc
            WHEN 'KeHE'        THEN cr.rate_kehe
            ELSE cr.rate_regional
        END AS trade_rate
    FROM revenue_by_retailer r
    CROSS JOIN channel_rates cr
)
SELECT
    retailer,
    gross_revenue,
    gross_revenue * trade_rate            AS trade_spend,
    gross_revenue * (1.0 - trade_rate)    AS net_revenue,
    1.0 - trade_rate                      AS net_to_gross_ratio
FROM with_rate
ORDER BY net_revenue DESC
"""


def compute_net_revenue(conn) -> pd.DataFrame:
    """Return per-retailer net revenue DataFrame from a live Postgres connection.

    Columns: retailer, gross_revenue, trade_spend, net_revenue, net_to_gross_ratio
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_SQL)
        rows = cur.fetchall()
    if not rows:
        raise ValueError("No rows returned — scan_data or stores may be empty")
    return pd.DataFrame([dict(r) for r in rows])


def run() -> None:
    """Execute Move 1 and write results_net_revenue to results.db."""
    with source_conn() as conn:
        df = compute_net_revenue(conn)

    with results_conn() as conn:
        df.to_sql("results_net_revenue", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_net_revenue_retailer "
            "ON results_net_revenue(retailer)"
        )

    print(f"  Move 1 complete — {len(df)} retailers written to results_net_revenue")
