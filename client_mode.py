"""Client-mode CLI for trade-spend-leakage.

Analyze a client's trade-spend ledger and (optionally) their rate card to price
net revenue and flag rate discrepancies — validated, never committed, never
deployed. The demo Dash app + pipeline are untouched.

The rate card is intake as a LONG table (retailer, rate, effective_date) — one
row per retailer per rate change — NOT the demo's wide per-retailer-column shape,
which no client's rate card matches. The tool picks each retailer's latest rate
effective on or before the engagement as_of_date.

Usage:
    python client_mode.py --config engagement.yml --input client-data/trade_spend.csv \
        [--rate-card client-data/rate_card.csv] --out client-output [--final]
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path

from lailara_engagement import (
    ColumnSpec,
    PreflightSpec,
    build_provenance,
    load_config,
    read_table,
    run_preflight,
    validation_status_label,
    write_report,
)
from lailara_engagement import palette as P
from lailara_engagement.provenance import InputRef, Provenance

TOOL = "trade-spend-leakage"
TOOL_VERSION = "1.0"
RATE_DISCREPANCY_PTS = 0.5  # effective vs carded rate gap (percentage points) to flag


def _ledger_spec() -> PreflightSpec:
    return PreflightSpec(
        tool=TOOL, version=TOOL_VERSION,
        columns=[
            ColumnSpec(name="retailer", dtype="string", required=True, unique=True,
                       description="retailer/customer", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="gross_revenue", dtype="number", required=True, not_negative=True,
                       description="gross revenue", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="trade_spend", dtype="number", required=True, not_negative=True,
                       description="total trade spend (deductions + promo)", spec_ref="INPUT-SPEC §1"),
        ],
    )


def _num(v) -> float:
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return 0.0


def _load_rate_card(path: Path, as_of: date) -> dict[str, float]:
    """Long rate card -> {retailer: latest rate effective on/before as_of}."""
    read = read_table(str(path))
    cols = {c.lower(): c for c in read.columns}
    r_c = cols.get("retailer") or read.columns[0]
    rate_c = cols.get("rate") or cols.get("trade_spend_pct")
    eff_c = cols.get("effective_date") or cols.get("effective")
    best: dict[str, tuple[date, float]] = {}
    for _, row in read.frame.iterrows():
        r = str(row[r_c]).strip()
        if not r or rate_c is None:
            continue
        rate = _num(row[rate_c])
        eff = None
        if eff_c:
            try:
                eff = date.fromisoformat(str(row[eff_c]).strip())
            except Exception:
                eff = None
        if eff is not None and eff > as_of:
            continue
        key = eff or date.min
        if r not in best or key >= best[r][0]:
            best[r] = (key, rate)
    return {r: v[1] for r, v in best.items()}, read


def run(config_path: str, input_path: str, out_dir: str, *,
        rate_card_path: str | None = None, final: bool = False) -> dict:
    config = load_config(config_path)
    read = read_table(input_path)
    report = run_preflight(read, _ledger_spec(), config)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    inputs = [read]
    rate_card = {}
    rate_read = None
    if rate_card_path:
        rate_card, rate_read = _load_rate_card(Path(rate_card_path), config.as_of_date)
        inputs.append(rate_read)

    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=inputs, config=config,
        validation_status=validation_status_label(report.status, report.n_warnings))
    if not report.passed:
        paths = write_report(report, config, str(out), provenance=provenance,
                             draft=not final, basename="data-readiness-report",
                             title="Trade-Spend Data Readiness Report")
        return {"status": "blocked", "readiness_report": paths["html"]}

    m = report.column_mapping
    frame = read.frame
    rows = []
    tot_gross = tot_spend = 0.0
    discrepancies = 0
    for i in range(len(frame)):
        r = str(frame[m["retailer"]].iloc[i]).strip()
        gross = _num(frame[m["gross_revenue"]].iloc[i])
        spend = _num(frame[m["trade_spend"]].iloc[i])
        eff_rate = (spend / gross) if gross else 0.0
        carded = rate_card.get(r)
        gap = (eff_rate - carded) if carded is not None else None
        flagged = gap is not None and abs(gap * 100) > RATE_DISCREPANCY_PTS
        if flagged:
            discrepancies += 1
        rows.append({
            "retailer": r, "gross_revenue": round(gross, 2), "trade_spend": round(spend, 2),
            "net_revenue": round(gross - spend, 2), "effective_rate": round(eff_rate, 4),
            "carded_rate": None if carded is None else round(carded, 4),
            "rate_gap_pts": None if gap is None else round(gap * 100, 2),
            "flagged": flagged,
        })
        tot_gross += gross; tot_spend += spend

    rows.sort(key=lambda x: x["trade_spend"], reverse=True)
    summary = {
        "window": {"label": config.basis.get("window_label", ""), "as_of": config.as_of_date.isoformat()},
        "retailers": rows,
        "totals": {"gross_revenue": round(tot_gross, 2), "trade_spend": round(tot_spend, 2),
                   "net_revenue": round(tot_gross - tot_spend, 2),
                   "effective_rate": round(tot_spend / tot_gross, 4) if tot_gross else 0},
        "rate_discrepancies": discrepancies,
        "rate_card_provided": bool(rate_card),
    }
    limitations = []
    if not rate_card:
        limitations.append("No rate card supplied (--rate-card) — rate discrepancies not checked. "
                           "Provide a LONG rate card (retailer, rate, effective_date).")
    limitations.append("Ghost / double-funded / unauthorized leakage detection requires promo-level "
                       "authorization data (promo id, authorized flag, funding source) not in a "
                       "retailer-level ledger — out of scope for this intake.")

    json_dir = out / "json"; json_dir.mkdir(parents=True, exist_ok=True)
    (json_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path = out / "trade-spend-summary.html"
    report_path.write_text(_summary_html(config, summary, limitations, provenance, draft=not final),
                           encoding="utf-8")
    return {"status": "ok", "net_revenue": summary["totals"]["net_revenue"],
            "discrepancies": discrepancies, "report": str(report_path),
            "summary_json": str(json_dir / "summary.json"), "n_warnings": report.n_warnings}


def _d(v):
    return f"${v:,.0f}"


def _summary_html(config, s, limitations, provenance: Provenance, *, draft: bool) -> str:
    esc = html.escape
    wl = s["window"].get("label") or ""
    t = s["totals"]

    def _row(r):
        carded = "—" if r["carded_rate"] is None else f"{r['carded_rate'] * 100:.1f}%"
        if r["rate_gap_pts"] is None:
            gap = "—"
        else:
            gap = f"{r['rate_gap_pts']:+.2f}" + (" &#9873;" if r["flagged"] else "")
        return (f"<tr><td>{esc(r['retailer'])}</td><td class=num>{_d(r['gross_revenue'])}</td>"
                f"<td class=num>{_d(r['trade_spend'])}</td>"
                f"<td class=num>{r['effective_rate'] * 100:.1f}%</td>"
                f"<td class=num>{carded}</td><td class=num>{gap}</td>"
                f"<td class=num>{_d(r['net_revenue'])}</td></tr>")

    rows = "".join(_row(r) for r in s["retailers"])
    lim = "".join(f"<li>{esc(x)}</li>" for x in limitations)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Trade Spend — {esc(config.client_name)}</title><style>{_css(draft)}</style></head>
<body class="{' ll-draft' if draft else ''}"><main class=ll-page>
<header class=ll-header>
  <div class=ll-eyebrow>Lailara LLC · Trade Spend</div>
  <h1 class=ll-title>Net Revenue &amp; Trade-Spend Rates</h1>
  <div class=ll-client>
    <div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
    <div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
    <div><span class=ll-k>As of</span> {esc(s['window']['as_of'])}</div>
    <div><span class=ll-k>Window</span> {esc(wl) or '—'}</div>
  </div>
</header>
<section class=ll-banner>
  <div class=ll-score>{_d(t['net_revenue'])} net revenue</div>
  <div>{_d(t['trade_spend'])} trade spend on {_d(t['gross_revenue'])} gross
       ({t['effective_rate']*100:.1f}% effective) · {s['rate_discrepancies']} rate discrepancies</div>
</section>
<section class=ll-section>
  <h2 class=ll-h2>By retailer</h2>
  <table class=ll-table><thead><tr><th>Retailer</th><th>Gross</th><th>Trade spend</th>
  <th>Effective rate</th><th>Carded rate</th><th>Gap (pts)</th><th>Net revenue</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <p class=ll-note>Effective rate = trade spend / gross. Carded rate = latest rate in the
  long rate card effective on/before {esc(s['window']['as_of'])}; a gap over
  {RATE_DISCREPANCY_PTS:.1f} pts is flagged (⚑).</p>
</section>
<section class=ll-section><h2 class=ll-h2>Data limitations</h2><ul class=ll-limitations>{lim}</ul></section>
{provenance.to_html()}
</main></body></html>"""


def _css(draft: bool) -> str:
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:34px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-banner{{border-radius:2px;padding:16px 20px;margin-bottom:32px;background:{P.LL_HK_SURFACE};color:{P.LL_HK_DARK}}}
.ll-score{{font-family:var(--s);font-weight:700;font-size:22px}}
.ll-section{{margin:0 0 32px}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;
margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-note{{font-size:13px;color:{P.LL_TEXT_SEC};margin-top:8px}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table th{{text-align:left;background:{P.LL_CHICAGO};color:#fff;padding:8px 12px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-limitations{{margin:0;padding-left:20px}}.ll-limitations li{{margin-bottom:6px}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};
padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}
.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="trade-spend-leakage client mode")
    ap.add_argument("--config", required=True)
    ap.add_argument("--input", required=True, help="trade-spend ledger (retailer, gross_revenue, trade_spend)")
    ap.add_argument("--rate-card", default=None, help="optional LONG rate card (retailer, rate, effective_date)")
    ap.add_argument("--out", default="client-output")
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.input, args.out, rate_card_path=args.rate_card, final=args.final)
    if result["status"] == "blocked":
        print(f"BLOCKED — data not ready. See {result['readiness_report']}")
        return 3
    print(f"net revenue {_d(result['net_revenue'])}; {result['discrepancies']} rate discrepancies")
    print(f"report -> {result['report']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
