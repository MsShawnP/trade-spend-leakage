# trade-spend-leakage — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Complete Phase 1 (scoping and planning) so the project is ready to build.

## Why this arc, why now

Project just initialized. No stack, no spec, no plan. Phase 1 gates the build — nothing gets built until /clarify, /office-hours, /plan-ceo-review, and /plan-eng-review are done.

## Business question this arc answers

What exactly are we building, for whom, and how — so the build phase has no ambiguity about scope or deliverables.

## Goal — 2026-05-31 (confirmed via /clarify)

A portfolio piece demonstrating trade spend domain expertise to CFO/CEO buyers. Two linked deliverables:

1. **Interactive dashboard** — hosted at a public URL (Fly.io or Vercel), fully self-serve, covering all 5 analytical moves: net revenue ranking, trade spend efficiency, leakage detection (4 sub-types), promotional ROI, accrual reconciliation. Backed by read-only Cinderhaven Postgres on Fly.io.
2. **Excel workbook** — downloadable from the dashboard. CFO can click a finding on screen, then trace it to specific rows in the workbook. Credibility artifact ("this is the depth of what you'd get"), not a self-serve tool.

**What done looks like:** Live URL a client opens independently, all 5 moves functional, Excel downloadable and traceable to dashboard numbers.

**Out of scope:** Modifying Cinderhaven SSOT, self-serve client data input, ongoing TPM tooling.

**Constraints:** Read-only Postgres on Fly.io. No Streamlit. No Netlify. Stack decided during /ce:brainstorm to serve the deliverable.

---

## Tasks

- [x] Run /clarify to reach 95% confidence on scope and requirements
- [x] Run /office-hours to stress-test the idea and approach
- [x] Run /plan-ceo-review for the product gate
- [x] Run /plan-eng-review for the architecture gate
- [x] Determine and record the stack (Dash + Fly.io + SQLite snapshot)
- [x] Define the Cinderhaven synthetic data schema (verified via trade-spend-data-diagnostic codebase)
- [x] Update PLAN.md with Phase 2 (build) arc

## Out of scope for this arc

- Any actual code
- Data generation / synthetic dataset creation
- Visualization implementation
- Excel workbook generation

## Definition of done for this arc

- [x] /clarify complete — business question, deliverables, success criteria all written down
- [x] Stack chosen and recorded in DECISIONS.md
- [x] Cinderhaven synthetic data schema defined
- [x] All four Heavy-tier gate commands run
- [x] Phase 2 arc defined in PLAN.md

---

## Phase 2 — Build (current arc)

See `docs/plans/2026-05-31-001-feat-trade-spend-leakage-dashboard-plan.md` for full implementation plan.

### Goal

Ship the Dash dashboard and linked Excel workbook across 8 implementation units, built in sales-impact order.

### Tasks

- [x] U1 — Project setup: `cinderhaven-data` submodule, `pipeline/db.py`, `app/app.py` skeleton
- [x] U1.5 — Switch `pipeline/db.py` `source_conn()` from SQLite to Postgres (`DATABASE_URL` via psycopg2) — required before any move pipeline logic is written
- [x] U2 — Move 1: Net Revenue Ranking bump chart + app shell (first shippable milestone)
- [x] U3 — Move 3: Leakage Detection ledger + AG Grid expand (second shippable milestone)
- [x] U4 — Move 2: Trade Spend Efficiency dual-measure chart
- [x] U5 — Move 4: Promotional ROI scatter chart + rolling-median baseline
- [ ] U6 — Move 5: Accrual Reconciliation bar chart
- [ ] U7 — Excel workbook generation + download button
- [ ] U8 — Fly.io deployment

### Definition of done for Phase 2

- [ ] Dashboard accessible at a public Fly.io URL without login
- [ ] All 5 analytical moves functional
- [ ] "Download workbook" produces a valid xlsx with 6 sheets
- [ ] Workbook numbers match dashboard numbers

---

## Arc history

### 2026-05-31 — Phase 1: Planning complete
- Outcome: All Heavy-tier gates run, requirements doc and implementation plan written
- Tag: v0.1-foundation

### 2026-05-31 — Project initialized
- Outcome: Repo created, scaffolding complete, state files in place
- Tag: v0.1-foundation

---

## Improvement history

<!-- Entries are added by /improve — don't delete this section -->
