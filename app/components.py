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


def promo_callout_card(row: pd.Series) -> html.Div:
    """Dark pinned callout card showing one promotion's ROI breakdown."""
    cost_str = f"${float(row['promo_cost']):,.0f}" if pd.notna(row.get("promo_cost")) else "N/A"
    has_baseline = bool(row.get("has_sufficient_baseline", 0))

    if has_baseline and pd.notna(row.get("incremental_revenue")):
        incr = float(row["incremental_revenue"])
        cost = float(row["promo_cost"]) if pd.notna(row.get("promo_cost")) else None
        incr_str = f"${incr:,.0f}"
        roi_str = (
            f"{((incr - cost) / cost * 100):+.1f}%"
            if cost and cost != 0
            else "N/A"
        )
    else:
        incr_str = "Insufficient data"
        roi_str = "N/A"

    heading = f"{row['promo_id']}"
    sub = f"{row.get('sku_id', '')}  ·  {row.get('retailer', '')}  ·  {row.get('promo_type', '')}"

    return html.Div([
        html.Div(heading, style={
            "color": CARD_TEXT,
            "fontFamily": FONT_SERIF,
            "fontSize": "18px",
            "fontWeight": "700",
            "marginBottom": "4px",
        }),
        html.Div(sub, style={
            "color": CARD_SUBTITLE,
            "fontFamily": FONT_SANS,
            "fontSize": "13px",
            "marginBottom": "14px",
        }),
        html.Div([
            _card_stat("Promo Cost", cost_str),
            _card_stat("Incremental Rev", incr_str),
            _card_stat("ROI", roi_str),
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
