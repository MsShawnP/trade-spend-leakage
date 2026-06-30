"""Plotly chart builders and table components — Lailara Design System v2 styling."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import html
from plotly.subplots import make_subplots

from lailara_palette import LL_CHICAGO_SURFACE

from app.constants import (
    CANVAS,
    CATEGORICAL,
    DISABLED,
    FONT_SANS,
    GRIDLINE,
    HK,
    HK_DEFAULT,
    INK,
    NAVY,
    REFERENCE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TOKYO_DEFAULT,
    PASS_BG,
    PASS_TEXT,
    WARN_BG,
    WARN_TEXT,
)

CHICAGO_SURFACE = LL_CHICAGO_SURFACE


def bump_chart(df: pd.DataFrame, pinned: str | None = None) -> go.Figure:
    """Gross-to-net revenue slopegraph in dollars.

    One Scatter trace per retailer. x=0 is gross revenue, x=1 is net revenue.
    Lines slope downward showing trade-cost impact; top-3 visibly converge.
    End labels on the right show retailer name + net value.
    When pinned is set, non-selected retailers dim to 0.2 opacity.
    """
    df = df.copy().sort_values("gross_revenue", ascending=False).reset_index(drop=True)
    n = len(df)

    fig = go.Figure()

    for i, (_, row) in enumerate(df.iterrows()):
        retailer = str(row["retailer"])
        gross = float(row["gross_revenue"])
        net = float(row["net_revenue"])
        color = CATEGORICAL[i % len(CATEGORICAL)]
        is_pinned = pinned is not None and retailer == pinned
        opacity = 1.0 if (pinned is None or is_pinned) else 0.2
        line_width = 3.0 if is_pinned else 1.8

        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[gross, net],
            mode="lines+markers",
            name=retailer,
            line=dict(color=color, width=line_width),
            marker=dict(color=color, size=8),
            opacity=opacity,
            customdata=[retailer, retailer],
            hovertemplate=(
                f"<b>{retailer}</b><br>"
                "$%{y:,.0f}<br>"
                "<extra></extra>"
            ),
        ))

    # End labels on the right side showing retailer name + net dollar value
    # Deconflict close labels by nudging y positions apart
    net_values = df.sort_values("net_revenue", ascending=False).reset_index(drop=True)
    label_positions = [float(row["net_revenue"]) for _, row in net_values.iterrows()]
    min_gap = (max(label_positions) - min(label_positions)) * 0.065 if len(label_positions) > 1 else 0
    for i in range(1, len(label_positions)):
        if label_positions[i - 1] - label_positions[i] < min_gap:
            label_positions[i] = label_positions[i - 1] - min_gap

    for i, (_, row) in enumerate(net_values.iterrows()):
        retailer = str(row["retailer"])
        net = float(row["net_revenue"])
        color_idx = df[df["retailer"] == retailer].index[0]
        color = CATEGORICAL[color_idx % len(CATEGORICAL)]
        is_pinned = pinned is not None and retailer == pinned
        opacity = 1.0 if (pinned is None or is_pinned) else 0.2

        fig.add_annotation(
            x=1,
            y=label_positions[i],
            text=f"  {retailer}  ${net / 1e6:.1f}M",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(family=FONT_SANS, size=11, color=color),
            opacity=opacity,
            xref="x",
            yref="y",
        )

    fig.update_layout(
        template="simple_white",
        paper_bgcolor=CANVAS,
        plot_bgcolor=CANVAS,
        height=460,
        margin=dict(l=60, r=180, t=20, b=60),
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 1],
            ticktext=["Gross Revenue", "Net Revenue"],
            tickfont=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY),
            showgrid=False,
            zeroline=False,
            range=[-0.05, 1.08],
        ),
        yaxis=dict(
            tickprefix="$",
            tickformat=",.0f",
            tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
            gridcolor=GRIDLINE,
            zeroline=False,
            title=dict(text="Revenue", font=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY)),
        ),
        showlegend=False,
        font=dict(family=FONT_SANS, size=13, color=INK),
        hoverlabel=dict(bgcolor=CANVAS, font_family=FONT_SANS),
    )

    return fig


# ---------------------------------------------------------------------------
# Leakage ledger — summary table (4 rows + total)
# ---------------------------------------------------------------------------

_CLASSIFICATION_STYLE = {
    "Recoverable":  {"background": PASS_BG,  "color": PASS_TEXT},
    "Reallocatable": {"background": WARN_BG, "color": WARN_TEXT},
}

_LEDGER_HEADER_STYLE = {
    "fontFamily": FONT_SANS,
    "fontSize": "12px",
    "fontWeight": "600",
    "color": TEXT_SECONDARY,
    "textTransform": "uppercase",
    "letterSpacing": "0.06em",
    "padding": "8px 12px",
    "borderBottom": f"2px solid {INK}",
    "textAlign": "left",
    "whiteSpace": "nowrap",
}

_LEDGER_CELL_STYLE = {
    "fontFamily": FONT_SANS,
    "fontSize": "14px",
    "color": TEXT_PRIMARY,
    "padding": "10px 12px",
    "borderBottom": f"1px solid {GRIDLINE}",
    "verticalAlign": "middle",
}


def leakage_ledger(df: pd.DataFrame, pinned: str | None = None) -> html.Div:
    """Styled summary ledger for the four leakage sub-types.

    Each data row is clickable — it carries an id for pattern-matching callbacks.
    Click-to-pin: selected row highlights; clicking again dismisses.
    """
    header = html.Tr([
        html.Th("Leakage type",   style=_LEDGER_HEADER_STYLE),
        html.Th("$ Total",        style={**_LEDGER_HEADER_STYLE, "textAlign": "right"}),
        html.Th("Instances",      style={**_LEDGER_HEADER_STYLE, "textAlign": "right"}),
        html.Th("Classification", style=_LEDGER_HEADER_STYLE),
    ])

    data_rows = []
    grand_total = 0.0
    grand_count = 0

    for _, row in df.iterrows():
        ltype = str(row["leakage_type"])
        is_pinned = pinned == ltype
        bg = CHICAGO_SURFACE if is_pinned else "transparent"
        border_left = f"3px solid {NAVY}" if is_pinned else "3px solid transparent"

        cls_chip = row.get("classification", "")
        cls_style = _CLASSIFICATION_STYLE.get(cls_chip, {})
        chip = html.Span(cls_chip, style={
            **cls_style,
            "fontFamily": FONT_SANS,
            "fontSize": "12px",
            "fontWeight": "500",
            "padding": "2px 8px",
            "borderRadius": "2px",
        })

        data_rows.append(html.Tr(
            id={"type": "leakage-row", "index": ltype},
            n_clicks=0,
            children=[
                html.Td(str(row["display_name"]), style={
                    **_LEDGER_CELL_STYLE,
                    "borderLeft": border_left,
                    "fontWeight": "600" if is_pinned else "400",
                    "cursor": "pointer",
                }),
                html.Td(f"${float(row['dollar_total']):,.0f}", style={
                    **_LEDGER_CELL_STYLE, "textAlign": "right", "cursor": "pointer",
                }),
                html.Td(f"{int(row['instance_count']):,}", style={
                    **_LEDGER_CELL_STYLE, "textAlign": "right", "cursor": "pointer",
                }),
                html.Td(chip, style={**_LEDGER_CELL_STYLE, "cursor": "pointer"}),
            ],
            style={"background": bg},
        ))

        grand_total += float(row["dollar_total"])
        grand_count += int(row["instance_count"])

    total_row = html.Tr([
        html.Td("Total", style={
            **_LEDGER_CELL_STYLE,
            "fontWeight": "700",
            "borderTop": f"2px solid {INK}",
            "borderLeft": "3px solid transparent",
        }),
        html.Td(f"${grand_total:,.0f}", style={
            **_LEDGER_CELL_STYLE,
            "fontWeight": "700",
            "textAlign": "right",
            "borderTop": f"2px solid {INK}",
        }),
        html.Td(f"{grand_count:,}", style={
            **_LEDGER_CELL_STYLE,
            "fontWeight": "700",
            "textAlign": "right",
            "borderTop": f"2px solid {INK}",
        }),
        html.Td("", style={
            **_LEDGER_CELL_STYLE,
            "borderTop": f"2px solid {INK}",
        }),
    ])

    table = html.Table(
        [html.Thead(header), html.Tbody(data_rows + [total_row])],
        style={"width": "100%", "borderCollapse": "collapse"},
    )

    return html.Div(table, style={"overflowX": "auto"})


# ---------------------------------------------------------------------------
# Leakage instances AG Grid
# ---------------------------------------------------------------------------

def leakage_instances_grid(df: pd.DataFrame) -> "dash_ag_grid.AgGrid":
    import dash_ag_grid as dag

    col_defs = [
        {"field": "deduction_id",  "headerName": "Deduction ID",   "width": 140},
        {"field": "retailer_id",   "headerName": "Retailer",        "width": 160},
        {"field": "promo_id",      "headerName": "Promo / Type",    "width": 150,
         "valueFormatter": {"function": "params.value ?? '—'"}},
        {"field": "period",        "headerName": "Date",            "width": 120},
        {"field": "agreed_amount", "headerName": "Agreed ($)",      "width": 120,
         "type": "numericColumn",
         "valueFormatter": {"function": "params.value != null ? '$' + params.value.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) : '—'"}},
        {"field": "actual_amount", "headerName": "Actual ($)",      "width": 120,
         "type": "numericColumn",
         "valueFormatter": {"function": "'$' + params.value.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})"}},
        {"field": "variance",      "headerName": "Variance ($)",    "width": 120,
         "type": "numericColumn",
         "valueFormatter": {"function": "params.value != null ? '$' + params.value.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) : '—'"},
         "cellStyle": {"function": f"params.value > 0 ? {{'color': '{TOKYO_DEFAULT}'}} : {{}}"}},
        {"field": "classification", "headerName": "Classification", "width": 140},
    ]

    return dag.AgGrid(
        id="leakage-instances-grid",
        rowData=df.to_dict("records"),
        columnDefs=col_defs,
        defaultColDef={
            "resizable": True,
            "sortable": True,
            "filter": True,
            "suppressMovable": True,
        },
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 20,
            "domLayout": "autoHeight",
        },
        style={"height": None},
        className="ag-theme-alpine",
    )


# ---------------------------------------------------------------------------
# Trade Spend Efficiency — dual-panel horizontal bar chart
# ---------------------------------------------------------------------------

# Threshold for "high" trade spend — specialty food structural average
_HIGH_TRADE_SPEND_PCT = 0.17


def efficiency_chart(df: pd.DataFrame) -> go.Figure:
    """Two-panel horizontal bar chart for Move 2 trade spend efficiency.

    Left panel: Trade spend as % of gross revenue.
      Bars colored SG orange when above the 17% specialty food average,
      HK teal when at or below it.

    Right panel: Revenue per promo dollar (promo-period scan revenue ÷ total
      promo cost). Bars colored on HK teal scale; DISABLED gray for retailers
      with no measurable promo data.

    Retailers sorted by ascending trade_spend_pct (most efficient at top).
    """
    df = df.copy().sort_values("trade_spend_pct", ascending=True)
    retailers = df["retailer"].tolist()
    n = len(retailers)

    # --- Left panel colors: HK teal gradient (darkest = largest value)
    trade_pcts = [float(row["trade_spend_pct"]) for _, row in df.iterrows()]
    tsp_min = min(trade_pcts) if trade_pcts else 0
    tsp_max = max(trade_pcts) if trade_pcts else 1

    hk_trade_stops = [HK[85], HK[70], HK[55], HK[35], HK[25], HK[15], HK[5]]

    def _trade_color(pct: float) -> str:
        if tsp_max == tsp_min:
            return HK_DEFAULT
        normalized = (pct - tsp_min) / (tsp_max - tsp_min)
        idx = min(int(normalized * len(hk_trade_stops)), len(hk_trade_stops) - 1)
        return hk_trade_stops[idx]

    trade_colors = [_trade_color(p) for p in trade_pcts]
    trade_text = [f"{p:.1%}" for p in trade_pcts]

    # --- Right panel colors: HK teal scale (darker = better), gray for N/A ---
    # Normalize lift values for color mapping
    measurable = df[df["lift_measurable"] == 1]["revenue_per_promo_dollar"].dropna()
    if not measurable.empty:
        lift_min = measurable.min()
        lift_max = measurable.max()
    else:
        lift_min = lift_max = 0.0

    hk_lift_stops = [HK[85], HK[70], HK[55], HK[35], HK[25], HK[15], HK[5]]

    def _lift_color(val, measurable_flag: int) -> str:
        if not measurable_flag or val is None or pd.isna(val):
            return DISABLED
        if lift_max == lift_min:
            return HK_DEFAULT
        normalized = (float(val) - lift_min) / (lift_max - lift_min)
        idx = min(int(normalized * len(hk_lift_stops)), len(hk_lift_stops) - 1)
        return hk_lift_stops[idx]

    lift_colors = [
        _lift_color(row["revenue_per_promo_dollar"], int(row["lift_measurable"]))
        for _, row in df.iterrows()
    ]

    lift_values = [
        float(row["revenue_per_promo_dollar"]) if int(row["lift_measurable"]) else 0.0
        for _, row in df.iterrows()
    ]
    lift_text = [
        f"${float(row['revenue_per_promo_dollar']):.1f}" if int(row["lift_measurable"])
        else "No data"
        for _, row in df.iterrows()
    ]

    # --- Build figure ---
    fig = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        column_widths=[0.5, 0.5],
        horizontal_spacing=0.06,
        subplot_titles=[
            "Trade Spend as % of Revenue",
            "Revenue per Promo Dollar Invested",
        ],
    )

    fig.add_trace(
        go.Bar(
            x=df["trade_spend_pct"].tolist(),
            y=retailers,
            orientation="h",
            marker=dict(color=trade_colors, line=dict(width=0)),
            name="Trade Spend %",
            text=trade_text,
            textposition="outside",
            textfont=dict(family=FONT_SANS, size=12, color=TEXT_PRIMARY),
            showlegend=False,
            hovertemplate="%{y}: %{text}<extra></extra>",
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Bar(
            x=lift_values,
            y=retailers,
            orientation="h",
            marker=dict(color=lift_colors, line=dict(width=0)),
            name="Revenue / Promo $",
            text=lift_text,
            textposition="outside",
            textfont=dict(family=FONT_SANS, size=12, color=TEXT_PRIMARY),
            showlegend=False,
            hovertemplate="%{y}: %{text}<extra></extra>",
        ),
        row=1, col=2,
    )

    # Reference line at 17% threshold on left panel
    fig.add_vline(
        x=_HIGH_TRADE_SPEND_PCT,
        line=dict(color=REFERENCE, dash="dash", width=1.5),
        row=1, col=1,
    )

    row_height = max(48, 320 // max(n, 1))
    total_height = max(280, n * row_height + 80)

    fig.update_layout(
        template="simple_white",
        paper_bgcolor=CANVAS,
        plot_bgcolor=CANVAS,
        height=total_height,
        margin=dict(l=20, r=80, t=50, b=40),
        font=dict(family=FONT_SANS, size=12, color=INK),
        hoverlabel=dict(bgcolor=CANVAS, font_family=FONT_SANS),
    )

    fig.update_xaxes(
        tickformat=".0%",
        tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
        gridcolor=GRIDLINE,
        showgrid=True,
        zeroline=False,
        row=1, col=1,
    )
    fig.update_xaxes(
        tickprefix="$",
        tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
        gridcolor=GRIDLINE,
        showgrid=True,
        zeroline=False,
        row=1, col=2,
    )
    fig.update_yaxes(
        tickfont=dict(family=FONT_SANS, size=12, color=TEXT_PRIMARY),
        gridcolor=GRIDLINE,
        showgrid=False,
    )

    # Style subplot title annotations
    for ann in fig.layout.annotations:
        ann.update(
            font=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY),
            y=ann.y + 0.02,
        )

    return fig


# ---------------------------------------------------------------------------
# Promotional ROI scatter chart (Move 4)
# ---------------------------------------------------------------------------

def promo_roi_chart(df: pd.DataFrame, pinned: str | None = None) -> go.Figure:
    """Scatter chart — promo cost (x) vs incremental revenue (y).

    Break-even line: y = x (dashed REFERENCE gray).
    Points above line: HK teal (ROI positive).
    Points below line: Tokyo rose (money-losing).
    Points with insufficient baseline: DISABLED gray.
    Pinned promo highlights; others dim to 0.2 opacity.
    """
    fig = go.Figure()

    if df.empty:
        _add_breakeven_line(fig, 0, 1)
        _apply_promo_roi_layout(fig)
        return fig

    # Determine axis range for break-even line
    all_costs = df["promo_cost"].dropna()
    all_incr = df["incremental_revenue"].dropna()
    axis_max = float(max(
        all_costs.max() if not all_costs.empty else 1000,
        all_incr.max() if not all_incr.empty else 1000,
    )) * 1.1
    axis_max = max(axis_max, 100.0)

    # Break-even line first (renders behind points)
    _add_breakeven_line(fig, 0, axis_max)

    # One trace per point — allows individual opacity control
    for _, row in df.iterrows():
        pid = str(row["promo_id"])
        has_baseline = bool(row.get("has_sufficient_baseline", 0))
        cost = row.get("promo_cost")
        incr = row.get("incremental_revenue")
        is_losing = row.get("is_money_losing")
        promo_type = str(row.get("promo_type") or "")
        retailer = str(row.get("retailer") or "")
        sku = str(row.get("sku_id") or "")

        if not has_baseline or cost is None or pd.isna(cost):
            color = DISABLED
        elif is_losing == 1 or is_losing is True:
            color = TOKYO_DEFAULT
        else:
            color = HK_DEFAULT

        is_pinned = pinned is not None and pid == pinned
        opacity = 1.0 if (pinned is None or is_pinned) else 0.2
        size = 12 if is_pinned else 9
        line_width = 2 if is_pinned else 0

        # Hover text
        if has_baseline and cost is not None and pd.notna(cost) and incr is not None and pd.notna(incr):
            roi_pct = ((float(incr) - float(cost)) / float(cost) * 100) if float(cost) != 0 else None
            hover = (
                f"<b>{pid}</b><br>"
                f"Retailer: {retailer}<br>"
                f"SKU: {sku}<br>"
                f"Type: {promo_type}<br>"
                f"Cost: ${float(cost):,.0f}<br>"
                f"Incremental rev: ${float(incr):,.0f}<br>"
                + (f"ROI: {roi_pct:+.1f}%" if roi_pct is not None else "ROI: N/A")
                + "<extra></extra>"
            )
        else:
            cost_str = f"${float(cost):,.0f}" if cost is not None and pd.notna(cost) else "N/A"
            hover = (
                f"<b>{pid}</b><br>"
                f"Retailer: {retailer}<br>"
                f"SKU: {sku}<br>"
                f"Type: {promo_type}<br>"
                f"Cost: {cost_str}<br>"
                "Insufficient pre-promo data<extra></extra>"
            )

        x_val = float(cost) if cost is not None and pd.notna(cost) else None
        y_val = float(incr) if incr is not None and pd.notna(incr) else None

        fig.add_trace(go.Scatter(
            x=[x_val],
            y=[y_val],
            mode="markers",
            name=pid,
            showlegend=False,
            marker=dict(
                color=color,
                size=size,
                opacity=opacity,
                line=dict(color=INK, width=line_width),
            ),
            customdata=[[pid, retailer, sku, promo_type]],
            hovertemplate=hover,
        ))

    _apply_promo_roi_layout(fig, axis_max)
    return fig


def _add_breakeven_line(fig: go.Figure, lo: float, hi: float) -> None:
    fig.add_trace(go.Scatter(
        x=[lo, hi],
        y=[lo, hi],
        mode="lines",
        name="Break-even",
        showlegend=False,
        line=dict(color=REFERENCE, dash="dash", width=1.5),
        hoverinfo="skip",
    ))


def _apply_promo_roi_layout(fig: go.Figure, axis_max: float = 1.0) -> None:
    fig.update_layout(
        template="simple_white",
        paper_bgcolor=CANVAS,
        plot_bgcolor=CANVAS,
        height=460,
        margin=dict(l=60, r=20, t=20, b=60),
        font=dict(family=FONT_SANS, size=12, color=INK),
        hoverlabel=dict(bgcolor=CANVAS, font_family=FONT_SANS),
        showlegend=False,
        xaxis=dict(
            title=dict(
                text="Promotion cost ($)",
                font=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY),
            ),
            tickprefix="$",
            tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
            gridcolor=GRIDLINE,
            zeroline=False,
            range=[0, axis_max],
        ),
        yaxis=dict(
            title=dict(
                text="Incremental revenue ($)",
                font=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY),
            ),
            tickprefix="$",
            tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
            gridcolor=GRIDLINE,
            zeroline=False,
        ),
    )



# ---------------------------------------------------------------------------
# Accrual Reconciliation — grouped bar + variance line (Move 5)
# ---------------------------------------------------------------------------


def accrual_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart — accrued vs actual deducted per month.

    Left Y axis: accrued (Chicago navy) and actual (HK teal) bars side by side.
    Right Y axis: variance line (REFERENCE gray dashed).
    Month labels formatted as 'Jan '24'.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if df.empty:
        fig.update_layout(
            template="simple_white",
            paper_bgcolor=CANVAS,
            plot_bgcolor=CANVAS,
            height=360,
            margin=dict(l=60, r=60, t=20, b=60),
            font=dict(family=FONT_SANS, size=12, color=INK),
        )
        return fig

    # Format month labels: "Jan '24"
    def _label(month_str: str) -> str:
        try:
            import datetime
            d = datetime.date.fromisoformat(month_str)
            return d.strftime("%b '%y")
        except Exception:
            return month_str

    labels = [_label(str(m)) for m in df["month"]]
    accrued = df["accrued"].tolist()
    actual = df["actual"].tolist()
    variance = df["variance"].tolist()

    fig.add_trace(
        go.Bar(
            name="Accrued",
            x=labels,
            y=accrued,
            marker=dict(color=NAVY, line=dict(width=0)),
            offsetgroup=0,
            hovertemplate="%{x}<br>Accrued: $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            name="Actual deducted",
            x=labels,
            y=actual,
            marker=dict(color=HK_DEFAULT, line=dict(width=0)),
            offsetgroup=1,
            hovertemplate="%{x}<br>Actual: $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            name="Variance",
            x=labels,
            y=variance,
            mode="lines+markers",
            line=dict(color=REFERENCE, dash="dash", width=1.5),
            marker=dict(color=REFERENCE, size=6),
            hovertemplate="%{x}<br>Variance: $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template="simple_white",
        paper_bgcolor=CANVAS,
        plot_bgcolor=CANVAS,
        height=400,
        margin=dict(l=60, r=60, t=20, b=60),
        font=dict(family=FONT_SANS, size=12, color=INK),
        hoverlabel=dict(bgcolor=CANVAS, font_family=FONT_SANS),
        barmode="group",
        legend=dict(
            orientation="h",
            x=0,
            y=1.08,
            font=dict(family=FONT_SANS, size=12, color=INK),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    fig.update_yaxes(
        tickprefix="$",
        tickformat=",.0f",
        tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
        gridcolor=GRIDLINE,
        zeroline=True,
        zerolinecolor=GRIDLINE,
        secondary_y=False,
    )
    fig.update_yaxes(
        title=dict(text="Variance ($)", font=dict(family=FONT_SANS, size=12, color=REFERENCE)),
        tickprefix="$",
        tickformat=",.0f",
        tickfont=dict(family=FONT_SANS, size=11, color=REFERENCE),
        gridcolor="rgba(0,0,0,0)",
        zeroline=False,
        secondary_y=True,
    )
    fig.update_xaxes(
        tickfont=dict(family=FONT_SANS, size=11, color=TEXT_SECONDARY),
        showgrid=False,
    )

    return fig
