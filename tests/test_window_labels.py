"""Trailing-window labels track the data, not a hardcoded span.

The Move 1 / Move 2 footnotes state a week span and the Move 5 footnote states a
month span. Before this guard those spans were literal text ("Trailing 52
weeks.", "trailing-12-month") that stayed put even if a reseed changed the
window — the exact silent-misstatement defect that motivated the trade-spend
warehouse_adapter fix. These tests assert each footnote is *derived* from the
pipeline output: the number moves with the data, and a stale span never survives.
"""

from __future__ import annotations

import pandas as pd
from dash import html

from app import layout
from app.db import get_accrual, get_net_revenue, get_net_revenue_window_weeks


def _footnote_texts(component) -> list[str]:
    """Return the text of every italic footnote (built by components.footnote) in a section."""
    out: list[str] = []

    def walk(node) -> None:
        children = getattr(node, "children", None)
        if isinstance(node, html.P) and (getattr(node, "style", {}) or {}).get("fontStyle") == "italic":
            if isinstance(children, str):
                out.append(children)
        if isinstance(children, (list, tuple)):
            for c in children:
                walk(c)
        elif children is not None and not isinstance(children, str):
            walk(children)

    walk(component)
    return out


def _net_revenue_footnote(weeks: int | None) -> str:
    section = layout._section_net_revenue(get_net_revenue(), weeks)
    return _footnote_texts(section)[0]


def _efficiency_footnote(weeks: int | None) -> str:
    # df content is irrelevant to the span; use an empty frame to avoid the chart path.
    section = layout._section_efficiency(pd.DataFrame(), weeks)
    return _footnote_texts(section)[0]


def _accrual_footnote(df: pd.DataFrame) -> str:
    section = layout._section_accrual(df)
    return _footnote_texts(section)[0]


# ---------------------------------------------------------------------------
# Week span — Move 1 (Net Revenue)
# ---------------------------------------------------------------------------

def test_net_revenue_footnote_reports_derived_week_span_when_weeks_provided():
    text = _net_revenue_footnote(weeks=40)
    assert "Trailing 40 weeks." in text
    assert "52 weeks" not in text  # the retired hardcode must not resurface


def test_net_revenue_footnote_omits_span_when_week_count_unavailable():
    # Missing window table (older/partial results.db) must not assert any span.
    text = _net_revenue_footnote(weeks=None)
    assert "weeks" not in text


# ---------------------------------------------------------------------------
# Week span — Move 2 (Efficiency), same source as Move 1
# ---------------------------------------------------------------------------

def test_efficiency_footnote_reports_derived_week_span_when_weeks_provided():
    text = _efficiency_footnote(weeks=40)
    assert "trailing 40 weeks," in text
    assert "52 weeks" not in text


def test_efficiency_footnote_matches_net_revenue_when_same_window():
    # Both footnotes read one window value, so they can never disagree.
    weeks = 37
    assert f"{weeks} weeks" in _net_revenue_footnote(weeks)
    assert f"{weeks} weeks" in _efficiency_footnote(weeks)


# ---------------------------------------------------------------------------
# Month span — Move 5 (Accrual), derived from the accrual row count
# ---------------------------------------------------------------------------

def test_accrual_footnote_reports_month_span_from_row_count():
    eight_months = get_accrual().head(8)
    text = _accrual_footnote(eight_months)
    assert "trailing-8-month" in text
    assert "12-month" not in text  # the retired hardcode must not resurface


def test_accrual_footnote_omits_month_span_when_no_data():
    text = _accrual_footnote(pd.DataFrame(columns=["month", "accrued", "actual", "variance"]))
    assert "-month" not in text


# ---------------------------------------------------------------------------
# Integration — the rendered spans equal the canonical baked data
# ---------------------------------------------------------------------------

def test_net_revenue_footnote_tracks_canonical_week_count():
    weeks = get_net_revenue_window_weeks()
    assert weeks == 52  # canonical Cinderhaven: CY2025 = 52 distinct scan weeks
    assert f"Trailing {weeks} weeks." in _net_revenue_footnote(weeks)


def test_accrual_footnote_tracks_canonical_month_count():
    df = get_accrual()
    assert len(df) == 12  # canonical Cinderhaven: 12 accrual months (CY2025)
    assert f"trailing-{len(df)}-month" in _accrual_footnote(df)
