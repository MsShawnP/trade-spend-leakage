# trade-spend-leakage — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

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
