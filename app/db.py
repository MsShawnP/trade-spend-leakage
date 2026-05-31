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


def get_leakage_summary() -> pd.DataFrame:
    """Return results_leakage_summary (4 rows, one per sub-type)."""
    conn = _connect()
    try:
        return pd.read_sql_query(
            "SELECT * FROM results_leakage_summary",
            conn,
        )
    except Exception:
        return pd.DataFrame(columns=[
            "leakage_type", "display_name", "dollar_total",
            "instance_count", "classification",
        ])
    finally:
        conn.close()


def get_leakage_instances(leakage_type: str | None = None) -> pd.DataFrame:
    """Return results_leakage_instances, optionally filtered by leakage_type."""
    conn = _connect()
    try:
        if leakage_type:
            return pd.read_sql_query(
                "SELECT * FROM results_leakage_instances WHERE leakage_type = ? "
                "ORDER BY actual_amount DESC",
                conn,
                params=(leakage_type,),
            )
        return pd.read_sql_query(
            "SELECT * FROM results_leakage_instances ORDER BY actual_amount DESC",
            conn,
        )
    except Exception:
        return pd.DataFrame(columns=[
            "leakage_type", "deduction_id", "retailer_id", "promo_id",
            "period", "agreed_amount", "actual_amount", "variance", "classification",
        ])
    finally:
        conn.close()
