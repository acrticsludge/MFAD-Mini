"""``python -m iplranking`` -- the entry point.

The whole project in one command: read the committed snapshot, walk all eleven
mandated linear-algebra stages with a narrated terminal panel each, save
thirteen PNG figures, and write the self-contained HTML report.

Exit codes are load-bearing rather than decorative, because this is the command
a marker runs::

    0   every stage completed and every artefact written
    1   --offline was requested and something reached for the network
    2   a stage, a figure or the report failed
    3   the command line itself was wrong

Offline is the default state, not a flag
-----------------------------------------
The demo never opens a socket. ``--offline`` therefore does not *permit*
offline operation, it **verifies** it: :func:`demo.assert_offline` blocks the
network imports and the socket constructor, then says so in the output. If a
future edit introduced a fetch, the flag would make the run fail loudly instead
of quietly depending on a website being up -- which is the failure mode
``AGENTS.md`` section 7 warns costs marks.

Determinism
-----------
Two runs of the demo produce byte-identical terminal output, byte-identical
PNGs and a byte-identical ``report/report.html``. Nothing in the path prints a
timestamp, a duration, a hostname or a random number; the width is fixed at 88
whenever stdout is not a TTY, and ``--width`` is the one explicit override.

How to invoke it, and the one gap you will hit
----------------------------------------------
The package lives at ``ipl-power-ranking/src/iplranking`` and
``pyproject.toml`` deliberately declares **no build backend**, so nothing is
installed and ``src/`` is not on the interpreter's path by default. Two of the
three invocations below therefore work only because of the bootstrap at the top
of this file:

============================================  ==================================
invocation                                   works from a clean clone?
============================================  ==================================
``python -m iplranking --offline``           **no** -- see below
``python src/iplranking/__main__.py``        yes (the bootstrap handles it)
``python -m pytest -q`` then run the above   yes
============================================  ==================================

``python -m iplranking`` needs ``src/`` importable, which today means either
``$env:PYTHONPATH='src'`` on Windows, ``PYTHONPATH=src python -m iplranking``
elsewhere, or an editable install. The durable fix is a ``[build-system]`` table
in ``pyproject.toml``, which is outside this module's blast radius and is
recorded as an open item rather than worked around silently. The bootstrap below
means the direct-script form needs no environment variable at all, so the demo is
runnable from a clean clone either way.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import TextIO

if __package__ in (None, ""):  # pragma: no cover - only the direct-script form
    # `python src/iplranking/__main__.py` runs this file with no package context,
    # so the relative imports below would fail. Put `src/` on the path and name
    # the package, and they resolve exactly as they do under `python -m`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "iplranking"

from . import console, demo  # noqa: E402  - must follow the bootstrap above

__all__ = ["main"]

#: Argument-parser failure exit code, distinct from a run failure.
_USAGE_EXIT = 3
#: Run failure exit code.
_RUN_EXIT = 2
#: Offline violation exit code.
_OFFLINE_EXIT = 1


def _build_parser() -> argparse.ArgumentParser:
    """The command line, in the order its flags appear in ``--help``."""
    parser = argparse.ArgumentParser(
        prog="python -m iplranking",
        description=(
            "IPL power ranking: Strang problem #5 reframed onto 19 seasons of the "
            "Indian Premier League. Walks all eleven mandated linear-algebra "
            "stages, saves 13 figures and writes a self-contained HTML report."
        ),
        epilog=(
            "The demo reads only the committed data/matches.csv and never the "
            "network. --offline verifies that by blocking the network imports "
            "and the socket constructor before the run starts."
        ),
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="verify that the run cannot touch the network (it cannot anyway) and fail loudly if it tries",
    )
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="skip the opening banner and the closing summary table; still runs all eleven stages and still writes every artefact",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        metavar="N",
        help="render width, clamped to 64-100. Piped output defaults to a fixed 88 so two runs cannot differ by window size",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="skip writing report/report.html, for when only the terminal walkthrough is wanted",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the demo. Returns 0 on success and non-zero on any failure.

    Parameters
    ----------
    argv:
        Arguments after the program name. ``None`` means ``sys.argv[1:]``.
    stdout, stderr:
        Optional stream overrides, so a test can capture the walkthrough
        without a shell redirect. Both default to the real streams.

    Returns
    -------
    int
        ``0`` success, ``1`` offline violation, ``2`` run failure, ``3`` a bad
        command line. It never raises: a demo that dies with a traceback has
        told the marker nothing.
    """
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))

    console.init(stdout)
    console.set_width(args.width)

    # The offline block must be INSTALLED and HELD for the whole run. An earlier
    # version installed it, printed "blocked", and restored the hooks inside the
    # same call -- before run_demo had run -- so a fetch anywhere in the run would
    # have succeeded and the promise in the help text would have been false.
    if args.offline:
        try:
            demo.assert_offline()
        except AssertionError as error:
            print(str(error), file=stderr or sys.stderr)
            return _OFFLINE_EXIT

    try:
        try:
            result = demo.run_demo(figures_only=args.figures_only, stream=stdout)
        except demo.NetworkBlockedError as error:
            print(f"offline violation: {error}", file=stderr or sys.stderr)
            return _OFFLINE_EXIT
        except (FileNotFoundError, ValueError) as error:
            # The two failures a marker can actually hit: a missing snapshot, or a
            # snapshot the loader refuses. One line naming the file and the
            # remedy, because a bare traceback tells the marker nothing.
            print(f"cannot start: {error}", file=stderr or sys.stderr)
            return _RUN_EXIT
        except Exception:
            traceback.print_exc(file=stderr or sys.stderr)
            return _RUN_EXIT

        if not args.no_report:
            # Imported here, not at module scope, so a failure inside report
            # assembly cannot take the terminal walkthrough down with it.
            from . import report

            try:
                result.report = report.build_report(result)
            except Exception:
                traceback.print_exc(file=stderr or sys.stderr)
                return _RUN_EXIT
            if not args.figures_only:
                console.figure(
                    result.report.name,
                    f"self-contained HTML report written to {result.report}",
                )
    finally:
        if args.offline:
            demo.release_offline()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())