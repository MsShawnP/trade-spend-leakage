"""Tests for pipeline.move1_net_revenue.

All tests require a live Postgres connection via DATABASE_URL — they skip
cleanly when it is absent rather than failing. The test CLAUDE.md
requires real synthetic data, not mocked inputs.
"""

import os
import pytest

skip_no_db = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live Postgres tests",
)


@skip_no_db
def test_compute_net_revenue_returns_expected_shape():
    from pipeline.db import source_conn
    from pipeline.move1_net_revenue import compute_net_revenue

    with source_conn() as conn:
        df = compute_net_revenue(conn)

    assert not df.empty, "Expected at least one retailer row"
    expected_cols = {"retailer", "gross_revenue", "trade_spend", "net_revenue", "net_to_gross_ratio"}
    assert expected_cols.issubset(set(df.columns)), f"Missing columns: {expected_cols - set(df.columns)}"
    # One row per distinct retailer (no duplicates)
    assert df["retailer"].nunique() == len(df), "Duplicate retailer rows found"


@skip_no_db
def test_net_rank_differs_from_gross_rank_for_at_least_one_retailer():
    """Trade spend should move at least one retailer's rank — that's the story."""
    from pipeline.db import source_conn
    from pipeline.move1_net_revenue import compute_net_revenue

    with source_conn() as conn:
        df = compute_net_revenue(conn)

    df["gross_rank"] = df["gross_revenue"].rank(ascending=False).astype(int)
    df["net_rank"] = df["net_revenue"].rank(ascending=False).astype(int)
    movers = (df["gross_rank"] != df["net_rank"]).sum()
    assert movers >= 1, "Expected at least one retailer to change rank — check trade rate data"


@skip_no_db
def test_dtc_net_revenue_equals_gross_revenue():
    """DTC has trade_spend_pct = 0, so net revenue must equal gross revenue."""
    from pipeline.db import source_conn
    from pipeline.move1_net_revenue import compute_net_revenue

    with source_conn() as conn:
        df = compute_net_revenue(conn)

    dtc = df[df["retailer"] == "DTC"]
    if dtc.empty:
        pytest.skip("DTC retailer not present in this dataset")

    row = dtc.iloc[0]
    assert abs(float(row["net_revenue"]) - float(row["gross_revenue"])) < 1.0, (
        f"DTC net_revenue ({row['net_revenue']:.2f}) should equal "
        f"gross_revenue ({row['gross_revenue']:.2f}) when trade rate is 0"
    )


@skip_no_db
def test_regional_chains_map_without_key_error():
    """Regional retailers (Green Basket, Southside, etc.) use trade_spend_pct_regional.

    The CASE ELSE branch handles them; this verifies no KeyError or NULL propagation
    results in a NaN net_revenue for those chains.
    """
    from pipeline.db import source_conn
    from pipeline.move1_net_revenue import compute_net_revenue

    with source_conn() as conn:
        df = compute_net_revenue(conn)

    regional_names = {"Green Basket Market", "Southside Grocers", "Fresh Mart", "Natural Harvest"}
    present = df[df["retailer"].isin(regional_names)]
    if present.empty:
        pytest.skip("No regional retailers found in this dataset")

    null_net = present["net_revenue"].isna().sum()
    assert null_net == 0, (
        f"{null_net} regional retailers have NULL net_revenue — "
        "check trade_spend_pct_regional column in sku_costs"
    )
