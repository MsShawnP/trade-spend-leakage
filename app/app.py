"""Trade Spend Leakage Dashboard — Dash entry point."""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is on sys.path when launched as `python app/app.py`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import dash_bootstrap_components as dbc
from dash import Dash

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder=str(_ROOT / "assets"),
    suppress_callback_exceptions=True,
    title="Trade Spend Leakage",
    meta_tags=[
        {"name": "description", "content": "Forensic detection of double-funded promotions, phantom promos, and rate discrepancies. Retailers reranked by net revenue."},
        {"property": "og:title", "content": "Trade Spend Leakage"},
        {"property": "og:description", "content": "Forensic detection of double-funded promotions, phantom promos, and rate discrepancies. Retailers reranked by net revenue."},
        {"property": "og:type", "content": "website"},
        {"property": "og:url", "content": "https://trade-spend.lailarallc.com/"},
        {"property": "og:image", "content": "https://lailarallc.com/og/s/trade-spend.png"},
        {"property": "og:image:secure_url", "content": "https://lailarallc.com/og/s/trade-spend.png"},
        {"property": "og:image:type", "content": "image/png"},
        {"property": "og:image:width", "content": "1200"},
        {"property": "og:image:height", "content": "630"},
        {"property": "og:image:alt", "content": "Trade Spend Leakage"},
        {"name": "twitter:card", "content": "summary_large_image"},
        {"name": "twitter:image", "content": "https://lailarallc.com/og/s/trade-spend.png"},
    ],
)
server = app.server


@server.route("/health")
def health():
    from flask import jsonify
    return jsonify({"status": "ok"})


from app.layout import create_layout
from app.callbacks import register_callbacks

app.layout = create_layout()
register_callbacks(app)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=port)
