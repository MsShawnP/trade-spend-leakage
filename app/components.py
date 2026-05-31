"""Reusable UI component builders for the Trade Spend dashboard."""

from __future__ import annotations

import pandas as pd
from dash import html

from app.constants import (
    CARD_BG,
    CARD_BORDER,
    CARD_ITEM_TEXT,
    CARD_MUTED,
    CARD_SUBTITLE,
    CARD_TEXT,
    FONT_SANS,
    FONT_SERIF,
    GRIDLINE,
    TEXT_SECONDARY,
)


def _card_stat(label: str, value: str) -> html.Div:
    return html.Div([
        html.Div(label, style={
            "color": CARD_MUTED,
            "fontFamily": FONT_SANS,
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "marginBottom": "4px",
        }),
        html.Div(value, style={
            "color": CARD_ITEM_TEXT,
            "fontFamily": FONT_SANS,
            "fontSize": "16px",
            "fontWeight": "600",
        }),
    ])


def callout_card(row: pd.Series) -> html.Div:
    """Dark pinned callout card showing one retailer's net revenue breakdown."""
    gross = f"${row['gross_revenue']:,.0f}"
    trade = f"${row['trade_spend']:,.0f}"
    net = f"${row['net_revenue']:,.0f}"
    ratio = f"{float(row['net_to_gross_ratio']):.1%}"

    return html.Div([
        html.Div(str(row["retailer"]), style={
            "color": CARD_TEXT,
            "fontFamily": FONT_SERIF,
            "fontSize": "18px",
            "fontWeight": "700",
            "marginBottom": "12px",
        }),
        html.Div([
            _card_stat("Gross Revenue", gross),
            _card_stat("Trade Spend", trade),
            _card_stat("Net Revenue", net),
            _card_stat("Net-to-Gross", ratio),
        ], style={"display": "flex", "gap": "32px", "flexWrap": "wrap"}),
    ], style={
        "background": CARD_BG,
        "padding": "20px 24px",
        "borderRadius": "2px",
        "border": f"1px solid {CARD_BORDER}",
        "marginBottom": "12px",
    })


def footnote(text: str) -> html.P:
    """Small italic footnote below a chart section."""
    return html.P(text, style={
        "fontFamily": FONT_SANS,
        "fontSize": "11px",
        "fontStyle": "italic",
        "color": TEXT_SECONDARY,
        "marginTop": "8px",
        "borderTop": f"1px solid {GRIDLINE}",
        "paddingTop": "6px",
    })
