"""Project-wide constants for the Trade Spend Leakage dashboard."""

from __future__ import annotations

# Lailara Design System v2 — color tokens
CANVAS = "#f5f3ee"
INK = "#0d0d0d"
TEXT_PRIMARY = "#333333"
TEXT_SECONDARY = "#595959"
GRIDLINE = "#d9d9d9"
REFERENCE = "#666666"
DISABLED = "#b3b3b3"

NAVY = "#1f2e7a"
NAVY_HOVER = "#141e52"
NAVY_LIGHT = "#8e9ad0"

RED = "#cc100a"

# Hong Kong sequential teal (darkest → lightest usable data stop)
HK = {
    5: "#063d32",
    15: "#0a5c4b",
    25: "#0e6e5a",
    35: "#158f75",
    45: "#1fa282",
    55: "#35b595",
    70: "#6dcdb5",
    85: "#b5e4d8",
}
HK_DEFAULT = HK[35]

# Singapore orange (warning)
SG_DEFAULT = "#ee8a2a"

# Tokyo berry/rose (risk, negative)
TOKYO_DEFAULT = "#b82d4a"

# Semantic status
PASS_BG = "#e4f5f0"
PASS_TEXT = "#0e6e5a"
WARN_BG = "#fdeee0"
WARN_TEXT = "#7a3d10"
FAIL_BG = "#fde8e7"
FAIL_TEXT = "#7a0906"
INFO_BG = "#e5e8f5"
INFO_TEXT = NAVY

# Dark callout card
CARD_BG = "#1a1a1a"
CARD_TEXT = "#ffffff"
CARD_SUBTITLE = "#d8d8d8"
CARD_MUTED = "#9a9a9a"
CARD_BORDER = "rgba(255,255,255,0.12)"
CARD_ITEM_TEXT = "#ededed"

# Layout
CONTENT_MAX_WIDTH = "900px"
SECTION_GAP = "60px"
BORDER_RADIUS = "2px"

# Categorical palette for charts (retailers)
# Chicago navy + Hong Kong teal sequence, 11 slots for 11 retailers
CATEGORICAL = [
    NAVY,
    HK[35],
    HK[55],
    NAVY_LIGHT,
    HK[70],
    HK[25],
    HK[15],
    HK[45],
    HK[85],
    SG_DEFAULT,
    TOKYO_DEFAULT,
]

# Retailer slug → display name mapping
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

# Channel → sku_costs column name
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
