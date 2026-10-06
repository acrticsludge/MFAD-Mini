#!/usr/bin/env python3
"""Run the IPL power ranking demo with no install step and no network.

``pyproject.toml`` deliberately declares **no build backend**, so nothing is
installed and ``python -m iplranking`` cannot find the package
(``AGENTS.md`` section 8 fixes the stack and requires a clean clone with no
network; a build backend would mean a fetch). pytest finds the package through
``pythonpath = ["src"]``; ``python -m`` does not read ``pyproject.toml``. This
launcher puts ``src`` on ``sys.path`` itself and hands over to the same entry
point, so the demo runs from a clean shell::

    python ipl-power-ranking/scripts/run_demo.py --offline

Two properties this file exists to guarantee, both regression-tested in
``tests/test_demo.py``:

* **the path comes from ``__file__``, not from the working directory.** The
  invocation above is run from the repository root, one level above ``src/``, so
  a ``cwd``-relative ``src`` would be wrong exactly there.
* **nothing is printed that the demo does not print.** Its output stays
  byte-identical to ``python -m iplranking``, and the exit code is the demo's
  own: ``0`` success, ``1`` offline violation, ``2`` a stage/figure/report
  failure, ``3`` a bad command line. ``2`` is also what this script returns when
  the package is not where it expects to find it, which is otherwise reported as
  a bare ``No module named iplranking``.

Every argument after the script name is forwarded verbatim, so ``--offline``,
``--width 88``, ``--figures-only`` and ``--no-report`` all behave exactly as
they do under ``python -m``; running it with no arguments runs the full default
demo.

This is a bootstrap, not a place for logic. The demo itself is
:mod:`iplranking.demo`, the CLI is :mod:`iplranking.__main__`, and neither is
modified by this file.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: ``<repo root>/ipl-power-ranking/src``, resolved from *this* file. The script
#: sits at ``ipl-power-ranking/scripts/run_demo.py``, so one ``parents`` step is
#: the package root and the next is ``src``.
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"

if not (SRC / "iplranking" / "__init__.py").is_file():
    # Without this the failure is ``ModuleNotFoundError: No module named
    # 'iplranking'``, which is indistinguishable from the defect this launcher
    # exists to fix. Say where it looked instead.
    print(
        f"run_demo.py: no uninstalled package at {SRC}\n"
        f"  expected {SRC / 'iplranking' / '__init__.py'}\n"
        f"  this script must sit at <repo root>/ipl-power-ranking/scripts/, "
        f"and the package at <repo root>/ipl-power-ranking/src/iplranking/",
        file=sys.stderr,
    )
    raise SystemExit(2)

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iplranking.__main__ import main  # noqa: E402  - must follow the path setup

if __name__ == "__main__":
    # No argv is passed: `main` reads `sys.argv[1:]` itself, which is exactly
    # what `python -m iplranking` would have read.
    raise SystemExit(main())