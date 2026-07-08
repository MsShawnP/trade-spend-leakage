"""Tests for pipeline.move5_accrual — accrual reconciliation pipeline.

Two layers:

  * Offline tests (no DATABASE_URL): schema, variance arithmetic, and the
    channel-rate CASE invariant that keeps Move 5 reconciled with Move 1.
    The CASE-invariant test is the regression guard for the Kroger bug —
    Move 5 previously omitted Kroger, silently accruing it at the regional
    rate while Move 1 used the Kroger rate card, so the two moves disagreed
    for a top-3 retailer.

  * Live tests (require DATABASE_URL): reconcile Kroger's accrual against its
    own rate card using real synthetic Cinderhaven data.
"""

import os
import re

import pandas as pd
import pytest

from pipeline.move1_net_revenue import _REVENUE_SQL
from pipeline.move5_accrual import (
    _SQL_ACCRUED,
    _empty_result,
    compute_accrual,
)

_LIVE = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live Postgres test",
)

# Retailers that must carry their own rate; only Regional Group falls to ELSE.
_NAMED_RETAILERS = {"Walmart", "Costco", "Kroger", "Whole Foods", "Sprouts"}


# ---------------------------------------------------------------------------
# Fake psycopg2 connection so compute_accrual can run without Postgres.
# ---------------------------------------------------------------------------

class _FakeCursor:
    def __init__(self, accrued_rows, actual_rows):
        self._accrued = accrued_rows
        self._actual = actual_rows
        self._last_sql = ""

    def execute(self, sql):
        self._last_sql = sql

    def fetchall(self):
        # _SQL_ACCRUED is the only query that mentions "accrued".
        return self._accrued if "accrued" in self._last_sql.lower() else self._actual

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, accrued_rows, actual_rows):
        self._cursor = _FakeCursor(accrued_rows, actual_rows)

    def cursor(self, cursor_factory=None):
        return self._cursor


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def test_empty_result_has_required_columns():
    df = _empty_result()
    assert list(df.columns) == ["month", "accrued", "actual", "variance"]


# ---------------------------------------------------------------------------
# Variance arithmetic
# ---------------------------------------------------------------------------

def test_variance_is_accrued_minus_actual():
    accrued = [
        {"month": "2024-01-01", "accrued": 100000.0},
        {"month": "2024-02-01", "accrued": 120000.0},
    ]
    actual = [
        {"month": "2024-01-01", "actual": 40000.0},
        {"month": "2024-02-01", "actual": 130000.0},
    ]
    df = compute_accrual(_FakeConn(accrued, actual))

    row_jan = df[df["month"] == "2024-01-01"].iloc[0]
    row_feb = df[df["month"] == "2024-02-01"].iloc[0]
    assert row_jan["variance"] == pytest.approx(60000.0)   # under-billed
    assert row_feb["variance"] == pytest.approx(-10000.0)  # over-billed


def test_missing_actual_month_defaults_to_zero():
    accrued = [{"month": "2024-03-01", "accrued": 55000.0}]
    actual = []  # no deductions recorded that month
    df = compute_accrual(_FakeConn(accrued, actual))
    row = df.iloc[0]
    assert row["actual"] == pytest.approx(0.0)
    assert row["variance"] == pytest.approx(55000.0)


def test_only_last_twelve_months_are_kept():
    accrued = [
        {"month": f"2024-{m:02d}-01", "accrued": 1000.0 * m}
        for m in range(1, 13)
    ] + [{"month": "2025-01-01", "accrued": 99000.0}]  # 13 months
    actual = []
    df = compute_accrual(_FakeConn(accrued, actual))
    assert len(df) == 12
    # Oldest month dropped, newest retained.
    assert "2024-01-01" not in df["month"].values
    assert "2025-01-01" in df["month"].values


# ---------------------------------------------------------------------------
# CASE invariant — Move 5 must apply the same per-retailer rate as Move 1.
# This is the direct regression guard for the Kroger reconciliation bug.
# ---------------------------------------------------------------------------

def _case_rate_map(sql: str) -> dict[str, str]:
    """Extract the retailer -> rate-column mapping from a CASE block."""
    return {
        retailer: rate
        for retailer, rate in re.findall(
            r"WHEN\s+'([^']+)'\s+THEN\s+cr\.(rate_\w+)", sql
        )
    }


def _case_else_rate(sql: str) -> str:
    m = re.search(r"ELSE\s+cr\.(rate_\w+)", sql)
    assert m, "CASE block has no ELSE branch"
    return m.group(1)


def test_move5_case_matches_move1_case():
    """Every named retailer maps to the same rate column in both moves."""
    move1 = _case_rate_map(_REVENUE_SQL)
    move5 = _case_rate_map(_SQL_ACCRUED)
    assert move5 == move1, (
        f"Move 5 CASE diverges from Move 1: "
        f"only in Move 1={set(move1) - set(move5)}, "
        f"only in Move 5={set(move5) - set(move1)}"
    )
    assert _case_else_rate(_SQL_ACCRUED) == _case_else_rate(_REVENUE_SQL) == "rate_regional"


def test_move5_accrues_kroger_at_kroger_rate_not_regional():
    """Kroger must have its own branch, not fall through to rate_regional."""
    move5 = _case_rate_map(_SQL_ACCRUED)
    assert move5.get("Kroger") == "rate_kroger", (
        "Move 5 does not accrue Kroger at rate_kroger — it would fall to the "
        "regional rate and stop reconciling with Move 1"
    )
    # rate_kroger must actually be selected in channel_rates, not just referenced.
    assert "rate_kroger" in _SQL_ACCRUED
    assert "trade_spend_pct_kroger" in _SQL_ACCRUED


def test_all_named_retailers_have_own_rate_in_move5():
    move5 = _case_rate_map(_SQL_ACCRUED)
    assert _NAMED_RETAILERS.issubset(set(move5)), (
        f"Move 5 is missing rate branches for: {_NAMED_RETAILERS - set(move5)}"
    )


# ---------------------------------------------------------------------------
# Live reconciliation — Move 1 vs Move 5 on Kroger, against real data.
# ---------------------------------------------------------------------------

# Per-retailer accrual over Move 5's trailing-365-day window, using the same
# channel-rate CASE. Used only as the reconciliation oracle in the live test.
_SQL_ACCRUED_BY_RETAILER = """
WITH trailing_bounds AS (
    SELECT MAX(week_ending) - INTERVAL '365 days' AS start_week
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
revenue AS (
    SELECT st.chain_name AS retailer, SUM(sd.dollars_sold) AS gross
    FROM raw.scan_data sd
    JOIN raw.stores st ON sd.store_id = st.store_id
    WHERE sd.week_ending >= (SELECT start_week FROM trailing_bounds)
    GROUP BY st.chain_name
)
SELECT
    r.retailer,
    r.gross,
    (SELECT rate_kroger FROM channel_rates)   AS rate_kroger,
    (SELECT rate_regional FROM channel_rates) AS rate_regional,
    r.gross * CASE r.retailer
        WHEN 'Walmart'     THEN cr.rate_walmart
        WHEN 'Costco'      THEN cr.rate_costco
        WHEN 'Kroger'      THEN cr.rate_kroger
        WHEN 'Whole Foods' THEN cr.rate_whole_foods
        WHEN 'Sprouts'     THEN cr.rate_sprouts
        ELSE cr.rate_regional
    END AS accrued
FROM revenue r
CROSS JOIN channel_rates cr
"""


@_LIVE
def test_kroger_accrues_at_own_rate_card(live_conn):
    """Live: Move 5 accrues Kroger at rate_kroger, not the regional rate."""
    import psycopg2.extras

    with live_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_SQL_ACCRUED_BY_RETAILER)
        rows = {r["retailer"]: r for r in cur.fetchall()}

    assert "Kroger" in rows, "Kroger not present in scan data"
    k = rows["Kroger"]
    rate_kroger = float(k["rate_kroger"])
    rate_regional = float(k["rate_regional"])
    gross = float(k["gross"])
    accrued = float(k["accrued"])

    # The bug is only observable if the two rates actually differ.
    assert rate_kroger != pytest.approx(rate_regional), (
        "rate_kroger equals rate_regional in this data — test is vacuous"
    )
    assert accrued == pytest.approx(gross * rate_kroger, rel=1e-6), (
        "Kroger accrual does not use rate_kroger"
    )
    assert accrued != pytest.approx(gross * rate_regional, rel=1e-6), (
        "Kroger accrual matches the regional rate — the Move 5 bug is back"
    )


@_LIVE
def test_move1_and_move5_agree_on_kroger_rate(live_conn):
    """Live: the effective Kroger rate in Move 1 equals the one in Move 5."""
    import psycopg2.extras

    with live_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_REVENUE_SQL)
        move1 = {r["retailer"]: dict(r) for r in cur.fetchall()}
        cur.execute(_SQL_ACCRUED_BY_RETAILER)
        move5 = {r["retailer"]: dict(r) for r in cur.fetchall()}

    assert "Kroger" in move1 and "Kroger" in move5
    m1 = move1["Kroger"]
    m1_rate = float(m1["structural_trade_spend"]) / float(m1["gross_revenue"])
    m5 = move5["Kroger"]
    m5_rate = float(m5["accrued"]) / float(m5["gross"])
    assert m1_rate == pytest.approx(m5_rate, rel=1e-6), (
        f"Move 1 Kroger rate {m1_rate:.6f} != Move 5 Kroger rate {m5_rate:.6f}"
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_conn():
    from dotenv import load_dotenv
    load_dotenv()
    from pipeline.db import source_conn
    with source_conn() as conn:
        yield conn
