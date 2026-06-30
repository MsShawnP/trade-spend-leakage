"""Regression guard: every hex color in chart/layout modules must trace to lailara_palette.

Scans app/charts.py, app/layout.py, and app/constants.py for hex-color literals
and fails if any are not in the allowed set exported by lailara_palette.
"""

from __future__ import annotations

import re
from pathlib import Path

import lailara_palette

# Modules to scan — chart-rendering code and the constants layer that feeds it
_APP_DIR = Path(__file__).resolve().parent.parent / "app"
_MODULES_TO_SCAN = ["charts.py", "layout.py", "constants.py"]

# rgba(…) transparency values that aren't palette colors — keep this tiny
_STRUCTURAL_EXCEPTIONS: set[str] = set()

_HEX_RE = re.compile(r"""(?<![&\w])#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F])""")


def _collect_palette_hexes() -> set[str]:
    """Walk every public attribute of lailara_palette and harvest hex strings."""
    hexes: set[str] = set()

    def _harvest(obj: object) -> None:
        if isinstance(obj, str):
            for m in _HEX_RE.finditer(obj):
                hexes.add(m.group(0).lower())
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _harvest(item)
        elif isinstance(obj, dict):
            for v in obj.values():
                _harvest(v)

    for name in dir(lailara_palette):
        if name.startswith("_"):
            continue
        _harvest(getattr(lailara_palette, name))

    return hexes


def _find_hex_literals_in_source(source: str) -> list[tuple[int, str]]:
    """Return (line_number, hex_literal) pairs from Python source, skipping comments."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        code_part = line.split("#")[0] if "#" in line else line
        for m in _HEX_RE.finditer(code_part):
            hits.append((lineno, m.group(0).lower()))
    return hits


def test_no_adhoc_hex_colors():
    allowed = _collect_palette_hexes() | _STRUCTURAL_EXCEPTIONS
    violations: list[str] = []

    for module_name in _MODULES_TO_SCAN:
        path = _APP_DIR / module_name
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        for lineno, hex_val in _find_hex_literals_in_source(source):
            if hex_val not in allowed:
                violations.append(f"{module_name}:{lineno} uses {hex_val} which is not in lailara_palette")

    assert not violations, (
        "Ad-hoc hex colors found — replace with lailara_palette constants:\n"
        + "\n".join(f"  {v}" for v in violations)
    )
