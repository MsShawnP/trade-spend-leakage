"""Dashboard layout — section-based, one section per analytical move."""

from __future__ import annotations

import pandas as pd
from dash import dcc, html

from app.charts import accrual_chart, bump_chart, efficiency_chart, leakage_ledger, promo_roi_chart
from app.components import footnote
from app.constants import (
    APP_SUBTITLE,
    APP_TITLE,
    CANVAS,
    CONTENT_MAX_WIDTH,
    FONT_SANS,
    FONT_SERIF,
    GRIDLINE,
    INK,
    NAVY,
    RED,
    SECTION_GAP,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from app.db import get_accrual, get_net_revenue, get_leakage_summary, get_trade_efficiency, get_promo_roi


# ---------------------------------------------------------------------------
# Brand header
# ---------------------------------------------------------------------------

def _brand_header() -> html.Div:
    return html.Div([
        html.Div([
            html.Span("Cinderhaven", style={
                "fontFamily": FONT_SERIF,
                "fontSize": "26px",
                "fontWeight": "700",
                "color": INK,
                "letterSpacing": "-0.01em",
            }),
            html.Span("  PROVISIONS", style={
                "fontFamily": FONT_SANS,
                "fontSize": "15px",
                "fontWeight": "400",
                "color": TEXT_SECONDARY,
                "textTransform": "uppercase",
                "letterSpacing": "0.04em",
                "marginLeft": "10px",
            }),
        ]),
        html.Div(APP_TITLE, style={
            "fontFamily": FONT_SERIF,
            "fontSize": "22px",
            "fontWeight": "700",
            "color": INK,
            "marginTop": "6px",
        }),
        html.Div(APP_SUBTITLE, style={
            "fontFamily": FONT_SANS,
            "fontSize": "14px",
            "color": TEXT_SECONDARY,
            "marginTop": "2px",
        }),
        html.Hr(style={"borderTop": f"1px solid {GRIDLINE}", "marginTop": "20px"}),
    ], style={"marginBottom": "40px"})


# ---------------------------------------------------------------------------
# Move 1 — Net Revenue Ranking
# ---------------------------------------------------------------------------

def _section_net_revenue(df: pd.DataFrame) -> html.Div:
    initial_fig = bump_chart(df)

    return html.Div([
        html.Div([
            html.Span("01", style={
                "fontFamily": FONT_SANS,
                "fontSize": "12px",
                "fontWeight": "500",
                "color": RED,
                "letterSpacing": "0.06em",
                "marginRight": "10px",
            }),
            html.Span("Net Revenue Ranking", style={
                "fontFamily": FONT_SERIF,
                "fontSize": "22px",
                "fontWeight": "700",
                "color": INK,
            }),
        ], style={"marginBottom": "10px"}),

        html.P(
            "Trade spend changes the revenue story. Retailers that appear "
            "largest by gross revenue may fall significantly when structural "
            "channel discounts are applied. The lines that cross tell the story.",
            style={
                "fontFamily": FONT_SANS,
                "fontSize": "17px",
                "color": TEXT_PRIMARY,
                "lineHeight": "1.6",
                "maxWidth": "660px",
                "marginBottom": "20px",
            },
        ),

        # Pinned callout card (hidden until a retailer is clicked)
        html.Div(id="bump-callout", style={"display": "none"}),

        dcc.Graph(
            id="bump-chart",
            figure=initial_fig,
            config={"displayModeBar": False},
            style={"marginLeft": "-8px"},
        ),

        footnote(
            "Structural trade spend rate applied per channel from negotiated rate card in sku_costs. "
            "Regional chains (Green Basket Market, Southside Grocers, Fresh Mart, Natural Harvest) "
            "use a blended regional rate. Trailing 52 weeks of scan data."
        ),
    ], id="section-net-revenue", style={"marginBottom": SECTION_GAP})


# ---------------------------------------------------------------------------
# Move 2 — Trade Spend Efficiency
# ---------------------------------------------------------------------------

def _section_efficiency(df: pd.DataFrame) -> html.Div:
    fig = efficiency_chart(df) if not df.empty else None

    chart_content: list = []
    if fig is not None:
        chart_content.append(dcc.Graph(
            id="efficiency-chart",
            figure=fig,
            config={"displayModeBar": False},
        ))
    else:
        chart_content.append(html.P(
            "No efficiency data — run the pipeline first: python pipeline/run.py --moves 2",
            style={"fontFamily": FONT_SANS, "fontSize": "14px", "color": TEXT_SECONDARY},
        ))

    return html.Div([
        html.Div([
            html.Span("02", style={
                "fontFamily": FONT_SANS,
                "fontSize": "12px",
                "fontWeight": "500",
                "color": RED,
                "letterSpacing": "0.06em",
                "marginRight": "10px",
            }),
            html.Span("Trade Spend Efficiency", style={
                "fontFamily": FONT_SERIF,
                "fontSize": "22px",
                "fontWeight": "700",
                "color": INK,
            }),
        ], style={"marginBottom": "10px"}),

        html.P(
            "Not all trade spend is equally productive. The left panel shows "
            "each retailer's structural trade rate — the share of gross revenue "
            "consumed before a dollar reaches the bottom line. Orange bars exceed "
            "the 17% specialty food average. The right panel shows revenue generated "
            "per promotional dollar invested during promotional periods.",
            style={
                "fontFamily": FONT_SANS,
                "fontSize": "17px",
                "color": TEXT_PRIMARY,
                "lineHeight": "1.6",
                "maxWidth": "660px",
                "marginBottom": "20px",
            },
        ),

        *chart_content,

        footnote(
            "Trade spend % from structural rate card in sku_costs, trailing 52 weeks. "
            "Revenue per promo dollar: total scan revenue across all stores during "
            "promotional periods ÷ total promo cost. Overlapping promo weeks are "
            "counted once. Does not adjust for baseline — see Move 4 for incremental lift. "
            "Dashed reference line at 17% (specialty food structural average)."
        ),
    ], id="section-efficiency", style={"marginBottom": SECTION_GAP})


# ---------------------------------------------------------------------------
# Move 3 — Leakage Detection
# ---------------------------------------------------------------------------

def _section_leakage(df_summary: pd.DataFrame) -> html.Div:
    ledger = leakage_ledger(df_summary)

    return html.Div([
        html.Div([
            html.Span("03", style={
                "fontFamily": FONT_SANS,
                "fontSize": "12px",
                "fontWeight": "500",
                "color": RED,
                "letterSpacing": "0.06em",
                "marginRight": "10px",
            }),
            html.Span("Leakage Detection", style={
                "fontFamily": FONT_SERIF,
                "fontSize": "22px",
                "fontWeight": "700",
                "color": INK,
            }),
        ], style={"marginBottom": "10px"}),

        html.P(
            "Not all trade spend is intentional. This ledger surfaces "
            "four types of leakage: promotions funded twice, billbacks "
            "with no matching promotion on record, deductions that exceed "
            "agreed rates, and charges outside the known operational set. "
            "Click a row to see the individual incidents.",
            style={
                "fontFamily": FONT_SANS,
                "fontSize": "17px",
                "color": TEXT_PRIMARY,
                "lineHeight": "1.6",
                "maxWidth": "660px",
                "marginBottom": "20px",
            },
        ),

        # Leakage summary ledger (4 rows + total)
        html.Div(id="leakage-ledger-container", children=ledger),

        # Instance drill-down — hidden until a row is clicked
        html.Div(id="leakage-instances-container", style={"marginTop": "20px"}),

        footnote(
            "Double-funded: promo_billback deductions matched to an off-invoice promotion "
            "(discount already embedded in invoice price). Ghost: promo_billback with no "
            "matching promotion record within ±14 days. Rate discrepancy: billback exceeds "
            "agreed promo_cost by >5%. Unauthorized: deduction types outside the known "
            "operational set."
        ),
    ], id="section-leakage", style={"marginBottom": SECTION_GAP})


# ---------------------------------------------------------------------------
# Move 4 — Promotional ROI
# ---------------------------------------------------------------------------

def _section_promo_roi(df: pd.DataFrame) -> html.Div:
    fig = promo_roi_chart(df) if not df.empty else None

    chart_content: list = []
    if fig is not None:
        chart_content.extend([
            # Pinned callout card (hidden until a point is clicked)
            html.Div(id="promo-roi-callout", style={"display": "none"}),
            dcc.Graph(
                id="promo-roi-chart",
                figure=fig,
                config={"displayModeBar": False},
            ),
        ])
    else:
        chart_content.append(html.P(
            "No promo ROI data — run the pipeline first: python pipeline/run.py --moves 4",
            style={"fontFamily": FONT_SANS, "fontSize": "14px", "color": TEXT_SECONDARY},
        ))

    measurable = int(df["has_sufficient_baseline"].sum()) if not df.empty else 0
    total = len(df) if not df.empty else 0

    return html.Div([
        html.Div([
            html.Span("04", style={
                "fontFamily": FONT_SANS,
                "fontSize": "12px",
                "fontWeight": "500",
                "color": RED,
                "letterSpacing": "0.06em",
                "marginRight": "10px",
            }),
            html.Span("Promotional ROI", style={
                "fontFamily": FONT_SERIF,
                "fontSize": "22px",
                "fontWeight": "700",
                "color": INK,
            }),
        ], style={"marginBottom": "10px"}),

        html.P(
            "Promotions above the break-even line returned more in scan revenue "
            "than they cost. Promotions below the line lost money — candidates "
            "for reallocation into higher-performing events. Click a point to see "
            "the detail.",
            style={
                "fontFamily": FONT_SANS,
                "fontSize": "17px",
                "color": TEXT_PRIMARY,
                "lineHeight": "1.6",
                "maxWidth": "660px",
                "marginBottom": "20px",
            },
        ),

        *chart_content,

        footnote(
            f"Baseline estimated from 8-week rolling median of weekly scan revenue "
            f"for the promoted SKU × retailer. {measurable} of {total} promotions "
            f"have sufficient pre-promotion data. Incremental revenue = promo-period "
            f"scan revenue minus expected baseline. Break-even line: promo cost = "
            f"incremental revenue. Gray points lack sufficient baseline data."
        ),
    ], id="section-promo-roi", style={"marginBottom": SECTION_GAP})


# ---------------------------------------------------------------------------
# Move 5 — Accrual Reconciliation
# ---------------------------------------------------------------------------

def _section_accrual(df: pd.DataFrame) -> html.Div:
    fig = accrual_chart(df) if not df.empty else None

    chart_content: list = []
    if fig is not None:
        chart_content.append(dcc.Graph(
            id="accrual-chart",
            figure=fig,
            config={"displayModeBar": False},
        ))
    else:
        chart_content.append(html.P(
            "No accrual data — run the pipeline first: python pipeline/run.py --moves 5",
            style={"fontFamily": FONT_SANS, "fontSize": "14px", "color": TEXT_SECONDARY},
        ))

    return html.Div([
        html.Div([
            html.Span("05", style={
                "fontFamily": FONT_SANS,
                "fontSize": "12px",
                "fontWeight": "500",
                "color": RED,
                "letterSpacing": "0.06em",
                "marginRight": "10px",
            }),
            html.Span("Accrual Reconciliation", style={
                "fontFamily": FONT_SERIF,
                "fontSize": "22px",
                "fontWeight": "700",
                "color": INK,
            }),
        ], style={"marginBottom": "10px"}),

        html.P(
            "Each month, the rate card implies a specific trade spend accrual. "
            "This chart compares that expected amount against what retailers "
            "actually deducted. A persistent gap — in either direction — signals "
            "a mismatch between contracted terms and execution.",
            style={
                "fontFamily": FONT_SANS,
                "fontSize": "17px",
                "color": TEXT_PRIMARY,
                "lineHeight": "1.6",
                "maxWidth": "660px",
                "marginBottom": "20px",
            },
        ),

        *chart_content,

        footnote(
            "Accrued trade spend: trailing-12-month scan revenue × structural "
            "rate card per channel (sku_costs). Actual: all deductions recorded in "
            "retailer_deductions, grouped by month. Positive variance = accrued "
            "more than was taken (under-billed). Dashed line shows monthly variance "
            "on secondary axis."
        ),
    ], id="section-accrual", style={"marginBottom": SECTION_GAP})


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def create_layout() -> html.Div:
    """Return the full page layout. Loads results.db at startup."""
    _EMPTY_NET = pd.DataFrame(columns=[
        "retailer", "gross_revenue", "trade_spend", "net_revenue", "net_to_gross_ratio",
    ])
    _EMPTY_EFFICIENCY = pd.DataFrame(columns=[
        "retailer", "trade_spend_pct", "trade_spend", "gross_revenue",
        "total_promo_cost", "promo_period_revenue", "revenue_per_promo_dollar",
        "lift_measurable",
    ])
    _EMPTY_LEAKAGE = pd.DataFrame(columns=[
        "leakage_type", "display_name", "dollar_total", "instance_count", "classification",
    ])
    _EMPTY_PROMO_ROI = pd.DataFrame(columns=[
        "promo_id", "sku_id", "retailer_id", "retailer",
        "start_week", "end_week", "promo_cost", "promo_type",
        "has_sufficient_baseline", "baseline_weekly_revenue",
        "promo_revenue", "promo_weeks", "incremental_revenue",
        "incremental_margin", "is_money_losing",
    ])
    _EMPTY_ACCRUAL = pd.DataFrame(columns=["month", "accrued", "actual", "variance"])

    try:
        df_net = get_net_revenue()
    except FileNotFoundError:
        df_net = _EMPTY_NET

    df_efficiency = get_trade_efficiency()
    if df_efficiency.empty:
        df_efficiency = _EMPTY_EFFICIENCY

    df_leakage = get_leakage_summary()
    if df_leakage.empty:
        df_leakage = _EMPTY_LEAKAGE

    df_promo_roi = get_promo_roi()
    if df_promo_roi.empty:
        df_promo_roi = _EMPTY_PROMO_ROI

    df_accrual = get_accrual()
    if df_accrual.empty:
        df_accrual = _EMPTY_ACCRUAL

    return html.Div([
        dcc.Store(id="bump-pin-store", data=None),
        dcc.Store(id="leakage-pin-store", data=None),
        dcc.Store(id="promo-roi-pin-store", data=None),
        html.Div([
            _brand_header(),
            _section_net_revenue(df_net),
            _section_efficiency(df_efficiency),
            _section_leakage(df_leakage),
            _section_promo_roi(df_promo_roi),
            _section_accrual(df_accrual),
        ], style={
            "maxWidth": CONTENT_MAX_WIDTH,
            "margin": "0 auto",
            "padding": "48px 24px",
            "fontFamily": FONT_SANS,
        }),
    ], style={"background": CANVAS, "minHeight": "100vh"})
