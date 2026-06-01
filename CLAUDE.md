# trade-spend-leakage — Project Context for Claude

**Tier:** Heavy

## What this project is

Forensic trade spend analysis for specialty food brands ($5M–$30M). Detects leakage across five categories — double-funded promotions, phantom promos, rate discrepancies, unauthorized deductions, and ineffective spend — and reranks retailers by net revenue after all trade costs. Dual delivery: an interactive executive dashboard (the CEO's "aha" moment) and an audit-ready Excel workbook (the CFO's working model). The portfolio piece for Lailara LLC. Uses synthetic Cinderhaven data.

**Business question this project answers:** Which retailers are actually profitable after trade spend, and where is the trade budget leaking?

## Stack and tools

- Primary language: Python (Dash + pipeline)
- Key packages: Dash, dash-bootstrap-components, dash-ag-grid, Plotly, pandas, openpyxl, gunicorn
- Database: see Data architecture below
- Entry point: `app/app.py` (dashboard), `pipeline/run.py` (analysis pipeline)
- Other tools: Excel workbook (CFO deliverable via openpyxl + dcc.Download)

## Data architecture

**The Cinderhaven Data Platform (Fly.io Postgres + dbt pipeline) is the only SSOT for all Cinderhaven data.**

**⚠ PENDING CHANGE: This project's data source must be switched from the SQLite snapshot to direct Postgres connection (cinderhaven-data-platform on Fly.io). The SQLite approach in U1 is a placeholder. Before U2 ships to production, `pipeline/db.py` `source_conn()` must connect to Postgres via `DATABASE_URL`, not the local SQLite file. Update the plan and Dockerfile accordingly.**

- `data/cinderhaven-data/` is a git submodule containing a read-only SQLite snapshot. It was used for U1 scaffolding only — do not build further pipeline logic on top of it.
- If a number in the SQLite file disagrees with the Postgres platform, trust Postgres.
- This project never writes to Postgres. Read-only without exception.
- `data/results.db` is this project's pipeline output — gitignored.

## Project files

- CLAUDE.md (this file) — permanent rules and facts
- DECISIONS.md — durable choices and reasoning
- HANDOFF.md — current session state
- PLAN.md — current work arc
- FAILURES.md — things tried that didn't work
- `docs/solutions/` — documented solutions to past bugs and patterns, organized by category with YAML frontmatter (`module`, `tags`, `problem_type`). Relevant when writing or debugging pipeline SQL.

Read PLAN.md and HANDOFF.md at session start. DECISIONS.md and
FAILURES.md as relevant.

## Voice and standards

- Economist style for all written deliverables: sober, declarative, data-forward
- No marketing voice or consultant filler ("leverage," "synergy," "best-in-class," "unlock," "drive value")
- No hedging that softens a real finding
- Charts must be readable by non-data-scientist, non-researcher audiences
- Frame "ineffective promotions" as leverage and reallocation opportunity — not as a sales-team report card

## Rules

### Honesty and judgment

- Say "I don't know" or "I can't verify this" instead of guessing.
  This applies to industry context, technical claims, what code did,
  and anything else.
- Tell me what I need to hear, not what I want to hear. If a decision
  looks wrong, say so. If code I wrote has problems, say so. Honest
  assessment, not validation.
- If a rule in this file is too vague to verify whether you're
  following it, flag it for revision rather than guessing at compliance.

### Building and proposing

- No speculative abstractions. If something isn't needed right now,
  don't build it. Helper functions get added when called by real code,
  not in anticipation. Parameters get added when there's a second use
  case, not the first.
- When proposing a tool, library, or approach, present at least two
  alternatives with tradeoffs, even if one is clearly preferred. Do
  not propose a single solution and move on.
- Tie proposals back to the business question this project is
  answering. If you can't connect a proposal to that question, the
  proposal is probably fluff and should be reconsidered.
- **Do not suggest Streamlit.** User strongly dislikes it. Alternatives:
  Dash, Evidence, Observable, Panel, plain HTML/JS with D3/Vega, or
  a notebook-based approach.

### How to work the project

- Work in vertical slices, not horizontal phases. Build one feature
  end-to-end (working from input to output) before moving to the
  next. Don't build all the backend, then all the frontend — build
  one complete piece at a time.
- When a feature is working, suggest a simple test to verify it stays
  working: "This works now — want to add a quick test so it doesn't
  break later?" Don't force testing, but make it easy to say yes.
- Do not start tasks outside the current PLAN.md arc without flagging
  it to the user first.
- Do not refactor unrelated code unprompted.
- Do not rename things unless asked.

### Git branching

- Before risky or experimental changes, suggest creating a branch:
  > "This is a significant change. Want to work on a branch so we
  > can easily undo it if it doesn't work out?"
- What counts as "risky": changing how the project is structured,
  trying a new library, rewriting a working feature, anything where
  you'd say "I'm not sure this will work."
- Keep it simple: `git checkout -b experiment/short-description`
  before the change, merge back to main if it works.

### Scope creep detection

- Periodically check whether the current work matches PLAN.md.
  If the user has been building something not in the plan for more
  than ~15 minutes, flag it.
- Flag if the user keeps adding tasks to PLAN.md without completing
  existing ones — the plan is growing instead of shrinking.

## Working with PLAN.md

PLAN.md defines the current arc of work. Read it at session start.

- Mark tasks complete as they're finished, in the same commit as the work
- If a task is wrong-sized, in the wrong order, or no longer relevant,
  flag it rather than silently restructuring
- "Out of scope" items are decisions, not suggestions — do not pull
  them into the current arc without explicit user approval

## Session reminders

### Reminding the user to /log

Prompt the user to run /log when:
- A meaningful change just landed
- A natural pause point is reached
- Roughly 30–45 minutes have passed since the last /log

### Reminding the user to /wrap

Prompt the user to run /wrap when:
- Context usage crosses 65%
- The user says anything that suggests they're stopping
- A natural milestone is reached
- 90+ minutes have passed and work is winding down

### Session start protocol

1. Read CLAUDE.md, PLAN.md, and HANDOFF.md
2. If HANDOFF.md's most recent entry is more than 24 hours old AND
   there are uncommitted changes, flag this
3. Briefly state the starting point from HANDOFF.md so the user
   confirms you're caught up
4. Confirm the current PLAN.md arc is still active
5. Check the Improvement History section of PLAN.md. If overdue,
   mention it.
6. Remind the user what commands are available.

### Suggesting commands during work

- User just finished a task → "Good time to /log that."
- User seems unsure what to do next → "Want to run /improve to see what needs attention?"
- User is about to stop → "Run /wrap before you go so your next session picks up here."
- User asks "what can I do?" → "Run /commands to see everything available."
- User just built a UI feature → "Want to run /qa to test that?"
- User is starting a new arc → "Run /office-hours to stress-test the approach."
- User has a plan but hasn't reviewed it → "Run /plan-ceo-review then /plan-eng-review."

## Defaults

- Default to flagging gaps rather than filling with plausible-sounding but unverified content
- Default to short responses unless the task is substantive
- Default to asking before promoting a log entry to a DECISIONS.md entry
- Default to answering, not offering to answer
