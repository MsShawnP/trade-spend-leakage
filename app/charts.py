"""Plotly chart builders and table components — Lailara Design System v2 styling."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import html

from app.constants import (
    CANVAS,
    CATEGORICAL,
    FONT_SANS,
    FONT_SERIF,
    GRIDLINE,
    INK,
    NAVY,
    RED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TOKYO_DEFAULT,
    SG_DEFAULT,
    PASS_BG,
    PASS_TEXT,
    WARN_BG,
    WARN_TEXT,
)


def bump_chart(df: pd.DataFrame, pinned: str | None = None) -> go.Figure:
    """Gross-revenue rank vs net-revenue rank bump chart.

    One Scatter trace per retailer. x=0 is gross rank, x=1 is net rank.
    Rank 1 (highest) plotted at the top via reversed y-axis.
    When pinned is set, non-selected retailers dim to 0.2 opacity.
    """
    df = df.copy()
    df["gross_rank"] = df["gross_revenue"].rank(ascending=False).astype(int)
    df["net_rank"] = df["net_revenue"].rank(ascending=False).astype(int)
    n = len(df)

    fig = go.Figure()

    for i, (_, row) in enumerate(df.iterrows()):
        retailer = str(row["retailer"])
        color = CATEGORICAL[i % len(CATEGORICAL)]
        is_pinned = pinned is not None and retailer == pinned
        opacity = 1.0 if (pinned is None or is_pinned) else 0.2
        line_width = 2.5 if is_pinned else 1.5

        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[int(row["gross_rank"]), int(row["net_rank"])],
            mode="lines+markers",
            name=retailer,
            line=dict(color=color, width=line_width),
            marker=dict(color=color, size=10),
            opacity=opacity,
            customdata=[retailer, retailer],
            hovertemplate=(
                f"<b>{retailer}</b><br>"
                "Rank: %{y}<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        template="simple_white",
        paper_bgcolor=CANVAS,
        plot_bgcolor=CANVAS,
        height=420,
        margin=dict(l=20, r=120, t=20, b=60),
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 1],
            ticktext=["By Gross Revenue", "By Net Revenue"],
            tickfont=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY),
            showgrid=False,
            zeroline=False,
            range=[-0.15, 1.25],
        ),
        yaxis=dict(
            autorange="reversed",
            tickmode="linear",
            tick0=1,
            dtick=1,
            tickfont=dict(family=FONT_SANS, size=12, color=TEXT_SECONDARY),
            gridcolor=GRIDLINE,
            zeroline=False,
            title=dict(text="Rank", font=dict(family=FONT_SANS, size=13, color=TEXT_SECONDARY)),
        ),
        showlegend=True,
        legend=dict(
            x=1.02,
            y=0.5,
            xanchor="left",
            yanchor="middle",
            font=dict(family=FONT_SANS, size=12, color=INK),
            bgcolor="rgba(0,0,0,0)",
        ),
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
    "borderBottom": "1px solid #e8e6e1",
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
        bg = "#e8eaf3" if is_pinned else "transparent"
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
         "cellStyle": {"function": "params.value > 0 ? {'color': '#b82d4a'} : {}"}},
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
