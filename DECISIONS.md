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

### 2026-05-31 — promotions.retailer_id uses RET-* format; retailer_deductions uses lowercase slugs
- **Why:** Discovered during U4 when the slug_map VALUES CTE produced zero matches. `raw.promotions.retailer_id` = `RET-WALMART`, `RET-COSTCO`, etc. `raw.retailer_deductions.retailer_id` = `walmart`, `costco`, etc. Two different conventions coexist in the same Postgres schema with no documentation.
- **Scope:** All pipeline modules that join against `raw.promotions` (U4 move2_efficiency, U5 move4_promo_roi, and any future moves).
- **Do not:** Use `app/constants.py` `CHANNEL_RATE_COLS` keys or `RETAILER_DISPLAY` keys as the join key against `raw.promotions.retailer_id` — they will always miss. Use the `RET-*` format for promotions joins only.

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

---

## Visualization

### 2026-05-31 — Do not use Streamlit for the dashboard
- **Why:** User strongly dislikes Streamlit.
- **Scope:** Dashboard / interactive deliverable
- **Do not:** Suggest or implement Streamlit. Alternatives: Dash, Evidence, Observable, Panel, plain HTML/JS with D3/Vega.

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

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
