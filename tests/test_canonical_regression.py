"""
tests/test_canonical_regression.py -- Canonical regression tests for Cinderhaven baked data.

Validates that data/results.db (baked analytical output) and the upstream
cinderhaven_product_master.db contain expected baseline counts and structure.

Run:  pytest tests/test_canonical_regression.py -v
"""

import os
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DB = ROOT / "data" / "results.db"
UPSTREAM_DB = (
    ROOT / "data" / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _query_one(db_path: Path, sql: str):
    """Execute a query and return the single scalar result."""
    conn = sqlite3.connect(str(db_path))
    try:
        val = conn.execute(sql).fetchone()[0]
    finally:
        conn.close()
    return val


def _query_all(db_path: Path, sql: str):
    """Execute a query and return all rows."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql).fetchall()
    finally:
        conn.close()
    return rows


# ---------------------------------------------------------------------------
# 1. results.db exists and is a valid SQLite database
# ---------------------------------------------------------------------------

class TestResultsDB:

    def test_results_db_exists(self):
        assert RESULTS_DB.is_file(), f"results.db not found at {RESULTS_DB}"

    def test_results_db_is_valid_sqlite(self):
        """Opening and querying sqlite_master should succeed."""
        conn = sqlite3.connect(str(RESULTS_DB))
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            assert len(tables) > 0, "results.db has no tables"
        finally:
            conn.close()

    # 5. Smoke test: results.db has expected tables
    EXPECTED_TABLES = {
        "results_net_revenue",
        "results_trade_efficiency",
        "results_leakage_summary",
        "results_leakage_instances",
        "results_promo_roi",
        "results_accrual",
    }

    def test_results_db_expected_tables(self):
        tables = {
            row[0]
            for row in _query_all(
                RESULTS_DB,
                "SELECT name FROM sqlite_master WHERE type='table'",
            )
        }
        missing = self.EXPECTED_TABLES - tables
        assert not missing, f"Missing tables in results.db: {missing}"

    def test_results_db_tables_not_empty(self):
        """Every expected table should have at least one row."""
        for tbl in self.EXPECTED_TABLES:
            count = _query_one(RESULTS_DB, f"SELECT COUNT(*) FROM [{tbl}]")
            assert count > 0, f"Table {tbl} in results.db is empty"


# ---------------------------------------------------------------------------
# 2-4. Upstream cinderhaven_product_master.db
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not UPSTREAM_DB.is_file(),
    reason=f"Upstream DB not present at {UPSTREAM_DB} "
    "(cinderhaven-data submodule not checked out)",
)
class TestUpstreamDB:

    def test_upstream_db_exists(self):
        assert UPSTREAM_DB.is_file(), f"Upstream DB not found at {UPSTREAM_DB}"

    # 2. SKU count
    def test_sku_count_is_50(self):
        count = _query_one(UPSTREAM_DB, "SELECT COUNT(*) FROM product_master")
        assert count == 50, f"Expected 50 SKUs, got {count}"

    def test_distinct_sku_count_is_50(self):
        count = _query_one(
            UPSTREAM_DB, "SELECT COUNT(DISTINCT sku) FROM product_master"
        )
        assert count == 50, f"Expected 50 distinct SKUs, got {count}"

    # 3. Product line count
    def test_product_line_count(self):
        """Five product lines post re-export (Dried Goods and Snack Bites added)."""
        count = _query_one(
            UPSTREAM_DB,
            "SELECT COUNT(DISTINCT product_line) FROM product_master",
        )
        assert count == 5, f"Expected 5 product lines, got {count}"

    def test_known_product_lines_present(self):
        rows = _query_all(
            UPSTREAM_DB,
            "SELECT DISTINCT product_line FROM product_master ORDER BY product_line",
        )
        lines = {r[0] for r in rows}
        expected = {
            "Artisan Sauces",
            "Specialty Condiments",
            "Pantry Staples",
            "Dried Goods",
            "Snack Bites",
        }
        assert expected <= lines, f"Missing product lines: {expected - lines}"

    # 4. Distinct retailers -- Kroger and Sprouts separate, not collapsed
    def test_kroger_is_separate_retailer(self):
        count = _query_one(
            UPSTREAM_DB,
            "SELECT COUNT(*) FROM retailers WHERE retailer_id = 'kroger'",
        )
        assert count == 1, "Kroger should exist as a separate retailer"

    def test_sprouts_is_separate_retailer(self):
        count = _query_one(
            UPSTREAM_DB,
            "SELECT COUNT(*) FROM retailers WHERE retailer_id = 'sprouts'",
        )
        assert count == 1, "Sprouts should exist as a separate retailer"

    def test_kroger_not_collapsed_into_regional(self):
        """Kroger and Sprouts must not be merged into 'regional_group'."""
        rows = _query_all(
            UPSTREAM_DB,
            "SELECT retailer_id, name FROM retailers "
            "WHERE retailer_id IN ('kroger', 'sprouts', 'regional_group') "
            "ORDER BY retailer_id",
        )
        ids = [r[0] for r in rows]
        assert "kroger" in ids, "Kroger missing from retailers table"
        assert "sprouts" in ids, "Sprouts missing from retailers table"
        assert "regional_group" in ids, "Regional Group missing from retailers table"
        # All three should be distinct rows
        assert len(ids) == 3, (
            f"Expected 3 distinct rows (kroger, sprouts, regional_group), got {ids}"
        )

    def test_total_retailer_count(self):
        count = _query_one(UPSTREAM_DB, "SELECT COUNT(*) FROM retailers")
        assert count == 9, f"Expected 9 retailers, got {count}"
