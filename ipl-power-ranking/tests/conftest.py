"""Test configuration.

`pyproject.toml` already sets `pythonpath = ["src"]`, which is what makes
`python -m pytest -q` work from `ipl-power-ranking/` with no install step.
This file repeats it defensively so the suite also imports cleanly if it is
collected by a different rootdir, or run via `pytest` rather than
`python -m pytest`. Both mechanisms are idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src"

if PACKAGE_ROOT.is_dir() and str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
