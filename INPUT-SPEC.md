# INPUT-SPEC — trade-spend-leakage (client mode)

What to hand the tool in a client engagement. Derived from the fields the engine
consumes (`pipeline/`, `data/results.db`), not the README.

## 1. Trade-spend ledger (`--input`, required)

One row per retailer/customer, CSV or XLSX.

| Canonical | Type | Used for |
|---|---|---|
| `retailer` | string (unique) | Retailer/customer name. §1 |
| `gross_revenue` | number ≥ 0 | Gross revenue. §1 |
| `trade_spend` | number ≥ 0 | Total trade spend (deductions + promo). §1 |

`net_revenue = gross_revenue − trade_spend`; effective rate = `trade_spend / gross_revenue`.

## 2. Rate card (`--rate-card`, optional) — **long format**

A **long** rate card, one row per retailer per rate change — *not* the demo's
wide per-retailer-column shape, which no client's rate card matches:

| Canonical | Type | Used for |
|---|---|---|
| `retailer` | string | Retailer the rate applies to. |
| `rate` | number | Trade-spend rate (fraction, e.g. `0.10` = 10%). |
| `effective_date` | date | When the rate took effect. |

The tool picks each retailer's **latest rate effective on or before `as_of_date`**
and flags a rate discrepancy where the effective rate diverges from the carded
rate by more than 0.5 points. Without a rate card, discrepancy checks are disclosed
as skipped.

## Not in scope for this intake

Ghost / double-funded / unauthorized leakage detection needs **promo-level**
authorization data (promo id, authorized flag, funding source), not a
retailer-level ledger — disclosed as a data limitation, never fabricated.

## Basis & window (engagement.yml)

```yaml
as_of_date: "2026-01-31"          # rate-card as-of + analysis anchor; NEVER today
basis:
  window_label: "CY2025"          # printed on the output
```

## Run

```bash
pip install -e ../engagement-template/lib
python client_mode.py --config engagement.yml --input client-data/trade_spend.csv \
    [--rate-card client-data/rate_card.csv] --out client-output [--final]
```

Output to `client-output/` (gitignored): a branded, provenance-footed,
DRAFT-watermarked `trade-spend-summary.html` (net revenue + effective vs carded
rate + discrepancies by retailer) + `json/summary.json`; or a Data Readiness
Report if a required column is missing. The demo Dash app + pipeline are never edited.
