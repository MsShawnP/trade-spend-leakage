"""Project-wide constants for the Trade Spend Leakage dashboard."""

from __future__ import annotations

from lailara_palette import (
    LL_CANVAS,
    LL_CAT_10,
    LL_CHICAGO,
    LL_CHICAGO_HOVER,
    LL_CHICAGO_LIGHT,
    LL_DISABLED,
    LL_GRIDLINE,
    LL_HK,
    LL_HK_DARK,
    LL_HK_LIGHT,
    LL_INK,
    LL_RED,
    LL_REFERENCE,
    LL_SEQ,
    LL_SG,
    LL_TEXT,
    LL_TEXT_SEC,
    LL_TOKYO,
    LL_CARD_BG,
    LL_CARD_TEXT,
    LL_CARD_SUBTITLE,
    LL_CARD_MUTED,
    LL_CARD_BORDER,
    LL_CARD_ITEM,
    LL_HK_SURFACE,
    LL_SG_SURFACE,
    LL_RED_SURFACE,
    LL_CHICAGO_SURFACE,
)

# Lailara Design System v2 — color tokens (sourced from lailara_palette)
CANVAS = LL_CANVAS
INK = LL_INK
TEXT_PRIMARY = LL_TEXT
TEXT_SECONDARY = LL_TEXT_SEC
GRIDLINE = LL_GRIDLINE
REFERENCE = LL_REFERENCE
DISABLED = LL_DISABLED

NAVY = LL_CHICAGO
NAVY_HOVER = LL_CHICAGO_HOVER
NAVY_LIGHT = LL_CHICAGO_LIGHT

RED = LL_RED

# Hong Kong sequential teal (darkest -> lightest usable data stop)
HK = {
    5: LL_SEQ[0],
    15: LL_SEQ[1],
    25: LL_SEQ[2],
    35: LL_SEQ[3],
    45: LL_SEQ[4],
    55: LL_SEQ[5],
    70: LL_SEQ[6],
    85: LL_SEQ[7],
}
HK_DEFAULT = LL_HK

# Singapore orange (warning)
SG_DEFAULT = LL_SG

# Tokyo berry/rose (risk, negative)
TOKYO_DEFAULT = LL_TOKYO

# Semantic status
PASS_BG = LL_HK_SURFACE
PASS_TEXT = "#0e6e5a"
WARN_BG = LL_SG_SURFACE
WARN_TEXT = "#7a3d10"
FAIL_BG = LL_RED_SURFACE
FAIL_TEXT = "#7a0906"
INFO_BG = LL_CHICAGO_SURFACE
INFO_TEXT = NAVY

# Dark callout card
CARD_BG = LL_CARD_BG
CARD_TEXT = LL_CARD_TEXT
CARD_SUBTITLE = LL_CARD_SUBTITLE
CARD_MUTED = LL_CARD_MUTED
CARD_BORDER = LL_CARD_BORDER
CARD_ITEM_TEXT = LL_CARD_ITEM

# Layout
CONTENT_MAX_WIDTH = "900px"
SECTION_GAP = "60px"
BORDER_RADIUS = "2px"

# Categorical palette for charts — LL_CAT_10 paired system, first 6 slots
CATEGORICAL = LL_CAT_10[:6]

# Retailer slug -> display name mapping
RETAILER_DISPLAY = {
    "walmart": "Walmart",
    "costco": "Costco",
    "whole_foods": "Whole Foods",
    "unfi": "UNFI",
    "kehe": "KeHE",
    "dtc": "DTC",
    "green_basket": "Green Basket Market",
    "southside": "Southside Grocers",
    "fresh_mart": "Fresh Mart",
    "natural_harvest": "Natural Harvest",
    "regional": "Regional",
}

# Retailers that map to trade_spend_pct_regional in sku_costs
REGIONAL_RETAILERS = {
    "green_basket",
    "southside",
    "fresh_mart",
    "natural_harvest",
    "regional",
}

# Channel -> sku_costs column name
CHANNEL_RATE_COLS = {
    "walmart": "trade_spend_pct_walmart",
    "costco": "trade_spend_pct_costco",
    "whole_foods": "trade_spend_pct_whole_foods",
    "unfi": "trade_spend_pct_unfi",
    "dtc": "trade_spend_pct_dtc",
    "kehe": "trade_spend_pct_kehe",
    **{r: "trade_spend_pct_regional" for r in REGIONAL_RETAILERS},
}

APP_TITLE = "Trade Spend Leakage Analysis"
APP_SUBTITLE = "Cinderhaven Provisions · Lailara LLC"

# Typography
FONT_SERIF = "'Playfair Display', Georgia, 'Times New Roman', serif"
FONT_SANS = "'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif"
