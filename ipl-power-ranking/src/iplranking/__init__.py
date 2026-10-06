"""IPL power ranking — data layer, design matrices, snapshot parser.

The package resolves Strang problem #5 (*"Linear equations + college football
team ranking"*) onto IPL data: Massey least squares on the 558 matches that
carry a run margin, and a Colley eigenvector fit on all 1,218 matches that
have a winner at all. The divergence between the two is the project's result.

Entry points:

* :mod:`iplranking.canon`  -- the four-pair rename map; n = 15.
* :mod:`iplranking.parse`  -- build-time reader for the raw Cricsheet
  snapshot. **Not** on the demo path.
* :mod:`iplranking.data`   -- the demo's only data entry point. Reads the
  committed ``data/matches.csv`` and nothing else, so the demo runs offline.

Everything here is deterministic. There is no stochastic step, no network
call, and no environment variable; the only ordering is alphabetical by team
and chronological by match date.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"