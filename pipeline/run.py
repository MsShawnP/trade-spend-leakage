"""Pipeline orchestrator.

Usage:
  python pipeline/run.py                 # run all moves
  python pipeline/run.py --moves 1 3     # run Move 1 and Move 3 only
  python pipeline/run.py --moves none    # dry-run (no moves executed)
"""

from __future__ import annotations

import argparse
import sys

MOVE_REGISTRY: dict[str, str] = {
    "1": "pipeline.move1_net_revenue",
    "2": "pipeline.move2_efficiency",
    "3": "pipeline.move3_leakage",
    "4": "pipeline.move4_promo_roi",
    "5": "pipeline.move5_accrual",
}


def run(moves: list[str]) -> None:
    if not moves:
        print("No moves selected — nothing to run.")
        return

    for key in moves:
        module_path = MOVE_REGISTRY[key]
        print(f"Running Move {key} ({module_path})...")
        import importlib
        mod = importlib.import_module(module_path)
        mod.run()
        print(f"  Move {key} complete.")


def parse_args(argv: list[str] | None = None) -> list[str]:
    parser = argparse.ArgumentParser(description="Trade spend analysis pipeline")
    parser.add_argument(
        "--moves",
        nargs="*",
        default=list(MOVE_REGISTRY.keys()),
        help="Moves to run (1–5). Omit to run all. Pass 'none' to skip all.",
    )
    args = parser.parse_args(argv)
    selected = args.moves or []
    if selected == ["none"]:
        return []
    invalid = [m for m in selected if m not in MOVE_REGISTRY]
    if invalid:
        parser.error(f"Unknown move(s): {invalid}. Valid: {list(MOVE_REGISTRY.keys())}")
    return selected


if __name__ == "__main__":
    moves = parse_args(sys.argv[1:])
    run(moves)
