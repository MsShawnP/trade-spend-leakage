# Trade Spend Leakage Analysis

Forensic trade spend analysis for specialty food brands that detects leakage — double-funded promotions, phantom promos, rate discrepancies, and ineffective spend — and reranks retailers by net revenue after all trade costs.

## What it does

Joins three data sources brands already have but have never connected: promotional agreements, deduction/remittance data, and POS/shipment data. Surfaces the specific dollar amounts and instances of each leakage type, then reranks retailers by true net revenue. The headline finding: the retailer the brand treats as its #1 account is often one of its worst after trade spend.

Dual delivery:
- **Interactive dashboard** — gross-vs-net retailer bump chart, leakage ledger, per-retailer scorecards. The CEO's "aha" moment.
- **Excel workbook** — audit-ready data lineage from raw inputs to final leakage schedules. The CFO's working model.

Built on synthetic Cinderhaven data. Part of the Lailara LLC consulting portfolio.

## Data Contract

Cinderhaven canonical platform data: 50 SKUs across 5 product lines (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites), 6 contracted retailers (Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group), 3 distributors (UNFI, KeHE, DPI Northwest) + 1 DTC channel (Shopify). Source: `CINDERHAVEN_CANONICAL.md` in `cinderhaven-data-platform`.

> **Note:** Current baked data contains 3 product lines from an earlier platform export. A re-export with all 5 lines is pending.

## Stack

- **Dashboard:** Plotly Dash + dash-bootstrap-components, deployed to Fly.io
- **Data:** SQLite snapshot of Cinderhaven Provisions synthetic data (via `cinderhaven-data` submodule)
- **Pipeline:** Python — pre-computes all five analytical moves into `data/results.db`
- **Workbook:** openpyxl — generated server-side on demand


## Data contract

Canonical Cinderhaven conformance — 50 SKUs across 5 product lines and 6 contracted retailers.
## Live

**Live:** https://trade-spend.lailarallc.com

No login required. The dashboard runs on Fly.io with a pre-computed `results.db` baked into the image.

## How to run locally

**Prerequisites:** Python 3.11+, pip, access to the Cinderhaven Fly.io Postgres instance

```bash
# 1. Clone and initialise the submodule
git clone <repo-url>
git submodule update --init

# 2. Copy the Cinderhaven database into the submodule data/ directory
# (the .db file is not tracked in git — copy from a sibling project or
#  export from Fly.io: flyctl postgres connect -a cinderhaven-db)
# cp /path/to/cinderhaven_product_master.db data/cinderhaven-data/data/

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set DATABASE_URL and start the Fly.io Postgres proxy
fly proxy 5432 -a cinderhaven-db  # run in a separate terminal
export DATABASE_URL=postgresql://postgres:<password>@localhost:5432/cinderhaven

# 5. Run the analysis pipeline (generates data/results.db)
python pipeline/run.py

# 6. Start the dashboard
python app/app.py
# → open http://localhost:8050
```

**Run a specific move only:**

```bash
python pipeline/run.py --moves 1 3
```

**Run tests:**

```bash
pytest tests/
```

## Refreshing the live deployment

The deployed app uses a `results.db` baked into the Docker image at build time — there is no live database connection at runtime.

To update the deployed data:

```bash
# 1. Run the pipeline locally (requires DATABASE_URL + fly proxy running)
python pipeline/run.py

# 2. Redeploy — fly deploy copies the updated results.db into the new image
fly deploy
```

## Project state files

- `PLAN.md` — current work arc
- `HANDOFF.md` — session-by-session state
- `DECISIONS.md` — durable choices with rationale
- `FAILURES.md` — dead ends and why they failed

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
