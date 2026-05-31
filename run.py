"""Project entry point for local development.

Usage:
  python run.py              # run pipeline if results.db missing, then start app
  python run.py pipeline     # run pipeline only
  python run.py app          # start gunicorn
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS_DB = ROOT / "data" / "results.db"


def _pipeline() -> None:
    subprocess.run([sys.executable, "pipeline/run.py"], check=True)


def _app() -> None:
    port = os.environ.get("PORT", "8050")
    subprocess.run(
        [
            "gunicorn", "app.app:server",
            "-b", f"0.0.0.0:{port}",
            "-w", "1",
            "--worker-class", "gthread",
            "--threads", "4",
            "--timeout", "120",
        ],
        check=True,
    )


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pipeline":
        _pipeline()
    elif cmd == "app":
        _app()
    else:
        if not RESULTS_DB.exists():
            print("results.db not found — running pipeline first...")
            _pipeline()
        _app()
