"""Tests for pipeline.db connection helpers."""

import sqlite3
import pytest
from pathlib import Path


def test_source_conn_returns_valid_connection():
    from pipeline.db import source_conn
    with source_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM scan_data").fetchone()
    assert row["n"] > 0


def test_source_conn_missing_db_raises_file_not_found(tmp_path, monkeypatch):
    import pipeline.db as db_module
    monkeypatch.setattr(db_module, "SOURCE_DB", tmp_path / "missing.db")
    with pytest.raises(FileNotFoundError, match="missing.db"):
        with db_module.source_conn():
            pass


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
