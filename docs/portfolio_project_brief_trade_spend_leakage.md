# Portfolio Project Brief: Trade Spend Leakage Analysis

**Working title:** *"Your Best Retailer Isn't the One That Buys the Most"*

**Repo (recommended):** `trade-spend-leakage`

**Status:** Brainstorm / Brief stage
**Tier:** Curated backlog #3 (high-value, all-tier — drills into the second-largest line item in the business)
**Priority:** Build after SKU Rationalization and Competitive Shelf Intelligence.

---

### 1. The Pain

Trade spend is the second-largest line item in a specialty food brand's P&L after COGS — typically 15–30% of gross revenue. It's also the least controlled.

Trade spend is the money the brand pays retailers to sell its products: slotting fees, off-invoice allowances, bill-backs (MCBs), scan-downs, promotional funds, ad fees, free fills. It gets negotiated by sales, executed by the retailer, deducted automatically from payments, accrued as an estimate by finance — and reconciled by nobody.

The result is systematic leakage that nobody sees:

- **Paying twice.** The brand funds a promotion off-invoice (lower price at time of shipment) AND the retailer also takes a bill-back deduction for the same promotion. The mechanism: Sales enters the off-invoice discount into the ERP, while the retailer reads the same promotional contract as a scan-back/bill-back and deducts it on the backend. The two are tracked in different systems and never reconciled, so the brand pays for one promotion two ways.
- **Phantom promotions.** The brand is deducted for a promotion that never ran — no corresponding lift in the POS data, but the deduction hit the payment anyway.
- **Rate discrepancies.** The agreed promotional rate was 15% off; the deduction came through at 22%. Nobody checks.
- **Unauthorized deductions.** Trade spend deducted with no matching promotional agreement at all.
- **Promotions that didn't pay.** The promo ran, the brand funded it, but it generated no incremental lift — the brand paid the retailer to discount product that would have sold at full price anyway.
- **Untracked accruals.** Finance accrues for expected trade spend, but never reconciles accrued-vs-actual, so the variance leaks invisibly into "miscellaneous."

The deepest problem is conceptual: **the brand ranks its retailers by gross revenue.** The CEO knows Walmart is "our biggest account" because Walmart buys the most. But nobody computes net revenue after all trade spend and deductions. When they finally do, the ranking often inverts — the biggest gross account is one of the worst net accounts, because trade spend is eating it alive.

**Who feels it:**
- **$3M–$10M:** The founder negotiates trade spend personally and tracks it in their head. There's no system. The leakage is smaller in absolute terms but a higher percentage because the founder has no leverage in negotiations.
- **$10M–$15M:** Trade spend is now $1.5M–$4M. Nobody owns reconciliation. The CFO sees the total on the P&L but can't break it down by retailer, by promotion, or by whether it generated return.
- **$15M–$20M:** Trade spend is $3M–$6M — the second-biggest cost in the business and the least controlled. The board is starting to ask "what are we actually getting for our trade spend?" and nobody has an answer.

**How it compounds:** Trade spend leakage compounds with the deduction doom loop. A brand that can't reconcile trade spend can't tell legitimate promotional deductions from invalid ones — so it either disputes nothing (and leaks money) or disputes everything (and damages retailer relationships). And because trade spend is negotiated annually based on the prior year's spend, leakage gets baked into the next year's budget. The brand negotiates UP from an inflated, unreconciled base.

#### The Status Quo

Trade spend lives in three disconnected places: the promotional agreements (in sales' emails and a spreadsheet), the deductions (in the remittance data, coded cryptically), and the accruals (in the accounting system, as estimates). Nobody has joined them. The CEO sees one number — "trade spend: ~$3.6M/yr" (11.0% of scan revenue, trailing 52 weeks) — and has no way to ask which retailers, which promotions, or which dollars worked. So the question never gets asked, and the leakage never gets found.

---

### 2. Why This Piece

**Drills into the second-largest line item in the business.** COGS gets scrutinized constantly. Trade spend — nearly as large — gets almost none. This piece puts the same rigor on trade spend that brands already put on COGS.

**The "net revenue by retailer" reframe is the hook.** Ranking retailers by gross revenue is the default everywhere. Ranking by net revenue after trade spend inverts the list and changes strategic priorities. That reframe is the kind of "stop and think differently about your own business" moment that makes a portfolio piece land.

**Distinct from the existing deduction and channel pieces.** This is a common confusion point worth being precise about:
- **Retailer Deduction Recovery** recovers *invalid* deductions and chargebacks — money taken in error.
- **Where the Money Actually Comes From** analyzes channel profitability at the channel level.
- **Contract-to-Cash** traces the full gross-to-net path from invoice to cash.
- **Trade Spend Leakage** drills specifically into the *planned promotional investment* — whether trade spend was double-paid, phantom-charged, rate-mismatched, or simply ineffective. It's about the trade dollars the brand chose to spend, not the deductions it got hit with by surprise.

**All-tier.** Every brand spends on trade. The analysis scales: $5M brand finds $40K in leakage, $20M brand finds $600K. Same methodology, different scale.

**Compounds with the portfolio:**
- **Where the Money (#10):** Channel profitability sets the frame; this piece explains the single biggest driver of the gap between gross and net within each channel.
- **Retailer Deduction Recovery (#4):** Deduction recovery finds invalid charges; trade spend analysis finds the planned spend that leaked. Together they cover both halves of the deduction picture.
- **Velocity Decision Tool (#1):** Promotional lift analysis (did the promo move incremental units?) feeds the "promotions that didn't pay" finding.

---

### 3. The Analysis — What It Reveals

This is the heart of the piece. Five analytical moves:

**Move 1 — Net revenue by retailer.**
For each retailer, compute: gross revenue − COGS − all trade spend − all deductions = net revenue. Rank retailers by net, not gross. Show the reorder as a bump chart (connected rank-order lines) — retailers ranked by gross volume on the left, by true net revenue on the right, with lines connecting each retailer's two positions. The crossing lines are the visual: the retailer the brand has been treating as #1 visibly drops to #4. This is the headline.

**Move 2 — Trade spend efficiency by retailer.**
Trade spend as a percentage of gross revenue, by retailer. Then incremental lift generated per dollar of trade spend. Some retailers are efficient (every promo dollar drives real incremental volume); others are sinkholes (trade spend high, incremental lift low). The brand learns where its trade dollars actually work.

**Move 3 — Leakage detection.**
The forensic layer. Cross-reference promotional agreements against actual deductions to surface:
- Double-funded promotions (off-invoice + bill-back for the same event)
- Phantom promotions (deductions with no matching agreement and no POS lift)
- Rate discrepancies (deduction rate exceeds agreed rate)
- Unauthorized deductions (no agreement at all)
Each leak type gets a dollar total and a list of specific instances.

**Move 4 — Promotional ROI.**
For promotions that DID run as agreed: did they generate incremental lift, or did the brand pay to discount baseline volume? Isolate baseline from promotional lift using a rolling-median baseline (robust and clear for the portfolio piece; advanced autoregressive/seasonality models reserved for engagement delivery). Flag promotions where the trade spend exceeded the gross margin on the incremental units — i.e., promotions that lost money even when they "worked."

**Move 5 — The accrual reconciliation.**
Accrued trade spend vs. actual deducted trade spend, by period. The variance is the number finance has been guessing at. Closing this gap gives the CFO a real trade spend number for the first time.

#### The Output

Dual delivery, resolved:

- **The CFO's working model (lead deliverable):** an audit-ready Excel workbook with clear data lineage from raw remittance and promotional inputs to the final leakage schedules. The CFO runs on Excel and will want to audit the join logic; this is the operational engine.
- **The executive dashboard (the hook):** a clean interactive view — the gross-vs-net bump chart, a "leakage ledger" (total recoverable vs. total reallocatable), and per-retailer scorecards. This is what delivers the CEO's "aha" moment.

The Excel model gives the CFO credibility and auditability; the dashboard gives the CEO the reframe. Both, not either.

#### The Margin Math

For a $25M brand spending ~$3.6M/yr on trade (11.0% of scan revenue, trailing 52 weeks):

| Leakage Category | Typical % of Trade | Financial Impact | Strategic Action |
|------------------|:------------------:|:----------------:|------------------|
| Double-funding | 1–3% | $40K–$115K | Claw back (clerically invalid) |
| Phantom promotions + rate creep | 1–4% | $40K–$150K | Dispute / deduct back |
| Ineffective promotions (ran but lost money) | 10–25% | $380K–$950K | Reallocate to efficient windows |
| **Total value unlocked** | **12–32%** | **$460K–$1.2M** | **~2–5 points of margin expansion** |

The split matters: the double-funding, phantom, and rate-creep buckets are *recoverable* — money to claw back or dispute. The ineffective-promotion bucket (the largest) is *reallocatable* — money to redirect from promotions and retailers that don't generate return to ones that do. Plus the accrual true-up, which isn't a hard dollar recovery but gives the CFO a real trade spend number to budget and negotiate from.

#### Before / After

- **Before:** CEO treats Walmart as the #1 account because it buys the most. Trade spend is "~$3.6M/yr" — one number, no breakdown. Promotional decisions are made on relationship and habit. Nobody reconciles agreements against deductions.

- **After:** CEO sees Walmart ranks #4 by net revenue after its trade load. Sees ~$1.14M in identified leakage — $615K recoverable/preventable, $520K reallocatable. Reallocates trade spend from the sinkhole retailers to the efficient ones. Disputes the double-funded and phantom deductions with evidence. Next year's trade spend negotiation starts from a reconciled base, not an inflated one.

#### Who Else Sees This?

- **Primary:** CFO (owns the P&L line), CEO (makes the retailer prioritization calls), VP Sales (negotiates the trade spend).
- **Secondary:** Board (asking what trade spend buys), broker (sometimes complicit in the leakage, sometimes an ally in fixing it).
- **How it gets shared:** CFO builds the net-revenue ranking, shows the CEO: "Walmart isn't our best account." That single slide reorganizes the strategic conversation. The board sees the leakage total and asks for it quarterly.

---

### 4. Technical Notes (kept light)

The analysis joins three data sources the brand already has but has never connected: promotional agreements, deduction/remittance data, and POS/shipment data. The work is primarily in the join logic and the leakage-detection rules, not in exotic tooling. It runs on the Cinderhaven Data Platform alongside the deduction and channel models. Delivered as an interactive view for exploration plus an Excel workbook as the CFO's working model. Specific stack choices can follow the patterns already established in the portfolio (Streamlit + Excel + platform-backed data) and aren't worth over-specifying at the brief stage.

---

### 5. Skills Demonstrated

- **Trade spend domain fluency** — understanding off-invoice vs. bill-back, MCBs, scan-downs, accrual accounting for trade. This is specialized CPG finance knowledge that signals deep industry expertise.
- **Forensic reconciliation** — joining agreements to deductions to POS to find the leaks. This is detective work, not just reporting.
- **Incremental lift decomposition** — separating promotional incremental volume from baseline. A genuine analytical technique.
- **The reframe** — net revenue vs. gross revenue ranking. Demonstrates the practice's core skill: turning data the brand already has into a decision they've never been able to make.

---

### 6. Foot-in-the-Door Offering

- **Offering name:** Trade Spend Diagnostic
- **Format:** Fixed-fee 2–3 week engagement
- **Price range:** $15K–$25K
- **What the client gets:**
  1. Net revenue by retailer (the reordered ranking)
  2. Trade spend efficiency ranking — where the dollars work and where they don't
  3. Leakage report — double-funded, phantom, rate-discrepancy, unauthorized — with specific dollar amounts and instances
  4. Promotional ROI — which promotions made money, which lost money
  5. Accrual reconciliation — a real trade spend number for the CFO
  6. Reallocation recommendation — move $X from sinkhole retailers/promos to efficient ones
  7. Excel working model tuned to the client's data
- **Why this piece sells it:** The net-revenue reframe alone justifies the engagement. The CEO sees their retailer ranking invert and immediately wants the full analysis on their real numbers. The leakage total (recoverable money) often pays for the engagement several times over.

#### Client Lift

- **What the client provides:** Promotional agreements/calendar (often in spreadsheets and emails), deduction/remittance detail, and POS or shipment data. The agreements are usually the messy part — they live in sales' inboxes, not a system. One kickoff call plus a few hours assembling the promotional history.

#### The DIY Defense

- **The three data sources have never been joined.** Agreements live with sales, deductions live in remittance data, POS lives in retailer portals. Connecting them requires entity resolution (matching a deduction code to a promotional agreement to a POS lift) that nobody internally has built.
- **Trade spend coding is cryptic.** Deduction reason codes are retailer-specific and opaque. Knowing that a Walmart code maps to a specific promotional event — and whether that event was also funded off-invoice — requires both the data work and the domain knowledge.
- **Incremental lift decomposition is real analysis.** "Did the promo work?" requires separating incremental from baseline volume, controlling for seasonality. A spreadsheet can't do it; it needs a proper baseline model.

---

### 7. Competitor / Existing Content Scan

- **What exists:**
  - **Trade promotion management (TPM) software** — Vividly, CPGvision, Blacksmith, UpClear. Powerful but expensive ($30K–$150K/year), built for brands large enough to have a dedicated trade spend team. Sub-$30M brands can't justify them.
  - **Deduction management services** — focus on recovering invalid deductions, not analyzing trade spend efficiency.
  - **Broker reporting** — brokers sometimes report on promotional performance, but they're often party to the trade spend negotiation and not a neutral analyst.
  - **Generic "trade spend best practices" content** — trade press articles, consultant blogs. High-level, not analytical.
- **What's missing:** A diagnostic-level analysis for the $5M–$30M brand that can't afford TPM software but is leaking real money in trade spend. Nobody serves this band with actual forensic analysis.
- **Your angle:** The net-revenue reframe + forensic leakage detection + promotional ROI, delivered as a fixed-fee diagnostic, for the brand that's too small for Vividly but too big to keep ignoring a $3M line item.

---

### 8. Cinderhaven Integration

> **Scale note (2026-07-30).** The worked example below is an illustrative
> composite sized for a promo-active trade book. Cinderhaven's own promotional
> spend wound down in Nov 2024 (trailing-36m promo book: $328,891; cy2025: $0),
> so the live dashboard reports current — and much smaller — promo-side figures
> from Postgres. The leak taxonomy is what carries; the dollars below are not
> current Cinderhaven figures.

Cinderhaven runs ~$3.6M/yr in all-in trade (11.0% of scan revenue, trailing 52 weeks) across Walmart, Costco, UNFI/Whole Foods, KeHE, and DTC. On a promo-active book of that size, the analysis pattern finds:

- **The ranking inverts:** Walmart is #1 by gross revenue ($8M) but #4 by net revenue after $1.9M in trade spend. Costco, which buys less gross, keeps far more net.
- **$340K in double-funded promotions** — funded off-invoice and also deducted as bill-backs.
- **$180K in phantom promotions** — deducted with no matching agreement and no POS lift.
- **$95K in rate discrepancies** — deductions exceeding agreed promotional rates.
- **~$520K in ineffective promotions** — ran as agreed but generated no positive ROI (paid to discount baseline volume).

Total identified: ~$615K recoverable/preventable + ~$520K reallocatable — roughly 30% of a promo-active trade book. The headline: **a material slice of trade spend leaks, and the "best" retailer can be one of the worst.**

Runs on the existing Cinderhaven Data Platform — joins the `fct_deductions`, promotional, and POS marts. Consistent with the deduction figures in Retailer Deduction Recovery and the channel figures in Where the Money.

---

### 9. Tactical Notes

- **Lead with the reframe, not the leakage.** The net-revenue ranking inversion is the emotional hook — it challenges the CEO's mental model of their own business. The leakage detection is the proof that follows. Open with "your best retailer isn't the one that buys the most."
- **Be precise about the distinction from deduction recovery.** Buyers (and the CEO) will conflate this with chargeback recovery. The clean line: deduction recovery is about money taken *in error*; trade spend analysis is about money the brand *chose to spend* and whether it worked. Both matter; they're different.
- **The promotional agreements are the hard input.** Most brands don't have a clean promotional calendar — it's reconstructed from emails, broker confirmations, and memory. Acknowledge this. Part of the engagement's value is forcing the agreements into a structured form for the first time.
- **"Ineffective promotions" is the largest and most sensitive finding — frame it as leverage, not blame.** Telling a CEO that $500K of trade spend generated no return implicates the sales team that negotiated those promos. This is an *optimization and leverage* exercise, not a sales-mistake audit. The framing: "this $500K can be reallocated to promotions and windows that actually drive incremental volume" — money to redeploy, not money wasted. The sales team gets a sharper tool for negotiating the next promo calendar, not a report card.
- **Absorbs #27 and #115.** The curated backlog's "Trade Spend Data Diagnostic" (#27, the designated Excel proof piece) and the brainstorm's "Trade spend planned vs deducted" (#115) both fold into this piece. The Excel workbook is the lead deliverable, satisfying the Excel-proof-piece requirement; the accrual true-up (Move 5) is #115 realized. No separate trade spend pieces get built.

#### The Credibility Marker

Knowing exactly why double-funding happens: Sales enters an off-invoice discount into the ERP, while the retailer reads the *same* promotional contract as a scan-back/bill-back and takes a deduction on the backend. The two live in different systems — the ERP and the retailer's remittance — and nobody reconciles them, so the brand funds one promotion twice. Understanding this specific failure mode — and knowing that scan-downs, MCBs, free fills, and ad fees each leak through their own mechanism — is the practitioner signal. Generic "trade spend is hard to track" is not; "here is the exact systems disconnect that causes double-funding and how to detect it" is.

#### Data Paranoia / Security

Trade spend rates by retailer are among the most sensitive numbers a brand has — they're proprietary negotiation data. Cinderhaven's numbers are synthetic. Engagement uses NDA; deliverables can anonymize retailer names. The analysis runs on the brand's own data; nothing is retained.

---

### 10. Open Questions

- [x] ~~**Absorb #27 Trade Spend Data Diagnostic?**~~ Resolved: Yes. The Excel workbook is the lead deliverable here — no separate trade spend piece.
- [x] ~~**Absorb #115 Trade spend planned vs deducted?**~~ Resolved: Yes. It's the accrual true-up move (Move 5).
- [x] ~~**Lead deliverable: interactive or Excel?**~~ Resolved: Dual delivery. Excel is the lead (CFO audits the logic); interactive dashboard is the hook (CEO gets the inversion).
- [x] ~~**How much promotional ROI / lift decomposition?**~~ Resolved: Robust-but-clear historical median baseline for the portfolio piece; advanced autoregressive/seasonality models reserved for live engagement delivery.
- [ ] **Real or synthetic promotional agreement data for Cinderhaven?** Synthetic, seeded to produce the specific leakage findings described.

---

### 11. Build Estimate

- **Effort level:** Medium. The analytical logic (the joins, the leakage rules, the lift decomposition) is the work. Runs on the existing platform, so no new infrastructure.
- **Time estimate:** ~2–3 weeks. The promotional-to-deduction join logic and the leakage-detection rules are the long pole; the visualizations and Excel model follow established portfolio patterns.

#### Out of Scope

- **Trade promotion management going forward.** This is a diagnostic (what leaked, what's reallocatable), not an ongoing TPM system. Ongoing management is either a retainer or a software recommendation.
- **Negotiating trade spend rates.** The analysis shows what's leaking; it doesn't renegotiate the deals. That's the brand's job (or the broker's), informed by the analysis.
- **Recovering the deductions.** The analysis identifies recoverable leakage; actually disputing and recovering it is deduction-recovery engagement work (#4).

---

### Relationship to Existing Inventory

| Project | Relationship |
|---------|-------------|
| Where the Money Actually Comes From (#10, built) | Channel profitability sets the frame; this explains the biggest gross-to-net driver within each channel. |
| Retailer Deduction Recovery (#4, built) | Recovery finds money taken in error; this finds planned spend that leaked. Two halves of the deduction picture. |
| Contract-to-Cash (#9, built) | C2C traces the full gross-to-net path; this drills into the trade spend component of that gap. |
| Velocity Decision Tool (#1, built) | Promotional lift analysis feeds the "promotions that didn't pay" finding. |
| Trade Spend Data Diagnostic (#27 / curated backlog) | **Absorbed.** Excel workbook is the lead deliverable here — satisfies the Excel proof-piece requirement. No separate piece built. |
| Brainstorm #115 Trade spend planned vs deducted (21) | Absorbed — this IS the accrual reconciliation move. |
| Brainstorm #109 Trade promo calendar vs shipment data (21) | Absorbed — feeds the leakage detection. |
| Umbrella (#3, built) | Maps to a decision in the ten-decision framework — "how much of our top-line revenue is being clawed back." |

---

*Brief complete when open questions are resolved.*
