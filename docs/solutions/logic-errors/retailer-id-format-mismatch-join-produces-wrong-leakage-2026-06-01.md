---
title: "retailer_id format mismatch between raw.promotions and raw.retailer_deductions produces wrong leakage numbers"
date: "2026-06-01"
category: logic-errors
module: pipeline/leakage-detection
problem_type: logic_error
component: database
severity: critical
symptoms:
  - "detect_double_dips always returns 0 rows regardless of data volume"
  - "detect_rate_discrepancies always returns 0 rows regardless of data volume"
  - "detect_ghost_promos flags every promo_billback deduction as a ghost (NOT EXISTS always true)"
  - "Total leakage inflated from correct ~$144K to false ~$235K with no pipeline error raised"
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

# retailer_id format mismatch between raw.promotions and raw.retailer_deductions produces wrong leakage numbers

## Problem

Three of the four leakage detection queries in `pipeline/move3_leakage.py` joined `raw.promotions` to `raw.retailer_deductions` using `ON p.retailer_id = d.retailer_id` — a condition that can never be true because the two tables use incompatible `retailer_id` formats. The result was silent data corruption: double-funded and rate-discrepancy leakage disappeared entirely, while ghost promo leakage ballooned to include every billback deduction in the dataset.

## Symptoms

- `detect_double_dips` returned 0 rows on every pipeline run, suppressing all double-funded promotion findings.
- `detect_rate_discrepancies` returned 0 rows on every pipeline run.
- `detect_ghost_promos` inverted: its `NOT EXISTS` subquery checked for a matching promotion by `retailer_id`, and because the formats never matched, the subquery always found nothing — making every `promo_billback` deduction appear to be a ghost. This inflated the ghost promo total from the correct ~$96K to ~$235K.
- Total leakage reported ~$91K too high. Dashboard and Excel workbook leakage figures were both wrong.
- No exception raised. All queries executed successfully and returned structurally valid DataFrames.

## What Didn't Work

The original Move 3 was written assuming `raw.promotions.retailer_id` and `raw.retailer_deductions.retailer_id` shared the same format. The Cinderhaven Postgres schema uses two separate ID conventions with no foreign key or documented relationship between them:

| Table | `retailer_id` format | Example |
|---|---|---|
| `raw.promotions` | Prefixed | `RET-WALMART` |
| `raw.retailer_deductions` | Lowercase slug | `walmart` |

The bug went undetected during initial development because all pipeline tests were offline (no live Postgres), so no test ever executed the actual cross-table join. The queries ran without error and returned plausible-looking DataFrames — `double_dips` returning 0 rows looks like a clean dataset, not a broken join.

The `NOT EXISTS` inversion in the ghost promo query made the failure especially deceptive: the wrong result was a large positive number ($235K), not a zero or an exception, so it didn't trigger the "why is this empty?" alarm that would have caught the other two cases.

Note: `pipeline/move2_efficiency.py` correctly handled this format difference from the start using a `slug_map` CTE. Move 3 was written separately and the pattern was not carried forward.

## Solution

Add a `slug_map` CTE to every query that joins `raw.promotions` to `raw.retailer_deductions`. The CTE maps each `promo_retailer_id` (the `RET-*` format) to its corresponding `deduction_retailer_id` (the lowercase slug format). Both tables then join through the CTE rather than directly to each other.

The snippets below are abbreviated illustrations — refer to the full SQL constants in `pipeline/move3_leakage.py` for the complete query text.

**The shared CTE (defined as a module-level constant, evaluated at import time):**

```python
# Defined before the SQL f-strings that reference it — Python evaluates
# module-level f-strings at import time, so ordering matters.
# VALUES must be hardcoded literals; never construct this from external input.
_SLUG_MAP_CTE = """
slug_map (promo_retailer_id, deduction_retailer_id) AS (
    VALUES
        ('RET-WALMART',    'walmart'),
        ('RET-COSTCO',     'costco'),
        ('RET-KROGER',     'kroger'),
        ('RET-WHOLEFOODS', 'whole_foods'),
        ('RET-SPROUTS',    'sprouts'),
        ('RET-REGIONAL',   'regional')
)"""
```

**Before (broken — direct join, formats never match):**

```sql
-- detect_double_dips  (same broken pattern in detect_rate_discrepancies)
FROM raw.retailer_deductions d
JOIN raw.promotions p
    ON p.retailer_id = d.retailer_id   -- always false: 'RET-WALMART' != 'walmart'
   AND p.funding_mechanism = 'off_invoice'
   ...
```

```sql
-- detect_ghost_promos
WHERE d.deduction_type = 'promo_billback'
  AND NOT EXISTS (
      SELECT 1 FROM raw.promotions p
      WHERE p.retailer_id = d.retailer_id   -- always false → NOT EXISTS always true
        AND d.deduction_date BETWEEN ...
  )
```

**After (fixed — join through slug_map):**

```sql
-- detect_double_dips
WITH slug_map (promo_retailer_id, deduction_retailer_id) AS (
    VALUES ('RET-WALMART','walmart'), ('RET-COSTCO','costco'), ...
),
matches AS (
    SELECT DISTINCT ON (d.deduction_id) ...
    FROM raw.retailer_deductions d
    JOIN slug_map sm ON sm.deduction_retailer_id = d.retailer_id
    JOIN raw.promotions p
        ON p.retailer_id = sm.promo_retailer_id   -- formats now aligned
       AND p.funding_mechanism = 'off_invoice'
       ...
```

```sql
-- detect_ghost_promos
WITH slug_map (promo_retailer_id, deduction_retailer_id) AS (
    VALUES ('RET-WALMART','walmart'), ('RET-COSTCO','costco'), ...
)
SELECT ...
FROM raw.retailer_deductions d
JOIN slug_map sm ON sm.deduction_retailer_id = d.retailer_id
WHERE d.deduction_type = 'promo_billback'
  AND NOT EXISTS (
      SELECT 1 FROM raw.promotions p
      WHERE p.retailer_id = sm.promo_retailer_id   -- correctly scoped to matching retailer
        AND d.deduction_date BETWEEN ...
  )
```

## Prevention

**The `slug_map` CTE is the canonical pattern for any pipeline query that joins `raw.promotions` to any other Cinderhaven table.** Apply it without exception.

1. **Never join `raw.promotions` to `raw.retailer_deductions` directly on `retailer_id`.** The columns share a name but not a format. The join executes silently and returns 0 rows rather than raising an error.

2. **Use `pipeline/move2_efficiency.py` as the canonical reference for the `slug_map` CTE** — it predates the bug and has been correct from the start. Both `move2_efficiency.py` and `move3_leakage.py` must stay in sync; if Cinderhaven adds a new retailer, update the VALUES list in both files and any new pipeline module. The VALUES must be hardcoded string literals — never construct the CTE content from external input or runtime data (use psycopg2 parameterized queries for any values that come from outside the source file).

3. **Before shipping any new cross-table join, run `SELECT COUNT(*)` to confirm the join returns rows.** A zero count where hundreds are expected is a format mismatch, not a clean dataset. A `NOT EXISTS` on a broken join inverts — it returns a large positive result, not an error.

4. **Add a live integration test that asserts each detection function returns at least one row** against the real Cinderhaven dataset (or a fixture with known matches). The offline test suite would not have caught this bug — only a test that executes the actual join against Postgres would. Even a single `assert len(df) > 0` per detection function would have failed immediately.

5. **The full ID format convention is in `DECISIONS.md`** (entry: "2026-05-31 — promotions.retailer_id uses RET-\* format; retailer_deductions uses lowercase slugs"). Read that entry before writing any new pipeline SQL touching these tables.

## Related Issues

- `DECISIONS.md` — "promotions.retailer_id uses RET-\* format; retailer_deductions uses lowercase slugs"
- `pipeline/move2_efficiency.py` — canonical reference implementation of the `slug_map` CTE (correct from the start)
- `pipeline/move3_leakage.py` — the fixed file; all three affected SQL constants now use `_SLUG_MAP_CTE`
