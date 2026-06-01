"""Tests for pipeline.move3_leakage — leakage detection functions."""

import os
import pytest

from pipeline.move3_leakage import (
    _INSTANCE_COLS,
    _empty_instances,
    detect_double_dips,
    detect_ghost_promos,
    detect_rate_discrepancies,
    detect_unauthorized,
    _build_summary,
)

_LIVE = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live Postgres test",
)


# ---------------------------------------------------------------------------
# Empty-result consistency — no live data required
# ---------------------------------------------------------------------------

def test_empty_instances_has_correct_columns():
    df = _empty_instances()
    assert list(df.columns) == _INSTANCE_COLS


def test_build_summary_from_empty_instances_returns_four_rows():
    df = _build_summary(_empty_instances())
    assert len(df) == 4
    assert set(df["leakage_type"]) == {
        "double_funded", "ghost_promo", "rate_discrepancy", "unauthorized"
    }


def test_build_summary_zero_dollars_when_no_instances():
    df = _build_summary(_empty_instances())
    assert (df["dollar_total"] == 0.0).all()
    assert (df["instance_count"] == 0).all()


# ---------------------------------------------------------------------------
# Column consistency — all detection functions return _INSTANCE_COLS
# ---------------------------------------------------------------------------

@_LIVE
def test_detect_double_dips_returns_instance_cols(live_conn):
    df = detect_double_dips(live_conn)
    assert list(df.columns) == _INSTANCE_COLS


@_LIVE
def test_detect_ghost_promos_returns_instance_cols(live_conn):
    df = detect_ghost_promos(live_conn)
    assert list(df.columns) == _INSTANCE_COLS


@_LIVE
def test_detect_rate_discrepancies_returns_instance_cols_even_if_empty(live_conn):
    df = detect_rate_discrepancies(live_conn)
    assert list(df.columns) == _INSTANCE_COLS


@_LIVE
def test_detect_unauthorized_returns_instance_cols(live_conn):
    df = detect_unauthorized(live_conn)
    assert list(df.columns) == _INSTANCE_COLS


# ---------------------------------------------------------------------------
# Happy-path counts against live data
# ---------------------------------------------------------------------------

@_LIVE
def test_detect_double_dips_returns_rows(live_conn):
    df = detect_double_dips(live_conn)
    assert len(df) > 0, "Expected double-dip instances — check raw.retailer_deductions + promotions"
    assert (df["leakage_type"] == "double_funded").all()
    assert (df["classification"] == "Recoverable").all()
    assert df["actual_amount"].gt(0).all()


@_LIVE
def test_detect_ghost_promos_returns_rows_and_is_reallocatable(live_conn):
    df = detect_ghost_promos(live_conn)
    assert len(df) > 0, "Expected ghost promo instances — check raw.retailer_deductions"
    assert (df["leakage_type"] == "ghost_promo").all()
    assert (df["classification"] == "Reallocatable").all()
    assert df["promo_id"].isna().all(), "Ghost promos should have no matching promo_id"


@_LIVE
def test_detect_rate_discrepancies_handles_zero_results_without_error(live_conn):
    df = detect_rate_discrepancies(live_conn)
    # Result may be 0 rows — that's valid. Just assert no exception and correct shape.
    assert list(df.columns) == _INSTANCE_COLS


@_LIVE
def test_detect_unauthorized_finds_pricing_error_type(live_conn):
    df = detect_unauthorized(live_conn)
    assert len(df) > 0, "Expected pricing_error deductions in unauthorized bucket"
    assert (df["leakage_type"] == "unauthorized").all()
    assert (df["classification"] == "Recoverable").all()


# ---------------------------------------------------------------------------
# Summary integration
# ---------------------------------------------------------------------------

@_LIVE
def test_summary_dollar_totals_match_instance_sums(live_conn):
    from pipeline.move3_leakage import _build_summary
    import pandas as pd
    dfs = [
        detect_double_dips(live_conn),
        detect_ghost_promos(live_conn),
        detect_rate_discrepancies(live_conn),
        detect_unauthorized(live_conn),
    ]
    instances = pd.concat(dfs, ignore_index=True)
    summary = _build_summary(instances)
    for _, row in summary.iterrows():
        sub = instances[instances["leakage_type"] == row["leakage_type"]]
        expected = float(sub["actual_amount"].sum())
        assert abs(row["dollar_total"] - expected) < 0.01, (
            f"{row['leakage_type']}: summary ${row['dollar_total']:.2f} "
            f"!= instance sum ${expected:.2f}"
        )


# ---------------------------------------------------------------------------
# Slug map coverage — guards against the retailer_id format mismatch bug
#
# See: docs/solutions/logic-errors/retailer-id-format-mismatch-join-produces-wrong-leakage-2026-06-01.md
# A new Cinderhaven retailer not added to _SLUG_MAP_CTE will silently produce
# 0 rows from detect_double_dips / detect_rate_discrepancies and inflate
# detect_ghost_promos (NOT EXISTS becomes always-true).
# ---------------------------------------------------------------------------

@_LIVE
def test_slug_map_covers_all_promotions_retailer_ids(live_conn):
    """All raw.promotions retailer_ids must appear in _SLUG_MAP_CTE promo side."""
    _MAPPED = {
        'RET-WALMART', 'RET-COSTCO', 'RET-KROGER',
        'RET-WHOLEFOODS', 'RET-SPROUTS', 'RET-REGIONAL',
    }
    with live_conn.cursor() as cur:
        cur.execute("SELECT DISTINCT retailer_id FROM raw.promotions ORDER BY retailer_id")
        live_ids = {row[0] for row in cur.fetchall()}

    unmapped = live_ids - _MAPPED
    assert not unmapped, (
        f"{sorted(unmapped)} in raw.promotions missing from _SLUG_MAP_CTE — "
        "add to pipeline/move3_leakage.py and pipeline/move2_efficiency.py"
    )


@_LIVE
def test_slug_map_covers_all_deductions_retailer_ids(live_conn):
    """All raw.retailer_deductions retailer_ids must appear in _SLUG_MAP_CTE deduction side."""
    _MAPPED = {'walmart', 'costco', 'kroger', 'whole_foods', 'sprouts', 'regional'}
    with live_conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT retailer_id FROM raw.retailer_deductions ORDER BY retailer_id"
        )
        live_ids = {row[0] for row in cur.fetchall()}

    unmapped = live_ids - _MAPPED
    assert not unmapped, (
        f"{sorted(unmapped)} in raw.retailer_deductions missing from _SLUG_MAP_CTE — "
        "add to pipeline/move3_leakage.py and pipeline/move2_efficiency.py"
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
