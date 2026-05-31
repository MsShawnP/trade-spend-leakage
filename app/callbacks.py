"""Dash callbacks — all callbacks registered via register_callbacks(app)."""

from __future__ import annotations

from dash import ALL, Input, Output, State, ctx, dcc

from app.charts import bump_chart, leakage_ledger, leakage_instances_grid, promo_roi_chart
from app.components import callout_card, promo_callout_card
from app.db import get_net_revenue, get_leakage_summary, get_leakage_instances, get_promo_roi
from app.db import RESULTS_DB
from workbook.generator import generate_workbook


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

    # ----------------------------------------------------------
    # e) Promo ROI chart click → update promo pin store
    #    Second click on same point clears the pin.
    # ----------------------------------------------------------
    @app.callback(
        Output("promo-roi-pin-store", "data"),
        Input("promo-roi-chart", "clickData"),
        State("promo-roi-pin-store", "data"),
        prevent_initial_call=True,
    )
    def update_promo_pin(click_data, current_pin):
        if not click_data:
            return None
        point = click_data["points"][0]
        custom = point.get("customdata")
        if not custom or not custom[0]:
            return None
        promo_id = str(custom[0][0]) if isinstance(custom[0], list) else str(custom[0])
        if promo_id == current_pin:
            return None
        return promo_id

    # ----------------------------------------------------------
    # f) Promo pin store → update scatter opacity + callout card
    # ----------------------------------------------------------
    @app.callback(
        Output("promo-roi-chart", "figure"),
        Output("promo-roi-callout", "style"),
        Output("promo-roi-callout", "children"),
        Input("promo-roi-pin-store", "data"),
    )
    def update_promo_display(pinned_promo):
        df = get_promo_roi()
        fig = promo_roi_chart(df, pinned=pinned_promo)

        if not pinned_promo:
            return fig, {"display": "none"}, []

        matches = df[df["promo_id"].astype(str) == str(pinned_promo)]
        if matches.empty:
            return fig, {"display": "none"}, []

        card = promo_callout_card(matches.iloc[0])
        return fig, {"display": "block"}, card

    # ----------------------------------------------------------
    # g) Download workbook button → stream xlsx bytes
    # ----------------------------------------------------------
    @app.callback(
        Output("download-workbook", "data"),
        Input("btn-download-workbook", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_workbook(n_clicks):
        workbook_bytes = generate_workbook(RESULTS_DB)
        return dcc.send_bytes(workbook_bytes, "cinderhaven-trade-spend-analysis.xlsx")
