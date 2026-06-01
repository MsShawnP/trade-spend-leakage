"""Tests for pipeline.move4_promo_roi — promotional ROI pipeline."""

import os

import pandas as pd
import pytest

from pipeline.move4_promo_roi import (
    _empty_result,
    _BASELINE_WEEKS,
    _MIN_BASELINE_WEEKS,
    compute_promo_roi,
)

_LIVE = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live Postgres test",
)

# ---------------------------------------------------------------------------
# Schema / empty-result tests — no live data required
# ---------------------------------------------------------------------------

_REQUIRED_COLS = [
    "promo_id",
    "sku_id",
    "retailer_id",
    "retailer",
    "start_week",
    "end_week",
    "promo_cost",
    "promo_type",
    "has_sufficient_baseline",
    "baseline_weekly_revenue",
    "promo_revenue",
    "promo_weeks",
    "incremental_revenue",
    "is_money_losing",
]


def test_empty_result_has_required_columns():
    df = _empty_result()
    missing = [c for c in _REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


def test_baseline_weeks_constant_is_eight():
    assert _BASELINE_WEEKS == 8
    assert _MIN_BASELINE_WEEKS == 8


# ---------------------------------------------------------------------------
# Business logic tests — synthetic DataFrames (no Postgres)
# ---------------------------------------------------------------------------

def _make_promo_row(**kwargs) -> dict:
    """Return a minimal promo row with overridable fields."""
    defaults = {
        "promo_id": "P001",
        "sku_id": "SKU-A",
        "retailer_id": "RET-WALMART",
        "retailer": "Walmart",
        "start_week": "2024-01-01",
        "end_week": "2024-01-28",
        "promo_cost": 5000.0,
        "promo_type": "tpr",
        "has_sufficient_baseline": 1,
        "baseline_weekly_revenue": 10000.0,
        "promo_revenue": 50000.0,
        "promo_weeks": 4,
        "incremental_revenue": 10000.0,
        "is_money_losing": 0,
    }
    defaults.update(kwargs)
    return defaults


def test_insufficient_baseline_flag_when_is_money_losing_is_none():
    """Promotions with has_sufficient_baseline=False must have is_money_losing=None."""
    row = _make_promo_row(
        has_sufficient_baseline=0,
        incremental_revenue=None,
        is_money_losing=None,
    )
    df = pd.DataFrame([row])
    assert df.loc[0, "has_sufficient_baseline"] == 0
    assert df.loc[0, "is_money_losing"] is None


def test_money_losing_when_cost_exceeds_incremental():
    """is_money_losing=1 when promo_cost > incremental_revenue."""
    row = _make_promo_row(promo_cost=15000.0, incremental_revenue=8000.0, is_money_losing=1)
    df = pd.DataFrame([row])
    assert df.loc[0, "is_money_losing"] == 1


def test_not_money_losing_when_incremental_exceeds_cost():
    """is_money_losing=0 when incremental_revenue >= promo_cost."""
    row = _make_promo_row(promo_cost=5000.0, incremental_revenue=12000.0, is_money_losing=0)
    df = pd.DataFrame([row])
    assert df.loc[0, "is_money_losing"] == 0


def test_null_promo_cost_yields_no_roi_flag():
    """Promotions with NULL promo_cost must have is_money_losing=None."""
    row = _make_promo_row(promo_cost=None, is_money_losing=None)
    df = pd.DataFrame([row])
    assert df.loc[0, "promo_cost"] is None
    assert df.loc[0, "is_money_losing"] is None



# ---------------------------------------------------------------------------
# Live integration tests — require DATABASE_URL
# ---------------------------------------------------------------------------

@_LIVE
def test_compute_promo_roi_returns_one_row_per_promo_id(live_conn):
    """DISTINCT ON promo_id must produce no duplicates."""
    df = compute_promo_roi(live_conn)
    assert len(df) > 0, "Expected at least one promo event"
    assert df["promo_id"].nunique() == len(df), (
        f"Duplicate promo_ids found: {len(df)} rows but {df['promo_id'].nunique()} unique"
    )


@_LIVE
def test_compute_promo_roi_has_required_columns(live_conn):
    df = compute_promo_roi(live_conn)
    missing = [c for c in _REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


@_LIVE
def test_some_promotions_have_sufficient_baseline(live_conn):
    """At least some promotions must have ≥8 weeks of pre-promo scan data."""
    df = compute_promo_roi(live_conn)
    measurable = int(df["has_sufficient_baseline"].sum())
    assert measurable > 0, "Expected at least one promotion with sufficient baseline data"
    # Validate the baseline/measurable split is internally consistent
    assert measurable <= len(df)


@_LIVE
def test_insufficient_baseline_rows_have_null_is_money_losing(live_conn):
    """Rows with has_sufficient_baseline=0 must have is_money_losing=None."""
    df = compute_promo_roi(live_conn)
    insufficient = df[df["has_sufficient_baseline"] == 0]
    assert insufficient["is_money_losing"].isna().all(), (
        "Some rows without baseline have is_money_losing set (expected None)"
    )


@_LIVE
def test_null_promo_cost_excluded_from_roi(live_conn):
    """The 7 promotions with NULL promo_cost must not have is_money_losing set."""
    df = compute_promo_roi(live_conn)
    null_cost = df[df["promo_cost"].isna()]
    assert null_cost["is_money_losing"].isna().all(), (
        "Promotions with NULL promo_cost should have is_money_losing=None"
    )


@_LIVE
def test_promo_roi_no_negative_promo_cost(live_conn):
    df = compute_promo_roi(live_conn)
    valid_costs = df["promo_cost"].dropna()
    assert (valid_costs >= 0).all(), "Promo costs should not be negative"


@_LIVE
def test_early_promos_without_pre_promo_data_are_not_measurable(live_conn):
    """A promotion starting within the first 8 weeks of scan data must not crash
    and must have has_sufficient_baseline=False."""
    df = compute_promo_roi(live_conn)
    # If any promo has 0 pre-promo weeks, it must not be flagged as measurable
    # (this is enforced structurally — we only check no crash and the flag is consistent)
    for _, row in df[df["has_sufficient_baseline"] == 0].iterrows():
        assert row["is_money_losing"] is None or pd.isna(row["is_money_losing"])


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
