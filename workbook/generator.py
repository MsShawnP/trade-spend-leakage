"""Generate the trade spend leakage workbook and return it as bytes."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from openpyxl import Workbook

from workbook.styles import TAB_NAMES
from workbook.tab_accrual import build_accrual
from workbook.tab_efficiency import build_efficiency
from workbook.tab_leakage import build_leakage
from workbook.tab_net_revenue import build_net_revenue
from workbook.tab_promo_roi import build_promo_roi
from workbook.tab_summary import build_summary

# Tab colours: active analysis tabs get Chicago navy; supporting tabs get teal.
_TAB_COLORS = {
    "Summary": "1f2e7a",
    "Net Revenue Ranking": "1f2e7a",
    "Leakage Detection": "1f2e7a",
    "Trade Spend Efficiency": "1f2e7a",
    "Promotional ROI": "158f75",
    "Accrual Reconciliation": "158f75",
}

_TAB_BUILDERS = {
    "Summary": build_summary,
    "Net Revenue Ranking": build_net_revenue,
    "Leakage Detection": build_leakage,
    "Trade Spend Efficiency": build_efficiency,
    "Promotional ROI": build_promo_roi,
    "Accrual Reconciliation": build_accrual,
}


def generate_workbook(results_db_path: Path, built_date=None) -> bytes:
    """Build the six-sheet workbook and return its contents as bytes.

    If results.db is missing or a table hasn't been computed yet, affected
    sheets get a header row and a 'Not yet computed — run the pipeline first.'
    placeholder rather than raising an error.
    """
    wb = Workbook()
    wb.remove(wb.active)

    for name in TAB_NAMES:
        ws = wb.create_sheet(title=name)
        ws.sheet_properties.tabColor = _TAB_COLORS[name]
        _TAB_BUILDERS[name](ws, results_db_path, built_date)

    wb.active = 0

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
