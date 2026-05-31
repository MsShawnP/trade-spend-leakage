# Test conventions for this project's `tests/`

This file applies when Claude is working in `trade-spend-leakage/tests/`.

## What gets tested

- Public-facing functions and behaviors.
- All five leakage detection rules (double-funding, phantom promos, rate discrepancies, unauthorized deductions, ineffective promotions).
- Edge cases the user surfaced during /clarify.
- Anything in FAILURES.md that has a corresponding fix in code.
- Join logic — row counts, key matching, unexpected nulls.

## What doesn't need a test

- Glue code (one-line wrappers, trivial mappings).
- Configuration constants.
- Pure type definitions.

## Structure

- Mirror the source tree: `src/foo/bar.py` → `tests/foo/test_bar.py`.
- One file per source module unless tests are huge.
- Group related tests by behavior, not by function name.

## Test names

- Describe what the test verifies, in plain English.
- Pattern: `test_<behavior>_when_<condition>`
- Bad: `test_function_1`, `test_leakage`
- Good: `test_detects_double_funding_when_off_invoice_and_billback_match_same_promo`

## Setup and teardown

- Prefer fresh state per test over shared mutable state.
- Synthetic Cinderhaven fixtures live in `tests/fixtures/` and are committed to git.
- If setup is heavy (large synthetic dataset), pin it explicitly and document why.

## Assertions

- One concept per test. If a test asserts five unrelated things, split it.
- Assertions should print useful failure messages.

## Mocks and fakes

- Mock at the boundary (file I/O, external APIs), not internal pure functions.
- The leakage detection logic must be tested against real synthetic data, not mocked inputs.

## Running

- Tests must be runnable with a single command. Document it in README.md.
- A failing test is more useful than an unrun test.

## When a test fails

- Read the actual output, not what you expected to see.
- Bisect: which change broke it?
- Don't suppress with `skip` or `xfail` without an issue or PLAN item to come back to.
