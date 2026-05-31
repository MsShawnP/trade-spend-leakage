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

**Status:** Resolved

**Tags:** cinderhaven, postgres, sqlite, architecture, data-source
