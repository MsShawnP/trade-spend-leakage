"""Client-mode tests for trade-spend-leakage.

Adversarial fixtures per checklist §6: clean run, LONG rate card discrepancy
flagging, no-rate-card disclosure, missing required column (blocked), duplicate
retailer, empty file, and the --final watermark. Fictional-placeholder identity.

Skipped if lailara_engagement isn't installed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("lailara_engagement")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client_mode  # noqa: E402

from lailara_engagement.errors import ReadError  # noqa: E402

_CONFIG = """
client: {name: Meridian Farms}
engagement: {id: MER-2026-08}
as_of_date: "2026-01-31"
demo: true
basis: {window_label: CY2025}
columns: {retailer: retailer, gross_revenue: gross_revenue, trade_spend: trade_spend}
"""

_LEDGER = (
    "retailer,gross_revenue,trade_spend\n"
    "Harborline Markets,1000000,120000\n"     # eff rate 12%
    "Cedarwood Foods,500000,50000\n"          # eff rate 10%
)

# Long rate card: retailer, rate, effective_date (a superseded + current row).
_RATE_CARD = (
    "retailer,rate,effective_date\n"
    "Harborline Markets,0.08,2023-01-01\n"
    "Harborline Markets,0.10,2025-01-01\n"    # current (<= as_of 2026-01-31) -> 10%
    "Cedarwood Foods,0.10,2024-01-01\n"
)


def _cfg(tmp_path):
    p = tmp_path / "engagement.yml"
    p.write_text(_CONFIG, encoding="utf-8")
    return str(p)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_clean_run_no_rate_card(tmp_path):
    src = _write(tmp_path, "l.csv", _LEDGER)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "ok"
    assert result["net_revenue"] == 1330000.0        # (1000000-120000)+(500000-50000)
    s = json.load(open(result["summary_json"], encoding="utf-8"))
    assert s["rate_card_provided"] is False
    assert "rate card" in open(result["report"], encoding="utf-8").read().lower()


def test_long_rate_card_flags_discrepancy(tmp_path):
    src = _write(tmp_path, "l.csv", _LEDGER)
    rc = _write(tmp_path, "rc.csv", _RATE_CARD)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"), rate_card_path=rc)
    assert result["status"] == "ok"
    s = json.load(open(result["summary_json"], encoding="utf-8"))
    by = {r["retailer"]: r for r in s["retailers"]}
    # Harborline effective 12% vs carded 10% (latest <= as_of) -> +2.0 pts, flagged
    assert by["Harborline Markets"]["carded_rate"] == 0.10
    assert by["Harborline Markets"]["rate_gap_pts"] == 2.0
    assert by["Harborline Markets"]["flagged"] is True
    # Cedarwood effective 10% == carded 10% -> not flagged
    assert by["Cedarwood Foods"]["flagged"] is False
    assert result["discrepancies"] == 1


def test_window_label_and_as_of_track_config_not_hardcoded(tmp_path):
    """The rendered window label and as-of date must come from config
    (basis.window_label / as_of_date), not a hardcoded default. The suite
    asserted net revenue and rate-gap flags but never the window/as-of text — a
    hardcoded window matching the demo would pass, the gap that let trade-spend's
    own Dash dashboard hardcode 'Trailing 52 weeks' (recorded as a dormant defect
    in DECISIONS.md).

    Both halves: feed a distinctive window_label + as_of and assert they render,
    AND assert the demo defaults are absent."""
    cfg = tmp_path / "engagement.yml"
    cfg.write_text(_CONFIG.replace("window_label: CY2025", "window_label: FY2099-pilot")
                          .replace('as_of_date: "2026-01-31"', 'as_of_date: "2099-09-09"'),
                   encoding="utf-8")
    src = _write(tmp_path, "l.csv", _LEDGER)
    result = client_mode.run(str(cfg), src, str(tmp_path / "out"))
    assert result["status"] == "ok"
    html = open(result["report"], encoding="utf-8").read()
    assert "FY2099-pilot" in html and "2099-09-09" in html
    assert "CY2025" not in html and "2026-01-31" not in html   # demo defaults must not survive


def test_missing_required_column_blocks(tmp_path):
    src = _write(tmp_path, "bad.csv", "retailer,gross_revenue\nA,100\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "blocked"
    assert "trade_spend" in open(result["readiness_report"], encoding="utf-8").read().lower()


def test_duplicate_retailer_blocks(tmp_path):
    src = _write(tmp_path, "dup.csv",
                 "retailer,gross_revenue,trade_spend\nA,100,10\nA,200,20\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "blocked"
    assert "duplicat" in open(result["readiness_report"], encoding="utf-8").read().lower()


def test_empty_file_raises(tmp_path):
    src = _write(tmp_path, "e.csv", "")
    with pytest.raises(ReadError):
        client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))


def test_final_drops_watermark(tmp_path):
    src = _write(tmp_path, "l.csv", _LEDGER)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"), final=True)
    assert "ll-draft" not in open(result["report"], encoding="utf-8").read()
