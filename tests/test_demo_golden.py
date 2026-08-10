"""Demo golden lock — trade-spend-leakage.

Byte-locks the committed pipeline results (data/results.db) the Dash app and the
Excel workbook both read, and pins the headline figures: net revenue and the
four leakage types. If a SHA or a figure moves, STOP: a golden moved.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "results.db"

GOLDEN_DB_SHA256_PREFIX = "3631bbfe3bfba573"


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    yield c
    c.close()


def test_results_db_sha256():
    digest = hashlib.sha256(DB.read_bytes()).hexdigest()[:16]
    assert digest == GOLDEN_DB_SHA256_PREFIX, (
        f"results.db changed (sha256[:16] {digest} != golden {GOLDEN_DB_SHA256_PREFIX}) "
        "— a demo golden moved; STOP and report."
    )


def test_net_revenue_totals(conn):
    gross, net = conn.execute(
        "SELECT ROUND(SUM(gross_revenue),2), ROUND(SUM(net_revenue),2) FROM results_net_revenue"
    ).fetchone()
    assert gross == 32323139.62      # canonical retail scan CY2025
    assert net == 28861184.99


def test_leakage_summary(conn):
    rows = dict(conn.execute(
        "SELECT leakage_type, ROUND(dollar_total,2) FROM results_leakage_summary"
    ).fetchall())
    assert rows == {
        "unauthorized": 148467.30,
        "ghost_promo": 78402.39,
        "double_funded": 21184.33,
        "rate_discrepancy": 260.17,
    }
    total, instances = conn.execute(
        "SELECT ROUND(SUM(dollar_total),2), SUM(instance_count) FROM results_leakage_summary"
    ).fetchone()
    assert total == 248314.19
    assert instances == 2569


def test_workbook_build_is_deterministic():
    # The "Built <date>" stamp must not be wall-clock (it made the workbook
    # non-reproducible). generate_workbook takes an explicit built_date.
    import inspect
    from workbook import generator
    sig = inspect.signature(generator.generate_workbook)
    assert "built_date" in sig.parameters
    src = Path(ROOT / "workbook" / "tab_summary.py").read_text(encoding="utf-8")
    assert "date.today()" not in src
