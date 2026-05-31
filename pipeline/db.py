"""Connection helpers for the trade spend pipeline.

Two connections:
  source_conn() — read-only to Cinderhaven Postgres on Fly.io (never write)
  results_conn() — read-write to data/results.db (pipeline output)
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DB = ROOT / "data" / "results.db"


@contextmanager
def source_conn():
    """Read-only connection to the Cinderhaven Postgres database on Fly.io.

    Requires DATABASE_URL env var set to the cinderhaven-data-platform
    connection string.  Raises RuntimeError if DATABASE_URL is not set.
    Never writes — callers must not issue DML.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set.\n"
            "Export the Fly.io Postgres connection string before running the pipeline:\n"
            "  $env:DATABASE_URL = 'postgresql://user:pass@host:port/db'  # PowerShell\n"
            "  export DATABASE_URL=postgresql://user:pass@host:port/db    # bash"
        )
    conn = psycopg2.connect(database_url)
    conn.set_session(readonly=True, autocommit=True)
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
