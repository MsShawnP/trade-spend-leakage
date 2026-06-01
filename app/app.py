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
    suppress_callback_exceptions=True,
    title="Trade Spend Leakage",
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
