"""Tests for pipeline.move2_efficiency — trade spend efficiency pipeline.

Offline tests build a real SQLite results_net_revenue and a fake Postgres
source (no promo rows) so compute_efficiency runs without DATABASE_URL. The
key behavioural guard: trade_spend_pct is TOTAL trade spend (structural
rate-card spend + operational deductions) over gross revenue — not a
structural-only rate. The metric is labelled accordingly in the UI and
workbook; a benchmark against a structural-only average would be apples to
oranges.
"""

import os
import sqlite3

import pytest

from pipeline.move2_efficiency import (
    _SLUG_TO_DISPLAY,
    compute_efficiency,
)

_LIVE = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live Postgres test",
)


# ---------------------------------------------------------------------------
# Fake psycopg2 source returning no promo rows.
# ---------------------------------------------------------------------------

class _FakeCursor:
    def execute(self, sql):
        pass

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeSource:
    def cursor(self, cursor_factory=None):
        return _FakeCursor()


@pytest.fixture
def net_revenue_db(tmp_path):
    """results.db with a single Move 1 row for Kroger (total trade spend)."""
    path = tmp_path / "results.db"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE results_net_revenue (
            retailer TEXT, gross_revenue REAL, trade_spend REAL,
            net_revenue REAL, net_to_gross_ratio REAL
        )
        """
    )
    # Kroger: gross 6,660,048.33, total trade spend 723,912.413 (matches the
    # baked results.db). trade_spend here is structural + operational.
    conn.execute(
        "INSERT INTO results_net_revenue VALUES (?,?,?,?,?)",
        ("Kroger", 6660048.33, 723912.413, 5936135.917, 0.8913052312639),
    )
    conn.commit()
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# The metric is TOTAL trade spend / gross, not structural-only.
# ---------------------------------------------------------------------------

def test_trade_spend_pct_is_total_trade_spend_over_gross(net_revenue_db):
    df = compute_efficiency(_FakeSource(), net_revenue_db)
    row = df[df["retailer"] == "Kroger"].iloc[0]
    expected = row["trade_spend"] / row["gross_revenue"]
    assert row["trade_spend_pct"] == pytest.approx(expected)
    # And that total trade spend is exactly what Move 1 wrote (not a subset).
    assert row["trade_spend"] == pytest.approx(723912.413)


def test_efficiency_has_expected_columns(net_revenue_db):
    df = compute_efficiency(_FakeSource(), net_revenue_db)
    expected = {
        "retailer", "trade_spend_pct", "trade_spend", "gross_revenue",
        "total_promo_cost", "promo_period_revenue", "revenue_per_promo_dollar",
        "lift_measurable",
    }
    assert expected.issubset(set(df.columns))


def test_lift_not_measurable_without_promo_data(net_revenue_db):
    df = compute_efficiency(_FakeSource(), net_revenue_db)
    row = df[df["retailer"] == "Kroger"].iloc[0]
    assert int(row["lift_measurable"]) == 0


def test_empty_net_revenue_raises(tmp_path):
    path = tmp_path / "empty.db"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE results_net_revenue (
            retailer TEXT, gross_revenue REAL, trade_spend REAL,
            net_revenue REAL, net_to_gross_ratio REAL
        )
        """
    )
    conn.commit()
    with pytest.raises(ValueError, match="results_net_revenue is empty"):
        compute_efficiency(_FakeSource(), conn)
    conn.close()


# ---------------------------------------------------------------------------
# Slug mapping — Kroger is a first-class retailer, not folded into regional.
# ---------------------------------------------------------------------------

def test_kroger_slug_maps_to_display_name():
    assert _SLUG_TO_DISPLAY["RET-KROGER"] == "Kroger"


def test_regional_is_distinct_from_named_retailers():
    assert _SLUG_TO_DISPLAY["RET-REGIONAL"] == "Regional Group"
    named = {"Walmart", "Costco", "Kroger", "Whole Foods", "Sprouts"}
    assert named.issubset(set(_SLUG_TO_DISPLAY.values()))


# ---------------------------------------------------------------------------
# Live integration
# ---------------------------------------------------------------------------

@_LIVE
def test_compute_efficiency_shape_live(live_conn, results_db_conn):
    df = compute_efficiency(live_conn, results_db_conn)
    assert not df.empty
    assert (df["trade_spend_pct"] >= 0).all()
    # trade_spend_pct must equal total trade_spend / gross for every retailer.
    recomputed = df["trade_spend"] / df["gross_revenue"]
    assert (df["trade_spend_pct"] - recomputed).abs().max() < 1e-9


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


@pytest.fixture(scope="module")
def results_db_conn():
    from pipeline.db import results_conn
    with results_conn() as conn:
        yield conn
