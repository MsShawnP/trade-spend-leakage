"""Results database reader — reads pre-computed output from data/results.db.

The pipeline writes results.db; the app reads it. This module never writes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DB = ROOT / "data" / "results.db"


def _connect() -> sqlite3.Connection:
    if not RESULTS_DB.exists():
        raise FileNotFoundError(
            f"results.db not found at {RESULTS_DB}. "
            "Run the pipeline first: python pipeline/run.py"
        )
    conn = sqlite3.connect(RESULTS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_net_revenue() -> pd.DataFrame:
    """Return results_net_revenue as a DataFrame, ordered by net_revenue DESC."""
    conn = _connect()
    try:
        return pd.read_sql_query(
            "SELECT * FROM results_net_revenue ORDER BY net_revenue DESC",
            conn,
        )
    finally:
        conn.close()
