"""Move 3 — Leakage Detection pipeline.

Detects four leakage sub-types in raw.retailer_deductions:

1. Double-funded promotions — promo_billback deductions that match an
   off_invoice promotion (retailer + date window). Off-invoice promos are
   already embedded in the invoice price; a subsequent billback is a
   double-charge.

2. Ghost promotions — promo_billback deductions with no matching promotion
   in raw.promotions at all (retailer + ±14 day date window). Real cash
   outflows against non-existent promotions.

3. Rate discrepancies — promo_billback deductions matched to a non-off-invoice
   promotion where the deduction amount exceeds the agreed promo_cost by more
   than 5%. (May yield zero rows — that's a valid result.)

4. Unauthorized deductions — deduction types outside the known operational
   set (currently: pricing_error).

Writes:
  results_leakage_summary   — one row per sub-type
  results_leakage_instances — one row per leakage incident

Both tables are written to results.db.
"""

from __future__ import annotations

import pandas as pd
import psycopg2.extras

from pipeline.db import source_conn, results_conn

# ---------------------------------------------------------------------------
# Column schema constants — shared by all four detection functions.
# ---------------------------------------------------------------------------

_INSTANCE_COLS = [
    "leakage_type",
    "deduction_id",
    "retailer_id",
    "promo_id",
    "period",
    "agreed_amount",
    "actual_amount",
    "variance",
    "classification",
]

_SUMMARY_COLS = ["leakage_type", "display_name", "dollar_total", "instance_count", "classification"]

_KNOWN_TYPES = frozenset({
    "promo_billback", "short_ship", "label_fine", "spoilage",
    "slotting", "late_delivery", "damaged", "pallet_fine",
})

# ---------------------------------------------------------------------------
# Detection functions — each returns a DataFrame with _INSTANCE_COLS.
# ---------------------------------------------------------------------------
# Both raw.promotions and raw.retailer_deductions use the same 'RET-*'
# retailer_id format, so all cross-table joins use direct equality.
# ---------------------------------------------------------------------------

_DOUBLE_DIP_SQL = """
WITH matches AS (
    SELECT DISTINCT ON (d.deduction_id)
        d.deduction_id,
        d.retailer_id,
        d.amount          AS actual_amount,
        d.deduction_date  AS period,
        p.promo_id,
        p.promo_cost      AS agreed_amount
    FROM raw.retailer_deductions d
    JOIN raw.promotions p
        ON p.retailer_id = d.retailer_id
       AND p.funding_mechanism = 'off_invoice'
       AND d.deduction_date BETWEEN p.start_week
                               AND p.end_week + INTERVAL '14 days'
    WHERE d.deduction_type = 'promo_billback'
    ORDER BY d.deduction_id, d.amount DESC
)
SELECT * FROM matches ORDER BY actual_amount DESC
"""

_GHOST_PROMO_SQL = """
SELECT
    d.deduction_id,
    d.retailer_id,
    d.amount        AS actual_amount,
    d.deduction_date AS period
FROM raw.retailer_deductions d
WHERE d.deduction_type = 'promo_billback'
  AND NOT EXISTS (
      SELECT 1 FROM raw.promotions p
      WHERE p.retailer_id = d.retailer_id
        AND d.deduction_date BETWEEN p.start_week - INTERVAL '14 days'
                                 AND p.end_week   + INTERVAL '14 days'
  )
ORDER BY d.amount DESC
"""

_RATE_DISCREPANCY_SQL = """
SELECT DISTINCT ON (d.deduction_id)
    d.deduction_id,
    d.retailer_id,
    d.amount            AS actual_amount,
    d.deduction_date    AS period,
    p.promo_id,
    p.promo_cost        AS agreed_amount,
    d.amount - p.promo_cost AS variance
FROM raw.retailer_deductions d
JOIN raw.promotions p
    ON p.retailer_id = d.retailer_id
   AND p.funding_mechanism != 'off_invoice'
   AND d.deduction_date BETWEEN p.start_week - INTERVAL '14 days'
                            AND p.end_week   + INTERVAL '14 days'
WHERE d.deduction_type = 'promo_billback'
  AND p.promo_cost IS NOT NULL
  AND d.amount > p.promo_cost * 1.05
ORDER BY d.deduction_id, variance DESC
"""

_UNAUTHORIZED_SQL = """
SELECT
    d.deduction_id,
    d.retailer_id,
    d.deduction_type,
    d.amount         AS actual_amount,
    d.deduction_date AS period
FROM raw.retailer_deductions d
WHERE d.deduction_type NOT IN %(known_types)s
ORDER BY d.amount DESC
"""


def _empty_instances() -> pd.DataFrame:
    return pd.DataFrame(columns=_INSTANCE_COLS)


def detect_double_dips(conn) -> pd.DataFrame:
    """Return double-funded promotion instances."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_DOUBLE_DIP_SQL)
        rows = cur.fetchall()
    if not rows:
        return _empty_instances()
    df = pd.DataFrame([dict(r) for r in rows])
    df["leakage_type"] = "double_funded"
    df["classification"] = "Recoverable"
    df["variance"] = df["actual_amount"]  # entire amount is the double-charge
    return df[_INSTANCE_COLS]


def detect_ghost_promos(conn) -> pd.DataFrame:
    """Return ghost promotion (phantom billback) instances."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_GHOST_PROMO_SQL)
        rows = cur.fetchall()
    if not rows:
        return _empty_instances()
    df = pd.DataFrame([dict(r) for r in rows])
    df["leakage_type"] = "ghost_promo"
    df["classification"] = "Reallocatable"
    df["promo_id"] = None
    df["agreed_amount"] = None
    df["variance"] = df["actual_amount"]
    return df[_INSTANCE_COLS]


def detect_rate_discrepancies(conn) -> pd.DataFrame:
    """Return rate discrepancy instances (may be empty)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_RATE_DISCREPANCY_SQL)
        rows = cur.fetchall()
    if not rows:
        return _empty_instances()
    df = pd.DataFrame([dict(r) for r in rows])
    df["leakage_type"] = "rate_discrepancy"
    df["classification"] = "Recoverable"
    return df[_INSTANCE_COLS]


def detect_unauthorized(conn) -> pd.DataFrame:
    """Return deductions with unauthorized (outside known operational set) types."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_UNAUTHORIZED_SQL, {"known_types": tuple(_KNOWN_TYPES)})
        rows = cur.fetchall()
    if not rows:
        return _empty_instances()
    df = pd.DataFrame([dict(r) for r in rows])
    df["leakage_type"] = "unauthorized"
    df["classification"] = "Recoverable"
    df["promo_id"] = df["deduction_type"]   # store the type name in promo_id slot
    df["agreed_amount"] = None
    df["variance"] = df["actual_amount"]
    return df[_INSTANCE_COLS]


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

_DISPLAY_NAMES = {
    "double_funded":   "Double-funded promotions",
    "ghost_promo":     "Ghost promotions",
    "rate_discrepancy": "Rate discrepancies",
    "unauthorized":    "Unauthorized deductions",
}


def _build_summary(instances: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for leakage_type, display_name in _DISPLAY_NAMES.items():
        sub = instances[instances["leakage_type"] == leakage_type]
        rows.append({
            "leakage_type":    leakage_type,
            "display_name":    display_name,
            "dollar_total":    float(sub["actual_amount"].sum()) if not sub.empty else 0.0,
            "instance_count":  len(sub),
            "classification":  sub["classification"].iloc[0] if not sub.empty else (
                "Reallocatable" if leakage_type == "ghost_promo" else "Recoverable"
            ),
        })
    return pd.DataFrame(rows, columns=_SUMMARY_COLS)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run() -> None:
    """Execute Move 3 and write leakage tables to results.db."""
    with source_conn() as conn:
        dfs = [
            detect_double_dips(conn),
            detect_ghost_promos(conn),
            detect_rate_discrepancies(conn),
            detect_unauthorized(conn),
        ]

    instances = pd.concat(dfs, ignore_index=True)
    for col in ["agreed_amount", "actual_amount", "variance"]:
        instances[col] = pd.to_numeric(instances[col], errors="coerce").astype(float)

    summary = _build_summary(instances)

    with results_conn() as conn:
        summary.to_sql("results_leakage_summary", conn, if_exists="replace", index=False)
        instances.to_sql("results_leakage_instances", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_leakage_instances_type "
            "ON results_leakage_instances(leakage_type)"
        )

    total = summary["dollar_total"].sum()
    print(
        f"  Move 3 complete — {len(instances)} instances / ${total:,.0f} total leakage "
        f"written to results_leakage_summary + results_leakage_instances"
    )
