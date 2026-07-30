# Trade Spend Leakage Analysis — find the money leaking out of promotions, then rerank retailers by what they actually pay

Forensic trade spend analysis for specialty food brands. Detects leakage —
double-funded promotions, phantom promos, rate discrepancies, and ineffective
spend — and reranks retailers by net revenue after all trade costs.

**Live:** https://trade-spend.lailarallc.com — no login required.

## What it does

Joins three data sources brands already have but have never connected:
promotional agreements, deduction/remittance data, and POS/shipment data. A
five-move Python pipeline pre-computes every analysis into a single results
database:

1. **Net revenue** — gross-to-net waterfall per retailer
2. **Efficiency** — trade spend efficiency by retailer and product line
3. **Leakage** — double-funded, phantom, and rate-discrepancy findings with
   specific dollar amounts and instances
4. **Promo ROI** — which promotions paid back and which didn't
5. **Accrual** — accrual vs. actual trade liability

Dual delivery on top of that pipeline:

- **Interactive dashboard** — gross-vs-net retailer bump chart, leakage
  ledger, per-retailer scorecards. The CEO's "aha" moment.
- **Excel workbook** — audit-ready data lineage from raw inputs to final
  leakage schedules, generated server-side on demand. The CFO's working model.

Built on synthetic Cinderhaven Provisions data. Part of the Lailara LLC
consulting portfolio.

## Why it matters

Trade spend is typically a specialty food brand's second-largest cost after
COGS, yet it is managed across disconnected systems — promo calendars in
spreadsheets, deductions in the ERP, POS data in retailer portals. Nobody
reconciles them, so double-funded promotions and unearned deductions go
undetected, and retailer rankings are based on gross revenue rather than what
each account actually nets. The headline finding this analysis produces: the
retailer a brand treats as its #1 account is often one of its worst after
trade spend.

## Quick start

**Prerequisites:** Python 3.11+, pip, and a `DATABASE_URL` pointing at the
Cinderhaven Postgres instance (only needed to regenerate the data — a
pre-computed `data/results.db` ships with the repo).

```bash
pip install -r requirements.txt

# Run the dashboard against the bundled results.db
python app/app.py
# -> open http://localhost:8050

# Or use the entry point (runs the pipeline first if results.db is missing)
python run.py

# Regenerate the analysis (requires DATABASE_URL)
export DATABASE_URL=postgresql://user:pass@host:port/db
python pipeline/run.py            # all five moves
python pipeline/run.py --moves 1 3  # specific moves only

# Run tests
pytest tests/
```

### Refreshing the live deployment

The deployed app uses a `results.db` baked into the Docker image at build
time — there is no live database connection at runtime:

```bash
python pipeline/run.py   # regenerate data locally (requires DATABASE_URL)
fly deploy               # image build copies the updated results.db
```

## Tech stack

- **Dashboard:** Plotly Dash, dash-bootstrap-components, dash-ag-grid
- **Pipeline:** Python + pandas; reads Postgres (psycopg2), writes a SQLite
  snapshot to `data/results.db`
- **Workbook:** openpyxl, generated server-side on demand
- **Serving/deploy:** gunicorn, Docker, Fly.io (`fly.toml`)
- **Tests:** pytest — pipeline moves, workbook generation, canonical
  regression, and design-palette adherence

## Data contract

Cinderhaven canonical platform data: 50 SKUs across 5 product lines (Artisan
Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites), 6
contracted retailers (Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional
Group), 3 distributors (UNFI, KeHE, DPI Northwest) + 1 DTC channel (Shopify).
Source: `CINDERHAVEN_CANONICAL.md` in `cinderhaven-data-platform`.

> **Note:** Baked data re-exported 2026-07-30 from the current production
> extract — all 5 product lines, all 50 SKUs. Pipeline run against the
> verified canonical dataset (scan rows 1,323,569; deductions 14,947;
> promotions 123 — exact canonical counts).

## Project structure

```
run.py            Entry point: pipeline-if-needed, then gunicorn
pipeline/         Move 1-5 analysis modules + orchestrator (pipeline/run.py)
app/              Dash app: layout, callbacks, charts, components
workbook/         openpyxl workbook generator (one module per tab)
data/results.db   Pre-computed analysis snapshot the app reads
tests/            pytest suite
```

Project state files: `PLAN.md` (current work arc), `HANDOFF.md`
(session-by-session state), `DECISIONS.md` (durable choices), `FAILURES.md`
(dead ends).

## License

MIT

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
