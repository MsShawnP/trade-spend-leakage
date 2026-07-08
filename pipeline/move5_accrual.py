"""Move 5 — Accrual Reconciliation pipeline.

For each of the last 12 months, computes:

  * accrued  — implied trade spend from structural rate card (sku_costs) ×
               monthly gross scan revenue. Same rate-assignment logic as Move 1.

  * actual   — total deductions taken (all types) from raw.retailer_deductions,
               grouped by month.

  * variance — accrued − actual.
               Positive: accrued more than was actually taken (under-billed).
               Negative: more was taken than accrued (over-billed).

Window: trailing 365 days relative to the most recent week_ending in scan_data.

Writes results_accrual to results.db (12 monthly rows).
"""

from __future__ import annotations

import pandas as pd
import psycopg2.extras

from pipeline.db import source_conn, results_conn

# ---------------------------------------------------------------------------
# SQL — monthly accrued trade spend
# The channel-rate CASE below MUST stay identical to move1_net_revenue.py:
# every retailer (Walmart, Costco, Kroger, Whole Foods, Sprouts) maps to its
# own rate, and only the Regional Group falls through to rate_regional. If a
# named retailer is missing here it is silently under/over-accrued at the
# regional rate and Move 1 and Move 5 stop reconciling.
# ---------------------------------------------------------------------------

_SQL_ACCRUED = """
WITH trailing_bounds AS (
    SELECT
        MAX(week_ending)                              AS max_week,
        MAX(week_ending) - INTERVAL '365 days'        AS start_week
    FROM raw.scan_data
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
monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', sd.week_ending)::date AS month,
        st.chain_name                              AS retailer,
        SUM(sd.dollars_sold)                       AS gross_revenue
    FROM raw.scan_data sd
    JOIN raw.stores st ON sd.store_id = st.store_id
    WHERE sd.week_ending >= (SELECT start_week FROM trailing_bounds)
    GROUP BY DATE_TRUNC('month', sd.week_ending), st.chain_name
)
SELECT
    mr.month,
    SUM(mr.gross_revenue * CASE mr.retailer
        WHEN 'Walmart'     THEN cr.rate_walmart
        WHEN 'Costco'      THEN cr.rate_costco
        WHEN 'Kroger'      THEN cr.rate_kroger
        WHEN 'Whole Foods' THEN cr.rate_whole_foods
        WHEN 'Sprouts'     THEN cr.rate_sprouts
        ELSE cr.rate_regional
    END)::float AS accrued
FROM monthly_revenue mr
CROSS JOIN channel_rates cr
GROUP BY mr.month
ORDER BY mr.month
"""

# ---------------------------------------------------------------------------
# SQL — monthly actual deductions (all types, trailing 365 days)
# ---------------------------------------------------------------------------

_SQL_ACTUAL = """
WITH trailing_bounds AS (
    SELECT
        MAX(week_ending)                       AS max_week,
        MAX(week_ending) - INTERVAL '365 days' AS start_week
    FROM raw.scan_data
)
SELECT
    DATE_TRUNC('month', d.deduction_date)::date AS month,
    SUM(d.amount)::float                         AS actual
FROM raw.retailer_deductions d
WHERE d.deduction_date >= (SELECT start_week FROM trailing_bounds)
  AND d.deduction_date <= (SELECT max_week  FROM trailing_bounds)
GROUP BY DATE_TRUNC('month', d.deduction_date)
ORDER BY month
"""


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_accrual(source) -> pd.DataFrame:
    """Return monthly accrual reconciliation DataFrame.

    Columns: month (str YYYY-MM-DD), accrued (float), actual (float),
             variance (float)
    """
    with source.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_SQL_ACCRUED)
        accrued_rows = [dict(r) for r in cur.fetchall()]

        cur.execute(_SQL_ACTUAL)
        actual_rows = [dict(r) for r in cur.fetchall()]

    if not accrued_rows:
        return _empty_result()

    df_accrued = pd.DataFrame(accrued_rows)
    df_accrued["month"] = df_accrued["month"].astype(str)
    df_accrued["accrued"] = pd.to_numeric(df_accrued["accrued"], errors="coerce").astype(float)

    if actual_rows:
        df_actual = pd.DataFrame(actual_rows)
        df_actual["month"] = df_actual["month"].astype(str)
        df_actual["actual"] = pd.to_numeric(df_actual["actual"], errors="coerce").astype(float)
    else:
        df_actual = pd.DataFrame(columns=["month", "actual"])

    df = df_accrued.merge(df_actual, on="month", how="left")
    df["actual"] = df["actual"].fillna(0.0)
    df["variance"] = df["accrued"] - df["actual"]

    # Keep only the last 12 months by row count (already ordered ASC from SQL)
    if len(df) > 12:
        df = df.tail(12).reset_index(drop=True)

    return df[["month", "accrued", "actual", "variance"]]


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=["month", "accrued", "actual", "variance"])


def run() -> None:
    """Execute Move 5 and write results_accrual to results.db."""
    with source_conn() as pg_conn:
        df = compute_accrual(pg_conn)

    if df.empty:
        print("  Move 5 — no accrual data found; results_accrual not written")
        return

    for col in ["accrued", "actual", "variance"]:
        df[col] = df[col].astype(float)

    with results_conn() as conn:
        df.to_sql("results_accrual", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_accrual_month "
            "ON results_accrual(month)"
        )

    total_variance = df["variance"].sum()
    sign = "+" if total_variance >= 0 else ""
    print(
        f"  Move 5 complete — {len(df)} months written to results_accrual "
        f"(net variance {sign}${total_variance:,.0f})"
    )
