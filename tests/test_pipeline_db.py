"""Tests for pipeline.db connection helpers."""

import os
import sqlite3
import pytest
import psycopg2.extras
from pathlib import Path


# ---------------------------------------------------------------------------
# source_conn — Postgres
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — skipping live Postgres test",
)
def test_source_conn_returns_valid_connection():
    from pipeline.db import source_conn
    with source_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS n FROM raw.scan_data")
            row = cur.fetchone()
    assert row["n"] > 0


def test_source_conn_missing_database_url_raises_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from pipeline.db import source_conn
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        with source_conn():
            pass


# ---------------------------------------------------------------------------
# results_conn — SQLite
# ---------------------------------------------------------------------------

def test_results_conn_creates_db_when_absent(tmp_path, monkeypatch):
    import pipeline.db as db_module
    target = tmp_path / "results.db"
    monkeypatch.setattr(db_module, "RESULTS_DB", target)
    with db_module.results_conn() as conn:
        conn.execute("CREATE TABLE smoke (id INTEGER PRIMARY KEY)")
    assert target.exists()


def test_results_conn_rollback_on_error(tmp_path, monkeypatch):
    import pipeline.db as db_module
    target = tmp_path / "results.db"
    monkeypatch.setattr(db_module, "RESULTS_DB", target)
    with pytest.raises(sqlite3.OperationalError):
        with db_module.results_conn() as conn:
            conn.execute("SELECT * FROM nonexistent_table")
    # DB file created but transaction rolled back — file exists, no table
    assert target.exists()
    conn2 = sqlite3.connect(target)
    tables = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn2.close()
    assert tables == []
