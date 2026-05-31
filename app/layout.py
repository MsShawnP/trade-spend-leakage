"""Dashboard layout — section-based, one section per analytical move.

U2 ships Move 1 (Net Revenue Ranking) only. Remaining move sections are
added in U3–U6.
"""

from __future__ import annotations

import pandas as pd
from dash import dcc, html

from app.charts import bump_chart
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
from app.db import get_net_revenue


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
# Public entry point
# ---------------------------------------------------------------------------

def create_layout() -> html.Div:
    """Return the full page layout. Loads results.db at startup."""
    try:
        df = get_net_revenue()
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "retailer", "gross_revenue", "trade_spend",
            "net_revenue", "net_to_gross_ratio",
        ])

    return html.Div([
        dcc.Store(id="bump-pin-store", data=None),
        html.Div([
            _brand_header(),
            _section_net_revenue(df),
        ], style={
            "maxWidth": CONTENT_MAX_WIDTH,
            "margin": "0 auto",
            "padding": "48px 24px",
            "fontFamily": FONT_SANS,
        }),
    ], style={"background": CANVAS, "minHeight": "100vh"})
