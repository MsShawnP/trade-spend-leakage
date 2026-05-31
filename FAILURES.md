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
