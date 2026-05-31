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

### 2026-05-31 — Use SQLite snapshot via `cinderhaven-data` git submodule, not live Postgres connection
- **Why:** Every other Cinderhaven portfolio project uses this pattern (retail-velocity-decision-tool, trade-spend-data-diagnostic, retailer-deduction-recovery). Postgres (`cinderhaven-db` on Fly.io) is the data export source; applications consume the SQLite snapshot. Reconcilability to Postgres SSOT preserved via `flyctl postgres connect -a cinderhaven-db` export chain. Live Postgres connections add connection pooling complexity and runtime fragility for no benefit on synthetic fixed data.
- **Scope:** Data architecture globally
- **Do not:** Add a live DATABASE_URL Postgres connection to the Dash app. If Cinderhaven data changes, refresh via the export chain and rebuild the Docker image.

### 2026-05-31 — Use actual Cinderhaven data numbers; brief's leakage targets were aspirational
- **Why:** The brief's specific dollar amounts ($340K double-dips, $180K phantom promos, $95K rate discrepancies) were written before the data was built. Verified actual numbers: 3 double-dips / $19K, 137 ghost promos / ~$96K, trailing-365 deductions $1.2M, structural trade spend $4.4M (17.3%). The story is still compelling on real numbers and more credible than inflated targets.
- **Scope:** All dashboard displays and workbook figures
- **Do not:** Hard-code the brief's aspirational dollar amounts. Dashboard and workbook must show whatever the actual Cinderhaven data produces.

### 2026-05-31 — Use synthetic Cinderhaven data
- **Why:** Trade spend rates by retailer are among the most sensitive numbers a brand has — proprietary negotiation data. Cinderhaven is the standard synthetic brand for all Lailara portfolio pieces.
- **Scope:** All data used in this project
- **Do not:** Use real brand data.

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
