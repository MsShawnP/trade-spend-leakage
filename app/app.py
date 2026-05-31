"""Trade Spend Leakage Dashboard — Dash entry point."""

from __future__ import annotations

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


# Layout and callbacks registered when modules are available (U2+)
try:
    from app.layout import create_layout
    from app.callbacks import register_callbacks

    app.layout = create_layout()
    register_callbacks(app)
except ImportError:
    from dash import html
    app.layout = html.Div(
        "Dashboard loading...",
        style={"fontFamily": "sans-serif", "padding": "48px"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=8050)
