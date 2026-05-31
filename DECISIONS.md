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

### 2026-05-31 — Use synthetic Cinderhaven data
- **Why:** Trade spend rates by retailer are among the most sensitive numbers a brand has — proprietary negotiation data. Cinderhaven is the standard synthetic brand for all Lailara portfolio pieces.
- **Scope:** All data used in this project
- **Do not:** Use real brand data. Seed synthetic data to produce the specific leakage findings described in the brief ($340K double-funded, $180K phantom, $95K rate discrepancy, ~$520K ineffective).

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
