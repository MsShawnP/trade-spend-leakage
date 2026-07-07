# trade-spend-leakage — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

---

## 2026-06-30

**Started from:** Prior session fixed chart colors (lailara_palette migration, paired categorical palette, HK gradient, Tokyo/HK divergent scatter, ad-hoc hex sweep) and added slopegraph label deconfliction + bracket annotations. Brackets still collided with y-axis ticks and end labels.

**Did:**

1. **Removed bracket annotations from Section 01 slopegraph:** Deleted the entire bracket block from `bump_chart()` — vertical bracket shapes, tick marks, "$820K"/"$586K" dollar labels, and "Top-3 gap..." caption (49 lines removed). Compression story is already in the Section 01 body copy and visible in the converging lines.

2. **Tightened chart margins:** Right margin 220→180, x-range [-0.12, 1.22] → [-0.05, 1.08], left margin 80→60 — brackets no longer need the extra room.

3. **Verified clean:** Screenshot confirms no brackets, no gap caption, no label collisions. 17/17 offline tests pass. Deployed to Fly.io.

**State:** Dashboard live at https://trade-spend.lailarallc.com/. All committed and pushed. Section 01 is clean: six paired-palette lines, per-retailer end labels, dollar y-axis, footnote. No open tasks.

**Next:** No active tasks. Next `/improve` due 2026-07-01.

---

## 2026-06-29

**Started from:** Project deployed but serving stale results.db. Prompted to re-run pipeline, fix Section 02 copy bug, and investigate flat slopegraph.

**Did:**

1. **Fixed Section 02 copy bug:** "Orange bars exceed the 17% specialty food average" replaced with "All six retailers fall well below the 17% specialty food average" — no bars are orange because all are 7–13%.

2. **Redefined Move 1 net revenue:** Was gross − structural rate-card trade spend only (7–12%, too compressed to flip ranks). Now: gross − structural trade − operational deductions (damaged, spoilage, late delivery, etc. from retailer_deductions; promo billbacks and slotting excluded to avoid double-counting with rate card). Added `_DEDUCTIONS_SQL` as a second query, merged in Python.

3. **Fixed Kroger rate bug:** `trade_spend_pct_kroger` column existed in sku_costs but was never referenced in the CASE statement — Kroger fell into the ELSE (regional at 7%) instead of its actual 10%. Added Kroger branch to the CASE.

4. **Re-ran full pipeline** (all 5 moves). Numbers: 2,569 leakage instances / $248,314. 123 promo events, 110 measurable. 5 product lines (CHP-AS, CHP-DG, CHP-PS, CHP-SB, CHP-SC). 12 accrual months, +$2.6M net variance.

5. **Slopegraph ranks do NOT flip.** Revenue gaps ($350K–$1.7M between adjacent retailers) are too large for trade cost differences ($20K–$220K) to bridge. Rewrote Section 01 copy: dropped "the lines that cross tell the story" narrative, reframed around gap compression (top 3 gross spread $820K compresses to $586K net, 29% absorption).

**State:** Deployed and live at https://trade-spend.lailarallc.com/. 17/17 offline tests pass. All committed and pushed.

**Move 1 key figures (new definition):**
| Retailer | Gross | Trade Cost | Net | Eff Rate |
|----------|-------|-----------|-----|----------|
| Walmart | $7,480,454 | $958,702 | $6,521,752 | 12.8% |
| Costco | $7,021,732 | $738,596 | $6,283,136 | 10.5% |
| Kroger | $6,660,048 | $723,912 | $5,936,136 | 10.9% |
| Whole Foods | $5,644,049 | $504,758 | $5,139,291 | 8.9% |
| Sprouts | $3,900,857 | $396,528 | $3,504,329 | 10.2% |
| Regional | $1,765,601 | $154,433 | $1,611,168 | 8.7% |

**Next:** No active tasks. Leakage/promo numbers unchanged ($248,314 / 2,569 / 123 promos). README figures still accurate. Next `/improve` due 2026-07-01.

---

## 2026-06-01

**Started from:** Project complete and client-ready. One open task: fix the compound doc that described the slug_map CTE as the fix when it was actually the bug.

**Did:** Rewrote `docs/solutions/logic-errors/retailer-id-format-mismatch-join-produces-wrong-leakage-2026-06-01.md` from scratch. The original doc had the root cause and fix backwards — it said "deductions uses lowercase slugs, add slug_map" when the truth is both tables use RET-* and the fix was removing the slug_map. Verified against current code and DECISIONS.md before rewriting. Committed.

**State:** Compound doc accurate. Project otherwise unchanged — dashboard live, 37 tests pass, all committed. No open tasks.

**Next:** No active tasks. Next `/improve` due 2026-07-01. If returning before then: (a) data refresh — `fly proxy 5434:5433 -a cinderhaven-db` → `python pipeline/run.py --moves 1 2 3 4 5` → `fly deploy`; (b) adapt for a real client's data.

---

## 2026-06-01 (second entry)

**Started from:** Project deployed, client-ready. HANDOFF recommended data refresh + live tests.

**Did:** Fixed Fly Postgres auth (pg_hba.conf md5→scram-sha-256 + password reset via sftp/SSH). Ran full pipeline. Live tests surfaced critical bug: slug_map from prior session mapped deductions to lowercase slugs but both tables use RET-* format — double-dip and ghost-promo detection returned 0 rows silently. Removed slug_map from move3_leakage.py, rewrote 3 queries with direct joins. Replaced slug_map tests with test_promotions_and_deductions_use_same_retailer_id_format. Fixed test_pipeline_db raw.scan_data. 37/37 pass. Redeployed. Correct numbers: 2,512 instances / $235,760 (173 double-funded · 817 ghost promos · 1 rate discrepancy · 1,521 unauthorized).

**State:** Dashboard live at https://trade-spend.lailarallc.com/ with correct data. 37 pass, 2 skip. All pushed. Fly proxy must use local 5434 → remote 5433 (not standard 5432). pg_hba.conf now uses scram-sha-256. Compound doc contains incorrect format description (marked as next task).

**Next:** Update docs/solutions/logic-errors/retailer-id-format-mismatch-join-produces-wrong-leakage-2026-06-01.md — it states "raw.retailer_deductions uses lowercase slugs" which is wrong; both tables use RET-* format. The slug_map was never needed.

---

## 2026-06-01

**Started from:** Project client-ready. HANDOFF recommended adding integration tests for leakage detection (compound doc suggestion).

**Did:** Added two @_LIVE slug-map coverage tests to tests/test_move3_leakage.py — one checking raw.promotions retailer_ids against _SLUG_MAP_CTE, one checking raw.retailer_deductions retailer_ids. Committed and pushed (60a4286). Note: the len > 0 tests the HANDOFF had listed as "Next" were already in place from the second /improve session.

**State:** 17/17 offline tests pass. 11 live tests in test_move3_leakage.py require DATABASE_URL + fly proxy. Dashboard live and correct at https://trade-spend.lailarallc.com/. No open tasks.

**Next:** No open tasks. If returning: (a) run full live test suite to verify new slug-map tests pass (`fly proxy 5432 -a cinderhaven-db`, then `pytest`); (b) data refresh if Cinderhaven data has updated; (c) adapt for real client data.


For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-06-01 — Wrap: second /improve pass + /ce:compound

**Started from:** Project deployed, tagged v1.0-client-ready. No open tasks. HANDOFF recommended /improve and /ce:compound.

**Did:** Second /improve pass with security + data-analysis deep reviews. Found and fixed critical Move 3 leakage SQL bug (RET-* vs lowercase slug retailer_id mismatch — double-dip and rate-discrepancy returned 0 rows; ghost promos inflated all billbacks). Re-ran pipeline Move 3, redeployed. Corrected leakage: 1,521 instances / $144,320. Also fixed Move 5 accrual footnote, debug=True, removed incremental_margin duplicate column, added Move 2 unknown-slug warning. Ran /ce:compound — documented the leakage SQL bug in docs/solutions/logic-errors/; updated CLAUDE.md and plan doc.

**State:** Dashboard live with correct data. All commits pushed. docs/solutions/ initialized. 17/17 tests pass. Project complete and client-ready.

**Next:** No open tasks. If returning: (a) add integration test for leakage detection functions (assert len > 0 per function against live Postgres — recommended by compound doc); (b) data refresh — run pipeline → fly deploy; (c) adapt for real client data.

---

## 2026-05-31 — Wrap: /improve complete, project client-ready

**Started from:** Project fully shipped (U8 complete). Dashboard live at https://trade-spend.lailarallc.com/. HANDOFF recommended a pre-client `/improve` pass.

**Did:** Ran full `/improve` audit. Fixed all 6 findings: README updated with live URL + deployed-state context + data refresh pattern; stale "75 rows" docstring removed from `app/db.py`; dead ImportError fallback removed from `app/app.py`; portfolio brief moved from root to `docs/`; empty `src/CLAUDE.md` removed; bare `except Exception` narrowed to `except sqlite3.OperationalError` across all 6 db readers. 18/18 tests pass.

**State:** Project is complete and client-ready. No open tasks. Dashboard live and stable.

**Next:** No active work. If returning: (a) data refresh — run pipeline locally → `fly deploy`; (b) new analytical move; or (c) adapt for a real client's data.

---

## 2026-05-31 23:00 — Wrap: U8 complete, project deployed

**Started from:** U7 complete, all 5 analytical moves functional, U8 (Fly.io deployment) the only remaining task.

**Did:** Wrote Dockerfile + fly.toml + run.py + .dockerignore. Created Fly app. Hit Depot DNS wall (build-time pipeline approach failed — Depot servers can't reach cinderhaven-db.internal). Switched to pre-generated results.db baked in via COPY. Deployed successfully. Phase 2 definition of done fully satisfied.

**State:** Dashboard live at https://trade-spend.lailarallc.com/ — health check 200, all 5 moves functional, workbook download wired. Two Fly machines running. results.db baked into image (352 KB). All 8 units complete.

**Next:** Phase 2 is done. Run /improve for a pre-client cleanup pass. Also document the refresh pattern (run pipeline locally → fly deploy) in README.

---

## 2026-05-31 22:00 — Full Heavy-tier planning complete

**Started from:** Fresh project with only the portfolio brief. No git, no scaffolding, no spec.

**Did:** Ran the full Heavy-tier workflow in one session: /new-project → /clarify → /office-hours → /plan-ceo-review → /plan-eng-review → /ce:brainstorm → /ce:plan. Key discoveries during /ce:plan: (1) `trade-spend-data-diagnostic` already exists with the Excel workbook fully built — this project is primarily the Dash dashboard layer on top; (2) Cinderhaven data is a SQLite snapshot exported from Postgres, not a live connection; (3) brief's leakage dollar amounts ($340K double-dips) are aspirational — actual data has 3 double-dips totaling $19K and 137 ghost promos at ~$96K.

**State:** All planning gates complete. Requirements doc at `docs/brainstorms/trade-spend-leakage-requirements.md`. Implementation plan at `docs/plans/2026-05-31-001-feat-trade-spend-leakage-dashboard-plan.md`. No code written. Stack: Dash + Fly.io + SQLite snapshot + pre-computed `results.db`. Build order: U1 (setup) → U2 (Move 1 bump chart) → U3 (Move 3 leakage) → U4–U6 (Moves 2, 4, 5) → U7 (workbook) → U8 (deploy).

**Next:** Start `/ce:work` on U1 — add `cinderhaven-data` as git submodule at `data/cinderhaven-data/`, scaffold `pipeline/db.py` with SQLite connection helpers (source + results), scaffold `app/app.py` Dash entry point. Reference: `retail-velocity-decision-tool/app/db.py` and `trade-spend-data-diagnostic/scripts/build_db.py`.

---

## 2026-05-31 — Project initialized

**Started from:** New project setup via /new-project.

**Did:** Created repo, set up CLAUDE.md/DECISIONS.md/HANDOFF.md/PLAN.md/
FAILURES.md, .gitignore, README.md, src/ and tests/ directories.
Tier: Heavy. Stack: TBD (to be determined during /clarify and /ce:brainstorm).
Project brief (portfolio_project_brief_trade_spend_leakage.md) preserved in root.

**State:** Foundation in place. PLAN.md Phase 1 arc defined. Ready to begin
Phase 1 — run /clarify next.

**Next:** Run /clarify to scope the work. Then /office-hours, /plan-ceo-review,
/plan-eng-review to complete the Heavy-tier gates before any code is written.

---

## 2026-05-31 23:30 — U1 complete: submodule, pipeline scaffold, app skeleton

**What changed:** U1 shipped — git submodule, pipeline/db.py, pipeline/run.py, app/app.py, app/constants.py, requirements.txt, 4 passing tests.

**Why:** First buildable unit of Phase 2. Establishes the data path (cinderhaven-data → pipeline → results.db) and Dash entry point before any analytical code.

**State:** `pipeline/run.py --moves none` exits 0. `from app.app import app` imports cleanly. `tests/test_pipeline_db.py` 4/4 green. `data/cinderhaven-data/data/cinderhaven_product_master.db` present (copied from published project — not git-tracked). No move modules exist yet (U2+).

**Next:** `/ce:work` U2 — `pipeline/move1_net_revenue.py` + `app/layout.py` + `app/charts.py` + `app/callbacks.py` + `app/db.py` (results reader). First shippable dashboard milestone.

---

## 2026-05-31 14:55 — Wrap: U1.5 + U2 complete

**Started from:** U1 complete (submodule, pipeline scaffold, Dash skeleton). U1.5 (Postgres source_conn switch) was the required gate before any move pipeline logic.

**Did:** U1.5 — switched source_conn() to Fly.io Postgres via DATABASE_URL (psycopg2), updated tests. U2 — full vertical slice for Move 1: pipeline query (scan_data→stores→sku_costs CTE), results.db writer, bump chart (go.Scatter, click-to-pin), dark callout card, section layout, callbacks. 3 tests pass, 5 skip (need DATABASE_URL).

**State:** App imports and serves. Bump chart renders empty state until pipeline runs with DATABASE_URL set. No U3+ code exists.

**Next:** Set DATABASE_URL to Fly.io Postgres, run `python pipeline/run.py --moves 1` to populate results.db and verify live data, then `/ce:work` U3 — Move 3 leakage detection ledger + AG Grid expand.

---

## 2026-05-31 14:54

**What changed:** U2 shipped — Move 1 bump chart + app shell (pipeline, app layer, callbacks, tests)

**Why:** First shippable milestone. Establishes the full vertical slice: Postgres query → results.db → Dash chart → click-to-pin callout card.

**State:** App imports and serves cleanly. 3 tests pass, 5 skip (need DATABASE_URL). Bump chart renders empty state until `pipeline/run.py --moves 1` is run with DATABASE_URL set. No move modules beyond Move 1 exist yet.

**Next:** Set DATABASE_URL to Fly.io Postgres, run `python pipeline/run.py --moves 1` to populate results.db, verify bump chart renders live data, then `/ce:work` U3 (Move 3 leakage detection ledger).

---

## 2026-05-31 14:36

**What changed:** U1.5 shipped — source_conn() switched from SQLite snapshot to Fly.io Postgres via DATABASE_URL (psycopg2)

**Why:** SQLite approach in U1 was a placeholder; Postgres is the only SSOT. Must be wired before any move pipeline logic is written against it.

**State:** `pipeline/db.py` source_conn() requires DATABASE_URL env var. results_conn() unchanged (SQLite). 3 tests pass, 1 live Postgres test skips when DATABASE_URL absent. No move modules yet.

**Next:** Set DATABASE_URL to the Fly.io Postgres connection string, then `/ce:work` U2 — `pipeline/move1_net_revenue.py` + bump chart layout/charts/callbacks.

---

## 2026-05-31 23:45 — Wrap: U1 complete, Phase 2 underway

**Started from:** All Heavy-tier planning done, no code written.

**Did:** Executed U1 end-to-end — cinderhaven-data submodule, pipeline/db.py (SQLite connection helpers), pipeline/run.py (--moves orchestrator), app/app.py (Dash skeleton), app/constants.py (Lailara tokens + channel rate map), requirements.txt, 4 passing tests. Key discovery: submodule clone omits the .db file (gitignored) — copy from trade-spend-data-diagnostic's submodule or export from Fly.io.

**State:** `pipeline/run.py --moves none` exits 0. `from app.app import app` clean. 4/4 tests green. DB present locally at `data/cinderhaven-data/data/cinderhaven_product_master.db`. No move modules (U2+) exist yet.

**Next:** Before U2 — switch `pipeline/db.py` `source_conn()` from SQLite snapshot to Postgres (cinderhaven-data-platform on Fly.io via `DATABASE_URL`). The SQLite approach in U1 is a placeholder; the Cinderhaven Data Platform Postgres is the only SSOT. Once source_conn() is wired to Postgres, proceed with U2: `pipeline/move1_net_revenue.py` + `app/db.py` + `app/layout.py` + `app/charts.py` (`bump_chart()`) + `app/callbacks.py` (click-to-pin).

---

## 2026-05-31 15:12

**What changed:** U2 verified against live Postgres data — 6 retailers populate the bump chart correctly.

**Why:** Two SQL bugs were blocking live data: bare table names needed `raw.` schema prefix, and `stores.retailer` doesn't exist (column is `chain_name`). Also fixed Decimal→float casting for SQLite write, and sys.path for `python app/app.py` launch mode.

**State:** `pipeline/run.py --moves 1` populates `results_net_revenue` with 6 retailers. App serves full layout with 6 populated chart traces. `.env` with Fly proxy DATABASE_URL is in place (gitignored). Proxy must be running (`fly proxy 5432 -a cinderhaven-db`) for pipeline to execute.

**Next:** `/ce:work` U3 — Move 3 leakage detection ledger + AG Grid expand.

---

## 2026-05-31 15:29

**What changed:** U3 complete — leakage detection pipeline + dashboard ledger + AG Grid drill-down.

**Why:** Second shippable milestone. Four sub-type detection queries against live Postgres; clickable summary ledger; instance AG Grid expands on row click.

**State:** `pipeline/run.py --moves 3` populates 2,512 instances / $235,760 total leakage. Dashboard renders Move 1 bump chart + Move 3 leakage ledger. 12 tests pass (3 offline, 9 live). Proxy must be running for pipeline. U4–U8 not started.

**Next:** `/ce:work` U4 — Move 2 Trade Spend Efficiency dual-measure chart.

---

## 2026-05-31 15:33

**Started from:** U2 code-complete but never run against live Postgres. DATABASE_URL unset.

**Did:** Wired Fly.io Postgres locally (proxy + .env). Fixed 4 bugs in move1 SQL (raw. prefix, chain_name, Sprouts rate, Decimal cast). Fixed sys.path in app.py and run.py. Verified U2 live (6 retailers). Implemented U3 full vertical slice: 4 leakage detection functions, 2,512 instances / $235,760, ledger + AG Grid click-to-expand, 12 passing tests. Updated plan with actual Postgres numbers.

**State:** Move 1 bump chart + Move 3 leakage ledger fully functional against live Postgres. `fly proxy 5432 -a cinderhaven-db` must be running for pipeline. Preview screenshot tool times out with Plotly — use `/_dash-layout` JSON to verify instead. U4–U8 not started.

**Next:** `/ce:work` U4 — Move 2 Trade Spend Efficiency dual-measure chart. Read U4 section of implementation plan, then check `trade-spend-data-diagnostic` for efficiency query pattern.

---

## 2026-05-31 16:10

**What changed:** U4 complete — Move 2 Trade Spend Efficiency pipeline + dual-measure chart

**Why:** Third dashboard section. Per-retailer structural trade spend % + promo revenue-per-dollar from Postgres. Key discovery: `promotions.retailer_id` uses `RET-WALMART` format (not lowercase slugs like deductions); slug_map corrected mid-run.

**State:** All three sections functional (Move 1, Move 2, Move 3). `python pipeline/run.py --moves 2` writes `results_trade_efficiency` — 6 retailers, trade spend 7–12%, all measurable. Chart renders as dual horizontal bar with HK teal gradient + 17% reference line. U5–U8 not started.

**Next:** `/ce:work` U5 — Move 4 Promotional ROI scatter chart + rolling-median baseline.

---

## 2026-05-31 16:15

**Started from:** U3 complete. Move 1 bump chart + Move 3 leakage ledger verified against live Postgres.

**Did:** U4 full vertical slice — `pipeline/move2_efficiency.py` (Postgres CTE with DISTINCT ON dedup, RET-* retailer_id format), `get_trade_efficiency()` db reader, `efficiency_chart()` make_subplots dual horizontal bar (HK teal gradient), `_section_efficiency()` section in layout between Move 1 and Move 3. Hit and fixed RET-* slug format mismatch mid-run.

**State:** Three sections functional (Move 1, 2, 3). All 6 retailers measurable in Move 2. `python pipeline/run.py --moves 1 2 3` populates all tables. App imports and serves cleanly. U5–U8 not started.

**Next:** `/ce:work` U5 — Move 4 Promotional ROI. Read U5 spec in plan. Adapt `retail-velocity-decision-tool/app/decisions/promo_roi.py`. Note: `promotions.retailer_id` uses `RET-*` format — carry into U5 SQL.

---

## 2026-05-31 16:30 — Wrap: U6 complete, all 5 moves functional

**Started from:** U5 committed, PLAN.md not yet updated. U6 (Move 5 Accrual Reconciliation) was the next task.

**Did:** Marked U5 complete in PLAN.md. Implemented U6 full vertical slice — `pipeline/move5_accrual.py` (two Postgres CTEs: monthly accrued via rate card × scan revenue, monthly actual via retailer_deductions; merge + variance), `get_accrual()` db reader, `accrual_chart()` (grouped bars + secondary-y variance line), `_section_accrual()` in layout. Ran pipeline against Fly.io Postgres — 12 months, +$2.4M net variance. Pushed and tagged `v0.5-all-moves`.

**State:** All 5 analytical moves functional. Five sections render in dashboard. results_accrual has 12 rows. App imports and serves cleanly. No workbook (U7) or deployment (U8) yet. Fly proxy must be running for pipeline.

**Next:** `/ce:work` U7 — Excel workbook generation + download button. Start with `workbook/styles.py` (copy from trade-spend-data-diagnostic verbatim), then `workbook/generator.py`, then one tab at a time. Wire `dcc.Download` callback last.

---

## 2026-05-31 16:25 — U6 complete: Move 5 Accrual Reconciliation

**What changed:** U6 shipped — Move 5 Accrual Reconciliation pipeline + grouped bar chart + variance line

**Why:** Fifth and final analytical move. Monthly accrued (rate card × scan revenue) vs actual deducted (retailer_deductions) — the $2.4M net positive variance is the punchline for this move.

**State:** All five analytical moves functional (Moves 1–5). Five sections render in the dashboard. `python pipeline/run.py --moves 5` writes 12 rows to results_accrual. App imports and serves cleanly. No workbook or deployment yet (U7–U8). Fly proxy must be running for pipeline.

**Next:** `/ce:work` U7 — Excel workbook generation + download button. Read U7 spec in plan; adapt `trade-spend-data-diagnostic/workbook/` modules to read from results.db.

---

## 2026-05-31 17:30

**What changed:** U5 shipped — Move 4 Promotional ROI scatter chart + rolling-median baseline pipeline

**Why:** Fourth dashboard section. Per-promo incremental revenue vs cost, 8-week pre-promo rolling median baseline. Key discovery: Postgres `promotions` table uses column `sku` (not `sku_id`) — fixed mid-run. Postgres dataset has 138 distinct promo events (vs plan's SQLite-based estimate of 75); 131 have sufficient baseline.

**State:** Four sections functional (Moves 1, 2, 3, 4). `python pipeline/run.py --moves 4` writes `results_promo_roi` — 138 events, 131 measurable, 121 money-losing. Scatter chart renders with break-even line; click-to-pin callout works. 14 tests pass (7 offline, 7 live). U6–U8 not started.

**Next:** `/ce:work` U6 — Move 5 Accrual Reconciliation: `pipeline/move5_accrual.py` + grouped bar chart (accrued vs actual by month, last 12 months). Reference: `trade-spend-data-diagnostic/workbook/tab_executive_pulse.py`.

---

## 2026-05-31 21:00

**What changed:** U7 shipped — Excel workbook generation + download button

**Why:** CFO credibility artifact. Six-sheet openpyxl workbook (Summary, Net Revenue Ranking, Leakage Detection, Trade Spend Efficiency, Promotional ROI, Accrual Reconciliation) generated server-side from results.db; streamed via `dcc.Download`. Handles partial build state — missing tables produce a placeholder row, not an error.

**State:** All 7 units through U7 complete. 18 offline tests pass (21 skip, need DATABASE_URL). App imports clean. `workbook/` package with 8 modules committed. "Download Workbook" button wired in layout + callbacks. U8 (Fly.io deployment) is the only remaining task.

**Next:** `/ce:work` U8 — Dockerfile + fly.toml + run.py entry point. Follow `retail-velocity-decision-tool/Dockerfile` pattern. Bake results.db into the image during build (pipeline runs at build time, no live DB at runtime).

---

## 2026-05-31 21:15 — Wrap: U7 complete

**Started from:** U6 complete, all 5 analytical moves functional (`v0.5-all-moves`). U7 (workbook) was next.

**Did:** Built full `workbook/` package — `styles.py`, `generator.py` (returns bytes via BytesIO), and six tab modules each reading from `results.db`. Wired "Download Workbook" button + `dcc.Download` callback. 5 new tests (18 total offline pass). Fixed missing `ALIGN_LEFT` import caught by tests.

**State:** U7 complete and committed. App imports clean. 18/18 offline tests pass. U8 (Fly.io deployment) is the only remaining unit. Phase 2 definition of done is one deploy away.

**Next:** `/ce:work` U8 — `Dockerfile` + `fly.toml` + `run.py`. Follow `retail-velocity-decision-tool/Dockerfile` exactly. Bake `results.db` into the image at build time (no live DB at runtime). `internal_port = 8050`, always-on service. Read the reference Dockerfile before writing.

---
