"""Plotly chart builders — Lailara Design System v2 styling."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app.constants import (
    CANVAS,
    CATEGORICAL,
    FONT_SANS,
    GRIDLINE,
    INK,
    TEXT_SECONDARY,
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
