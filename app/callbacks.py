"""Dash callbacks — all callbacks registered via register_callbacks(app)."""

from __future__ import annotations

from dash import Input, Output, State

from app.charts import bump_chart
from app.components import callout_card
from app.db import get_net_revenue


def register_callbacks(app) -> None:
    """Register every callback on *app*."""

    # ----------------------------------------------------------
    # a) Bump chart click → update pin store
    #    Second click on the same retailer clears the pin.
    # ----------------------------------------------------------
    @app.callback(
        Output("bump-pin-store", "data"),
        Input("bump-chart", "clickData"),
        State("bump-pin-store", "data"),
        prevent_initial_call=True,
    )
    def update_pin(click_data, current_pin):
        if not click_data:
            return None
        retailer = click_data["points"][0].get("customdata")
        if not retailer:
            return None
        # Toggle: clicking the same retailer again dismisses the card.
        if retailer == current_pin:
            return None
        return retailer

    # ----------------------------------------------------------
    # b) Pin store change → update figure opacity + callout card
    # ----------------------------------------------------------
    @app.callback(
        Output("bump-chart", "figure"),
        Output("bump-callout", "style"),
        Output("bump-callout", "children"),
        Input("bump-pin-store", "data"),
    )
    def update_bump_display(pinned_retailer):
        df = get_net_revenue()
        fig = bump_chart(df, pinned=pinned_retailer)

        if not pinned_retailer:
            return fig, {"display": "none"}, []

        matches = df[df["retailer"] == pinned_retailer]
        if matches.empty:
            return fig, {"display": "none"}, []

        card = callout_card(matches.iloc[0])
        return fig, {"display": "block"}, card
