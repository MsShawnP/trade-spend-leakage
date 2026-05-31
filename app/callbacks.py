"""Dash callbacks — all callbacks registered via register_callbacks(app)."""

from __future__ import annotations

from dash import ALL, Input, Output, State, ctx

from app.charts import bump_chart, leakage_ledger, leakage_instances_grid
from app.components import callout_card
from app.db import get_net_revenue, get_leakage_summary, get_leakage_instances


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

    # ----------------------------------------------------------
    # c) Leakage row click → update leakage pin store (toggle)
    # ----------------------------------------------------------
    @app.callback(
        Output("leakage-pin-store", "data"),
        Input({"type": "leakage-row", "index": ALL}, "n_clicks"),
        State("leakage-pin-store", "data"),
        prevent_initial_call=True,
    )
    def update_leakage_pin(n_clicks_list, current_pin):
        if not any(n_clicks_list):
            return current_pin
        triggered = ctx.triggered_id
        if not triggered:
            return current_pin
        clicked_type = triggered["index"]
        # Toggle: clicking the same row again clears the pin
        if clicked_type == current_pin:
            return None
        return clicked_type

    # ----------------------------------------------------------
    # d) Leakage pin store → re-render ledger + show instances
    # ----------------------------------------------------------
    @app.callback(
        Output("leakage-ledger-container", "children"),
        Output("leakage-instances-container", "children"),
        Input("leakage-pin-store", "data"),
    )
    def update_leakage_display(pinned_type):
        df_summary = get_leakage_summary()
        ledger = leakage_ledger(df_summary, pinned=pinned_type)

        if not pinned_type:
            return ledger, []

        df_instances = get_leakage_instances(pinned_type)
        if df_instances.empty:
            return ledger, []

        grid = leakage_instances_grid(df_instances)
        return ledger, grid
