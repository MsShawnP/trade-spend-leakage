---
title: "feat: Trade Spend Leakage — Dash dashboard + linked Excel workbook"
type: feat
status: active
date: 2026-05-31
origin: docs/brainstorms/trade-spend-leakage-requirements.md
---

# feat: Trade Spend Leakage — Dash dashboard + linked Excel workbook

## Summary

Build a Dash dashboard (Fly.io, public URL) and a linked downloadable Excel workbook that analyze Cinderhaven's trade spend across five analytical moves and rerank retailers by net revenue after all trade costs. Data flows from the `cinderhaven-data` SQLite submodule → a Python analysis pipeline that pre-computes results into `data/results.db` → the Dash app and workbook generator, both of which read exclusively from `results.db`. Reuses SQL logic and workbook structure from the existing `trade-spend-data-diagnostic` project; the Dash dashboard is the net-new deliverable.

---

## Problem Frame

Trade spend opacity costs specialty food brands real money — the brief and the `trade-spend-data-diagnostic` project establish this fully. (See origin requirements doc.) This plan addresses the implementation: how to build a self-serve, publicly hosted dashboard and a downloadable audit-ready workbook on top of the existing analytical work.

---

## Requirements

- R1. Analysis pipeline reads from `cinderhaven-data` SQLite (read-only) and writes pre-computed results to `data/results.db`.
- R2. Pipeline populates all five analytical moves.
- R3. Leakage detection identifies double-dip deductions, ghost promos, rate discrepancies, and unauthorized deductions — using actual Cinderhaven data numbers, not the brief's aspirational targets.
- R4. Promotional ROI uses rolling-median baseline per SKU/retailer/period.
- R5. Dash app follows `retail-velocity-decision-tool` conventions: Lailara Design System v2, Plotly charts, AG Grid for tables, `dash_bootstrap_components`.
- R6. All five analytical moves are independently shippable; Move 1 and Move 3 are the minimum viable portfolio piece.
- R7. Excel workbook generated dynamically via openpyxl on "Download workbook" click — reads from `results.db`.
- R8. Workbook has six sheets: Summary + one per move, named identically to dashboard sections.
- R9. Dashboard and workbook show identical numbers (same source: `results.db`).
- R10. Deployed to Fly.io as an always-on service; credentials via environment variables only.
- R11. Public URL, no authentication.

**Origin actors:** A1 (Operator/Shawn), A2 (Dashboard viewer — CFO/CEO prospect), A3 (Cinderhaven Data Platform)
**Origin flows:** F1 (Pipeline run), F2 (Dashboard exploration), F3 (Excel audit)
**Origin acceptance examples:** AE1 (bump chart click-to-pin, covers R5, R6), AE2 (leakage ledger expand, covers R3), AE3 (workbook download sheet order, covers R7, R8), AE4 (SSOT unchanged after pipeline run, covers R1), AE5 (shippable after Move 1, covers R6)

---

## Scope Boundaries

- No changes to `cinderhaven-data` generation scripts or SQLite schema
- No authentication or access control
- No self-serve client data input
- No automated pipeline scheduling
- No live Postgres connection from the dashboard (SQLite snapshot approach)
- No advanced lift decomposition models (ARIMA, regression) — rolling median only
- No Power BI dashboard (exists in `trade-spend-data-diagnostic` if needed)
- Brief's aspirational leakage dollar amounts ($340K double-dips, $180K phantom) are not targets — actual data drives the numbers

### Deferred to Follow-Up Work

- Refreshing the SQLite snapshot from Fly.io Postgres: `flyctl postgres connect -a cinderhaven-db` + export script — exists as a pattern in `trade-spend-data-diagnostic`; not needed until platform data changes
- Additional analytical moves beyond the five defined in the requirements

---

## Context & Research

### Relevant Code and Patterns

- `projects/published/retail-velocity-decision-tool/app/` — The reference Dash app. Follow exactly: `db.py` (connection pool pattern), `layout.py` (sidebar + main content structure), `callbacks.py` (dispatcher pattern), `charts.py` (Plotly chart builders), `constants.py`, `components.py`. Deploy pattern: `retail-velocity-decision-tool/Dockerfile` + `fly.toml`.
- `projects/published/retail-velocity-decision-tool/app/decisions/promo_roi.py` — Rolling-median promo ROI logic already implemented; adapt for this project's Move 4.
- `projects/published/trade-spend-data-diagnostic/workbook/` — All seven workbook tab generators. Directly reusable: `tab_leak_diagnostic.py`, `tab_promo_efficacy.py`, `tab_retailer_risk.py`, `tab_deduction_ledger.py`, `tab_executive_pulse.py`, `styles.py`. The new project adapts these into a six-sheet workbook reading from `results.db` instead of raw SQLite.
- `projects/published/trade-spend-data-diagnostic/workbook/queries.py` — Shared query helpers (channel rate columns, trailing bounds). Adapt for this project.
- `projects/published/trade-spend-data-diagnostic/sql/` — 22 SQL queries across categories (trade_rate, deductions, promo_roi, retailer, reconciliation, crosswalk). These are the analytical foundation for the pipeline.
- `projects/published/trade-spend-data-diagnostic/cinderhaven-data/` — The SQLite submodule reference. This project adds the same submodule at `data/cinderhaven-data/`.

### Institutional Learnings

- **Schema details confirmed** (from `trade-spend-data-diagnostic/HANDOFF.md`): `scan_data` uses `week_ending` (not `week_start`), revenue = `dollars_sold`, not `units × price`. `sku_costs` has per-channel columns (`trade_spend_pct_walmart`, `trade_spend_pct_costco`, `trade_spend_pct_whole_foods`, `trade_spend_pct_unfi`, `trade_spend_pct_dtc`, `trade_spend_pct_kehe`, `trade_spend_pct_regional`). `deductions.retailer_id` uses slugs (`walmart`, `costco`, etc.).
- **Actual data numbers** (from live Fly.io Postgres, verified 2026-05-31): double-dips 173 instances $15,264, ghost promos 817 instances $75,781, rate discrepancies 1 instance $395, unauthorized 1,521 instances $144,320. Total leakage: $235,760. Postgres dataset is ~4.5× larger than the SQLite snapshot in `TRADE_SPEND_VERIFICATION.md` — Postgres is SSOT per CLAUDE.md.
- **SQLite architecture** (from `trade-spend-data-diagnostic/DECISIONS.md`): Live Postgres connection is fragile on Windows (password management, flyctl proxy). Export to SQLite once; projects consume the SQLite file. Reconcilability to Postgres SSOT is maintained by the export chain: `flyctl postgres connect -a cinderhaven-db` → SQLite. All downstream projects use the same submodule.
- **Bump chart approach** (deferred in requirements, resolved): Use Plotly `go.Scatter` with two x-positions (x=0 = gross rank, x=1 = net rank). Each retailer is one trace, colored by Lailara categorical palette. Crossing lines emerge naturally from retailers where gross rank ≠ net rank. Rank 1 at top (y-axis inverted or rank=1 plotted at largest y-value).
- **Double-dip detection** (verified against Postgres 2026-05-31): No `is_double_dip` flag in Postgres. Detection: `promo_billback` deductions matched to a promotion with `funding_mechanism = 'off_invoice'` by `retailer_id + (start_week to end_week + 14 days)`; deduplicated on `deduction_id`. 173 instances / $15,264.
- **Ghost promo detection** (adapted from `sql/INVENTORY.md` query #14): `promo_billback` deductions with no matching promotion (any funding_mechanism) within ±14 day window. 817 instances / $75,781.

### External References

- Lailara Design System v2: `projects/published/lailara-design-system/LAILARA_DESIGN_SYSTEM.md` — colors, typography, chart conventions, click-to-pin interaction, print rules.

---

## Key Technical Decisions

- **SQLite snapshot via submodule, not live Postgres query**: Follows `trade-spend-data-diagnostic` pattern. Simpler, no flyctl dependency at runtime. Reconcilability to Postgres SSOT preserved by the export chain. (see origin: Key Decisions)
- **Pre-compute into `data/results.db`**: Pipeline reads `cinderhaven-data` SQLite (read-only), computes all five moves, writes to a separate `results.db`. Dashboard and workbook generator both read from `results.db` only. Keeps request path fast. (see origin: Key Decisions)
- **Reuse `trade-spend-data-diagnostic` query and workbook logic**: Do not rewrite what already works. Copy/adapt the relevant modules; own them in this repo. Avoids cross-repo import coupling while avoiding duplication.
- **Adapt `promo_roi.py` from `retail-velocity-decision-tool`**: Rolling-median baseline is already implemented there. Adapt for the pipeline layer rather than reimplementing.
- **Bump chart via `go.Scatter`**: Two x-positions (gross rank at x=0, net rank at x=1), one trace per retailer, connected lines. Rank 1 plotted highest on y-axis (invert axis or map rank to descending y-value). Avoids external bump-chart libraries.
- **Actual data numbers, not brief targets**: Brief's $340K double-dip / $180K phantom figures were aspirational. Dashboard shows actual Postgres data. Story is still compelling: $235K total leakage across 4 buckets against a 17.3% structural trade rate.
- **Build in sales-impact order**: Move 1 → Move 3 → Move 2 → Move 4 → Move 5. Each is independently deployable. (see origin: R26, Key Decisions)

---

## Open Questions

### Resolved During Planning

- **Cinderhaven schema**: Confirmed via `trade-spend-data-diagnostic` codebase. Key columns documented above in Institutional Learnings.
- **Actual leakage numbers**: Verified against live Postgres 2026-05-31. Double-dips: 173 / $15K. Ghost promos: 817 / $76K. Rate discrepancies: 1 / $395. Unauthorized: 1,521 / $144K. Total: $235,760. SQLite snapshot numbers in `TRADE_SPEND_VERIFICATION.md` are stale.
- **Bump chart implementation**: `go.Scatter` with dual x-positions. No external library needed.
- **`trade-spend-data-diagnostic` relationship**: Build on top — reuse queries and workbook modules. Own copies in this repo.
- **SQLite vs Postgres**: SQLite snapshot via `cinderhaven-data` submodule, same pattern as `trade-spend-data-diagnostic`.

### Deferred to Implementation

- **Rolling-median window size for Move 4**: Examine the `scan_data` date distribution (104-week window, weekly cadence) during U5 implementation. Use 8-week window as starting hypothesis; adjust if the synthetic promo lift signal is too noisy.
- **AG Grid version compatibility**: Confirm `dash-ag-grid` version available in the Dash ecosystem matches `retail-velocity-decision-tool`'s usage before installing.
- **`results.db` schema design**: Exact table and column names finalized during U1 pipeline scaffolding. Naming should mirror the move names (e.g., `results_net_revenue`, `results_leakage`, etc.).

---

## Output Structure

    trade-spend-leakage/
    ├── data/
    │   ├── cinderhaven-data/           ← git submodule (read-only source)
    │   └── results.db                  ← pipeline output (gitignored)
    ├── pipeline/
    │   ├── __init__.py
    │   ├── db.py                       ← SQLite connection helpers
    │   ├── move1_net_revenue.py        ← Move 1 computation
    │   ├── move2_efficiency.py
    │   ├── move3_leakage.py
    │   ├── move4_promo_roi.py
    │   ├── move5_accrual.py
    │   └── run.py                      ← orchestrates full pipeline run
    ├── app/
    │   ├── __init__.py
    │   ├── app.py                      ← Dash app entry point
    │   ├── layout.py
    │   ├── callbacks.py
    │   ├── charts.py
    │   ├── components.py
    │   ├── constants.py
    │   └── db.py                       ← results.db reader
    ├── workbook/
    │   ├── __init__.py
    │   ├── generator.py
    │   ├── styles.py
    │   ├── tab_summary.py
    │   ├── tab_net_revenue.py
    │   ├── tab_leakage.py
    │   ├── tab_efficiency.py
    │   ├── tab_promo_roi.py
    │   └── tab_accrual.py
    ├── tests/
    │   ├── test_move1_net_revenue.py
    │   ├── test_move3_leakage.py
    │   ├── test_move4_promo_roi.py
    │   └── test_workbook.py
    ├── Dockerfile
    ├── fly.toml
    ├── requirements.txt
    └── run.py                          ← entry point: `python run.py pipeline` or `python run.py app`

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
Data flow:

  cinderhaven-data/data/cinderhaven_product_master.db   ← read-only SQLite submodule
             │
             │  (pipeline/run.py — run once before deploying)
             ▼
  data/results.db   ← pre-computed results (5 move tables)
      │                        │
      │  app/db.py             │  workbook/generator.py
      ▼                        ▼
  Dash app                Excel workbook
  (Fly.io, public URL)    (downloaded via dcc.Download)

Dashboard interaction model (Lailara click-to-pin):
  User clicks chart element
    → callback stores clicked ID in dcc.Store
    → callout card renders above chart with pinned detail
    → non-selected elements dim to opacity 0.2-0.3
    → clicking again clears dcc.Store → card dismisses

Build order (each U is independently deployable):
  U1 (setup) → U2 (Move 1 + app shell) → U3 (Move 3) → U4 (Move 2) → U5 (Move 4) → U6 (Move 5) → U7 (workbook) → U8 (deploy)
```

---

## Implementation Units

### U1. Project setup — submodule, pipeline scaffold, and app skeleton

**Goal:** Wire the `cinderhaven-data` submodule, create `data/results.db` schema, scaffold the pipeline runner and Dash app entry point.

**Requirements:** R1, R10

**Dependencies:** None

**Files:**
- Create: `data/cinderhaven-data/` (git submodule — `git submodule add <cinderhaven-data-repo-url> data/cinderhaven-data`)
- Create: `pipeline/__init__.py`, `pipeline/db.py`, `pipeline/run.py`
- Create: `app/__init__.py`, `app/app.py`, `app/constants.py`
- Create: `requirements.txt`
- Create: `.gitignore` (add `data/results.db`, `.venv/`, `__pycache__/`)
- Modify: `README.md` (add How to Run section)

**Approach:**
- `pipeline/db.py` provides two connection helpers: `source_conn()` (read-only connection to `cinderhaven-data/data/cinderhaven_product_master.db`) and `results_conn()` (read-write connection to `data/results.db`). Follow the same `contextmanager` pattern as `retail-velocity-decision-tool/app/db.py`.
- `pipeline/run.py` imports each move module and runs them in order. Accepts a `--moves` flag to run a subset.
- `app/app.py` initializes the Dash app with `dash_bootstrap_components` and `BOOTSTRAP` theme. Imports `layout` and `callbacks`.
- `requirements.txt` pins: `dash`, `dash-bootstrap-components`, `dash-ag-grid`, `plotly`, `psycopg2-binary` (kept for Postgres export compatibility), `openpyxl`, `pandas`, `gunicorn`.

**Patterns to follow:**
- `retail-velocity-decision-tool/app/db.py` for connection management
- `retail-velocity-decision-tool/app/run.py` for app entry point
- `trade-spend-data-diagnostic/scripts/build_db.py` for submodule path resolution

**Test scenarios:**
- Happy path: `pipeline/db.py` `source_conn()` returns a valid SQLite connection; `SELECT COUNT(*) FROM scan_data` returns > 0 rows.
- Error path: If `cinderhaven_product_master.db` is missing, `source_conn()` raises a clear `FileNotFoundError` with the expected path in the message.
- Happy path: `results_conn()` creates `data/results.db` if it does not exist.
- Test expectation: `app.py` skeleton — none yet; behavioral tests come in U2.

**Verification:**
- `python pipeline/run.py --moves none` exits 0 with no errors.
- `python -c "from app.app import app"` imports without error.
- `data/results.db` is created and empty on first run.

---

### U2. Vertical slice — Move 1: Net Revenue Ranking

**Goal:** Analysis pipeline for Move 1 (net revenue by retailer) + Dash app shell with the bump chart section as the first visible, shippable dashboard.

**Requirements:** R1, R2, R5, R6, R11 — AE1, AE5

**Dependencies:** U1

**Files:**
- Create: `pipeline/move1_net_revenue.py`
- Create: `app/layout.py`
- Create: `app/callbacks.py`
- Create: `app/charts.py`
- Create: `app/components.py`
- Create: `app/db.py` (results reader)
- Test: `tests/test_move1_net_revenue.py`

**Approach:**
- `pipeline/move1_net_revenue.py`: Queries `scan_data` + `sku_costs` to compute per-retailer: `gross_revenue` (SUM of dollars_sold trailing 52w), `trade_spend` (gross_revenue × channel avg trade_spend_pct), `net_revenue` (gross_revenue − trade_spend), `net_to_gross_ratio`. Writes `results_net_revenue` table to `results.db`.
- Channel-to-trade-rate mapping: use `CHANNEL_RATE_COLS` pattern from `trade-spend-data-diagnostic/workbook/queries.py`. Regional chains (Green Basket Market, Southside Grocers, etc.) map to `trade_spend_pct_regional`.
- `app/layout.py`: Section-based layout. Move 1 section contains the bump chart div and a pinned-callout div (hidden by default). Follow `retail-velocity-decision-tool/app/layout.py` brand header + content area pattern.
- `app/charts.py` `bump_chart()`: Plotly `go.Figure` with one `go.Scatter` trace per retailer. x-axis: [0, 1] (gross rank, net rank). y-axis: rank value (1 = top). Each trace is a line + markers. Use Lailara categorical palette (Chicago navy + Hong Kong teal sequence). Axis labels: "By Gross Revenue" / "By Net Revenue". Rank 1 plotted at top (invert y-axis or map rank 1 → N, rank N → 1).
- `app/callbacks.py` click callback: stores `clickData` from bump chart in `dcc.Store`. A second callback reads the Store and renders the dark callout card (retailer name, gross revenue, trade spend, net revenue, net-to-gross %). Second click on same retailer clears Store (dismisses card). Non-selected elements dim via `opacity` style on traces.
- `app/db.py`: `get_net_revenue()` reads `results_net_revenue` from `results.db` into a pandas DataFrame.

**Patterns to follow:**
- `retail-velocity-decision-tool/app/charts.py` for Plotly chart builder pattern
- `retail-velocity-decision-tool/app/callbacks.py` for dispatcher pattern
- `trade-spend-data-diagnostic/workbook/queries.py` `fetch_channel_rates()` for channel rate mapping

**Test scenarios:**
- Happy path: `compute_net_revenue(conn)` returns a DataFrame with columns `[retailer, gross_revenue, trade_spend, net_revenue, net_to_gross_ratio]` and one row per active retailer.
- Happy path: Net revenue rank order differs from gross revenue rank order for at least one retailer (the story exists in the data).
- Edge case: Retailer with `trade_spend_pct = 0` (DTC) has `net_revenue == gross_revenue`.
- Edge case: Regional chains (5 separate retailer names) all use `trade_spend_pct_regional` — verify no KeyError.
- Integration: Covers AE5 — after U2 completes, `python app/app.py` serves the dashboard at localhost with the bump chart visible and the remaining sections absent (not erroring).

**Verification:**
- `python pipeline/run.py --moves 1` completes without error; `results_net_revenue` table exists in `results.db` with correct row count.
- `python app/app.py` serves the dashboard; bump chart renders with retailer lines; clicking a line shows the dark callout card.
- At least one retailer's net rank differs from its gross rank.

---

### U3. Vertical slice — Move 3: Leakage Detection

**Goal:** Analysis pipeline for Move 3 (leakage detection) + dashboard leakage ledger with click-to-expand AG Grid instance table. Second shippable milestone.

**Requirements:** R1, R2, R3, R5, R6 — AE2

**Dependencies:** U2

**Files:**
- Create: `pipeline/move3_leakage.py`
- Modify: `app/layout.py` (add Move 3 section)
- Modify: `app/callbacks.py` (leakage ledger click)
- Modify: `app/charts.py` (leakage ledger component)
- Modify: `app/db.py` (add `get_leakage()`)
- Test: `tests/test_move3_leakage.py`

**Approach:**
- `pipeline/move3_leakage.py` computes four leakage sub-types:
  1. **Double-dips**: `promo_billback` deductions matched (DISTINCT ON deduction_id) to a promotion with `funding_mechanism = 'off_invoice'` by retailer_id + (start_week to end_week + 14 days). No `is_double_dip` flag in Postgres. 173 instances / $15,264 (Postgres SSOT).
  2. **Ghost promos (phantom)**: `promo_billback` deductions with no matching promotion (any funding_mechanism) within ±14 day window. 817 instances / $75,781.
  3. **Rate discrepancies**: `promo_billback` matched to non-off_invoice promotion where `d.amount > p.promo_cost * 1.05`. 1 instance / $395.
  4. **Unauthorized**: `deduction_type NOT IN` known operational set — currently `pricing_error` type. 1,521 instances / $144,320.
  Writes `results_leakage_summary` (one row per sub-type: type, dollar_total, instance_count, classification) and `results_leakage_instances` (one row per instance) to `results.db`.
- Dashboard leakage ledger: A styled HTML table or `dash-ag-grid` with four rows (one per sub-type). Columns: type name, dollar total, instance count, classification (Recoverable / Reallocatable). Total row at bottom.
- Click-to-expand: clicking a row stores the sub-type in `dcc.Store`; a callback renders the AG Grid instance table below the ledger with promotion identifier, period, agreed amount, actual deduction, variance, classification.
- Adapt `trade-spend-data-diagnostic/workbook/tab_leak_diagnostic.py` logic for query structure.

**Patterns to follow:**
- `trade-spend-data-diagnostic/workbook/tab_leak_diagnostic.py` for leakage query patterns
- `trade-spend-data-diagnostic/sql/INVENTORY.md` query #9 (double-dip), #14 (ghost promos)
- `retail-velocity-decision-tool` callbacks for click-to-expand pattern

**Test scenarios (updated for Postgres SSOT 2026-05-31):**
- Happy path: `detect_double_dips(conn)` returns rows; all have leakage_type="double_funded" and classification="Recoverable".
- Happy path: `detect_ghost_promos(conn)` returns rows; all have classification="Reallocatable" and null promo_id.
- Edge case: `detect_rate_discrepancies(conn)` handles empty result set without error (1 row in current data).
- Edge case: All four sub-type functions return DataFrames with consistent _INSTANCE_COLS even when empty.
- Integration: Summary dollar totals match sum of instance actual_amounts per type.

**Verification:**
- `python pipeline/run.py --moves 3` populates `results_leakage_summary` and `results_leakage_instances`.
- Dashboard leakage ledger renders all four sub-types with correct dollar totals.
- Clicking a sub-type row expands the AG Grid instance table.

---

### U4. Vertical slice — Move 2: Trade Spend Efficiency

**Goal:** Analysis pipeline for Move 2 (trade spend % and incremental lift per dollar) + dashboard dual-measure chart.

**Requirements:** R1, R2, R5

**Dependencies:** U3 (for established app/callbacks/charts patterns)

**Files:**
- Create: `pipeline/move2_efficiency.py`
- Modify: `app/layout.py`
- Modify: `app/callbacks.py`
- Modify: `app/charts.py`
- Modify: `app/db.py`
- Test: (no dedicated test file — coverage via integration; Move 2 is read-only aggregation with no complex logic)

**Approach:**
- `pipeline/move2_efficiency.py`: Per retailer, compute (a) trade spend as % of gross revenue (from `results_net_revenue`) and (b) incremental lift per trade spend dollar (total promo lift units / total promo_cost from `promotions` where promo lift is measurable). Writes `results_trade_efficiency` to `results.db`.
- Incremental lift: for promotions with sufficient pre-promotion scan data (using rolling median baseline approach from Move 4 once available; in Move 2, use the simpler ratio from the `promotions` table if `promo_cost` and matching scan lift are available). If lift is not computable per retailer, show only trade spend %. Flag un-measurable lift with a "Insufficient data" indicator.
- Dashboard chart: Two-measure horizontal bar chart (or dual-axis) per retailer, ranked by efficiency. Use Lailara Hong Kong teal for efficiency (efficient = dark, inefficient = light) and Singapore orange for trade spend % when high.

**Patterns to follow:**
- `trade-spend-data-diagnostic/workbook/tab_retailer_risk.py` for per-retailer trade spend rate logic
- `trade-spend-data-diagnostic/sql/INVENTORY.md` query #17 (gross margin by channel), #18 (operational deductions by retailer)

**Test scenarios:**
- Test expectation: none — Move 2 is an aggregation join with no branching logic beyond the lift measurability flag. Covered by pipeline run verification.

**Verification:**
- `python pipeline/run.py --moves 2` populates `results_trade_efficiency` without error.
- Dashboard chart renders for all retailers; retailers with unmeasurable lift show the indicator.

---

### U5. Vertical slice — Move 4: Promotional ROI

**Goal:** Analysis pipeline for Move 4 (rolling-median baseline, incremental lift, promo ROI) + dashboard scatter chart with break-even line.

**Requirements:** R1, R2, R4, R5

**Dependencies:** U4

**Files:**
- Create: `pipeline/move4_promo_roi.py`
- Modify: `app/layout.py`
- Modify: `app/callbacks.py`
- Modify: `app/charts.py`
- Modify: `app/db.py`
- Test: `tests/test_move4_promo_roi.py`

**Approach:**
- `pipeline/move4_promo_roi.py`: For each promotion in the `promotions` table (188 rows, 75 distinct promo events), retrieve the weekly `scan_data` for the promoted SKU × retailer. Compute rolling-median baseline using an 8-week window preceding the promo start date. Incremental units = promo-period sales − baseline. Incremental gross margin = incremental units × (wholesale_price − COGS). Promo ROI flag: `promo_cost > incremental_gross_margin` = money-losing. Writes `results_promo_roi` to `results.db`.
- Adapt rolling-median logic from `retail-velocity-decision-tool/app/decisions/promo_roi.py`.
- Only 18 of 75 promo events have sufficient pre-promo baseline data (per `data_generation_log.md`). Flag the remaining 57 as "Insufficient baseline data."
- Dashboard chart: `go.Scatter` with one marker per promotion. x-axis: trade spend cost. y-axis: gross margin on incremental units. Break-even line: y = x (dashed, `#666666`). Promotions below line: Tokyo rose `#b82d4a`. Above line: Hong Kong teal. Hover/click-to-pin shows: promo event, SKU, retailer, cost, margin, ROI.
- Footnote below chart: "Baseline estimated from 8-week pre-promotion rolling median. 18 of 75 promotions have sufficient data."

**Patterns to follow:**
- `retail-velocity-decision-tool/app/decisions/promo_roi.py` for rolling-median baseline logic
- `trade-spend-data-diagnostic/workbook/tab_promo_efficacy.py` for promo-scan join pattern
- `trade-spend-data-diagnostic/sql/INVENTORY.md` query #12 (weekly volumes per SKU per retailer)

**Test scenarios:**
- Happy path: `compute_promo_roi(conn)` returns a DataFrame with 75 rows (one per promo event), including columns `promo_cost`, `incremental_margin`, `is_money_losing`, `has_sufficient_baseline`.
- Happy path: Promotions with `has_sufficient_baseline = False` have `is_money_losing = None`, not False.
- Edge case: Promotion with promo start date within the first 8 weeks of scan data window has `has_sufficient_baseline = False` — no crash.
- Edge case: Promotion with `promo_cost = NULL` (7 rows in the data) is excluded from ROI calculation, not treated as $0.
- Integration: 18 promotions flagged with `has_sufficient_baseline = True`; subset of those flagged `is_money_losing = True`.

**Verification:**
- `python pipeline/run.py --moves 4` populates `results_promo_roi` with 75 rows.
- Dashboard scatter chart renders; break-even line visible; footnote shown.

---

### U6. Vertical slice — Move 5: Accrual Reconciliation

**Goal:** Analysis pipeline for Move 5 (accrued vs actual trade spend by period) + dashboard bar chart.

**Requirements:** R1, R2, R5

**Dependencies:** U5

**Files:**
- Create: `pipeline/move5_accrual.py`
- Modify: `app/layout.py`
- Modify: `app/callbacks.py`
- Modify: `app/charts.py`
- Modify: `app/db.py`

**Approach:**
- `pipeline/move5_accrual.py`: Accrued trade spend = implied monthly trade spend from `sku_costs` rates × monthly gross revenue. Actual deducted = SUM of `deductions.amount` by month (trailing 365 days). Variance = accrued − actual. Writes `results_accrual` to `results.db`.
- Group by month; show last 12 months.
- Dashboard: Grouped bar chart (`go.Bar`) — accrued (Chicago navy) vs actual deducted (Hong Kong teal) side by side per month. Variance as a line overlay on secondary axis.

**Patterns to follow:**
- `trade-spend-data-diagnostic/workbook/tab_executive_pulse.py` for revenue + deduction aggregation by period

**Test scenarios:**
- Test expectation: none — straightforward period aggregation. Covered by pipeline run verification.

**Verification:**
- `python pipeline/run.py --moves 5` populates `results_accrual` with 12 monthly rows.
- Dashboard chart renders with grouped bars and variance line.

---

### U7. Excel workbook generation and download

**Goal:** Implement server-side Excel workbook generation via openpyxl, reading from `results.db`. Six sheets matching dashboard section names. Downloadable via `dcc.Download` button.

**Requirements:** R7, R8, R9 — AE3

**Dependencies:** U6 (all five results tables populated)

**Files:**
- Create: `workbook/__init__.py`, `workbook/generator.py`, `workbook/styles.py`
- Create: `workbook/tab_summary.py`, `workbook/tab_net_revenue.py`, `workbook/tab_leakage.py`, `workbook/tab_efficiency.py`, `workbook/tab_promo_roi.py`, `workbook/tab_accrual.py`
- Modify: `app/callbacks.py` (add download callback)
- Modify: `app/layout.py` (add Download button)
- Test: `tests/test_workbook.py`

**Approach:**
- Adapt `trade-spend-data-diagnostic/workbook/styles.py` (Lailara openpyxl style helpers) verbatim.
- `workbook/generator.py` `generate_workbook(results_db_path) -> bytes`: Creates an `openpyxl.Workbook`, calls each tab builder, returns `workbook.save()` to a `BytesIO` buffer, returns the buffer's bytes.
- Each tab module follows the `trade-spend-data-diagnostic` pattern: reads from `results.db` (not raw cinderhaven SQLite), applies openpyxl formatting via `styles.py`.
- Sheet naming: "Summary", "Net Revenue Ranking", "Leakage Detection", "Trade Spend Efficiency", "Promotional ROI", "Accrual Reconciliation" — identical to dashboard section labels.
- Leakage Detection sheet includes source identifiers (deduction_id, promo_id) so CFO can trace back to SSOT.
- `dcc.Download` callback: `Output("download-workbook", "data")` triggered by button click; calls `generate_workbook()`, returns `dcc.send_bytes(workbook_bytes, "cinderhaven-trade-spend-analysis.xlsx")`.

**Patterns to follow:**
- `trade-spend-data-diagnostic/workbook/` — all tab builders, styles, and generator pattern

**Test scenarios:**
- Covers AE3: `generate_workbook(results_db_path)` returns bytes that open as a valid xlsx with sheet names `["Summary", "Net Revenue Ranking", "Leakage Detection", "Trade Spend Efficiency", "Promotional ROI", "Accrual Reconciliation"]` in that order.
- Happy path: Each sheet has at least one row of data (not empty).
- Happy path: "Net Revenue Ranking" sheet and `results_net_revenue` table have identical retailer-level totals (same numbers, no drift).
- Edge case: `generate_workbook()` called when `results.db` has only Move 1 and Move 3 populated (partial build state) — produces a workbook with only those two move sheets populated; remaining sheets have a header row and a "Not yet computed" placeholder.

**Verification:**
- `generate_workbook()` produces a valid xlsx with correct sheet order.
- Download button in dashboard triggers download of named file.
- Net Revenue Ranking numbers in workbook match dashboard.

---

### U8. Fly.io deployment

**Goal:** Dockerfile, `fly.toml`, and deployment verification. Dashboard accessible at a public Fly.io URL.

**Requirements:** R10, R11 — AE5 (at scale)

**Dependencies:** U7 (full app complete)

**Files:**
- Create: `Dockerfile`
- Create: `fly.toml`
- Create: `run.py` (entry point — runs pipeline then starts gunicorn)

**Approach:**
- Follow `retail-velocity-decision-tool/Dockerfile` exactly. Key differences: this app uses SQLite only (no DATABASE_URL needed at runtime after the pipeline runs). The `data/results.db` must be generated during the Docker build step or included in the image.
- Build strategy: Run `python pipeline/run.py` during Docker build (after copying `cinderhaven-data/data/cinderhaven_product_master.db` into the image). `results.db` is baked into the image. No live database connection needed at runtime.
- `fly.toml`: `internal_port = 8050` (Dash default). Always-on service (no auto-stop).
- Credentials: No database credentials needed at runtime (SQLite only). If future Postgres refresh support is added, `DATABASE_URL` will be a Fly secret.
- `run.py`: Checks if `data/results.db` exists; if not, runs pipeline. Then starts gunicorn on `app.app:server`.

**Patterns to follow:**
- `retail-velocity-decision-tool/Dockerfile` and `fly.toml` for Fly.io deployment pattern

**Test scenarios:**
- Test expectation: none (deployment is a manual verification step, not unit-testable).

**Verification:**
- `docker build .` succeeds locally; `data/results.db` present in the built image.
- `fly deploy` succeeds; dashboard accessible at the Fly.io URL.
- "Download workbook" button produces a valid xlsx.

---

## System-Wide Impact

- **Interaction graph:** Dash callbacks are the only interaction surface. The pipeline is a one-shot script with no callbacks. No background workers, no WebSockets.
- **Error propagation:** `source_conn()` and `results_conn()` raise immediately on missing file — no silent failures. Pipeline run errors are logged to stdout and exit nonzero. Dashboard DB read errors surface as empty charts with a visible error div (follow `retail-velocity-decision-tool` pattern).
- **State lifecycle risks:** `results.db` is the only mutable state. It is generated once at build time (or via `pipeline/run.py`) and read-only at runtime. No partial-write risk during serving.
- **Unchanged invariants:** `cinderhaven-data` submodule (and its SQLite schema) is read-only. Pipeline must never call `INSERT`, `UPDATE`, or `DELETE` on the source database.
- **Integration coverage:** The complete flow — pipeline run → `results.db` populated → dashboard reads → workbook generated → download — must be verified end-to-end before deployment (manual check).

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Rolling-median baseline (U5) only has sufficient data for 18 of 75 promotions | Display `has_sufficient_baseline` flag prominently; "Insufficient data" is a valid analytical finding, not a bug |
| Bump chart (U2) crossing-line visual may be unclear with 11 retailers | Show only the 6 major retailers (Walmart, Costco, UNFI, Whole Foods, KeHE, DTC) by default; add toggle to show regional chains |
| `results.db` baked into Docker image means stale data if Cinderhaven Postgres updates | Acceptable for synthetic data that doesn't change; add a `refresh` README section explaining the export chain |
| `trade-spend-data-diagnostic` workbook modules may have openpyxl API drift from the version in this project | Pin openpyxl to same version range as `trade-spend-data-diagnostic/requirements.txt` (`>=3.1.5,<4.0`) |

---

## Documentation / Operational Notes

- README must document: how to run the pipeline (`python pipeline/run.py`), how to run the dashboard locally (`python app/app.py`), and how to refresh Cinderhaven data from Postgres (`flyctl proxy 5432:5432 -a cinderhaven-db` + export script pattern from `trade-spend-data-diagnostic`).
- `fly.toml` must document the `fly deploy` command.
- Update `DECISIONS.md` with the SQLite architecture decision once U1 is complete.

---

## Sources & References

- **Origin document:** [docs/brainstorms/trade-spend-leakage-requirements.md](docs/brainstorms/trade-spend-leakage-requirements.md)
- Reference app: `projects/published/retail-velocity-decision-tool/app/`
- Existing analytical work: `projects/published/trade-spend-data-diagnostic/workbook/` and `sql/`
- Promo ROI logic: `projects/published/retail-velocity-decision-tool/app/decisions/promo_roi.py`
- Verified Cinderhaven numbers: `projects/published/trade-spend-data-diagnostic/cinderhaven-data/TRADE_SPEND_VERIFICATION.md`
- Lailara Design System: `projects/published/lailara-design-system/LAILARA_DESIGN_SYSTEM.md`
