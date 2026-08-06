# trade-spend-leakage — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-31 — Reuse `trade-spend-data-diagnostic` workbook/query logic; own adapted copies in this repo
- **Why:** The workbook (7 tabs, 60 validation checks) and SQL queries (22 queries across all 5 analytical moves) are fully built and verified in `trade-spend-data-diagnostic`. Rebuilding from scratch wastes effort and risks drift. Cross-repo imports create coupling — adapted copies in this repo maintain independence while avoiding duplication.
- **Scope:** `workbook/` and `pipeline/` modules
- **Do not:** Import directly from `trade-spend-data-diagnostic`. Copy and adapt the relevant modules into this repo at U1/U7 setup.

### 2026-05-31 — Tier: Heavy
- **Why:** Portfolio piece maintained long-term; high analytical complexity; dual deliverable (dashboard + Excel); warrants full 11-step workflow with gstack gates.
- **Scope:** Global
- **Do not:** Skip /office-hours, /plan-ceo-review, or /plan-eng-review gates.

### 2026-05-31 — Dual delivery: Excel workbook (lead) + interactive dashboard (hook)
- **Why:** CFO needs to audit join logic and trace data lineage — Excel is the operational engine. CEO needs the net-revenue reframe visually — dashboard is the "aha" moment. Both, not either.
- **Scope:** Global deliverable structure
- **Do not:** Collapse to a single deliverable format.

---

## Data & Schema

### ~~2026-05-31 — Use SQLite snapshot via `cinderhaven-data` git submodule, not live Postgres connection~~ *(superseded 2026-05-31 — see Postgres entry below)*
- ~~**Why:** Every other Cinderhaven portfolio project uses this pattern. Live Postgres adds connection pooling complexity.~~
- ~~**Scope:** Data architecture globally~~
- ~~**Do not:** Add a live DATABASE_URL Postgres connection.~~

### 2026-05-31 — `source_conn()` must connect to Postgres (cinderhaven-data-platform), not SQLite snapshot *(supersedes SQLite entry above)*
- **Why:** The Cinderhaven Data Platform (Fly.io Postgres + dbt pipeline) is the only SSOT. The SQLite approach was adopted following other portfolio projects, but this project's pipeline must query the live platform. SQLite submodule may be kept for offline reference only.
- **Scope:** `pipeline/db.py` `source_conn()` and all pipeline move modules (U2–U6). `results_conn()` remains SQLite — that's pipeline output, not source data.
- **Do not:** Build pipeline query logic against the SQLite submodule. Do not silently fall back to SQLite if `DATABASE_URL` is unset — fail loudly so the misconfiguration is visible.

### 2026-05-31 — Query live Postgres schema before writing any pipeline SQL against a new source table
- **Why:** Postgres schema diverges from the SQLite snapshot in column names (`chain_name` not `retailer`), schema prefix (`raw.scan_data` not `scan_data`), missing flags (`is_double_dip` doesn't exist), and ID formats (`RET-WALMART` not `walmart`). Writing SQL against assumptions produces silent wrong results; discovering at verification time costs a full debug cycle.
- **Scope:** All pipeline move modules (U4–U6 and any future moves).
- **Do not:** Write pipeline SQL against a new source table without first running `information_schema.columns` + `SELECT DISTINCT` on key fields + row count. 5 minutes of schema exploration prevents hours of debugging.

### 2026-05-31 — Pipeline move modules use psycopg2 cursor pattern, not SQLite conn.execute()
- **Why:** `source_conn()` yields a psycopg2 connection. psycopg2 connections don't have `.execute()` — callers must create a cursor. Without `RealDictCursor`, rows are plain tuples and column-name access breaks silently.
- **Scope:** All pipeline move modules (U2–U6).
- **Do not:** Call `conn.execute()` on a source connection — that's the SQLite pattern. Always use `conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)`.

### 2026-05-31 — Cast Postgres numeric results to float before writing to SQLite via pandas to_sql
- **Why:** Postgres returns `numeric` columns as `decimal.Decimal` objects. SQLite's `sqlite3` module doesn't support `decimal.Decimal` as a bind parameter — raises `ProgrammingError: type 'decimal.Decimal' is not supported`. The cast must happen before `df.to_sql()`, not after.
- **Scope:** All pipeline `run()` functions (U2–U6) that read from Postgres and write to results.db.
- **Do not:** Pass a DataFrame with `decimal.Decimal` columns to `df.to_sql()` on a SQLite connection. Always cast numeric columns with `df[col] = df[col].astype(float)` first.

### ~~2026-05-31 — promotions.retailer_id uses RET-\* format; retailer_deductions uses lowercase slugs~~ *(superseded 2026-06-01 — see entry below)*
- ~~**Why:** Discovered during U4 when the slug_map VALUES CTE produced zero matches. `raw.promotions.retailer_id` = `RET-WALMART`. `raw.retailer_deductions.retailer_id` = `walmart`. Two different conventions coexist.~~
- ~~**Do not:** Use slug keys for promotions joins.~~

### 2026-06-01 — Both raw.promotions and raw.retailer_deductions use RET-\* retailer_id format *(supersedes 2026-05-31 entry above)*
- **Why:** Live data query confirms both tables use `RET-WALMART`, `RET-COSTCO`, etc. The prior entry was based on a U4 debugging session that misidentified the deductions format. A slug_map CTE built on the wrong assumption killed double-dip and ghost-promo detection silently for two sessions.
- **Scope:** All pipeline modules joining `raw.promotions` to `raw.retailer_deductions` (move3_leakage.py and any future moves). Direct equality join: `ON p.retailer_id = d.retailer_id`.
- **Do not:** Add a slug_map or format-translation CTE between these two tables. Do not assume the tables use different formats without running `SELECT DISTINCT retailer_id` on both first.

### 2026-05-31 — scan_data retailer names come from stores join, not a direct column
- **Why:** `scan_data` has `store_id`, not `retailer_id`. Retailer display names (`'Walmart'`, `'Whole Foods'`, etc.) come from `JOIN stores ON store_id`. Pipeline SQL CASE statements must match these display names. `constants.py` slug keys (`'walmart'`, `'whole_foods'`) are an app-layer convention only. Getting this wrong silently produces NULL trade rates.
- **Scope:** All pipeline move modules that aggregate by retailer (U2–U6 and any future moves).
- **Do not:** Reference `scan_data.retailer_id` — it doesn't exist. Do not use slug keys in pipeline SQL CASE statements.

### 2026-05-31 — Use actual Cinderhaven data numbers; brief's leakage targets were aspirational
- **Why:** The brief's specific dollar amounts ($340K double-dips, $180K phantom promos, $95K rate discrepancies) were written before the data was built. Verified actual numbers: 3 double-dips / $19K, 137 ghost promos / ~$96K, trailing-365 deductions $1.2M, structural trade spend $4.4M (17.3%). The story is still compelling on real numbers and more credible than inflated targets.
- **Scope:** All dashboard displays and workbook figures
- **Do not:** Hard-code the brief's aspirational dollar amounts. Dashboard and workbook must show whatever the actual Cinderhaven data produces.

### 2026-05-31 — Use synthetic Cinderhaven data
- **Why:** Trade spend rates by retailer are among the most sensitive numbers a brand has — proprietary negotiation data. Cinderhaven is the standard synthetic brand for all Lailara portfolio pieces.
- **Scope:** All data used in this project
- **Do not:** Use real brand data.

### 2026-05-31 — Pipeline moves use separate queries + Python merge, not single JOIN
- **Why:** Easier to debug each data source independently; avoids complex multi-source CTEs. Consistent with the pattern established in move2_efficiency (one Postgres query + one SQLite read merged via pandas). Each query can be run and inspected in isolation, and merge logic is visible as ordinary DataFrame code.
- **Scope:** All pipeline move modules that draw from multiple source tables (U5–U6 and any future moves).
- **Do not:** Combine accrued and actual deduction logic (or any other multi-source aggregation) into a single Postgres CTE or JOIN. Debug isolation is worth the extra round-trip.

### 2026-05-31 — Use `/_dash-layout` JSON to verify dashboard, not preview screenshot
- **Why:** Preview screenshot tool times out (30s) with Plotly's JS bundle. `/_dash-layout` returns the full component tree and figure data as JSON — verifies component IDs, trace counts, callback wiring, and data values reliably and instantly.
- **Scope:** All dashboard verification for this project (U4–U8).
- **Do not:** Rely on `preview_screenshot` to verify that chart data rendered correctly. Use it only for visual spot-checks where a timeout is acceptable. Use `curl http://127.0.0.1:<port>/_dash-layout | python -c "..."` for data/structure verification.

### 2026-06-01 — Use `fly proxy 5434:5433 -a cinderhaven-db` for local pipeline runs
- **Why:** `cinderhaven-db` Postgres listens on port 5433 (not standard 5432). Local port 5432 is occupied by a local Postgres install. `fly proxy 5433:5432` silently forwards to the wrong remote port; `fly proxy 5434:5433` is the correct mapping. DATABASE_URL must use port 5434: `postgres://postgres:<pass>@localhost:5434/cinderhaven`.
- **Scope:** All local `python pipeline/run.py` runs and live `pytest` runs requiring DATABASE_URL.
- **Do not:** Use `fly proxy 5432 -a cinderhaven-db` (port conflict) or `fly proxy 5433:5432 -a cinderhaven-db` (wrong remote port — Postgres is on 5433, not 5432).

### 2026-06-29 — Move 1 net revenue = gross − structural trade − operational deductions
- **Why:** Prior definition used only structural rate-card spend (7–12%), which was too compressed to differentiate retailers meaningfully. The dashboard claims to show revenue "after all trade costs," which requires actual deductions too. Operational deductions (damaged, spoilage, late delivery, short ship, label/pallet fines, pricing errors) from retailer_deductions are additive to the structural rate. Promo billbacks and slotting are excluded because the structural rate already funds those — including both would double-count.
- **Scope:** `pipeline/move1_net_revenue.py`. Move 2 derives trade_spend_pct from Move 1 results, so it inherits the fix automatically.
- **Do not:** Include promo_billback or slotting in the deduction add-on — they overlap with the structural rate card. Do not use total deductions as a replacement for structural trade spend — they measure different things (chargebacks vs off-invoice allowances).

### 2026-06-29 — Kroger uses dedicated trade_spend_pct_kroger column, not the regional ELSE
- **Why:** The sku_costs table has a `trade_spend_pct_kroger` column (10%) but the CASE statement was missing a Kroger branch, causing it to fall through to the ELSE (regional at 7%). Kroger's trade cost was understated by 3pp.
- **Scope:** `pipeline/move1_net_revenue.py` SQL CASE statement.
- **Do not:** Assume sku_costs column set matches the CASE branches without checking — query `information_schema.columns` when adding new retailers.

### 2026-06-29 — Section 01 slopegraph shows gap compression, not rank flips
- **Why:** With the corrected net-revenue definition (structural + operational deductions), no retailer changes rank gross→net. Revenue gaps between adjacent retailers ($350K–$1.7M) are too large for trade cost differences ($20K–$220K) to bridge. Rather than manufacture a finding, the copy was rewritten to frame what the data actually shows: trade costs compress the top-3 gap from $820K to $586K (29%). The slopegraph still communicates the compression visually through converging lines even without crossings.
- **Scope:** `app/layout.py` Section 01 copy and footnote.
- **Do not:** Hard-code aspirational rank flip narratives. The chart shows whatever the data produces.

### 2026-07-24 — Palette adherence regression test guards against ad-hoc hex drift
- **Why:** `constants.py` had 3 hardcoded hex literals copy-pasted from `LL_STATUS` values and `layout.py` had `#ffffff` instead of `CARD_TEXT` — all invisible to code review since they matched the palette by value. A systematic scan is the only reliable way to catch this class of drift. The test walks every public attribute of `lailara_palette` (including nested lists/dicts) to build the allowed set dynamically.
- **Scope:** `tests/test_palette_adherence.py` scans `app/charts.py`, `app/layout.py`, `app/constants.py`.
- **Do not:** Whitelist violations instead of fixing them. The `_STRUCTURAL_EXCEPTIONS` set exists for non-palette structural values only (e.g., rgba overlays defined in the spec) — keep it empty or near-empty.

### 2026-06-30 — Remove bracket annotations from Section 01 slopegraph; compression story lives in prose
- **Why:** The left/right vertical brackets, "$820K"/"$586K" dollar labels, and "Top-3 gap..." caption collided with y-axis ticks and end labels even after adjusting positions. The body copy already states the $820K → $586K / 29% compression, and the converging lines show it visually — the annotations were redundant. Removing them also let the right margin shrink from 220→180 and x-range from 1.22→1.08.
- **Scope:** `app/charts.py` `bump_chart()`.
- **Do not:** Re-add chart-level gap annotations. If the compression numbers change, update the Section 01 body copy in `app/layout.py`.

### 2026-08-06 — Derive trailing-window footnote spans from pipeline output; never hardcode them
- **Resolves:** the dormant-defect entry under "Known Defects (dormant)" below (now struck through) — this is the dedicated pass that entry deferred.
- **Decision:** The Dash demo footnotes state their week/month span from the data, not from a literal string.
- **Why:** `app/layout.py` hardcoded "Trailing 52 weeks." (Move 1), "trailing 52 weeks" (Move 2, "as computed in Move 1"), and "trailing-12-month" (Move 5). All three were TRUE for the fixed canonical Cinderhaven dataset but assert a data-dependent span independent of the data: a reseed or window change would leave the text asserting a span the data no longer has — the silent-misstatement class that motivated the trade-spend `warehouse_adapter` fix (commit 4e2a6d9, Meridian dry run). Move 1 now persists the actual distinct-week count to a `results_net_revenue_window` table; the layout reads it (and the accrual month count from `len(results_accrual)`) and renders the number. `week_count = 52` is verified against `reference/canonical_values.json` (`scan_weeks.trailing_12m = 52`) and the `scan_data` provenance (2023-01-07..2025-12-27 = 156 weeks, so `LIMIT 52` yields exactly 52). For the canonical data the rendered footnote text is byte-identical (52 weeks / 12 months), so the screenshots do NOT change; only the `results.db` SHA golden moved (a table was added) and was updated deliberately in `tests/test_demo_golden.py`.
- **Scope:** `app/layout.py` footnotes (Moves 1, 2, 5), `pipeline/move1_net_revenue.py`, `app/db.py` (`get_net_revenue_window_weeks`), `tests/test_window_labels.py`, `tests/test_demo_golden.py` golden SHA. Branch `client-mode-2026-08` only — not deployed (main-gated).
- **Do not:** Re-hardcode a week or month count in any rendered surface. If a span must appear, read it from the pipeline output and omit it when unavailable. The identical defect still lives in the Excel workbook — `workbook/tab_net_revenue.py` (lines ~77, ~145), `workbook/tab_efficiency.py` (~133), `workbook/tab_accrual.py` (~101, ~165), `workbook/tab_summary.py` (~293) — which is a separate deliverable with its own golden; it is flagged for a follow-up, not fixed here.

### 2026-05-31 — results.db is pre-generated locally and baked into the Docker image via COPY
- **Why:** Fly Depot build servers don't have access to the Fly private network, so the pipeline can't connect to `cinderhaven-db.internal` during `fly deploy`. Pre-generating locally and including via `COPY` is simpler and equally reliable for synthetic data that doesn't change frequently.
- **Scope:** trade-spend-leakage Dockerfile and deployment process
- **Do not:** Attempt to run `pipeline/run.py` during Docker build via a build secret or build arg — Depot DNS will fail on any `.internal` / `.flycast` hostname. To refresh data: run pipeline locally, then `fly deploy`.

---

## Visualization

### 2026-05-31 — Do not use Streamlit for the dashboard
- **Why:** User strongly dislikes Streamlit.
- **Scope:** Dashboard / interactive deliverable
- **Do not:** Suggest or implement Streamlit. Alternatives: Dash, Evidence, Observable, Panel, plain HTML/JS with D3/Vega.

---

## Output Formats

### 2026-05-31 — Each workbook tab handles its own missing-data state
- **Why:** `generate_workbook()` iterates over all six tab builders regardless of which pipeline moves have run. Centralising a guard in the generator would require it to know which tables each tab needs — coupling that belongs in the tab. Each tab's `_read()` catches `Exception` on the SQLite query and returns `None`; the `build_*()` function writes a placeholder row. This keeps partial-build-state behaviour (only Move 1 populated → only Net Revenue sheet has real data) without generator logic.
- **Scope:** All `workbook/tab_*.py` modules.
- **Do not:** Add table-existence checks or try/except guards to `generator.py`. The guard lives in the tab, not the orchestrator.

---

## Writing & Voice

### 2026-05-31 — Economist style for all written output
- **Why:** Lailara design system standard. Sober, declarative, data-forward. No marketing voice.
- **Scope:** All written deliverables
- **Do not:** Use "leverage," "synergy," "best-in-class," "unlock," "drive value," or hedging language that softens a real finding.

### 2026-05-31 — Frame "ineffective promotions" as leverage, not blame
- **Why:** The $500K ineffective-promotion finding implicates the sales team. Framing it as "money to redeploy" rather than "money wasted" is both more accurate (it IS reallocatable) and preserves the relationship with the VP Sales buyer.
- **Scope:** All written output referencing ineffective/low-ROI promotions
- **Do not:** Call it a "sales mistake," "wasted spend," or imply the sales team made poor decisions.

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

---

## Known Defects (dormant)

### ~~2026-08-06 — Dormant defect: Dash "Trailing 52 weeks" / "trailing-12-month" window footnotes (DO NOT fix now)~~ *(RESOLVED 2026-08-06 — fixed in the dedicated pass it called for; see "Derive trailing-window footnote spans from pipeline output" under Architecture & Pipeline)*
- **Resolved:** The dedicated fix this entry deferred has now landed. `app/layout.py` derives the Move 1/2 week span (from `results_net_revenue_window`, written by `pipeline/move1_net_revenue.py`) and the Move 5 month span (from `len(results_accrual)`), omitting the span when unavailable. `tests/test_window_labels.py` locks the behavior. The rendered text is byte-identical for the canonical data (52 weeks / 12 months) so screenshots did not change; only the `results.db` SHA golden moved and was updated deliberately. The trigger conditions below (reseed / window change) are now handled automatically — kept here as history.
- ~~**Decision:** Leave the hardcoded trailing-window labels in the Dash dashboard as-is for now; fix them in a dedicated pass, not as a drive-by.~~
- **Why (history):** `app/layout.py:208` rendered the Move 1 footnote "Trailing 52 weeks." and `app/layout.py:470` rendered "Accrued trade spend: trailing-12-month scan revenue × structural...". Both were **hardcoded strings that assert a data-dependent span independent of the data** — the exact defect class the Meridian dry run caught in `trade-spend-data-diagnostic/warehouse_adapter.py` (fixed in that repo's commit 4e2a6d9: labels clamp to actual coverage + honor config). They were **correct** only because the Dash app runs on the fixed canonical Cinderhaven dataset, which genuinely spans 52 weeks / 12 months; the correctness was an accident of the current data, not a computed fact. (A third instance — Move 2's "trailing 52 weeks, as computed in Move 1" at `app/layout.py:272` — was the same defect and was fixed in the same pass.)
  - The **client-mode adapter was unaffected**: `client_mode.py` derives its window label from `basis.window_label` + `as_of_date` (config), pinned by `tests/test_client_mode.py::test_window_label_and_as_of_track_config_not_hardcoded`.
- **Trigger that unmasked it (now handled):** any **data reseed** of the Cinderhaven platform, or any **window/config change** making the actual trailing coverage ≠ 52 weeks / 12 months. The label now recomputes from the pipeline output, so divergence self-corrects instead of silently misstating.
- **Still open:** The same defect class lives in the Excel workbook (`workbook/tab_net_revenue.py`, `tab_efficiency.py`, `tab_accrual.py`, `tab_summary.py`) — a separate deliverable/golden, flagged for a follow-up pass.
