---
title: "slug_map CTE built on wrong assumption about retailer_deductions format silently breaks move3 leakage detection"
date: "2026-06-01"
category: logic-errors
module: pipeline/leakage-detection
problem_type: logic_error
component: database
severity: critical
symptoms:
  - "detect_double_dips returns 0 rows after a slug_map CTE is added to the query"
  - "detect_ghost_promos returns 0 rows after a slug_map CTE is added to the query"
  - "Total leakage drops from correct ~$235K to false ~$144K with no pipeline error raised"
root_cause: logic_error
resolution_type: code_fix
related_components:
  - service_object
tags:
  - retailer-id
  - slug-map
  - cross-table-join
  - leakage-detection
  - cinderhaven
  - silent-data-corruption
---

# slug_map CTE built on wrong assumption about retailer_deductions format silently breaks move3 leakage detection

## Problem

A `_SLUG_MAP_CTE` was added to three detection queries in `pipeline/move3_leakage.py` based on an incorrect entry in `DECISIONS.md` that claimed `raw.retailer_deductions.retailer_id` uses lowercase slug format (e.g. `walmart`). Both tables actually use `RET-*` format (e.g. `RET-WALMART`). The slug_map translated `RET-WALMART` → `walmart`, then tried to join against `raw.retailer_deductions` records that store `RET-WALMART` — a condition that can never be true. The result was silent data corruption: double-funded and ghost-promo leakage dropped to zero rows.

## Symptoms

- `detect_double_dips` returned 0 rows after the slug_map CTE was added, suppressing all double-funded promotion findings.
- `detect_ghost_promos` returned 0 rows after the slug_map CTE was added.
- Total leakage dropped from the correct ~$235K / 2,512 instances to a false ~$144K / 1,521 instances.
- No exception raised. All queries executed successfully and returned structurally valid DataFrames.
- The drop in instance count looked like a "correction" (removing inflated results) rather than a regression — the wrong result was plausible.

## What Didn't Work

### The wrong assumption: table formats differ

An earlier debugging session (U4, `pipeline/move2_efficiency.py`) produced a `DECISIONS.md` entry stating:

> `raw.promotions.retailer_id` = `RET-WALMART`. `raw.retailer_deductions.retailer_id` = `walmart`. Two different conventions coexist.

That entry was a misidentification. `move2_efficiency.py` joins `raw.promotions` to a different context — not `raw.retailer_deductions`. Live data confirms both tables use the same format:

| Table | `retailer_id` format | Example |
|---|---|---|
| `raw.promotions` | Prefixed | `RET-WALMART` |
| `raw.retailer_deductions` | Prefixed | `RET-WALMART` |

The correct cross-table join is direct equality: `ON p.retailer_id = d.retailer_id`.

### Why the slug_map silently broke things

A subsequent `/improve` session read the (wrong) `DECISIONS.md` entry and added `_SLUG_MAP_CTE` to `move3_leakage.py`. The CTE translated each `RET-*` promo retailer ID to a lowercase slug equivalent, then joined against `raw.retailer_deductions` on that slug. Because deductions actually store `RET-WALMART` (not `walmart`), the join predicate was always false. Queries returned 0 rows or, for `detect_ghost_promos`, a `NOT EXISTS` that always evaluated to true — both silently wrong.

The bug was only caught when live integration tests were run against the actual Postgres database, two sessions after the `/improve` change was made.

## Solution

Remove `_SLUG_MAP_CTE` from all three affected SQL constants in `move3_leakage.py`. Use direct equality for all `raw.promotions` ↔ `raw.retailer_deductions` joins.

**Before (broken — slug_map translates RET-* to lowercase, join always fails):**

```sql
-- detect_double_dips
WITH slug_map (promo_retailer_id, deduction_retailer_id) AS (
    VALUES ('RET-WALMART','walmart'), ('RET-COSTCO','costco'), ...
),
matches AS (
    SELECT DISTINCT ON (d.deduction_id) ...
    FROM raw.retailer_deductions d
    JOIN slug_map sm ON sm.deduction_retailer_id = d.retailer_id  -- 'walmart' != 'RET-WALMART'
    JOIN raw.promotions p
        ON p.retailer_id = sm.promo_retailer_id
       AND p.funding_mechanism = 'off_invoice'
       ...
```

**After (correct — direct join, both use RET-* format):**

```sql
-- detect_double_dips
WITH matches AS (
    SELECT DISTINCT ON (d.deduction_id) ...
    FROM raw.retailer_deductions d
    JOIN raw.promotions p
        ON p.retailer_id = d.retailer_id   -- both 'RET-WALMART': join works
       AND p.funding_mechanism = 'off_invoice'
       ...
```

Same fix applies to `detect_ghost_promos` and `detect_rate_discrepancies`.

## Prevention

1. **Before writing any cross-table join on a shared column name, run `SELECT DISTINCT column LIMIT 10` on both tables.** Column names can be identical while formats differ — but they can also be identical and share the same format. Do not assume either way.

2. **A `NOT EXISTS` on a broken join inverts silently.** If `NOT EXISTS` returns a large positive count where a small one is expected, the subquery join predicate is probably always false — every row has "no match" because the match condition never evaluates true.

3. **Add a live integration test that asserts each detection function returns at least one row** against the real Cinderhaven dataset. An offline test suite would not have caught this bug — only a test executing the actual join against Postgres would. Even `assert len(df) > 0` per detection function would fail immediately.

4. **`DECISIONS.md` entries can be wrong.** The stale entry (struck through in the current file) survived two sessions before being caught by a live test. Before adding a format-translation layer, verify against the database: `SELECT DISTINCT retailer_id FROM raw.retailer_deductions LIMIT 10`.

5. **`pipeline/move2_efficiency.py` is NOT a canonical reference for `move3_leakage.py` joins.** `move2` joins `raw.promotions` to different tables; its format handling does not transfer to `move3`'s `raw.retailer_deductions` joins.

6. **The correct ID convention** (confirmed via live Postgres, recorded in current `DECISIONS.md`): both `raw.promotions.retailer_id` and `raw.retailer_deductions.retailer_id` use `RET-*` format. Direct equality join. No translation CTE.

## Related Issues

- `DECISIONS.md` — "2026-06-01 — Both raw.promotions and raw.retailer_deductions use RET-\* retailer_id format" (the superseded entry immediately above is struck through)
- `pipeline/move3_leakage.py` — the fixed file; module-level comment confirms direct equality joins
