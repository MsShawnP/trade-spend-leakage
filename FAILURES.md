# trade-spend-leakage — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

### 2026-05-31 — Assumed live Postgres connection; actual pattern is SQLite snapshot

**Attempted:** During /clarify, accepted the user's statement "Postgres database" at face value and spec'd the architecture around a live Postgres connection from the dashboard (connection pooling, Fly.io internal networking, DATABASE_URL at runtime). Requirements doc was written with `fct_deductions` / mart-style table references and the /plan-eng-review focused on connection pooling concerns for Vercel vs Fly.io.

**Why it didn't work:** Every other portfolio project that uses Cinderhaven data (`retail-velocity-decision-tool`, `trade-spend-data-diagnostic`, `retailer-deduction-recovery`) exports Postgres data to a SQLite snapshot and ships that snapshot. The Postgres is the SSOT for data generation; applications never query it at runtime. The user said "Postgres" because that's where the data lives, not because apps connect to it directly.

**What we tried instead:** Discovered the actual pattern during /ce:plan research — read `trade-spend-data-diagnostic/HANDOFF.md`, `retailer-deduction-recovery/DECISIONS.md`, and the `.env.example` files. Revised the architecture to SQLite snapshot via `cinderhaven-data` git submodule, same as every other portfolio project.

**Status:** Partially resolved — see 2026-05-31 entry below re: Postgres reversal.

**Tags:** cinderhaven, postgres, sqlite, architecture, data-source

---

### 2026-05-31 — Submodule clone does not include the SQLite .db file

**Attempted:** Added `cinderhaven-data` as a git submodule and assumed `git submodule update --init` would make the database available at `data/cinderhaven-data/data/cinderhaven_product_master.db`.

**Why it didn't work:** The 130MB SQLite file is gitignored inside the submodule repo — it is exported from Fly.io Postgres and never tracked in git. A fresh clone of the submodule has an empty `data/` directory.

**What we tried instead:** Copied the file from `trade-spend-data-diagnostic/cinderhaven-data/data/` (same synthetic dataset, already present on this machine). For a clean machine setup, the correct path is to export from Fly.io: `flyctl postgres connect -a cinderhaven-db`. Documented in README.md How-to-Run section.

**Status:** Resolved for local dev; will be moot once source_conn() switches to Postgres.

**Tags:** cinderhaven, submodule, sqlite, setup, gitignore

---

### 2026-05-31 — SQLite snapshot approach in source_conn() must be replaced with Postgres

**Attempted:** U1 implemented `pipeline/db.py` `source_conn()` as a read-only SQLite connection to the submodule snapshot, following the pattern of `trade-spend-data-diagnostic`. The planning session had resolved to use SQLite for simplicity (see previous failure entry).

**Why it didn't work:** The Cinderhaven Data Platform (Fly.io Postgres + dbt pipeline) is the only SSOT. This project must connect directly to that Postgres instance — not a snapshot. The SQLite approach was a carryover assumption from other portfolio projects; the user confirmed it is not the correct source for this dashboard.

**What we tried instead:** Nothing yet — identified at wrap. Next session must replace `source_conn()` with a Postgres connection via `DATABASE_URL` (psycopg2) before any move pipeline logic is written. `pipeline/db.py` is the only file that needs to change; the rest of U1 is unaffected.

**Status:** Open — fix required before U2.

**Tags:** cinderhaven, postgres, sqlite, source_conn, pipeline, data-source, architecture

---

### 2026-05-31 — Preview screenshot tool times out with Plotly charts

**Attempted:** Used `mcp__Claude_Preview__preview_screenshot` to verify the dashboard renders correctly after wiring live data and after U3.

**Why it didn't work:** The preview tool has a 30-second rendering timeout. Plotly's JS bundle is large enough that mounting a full chart (Scatter traces + layout) exceeds 30s in the headless preview browser environment. The tool returns a timeout error; it is not an app bug.

**What we tried instead:** Verified layout via `curl http://127.0.0.1:<port>/_dash-layout | python` — inspects the full component tree and figure data as JSON. Confirmed component IDs, trace counts, callback wiring, and data values without a browser. Reliable and fast. Use this pattern for all Plotly dashboard verification going forward.

**Status:** Resolved (workaround established).

**Tags:** plotly, preview, screenshot, dash, verification, timeout

---

### 2026-05-31 — Wrote pipeline SQL before querying Postgres schema; caught multiple column/schema bugs at verification

**Attempted:** Wrote `pipeline/move1_net_revenue.py` SQL referencing `scan_data`, `stores`, `sku_costs` (bare table names) and `stores.retailer` (column name from SQLite diagnostic), assuming the Postgres schema matched the SQLite snapshot.

**Why it didn't work:** Postgres tables are in the `raw` schema (requires `raw.scan_data` etc.). The `stores` table uses `chain_name`, not `retailer`. UNFI, KeHE, and DTC are not retail chains in the `stores` table (they appear in `sku_costs` rate columns but are distributor/DTC channels). The same issue recurred in U3 planning — the `is_double_dip` flag exists in the SQLite snapshot but not in Postgres.

**What we tried instead:** Added a schema exploration step before writing U3 SQL — queried `information_schema.columns`, `DISTINCT` values, and row counts for all source tables before writing any query. Caught column names, ID formats (`RET-WALMART` not `walmart`), and missing flags up front.

**Status:** Resolved. Rule going forward: always query live schema before writing pipeline SQL against a new source table.

**Tags:** postgres, schema, sql, column-names, raw-schema, pipeline, move1, move3

---

### 2026-05-31 — promotions.retailer_id uses RET-* format, not lowercase slugs

**Attempted:** Built the slug_map VALUES CTE in `pipeline/move2_efficiency.py` using lowercase slug format (`'walmart' → 'Walmart'`), consistent with `retailer_deductions.retailer_id` and the project constants. First pipeline run returned 0 retailers with measurable lift.

**Why it didn't work:** `raw.promotions.retailer_id` uses `RET-WALMART` / `RET-COSTCO` format — a different convention than `raw.retailer_deductions.retailer_id` which uses `walmart` / `costco`. The JOIN on `sm.slug = p.retailer_id` matched nothing. One diagnostic query (`SELECT DISTINCT retailer_id FROM raw.promotions`) exposed the format immediately.

**What we tried instead:** Updated the VALUES CTE and `_SLUG_TO_DISPLAY` dict to use `RET-*` keys. Re-ran pipeline — 6/6 retailers measurable. Also discovered live chain_names are Walmart, Costco, Kroger, Whole Foods, Sprouts, Regional Group — not the UNFI/KeHE/DTC set in constants.py (which reflects the SQLite snapshot, not Postgres).

**Status:** Resolved.

**Tags:** postgres, promotions, retailer_id, slug-format, RET-format, move2, pipeline, schema

---

### 2026-05-31 — charts.py edit duplicated a function by targeting the wrong insertion point

**Attempted:** Used Edit to insert `accrual_chart()` before `_apply_promo_roi_layout` in `charts.py`. The old_string matched the function *signature line*, but the function body immediately followed — so the edit inserted new code before the signature, then the original body was still there, producing two complete definitions of `_apply_promo_roi_layout` plus a junk sentinel variable.

**Why it didn't work:** The Edit tool replaces old_string with new_string verbatim. When the target string is the function signature only (not including its body), the result inserts before the signature and leaves the original body intact — effectively duplicating the function.

**What we tried instead:** Read the file to inspect the actual line range, then targeted the junk sentinel + duplicate function body as old_string and replaced with just the new `accrual_chart()` function. Removed duplicate cleanly in one edit.

**Status:** Resolved.

**Tags:** charts, edit-tool, duplication, insertion-point, charts.py
