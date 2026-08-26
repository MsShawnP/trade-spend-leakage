"""Trailing-window spans read from results.db, for workbook labels.

The workbook tabs state a week/month window in their headers and notes. These
readers return the span the pipeline actually produced so the text tracks the
data instead of a hardcoded "52 weeks" / "12 months" that a reseed could
silently falsify — the same fix applied to the Dash demo footnotes. Each returns
None when the value is unavailable (missing table / older results.db) so the
caller omits the span rather than asserting a wrong one.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def read_trailing_weeks(db_path: Path) -> int | None:
    """Distinct-week count Move 1's trailing window spans (from results_net_revenue_window)."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT week_count FROM results_net_revenue_window LIMIT 1"
        ).fetchone()
        return int(row[0]) if row is not None else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def read_trailing_months(db_path: Path) -> int | None:
    """Number of monthly rows Move 5 produced (from results_accrual)."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM results_accrual").fetchone()
        count = int(row[0]) if row is not None else 0
        return count or None
    except sqlite3.Error:
        return None
    finally:
        conn.close()
