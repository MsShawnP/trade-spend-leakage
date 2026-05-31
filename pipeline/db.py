"""SQLite connection helpers for the trade spend pipeline.

Two connections:
  source_conn() — read-only to cinderhaven_product_master.db (never write)
  results_conn() — read-write to data/results.db (pipeline output)
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DB = ROOT / "data" / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"
RESULTS_DB = ROOT / "data" / "results.db"


@contextmanager
def source_conn():
    """Read-only connection to the Cinderhaven source database.

    Raises FileNotFoundError if the database has not been initialised.
    Run `git submodule update --init` and copy cinderhaven_product_master.db
    into data/cinderhaven-data/data/ before using this.
    """
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Cinderhaven source database not found: {SOURCE_DB}\n"
            "Run: git submodule update --init\n"
            "Then copy cinderhaven_product_master.db into data/cinderhaven-data/data/"
        )
    conn = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def results_conn():
    """Read-write connection to results.db.  Creates the file if absent."""
    RESULTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(RESULTS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
