---
date: 2026-05-31
topic: trade-spend-leakage
---

# Trade Spend Leakage — Requirements

## Summary

A Lailara portfolio piece — Dash dashboard deployed on Fly.io + downloadable Excel workbook — that analyzes synthetic Cinderhaven trade spend across five analytical moves and reranks retailers by net revenue after all trade costs. The headline finding: the retailer the brand treats as its #1 account is often one of its worst. Targeted at CFO/CEO buyers at $5M–$30M specialty food brands to generate $15K–$25K Trade Spend Diagnostic engagements.

---

## Problem Frame

Trade spend is the second-largest line item in a specialty food brand's P&L — typically 15–30% of gross revenue — and the least controlled. It lives in three disconnected places: promotional agreements (in sales' inbox and spreadsheets), deductions (in remittance data, coded cryptically), and accruals (in the accounting system, as estimates). Nobody has joined them.

The result is systematic leakage nobody sees: brands paying for the same promotion twice (off-invoice and bill-back), deductions taken for promotions that never ran, rate discrepancies that go unchecked, and promotional spend that generated no incremental lift. When brands finally compute net revenue by retailer, the ranking often inverts — the biggest gross account is one of the worst net accounts.

Brands in the $5M–$30M range can't justify $30K–$150K/year for trade promotion management software. They need a diagnostic-level analysis that finds the leakage and reframes their retailer strategy — but nobody serves this band with actual forensic analysis.

---

## Actors

- A1. **Operator (Shawn)** — runs the analysis pipeline, manages Postgres, deploys to Fly.io, downloads the Excel
- A2. **Dashboard viewer (CFO or CEO prospect)** — opens the Fly.io URL independently, explores findings, downloads Excel
- A3. **Cinderhaven Data Platform** — read-only Postgres on Fly.io; source of truth for deductions, promotional, and POS data

---

## Key Flows

- F1. **Analysis pipeline run**
  - **Trigger:** Operator runs the pipeline script manually
  - **Actors:** A1, A3
  - **Steps:** Operator executes pipeline command → script reads from Cinderhaven SSOT (read-only) → computes all five analytical moves → writes results to `trade_spend_analysis` schema in the same Postgres instance → logs completion
  - **Outcome:** Pre-computed results available in Postgres; dashboard reflects current analysis on next page load
  - **Covered by:** R1, R2, R3, R4, R5

- F2. **Dashboard exploration**
  - **Trigger:** Viewer opens the Fly.io URL
  - **Actors:** A2
  - **Steps:** Viewer lands on Move 1 (net revenue ranking) by default → sees the bump chart with retailer ranking inversion → clicks a retailer line to pin detail card → navigates to Move 3 (leakage detection) → clicks a leakage category to expand instance table → continues through remaining moves → clicks "Download workbook"
  - **Outcome:** Viewer understands the core finding and has a workbook to audit the numbers independently
  - **Covered by:** R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R17, R18, R19

- F3. **Excel audit**
  - **Trigger:** Viewer clicks "Download workbook" on the dashboard
  - **Actors:** A2
  - **Steps:** Browser downloads the generated .xlsx file → viewer opens it → navigates to the tab matching the dashboard section they want to verify → traces a dollar amount from dashboard to workbook row using source identifiers → reviews data lineage
  - **Outcome:** CFO can verify that dashboard numbers are correct and understand exactly how they were derived
  - **Covered by:** R20, R21, R22, R23

---

## Requirements

**Analysis pipeline**

- R1. A Python script reads from the Cinderhaven SSOT (read-only) and writes computed results to a separate `trade_spend_analysis` schema in the same Postgres instance. No changes are made to SSOT tables or data.
- R2. The pipeline populates results for all five analytical moves: net revenue by retailer, trade spend efficiency, leakage detection (four sub-types), promotional ROI, and accrual reconciliation.
- R3. Leakage detection identifies and stores four sub-types with dollar amount and instance count per sub-type: (a) double-funded promotions — same promotional event funded off-invoice AND deducted as a bill-back; (b) phantom promotions — deduction with no matching promotional agreement and no corresponding POS lift; (c) rate discrepancies — deduction rate exceeds the agreed promotional rate; (d) unauthorized deductions — deduction with no promotional agreement at all.
- R4. Promotional ROI uses a rolling-median baseline per SKU/retailer/period to separate incremental lift from baseline volume. Promotions where trade spend exceeded gross margin on incremental units are flagged as money-losing.
- R5. The pipeline is a one-time run against fixed synthetic Cinderhaven data. No scheduling, automation, or incremental refresh is required.

**Dashboard — general**

- R6. The dashboard is a Dash app following the `retail-velocity-decision-tool` conventions: Lailara Design System v2 (Chicago navy #1f2e7a, London greyscale, Hong Kong teal for sequential data, Playfair Display headings, Source Sans 3 body), Plotly charts, AG Grid for tabular data, `dash_bootstrap_components` layout.
- R7. Navigation is a section-based layout with five named sections, one per analytical move, in build-order sequence: Net Revenue Ranking, Leakage Detection, Trade Spend Efficiency, Promotional ROI, Accrual Reconciliation.
- R8. The dashboard is read-only. No user inputs beyond section navigation and drill-down interactions defined in R12 and R15.
- R9. All interactions follow Lailara click-to-pin convention: clicking a chart element or table row pins a dark callout card above the chart; clicking again dismisses it. Non-selected elements dim to 0.2–0.3 opacity on pin.
- R10. All charts use SVG rendering (not canvas) for print compatibility.

**Dashboard — Move 1: Net Revenue Ranking**

- R11. A bump chart shows retailers ranked by gross revenue (left axis) and by net revenue after all trade spend (right axis), with connecting lines per retailer. The crossing lines are the primary visual. Line color follows Lailara categorical palette.
- R12. Clicking a retailer line pins a dark callout card showing: retailer name, gross revenue, total trade spend, net revenue, and net-to-gross ratio (%). Clicking again dismisses.

**Dashboard — Move 2: Trade Spend Efficiency**

- R13. A chart shows two measures per retailer: trade spend as a percentage of gross revenue, and incremental lift generated per trade spend dollar. Retailers are ranked from most to least efficient. Both measures appear on the same chart to show the correlation (or lack of it).

**Dashboard — Move 3: Leakage Detection**

- R14. A leakage ledger shows four rows — one per leakage sub-type from R3 — with total dollar amount and instance count. Each row is labeled "Recoverable" (double-funded, phantom, rate discrepancy, unauthorized) or "Reallocatable" (ineffective spend — see R17). A total appears at the bottom.
- R15. Clicking a leakage sub-type row expands an AG Grid table of specific instances. Each row shows: promotion identifier, period, agreed amount, actual deduction, variance, and leakage classification.
- R16. The Excel workbook tab for Move 3 contains all instance-level detail from R15 plus the source identifiers (deduction ID, promotional agreement ID) needed to trace each instance back to the SSOT.

**Dashboard — Move 4: Promotional ROI**

- R17. A chart shows each promotion plotted by trade spend cost (x-axis) vs. gross margin on incremental units (y-axis). A break-even line (y = x) divides the chart. Promotions below the line are labeled "Lost money" and colored using Tokyo rose (#b82d4a). Promotions above the line are colored using Hong Kong teal.
- R18. A visible footnote on the Move 4 chart documents the rolling-median baseline methodology in plain language (one sentence: what baseline is, how the window was chosen).

**Dashboard — Move 5: Accrual Reconciliation**

- R19. A bar or grouped chart shows accrued trade spend vs. actual deducted trade spend by period (monthly or quarterly, depending on the Cinderhaven data granularity). A variance line or column shows the gap — the number the CFO has been estimating rather than knowing.

**Excel workbook**

- R20. The Excel workbook is generated dynamically via openpyxl when the user clicks "Download workbook." It reads from the same `trade_spend_analysis` schema as the dashboard. Dashboard and workbook numbers are always identical because they share the same source.
- R21. The workbook contains six sheets: "Summary" (first), then one sheet per analytical move named identically to the dashboard section names: "Net Revenue Ranking," "Leakage Detection," "Trade Spend Efficiency," "Promotional ROI," "Accrual Reconciliation."
- R22. Each move sheet contains instance-level detail including all source identifiers (deduction IDs, agreement IDs, period keys) that allow the CFO to trace any dollar amount on the dashboard back to specific SSOT rows.
- R23. The Summary sheet shows five findings at a glance: (a) net revenue by retailer ranked table, (b) total leakage by category (recoverable and reallocatable), (c) total ineffective promotional spend, (d) accrual variance total, (e) a one-line "what to do" recommendation per finding.

**Deployment**

- R24. The Dash app is deployed to Fly.io as an always-on service. Postgres credentials are passed via environment variables, never hardcoded. Follows `retail-velocity-decision-tool` Dockerfile as the reference.
- R25. The public Fly.io URL requires no authentication. Any viewer with the link can access the dashboard.

**Build order**

- R26. Moves are built and deployed in sales-impact order: Move 1 (Net Revenue Ranking) first, Move 3 (Leakage Detection) second, then Moves 2, 4, 5 in sequence. Each move is independently shippable — the dashboard is a valid portfolio piece after Move 1 alone, and stronger after Move 3.

---

## Acceptance Examples

- AE1. **Covers R11, R12.** Given the pipeline has run and Walmart is the highest gross-revenue retailer but fourth-highest net-revenue retailer, the bump chart shows Walmart's line crossing downward from position 1 (left) to position 4 (right). Clicking the line pins a dark card showing Walmart's gross revenue, $1.9M trade spend, net revenue, and 76% net-to-gross ratio.

- AE2. **Covers R14, R15.** Given the pipeline has identified 8 double-funded promotion instances totaling $340K, the leakage ledger shows "Double-funded promotions — $340K — 8 instances — Recoverable." Clicking that row expands an AG Grid table with 8 rows, each showing the promotion name, period, off-invoice amount, bill-back amount, and $340K apportioned across instances.

- AE3. **Covers R20, R21.** Given a viewer clicks "Download workbook," the browser downloads `cinderhaven-trade-spend-analysis.xlsx`. Opening it shows "Summary" as the first sheet, followed by five sheets in this order: "Net Revenue Ranking," "Leakage Detection," "Trade Spend Efficiency," "Promotional ROI," "Accrual Reconciliation."

- AE4. **Covers R1.** Given the pipeline script is run to completion, a `SELECT` on all Cinderhaven SSOT tables returns identical row counts and values before and after. All computed data exists only in the `trade_spend_analysis` schema.

- AE5. **Covers R26.** Given Move 1 is deployed and Moves 2–5 are not yet built, the dashboard is accessible at the Fly.io URL, shows the net revenue ranking bump chart, and the "Download workbook" button generates an Excel file containing only the Net Revenue Ranking sheet (plus Summary). The dashboard is a valid portfolio piece at this state.

---

## Success Criteria

- A CFO or CEO who opens the dashboard URL without any introduction from Shawn understands the core finding — their "best" retailer is not actually their best — within the first 30 seconds.
- A CFO can download the Excel workbook and trace any dollar amount visible on the dashboard back to specific rows in the workbook using source identifiers, without needing to ask for explanation.
- Planning (`/ce:plan`) can proceed without inventing analytical methodology, dashboard layout, chart types, Excel structure, or build sequence.
- The dashboard is a credible portfolio piece after Move 1 alone, and closes the deal after Move 3. The remaining three moves deepen the story but are not required for the piece to work.

---

## Scope Boundaries

- Modifying Cinderhaven SSOT schema or data — read-only throughout
- Authentication or access control on the dashboard
- Self-serve client data input (clients cannot plug in their own numbers)
- Automated pipeline scheduling or incremental refresh
- Real-time data refresh on the dashboard
- Advanced autoregressive or seasonality models for lift decomposition — rolling median baseline only for the portfolio piece
- Trade promotion management going forward — diagnostic only, not an ongoing TPM tool
- Actually recovering disputed deductions — the analysis identifies them; recovery is a separate engagement
- Retailer name anonymization — Cinderhaven is synthetic, retailer names are fictional

---

## Key Decisions

- **Dash over Streamlit:** already proven on Fly.io in `retail-velocity-decision-tool`; same Plotly foundation; consistent Lailara design system; no cold-start problem. User strongly dislikes Streamlit.
- **Fly.io for dashboard hosting:** same platform as Cinderhaven Postgres; internal networking eliminates connection pooling complexity.
- **Pre-compute into separate schema:** analytical computations (especially rolling median baseline) do not belong in the dashboard request path; pre-computing keeps the dashboard fast and separates analysis logic from display logic.
- **Dynamic Excel generation:** workbook and dashboard always show identical numbers because they draw from the same pre-computed results schema. Static file risks drift.
- **Build in sales-impact order (Move 1 → Move 3 first):** protects against partial completion — if the project stops early, the highest-value moves ship first.
- **Rolling-median baseline for Move 4:** manageable complexity for a portfolio piece; advanced models (ARIMA, regression) deferred to live engagement delivery.

---

## Dependencies / Assumptions

- **Cinderhaven schema is unverified.** The SSOT is assumed to contain `fct_deductions`, a promotional mart, and a POS mart — referenced in the project brief — but exact table names, column names, data types, and join keys are unknown until the database is queried. The analysis pipeline cannot be designed until schema discovery is complete.
- **`retail-velocity-decision-tool` serves as the implementation reference.** Its Fly.io Dockerfile, Lailara design system implementation, and Plotly/Dash conventions are inherited. It must be reviewed before planning to confirm which patterns to replicate.
- The bump chart (Move 1) requires custom implementation beyond Plotly's standard chart types. Whether this is achieved via `go.Scatter` with shape annotations, a Plotly figure factory approach, or a custom Dash component is unresolved.
- Synthetic Cinderhaven data is seeded to produce the specific leakage findings described in the project brief ($340K double-funded, $180K phantom, $95K rate discrepancy, ~$520K ineffective). If the current SSOT data does not already reflect these values, seeding or data correction is a prerequisite.

---

## Outstanding Questions

### Resolve Before Planning

- **[Affects R1–R5][Schema discovery]** What are the exact table names, column names, data types, and join keys in the Cinderhaven SSOT? The analysis pipeline cannot be designed without this. Resolve by querying the Fly.io Postgres directly in the first planning session.
- **[Affects R2, R3][Data verification]** Does the current Cinderhaven synthetic data produce the specific leakage findings in the project brief ($340K double-funded, $180K phantom, $95K rate discrepancy)? If not, what seeding or data correction is needed?

### Deferred to Planning

- **[Affects R11][Technical]** Bump chart implementation approach: `go.Scatter` with line shape annotations, Plotly figure factory, or a custom Dash component? Investigate during planning using the actual retailer data.
- **[Affects R4][Technical]** Rolling median window size for the baseline: what period length (4-week, 8-week?) best fits the Cinderhaven synthetic POS data cadence? Determine during analysis pipeline implementation.
- **[Affects R24][Technical]** Fly.io deployment topology: same Fly.io org and region as the Cinderhaven Postgres app, or separate? Confirm connection string and internal networking configuration during planning.
- **[Affects R6][Reference]** Review `retail-velocity-decision-tool` source before planning to confirm which Lailara design system patterns (color tokens, font loading, component layout) to replicate vs. adapt.
