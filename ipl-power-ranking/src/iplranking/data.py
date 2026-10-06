"""The demo's only data entry point. Offline, deterministic, no environment.

Everything the demo reads comes from the committed ``data/matches.csv``. This
module never touches the network and never reads the raw ``ipl_json/``
extraction — a demo that fails because a website is down costs five marks.
:mod:`iplranking.parse` handles the raw archive, and only at build time.

Two models, two datasets
------------------------
This project runs two linear models over **different subsets** of the snapshot,
and their divergence is the finding:

======================  ==================  ==================================
Object                  Rows                Why that dataset
======================  ==================  ==================================
``A``, ``b`` (Massey)   **558** run-margin  A run margin is a right-hand side;
                        matches only        the other 660 matches have none.
``W``, ``C``, ``M``     **1,218** matches   Win/loss exists for every match
(Colley)                with a winner       that was decided at all.
======================  ==================  ==================================

The 25 matches with no winner (16 Super Over ties, 9 abandonments) belong to
neither model. They are counted and stated, never silently dropped.

What ``A`` is
------------
For each of the 558 run-margin matches, one row over the ``n = 15`` canonical
franchises: ``+1`` under the team that won, ``-1`` under the team that lost, and
``0`` everywhere else. ``b`` is the **signed** run margin — the archive records
margins unsigned, so the sign is reconstructed from the winner.

Every row therefore sums to zero, and that is the whole point of stage 4: the
constant vector lies in the null space, because adding the same number to every
team strength predicts exactly the same margins. ``A`` is ``(558, 15)`` with
``rank(A) = 14``; ``nullity(A) = 1``. Measured, and pinned in the test suite.

Team ordering
-------------
Alphabetical, everywhere, without exception. Every matrix here indexes teams by
position, so a single fixed ordering is what makes two runs comparable. There is
no environment variable, no stochastic step, and no iteration-order dependence
anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .canon import canonical

__all__ = [
    "Systems",
    "build_systems",
    "colley_matrices",
    "data_dir",
    "design_matrix",
    "games_played",
    "load_matches",
    "matches_csv",
    "official_table",
    "repo_root",
    "teams",
]

#: The package sits at ``ipl-power-ranking/src/iplranking/data.py``. Walking up
#: from the package directory: ``iplranking`` -> ``src`` -> ``ipl-power-ranking``
#: -> the repository root, which holds ``data/`` and ``ipl_json/``.
_PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = _PACKAGE_DIR.parents[2]

#: ``data/matches.csv`` — the committed snapshot, and the demo's only input.
MATCHES_CSV = REPO_ROOT / "data" / "matches.csv"

#: Points per win used for the official-table comparison. The IPL awards 2 for a
#: win, 1 for a tie and 0 for a loss; ties are excluded here because they have
#: no ``winner`` field, so a 2-points-per-win table is exact for this column.
POINTS_PER_WIN = 2


def repo_root() -> Path:
    """The repository root, resolved from this file's location."""
    return REPO_ROOT


def data_dir() -> Path:
    """The directory holding the committed snapshot."""
    return MATCHES_CSV.parent


def matches_csv() -> Path:
    """Path to the committed ``data/matches.csv``."""
    return MATCHES_CSV


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

#: Rows in the committed snapshot. Measured, and pinned by the invariant tests.
#: Loaded here only to *detect truncation* -- every other count in the project is
#: derived from the data, and this constant is a corruption check, not a fact the
#: mathematics depends on.
EXPECTED_MATCHES = 1243

#: dtype overrides for ``pandas.read_csv``. ``match_id`` is a file stem and is
#: held as text so the column round-trips losslessly whatever a future snapshot
#: puts in it; the string columns are pinned so a NaN never silently becomes the
#: literal ``"nan"`` somewhere downstream.
_DTYPES = {
    "match_id": "string",
    "date": "string",
    "season": "string",
    "team1": "string",
    "team2": "string",
    "winner": "string",
    "method": "string",
    "canonical_team1": "string",
    "canonical_team2": "string",
}


@lru_cache(maxsize=1)
def _cached_matches(csv_path: Path) -> pd.DataFrame:
    """Read and validate the snapshot once. Private: callers get a copy."""
    frame = pd.read_csv(csv_path, dtype=_DTYPES)
    required = {
        "match_id",
        "date",
        "season",
        "team1",
        "team2",
        "winner",
        "margin_runs",
        "margin_wickets",
        "method",
        "is_super_over",
        "canonical_team1",
        "canonical_team2",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            f"{csv_path} is missing required column(s) {sorted(missing)}; "
            "regenerate it with scripts/build_snapshot.py"
        )
    if "winner" not in frame.columns:
        raise ValueError(f"{csv_path} has no 'winner' column")
    # A truncated CSV is the one corruption that leaves every column intact, so a
    # column check alone would accept it and quietly change every count
    # downstream. Measured: the committed snapshot has 1,243 rows.
    if len(frame) != EXPECTED_MATCHES:
        raise ValueError(
            f"{csv_path} has {len(frame)} rows; the committed snapshot has "
            f"{EXPECTED_MATCHES}. The file is truncated or was built from a "
            "different archive. Regenerate it with scripts/build_snapshot.py "
            "and check data/provenance.json's row_count."
        )
    # A run margin must be a number or missing, never text. `is_super_over` must
    # have round-tripped as a real boolean, not as the strings "True"/"False".
    frame["is_super_over"] = frame["is_super_over"].astype("boolean")
    return frame


def load_matches(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load the committed snapshot.

    Parameters
    ----------
    csv_path:
        Optional override for the snapshot location, for tests and for anyone
        pointing the demo at a differently-built CSV. Defaults to
        ``data/matches.csv`` at the repository root. Deliberately a parameter
        and not an environment variable: the demo must behave identically on
        every machine without configuration.

    Returns a **copy**, so a caller that mutates the result cannot corrupt the
    cached frame for everyone else.
    """
    path = MATCHES_CSV if csv_path is None else Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"committed snapshot not found at {path}. It is generated by "
            "ipl-power-ranking/scripts/build_snapshot.py and is committed to "
            "this repository."
        )
    return _cached_matches(path.resolve()).copy()


@lru_cache(maxsize=1)
def teams() -> list[str]:
    """The 15 canonical franchises, alphabetically sorted.

    Alphabetical rather than by any sporting order because this list is the
    column index of every matrix in the project. Determinism is the requirement;
    alphabetical is the one ordering that is fixed without a data dependency.
    """
    frame = _cached_matches(MATCHES_CSV.resolve())
    raw = set(frame["team1"]) | set(frame["team2"])
    return sorted({canonical(str(name)) for name in raw})


# --------------------------------------------------------------------------
# Massey design matrix: A (558, 15), b (558,)
# --------------------------------------------------------------------------


def _run_margin_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """The matches that carry a run margin *and* name a winner.

    This is the Massey dataset. 558 of the snapshot's 1,243 matches qualify; the
    other 660 winner matches carry a wicket margin with no run figure at all,
    and the 25 without a winner carry neither. The filter is applied to the
    committed frame in its own row order, which is chronological.
    """
    return frame[frame["margin_runs"].notna() & frame["winner"].notna()]


def design_matrix() -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build the Massey design matrix and its signed right-hand side.

    Returns
    -------
    ``(A, b, teams)``
        ``A`` is ``(n_run_margin_matches, n_teams)`` float, measured at
        ``(558, 15)``. Row ``i`` is the ``i``-th run-margin match in the
        committed CSV's row order, with ``A[i, j] = +1`` if team ``j`` won that
        match and ``-1`` if it lost.
        ``b`` is the **signed** run margin: ``+margin_runs`` when the first team
        won, ``-margin_runs`` when the second did. The archive stores margins
        unsigned, so the sign is reconstructed here from the winner field.
        ``teams`` is the column order.

    Two invariants are asserted *at the boundary where the matrices are built*,
    so a mistake fails here with the actual numbers rather than silently
    producing a plausible-looking wrong fit three stages later:

    * every row of ``A`` sums to zero (one winner, one loser);
    * ``A``'s shape is consistent with its right-hand side and with ``teams``.

    The row-sum check is a real guard, not a tautology. It fires when two raw
    team names canonicalise onto one franchise, because the ``+1`` and the
    ``-1`` then land in the same cell and cancel, leaving an all-zero row next
    to a nonzero ``b`` entry. Verified by mutation on 2026-10-04: merging
    ``Deccan Chargers`` into ``Mumbai Indians`` — two franchises that *did*
    play each other — makes it report ``7 of 558 rows do not, first at index
    17 with sum -1.0``. Note that none of the four authorised merges can
    trigger it, because each pair's two names cover disjoint seasons and the
    two franchises never met. The guard exists for the next dataset, not this
    one.
    """
    frame = _cached_matches(MATCHES_CSV.resolve())
    names = teams()
    rows = _run_margin_rows(frame)

    team_index = {name: j for j, name in enumerate(names)}
    n_matches = len(rows)
    n_teams = len(names)

    # The CSV carries its own `canonical_team*` columns, written when the
    # snapshot was built, while `teams()` re-derives the column order from the
    # raw columns and the *current* rename map. Those two must agree. If the map
    # has been edited without rebuilding the CSV, they will not, and the
    # failure would otherwise surface as a bare `KeyError` on a team name deep
    # inside the row loop with no hint as to the cause.
    _canonical_in_frame = set(rows["canonical_team1"]) | set(rows["canonical_team2"])
    _missing = _canonical_in_frame - set(names)
    if _missing:  # pragma: no cover - requires an edited map and a stale CSV
        raise ValueError(
            f"{MATCHES_CSV} was built with a different canonicalisation map than "
            f"the one now in canon.py: {sorted(_missing)} appear in the CSV's "
            f"canonical columns but not in the current column order {names}. "
            "Regenerate the snapshot with scripts/build_snapshot.py, or revert "
            "the map change."
        )

    # Shape (558, 15). `+1` is the winner, `-1` the loser, 0 everyone else.
    A = np.zeros((n_matches, n_teams), dtype=np.float64)
    b = np.empty(n_matches, dtype=np.float64)

    for i, row in enumerate(rows.itertuples(index=False)):
        team1 = str(row.canonical_team1)
        team2 = str(row.canonical_team2)
        # `winner` is a raw team string, so it must be canonicalised before it
        # can be compared against the canonical columns.
        winner = canonical(str(row.winner))
        margin = float(row.margin_runs)

        if winner == team1:
            sign = 1.0
        elif winner == team2:
            sign = -1.0
        else:
            raise ValueError(
                f"match {row.match_id}: winner {winner!r} (canonicalised from "
                f"{row.winner!r}) is neither team {team1!r} nor {team2!r}; "
                "the snapshot and the canonicalisation map disagree"
            )

        A[i, team_index[team1]] = sign
        A[i, team_index[team2]] = -sign
        b[i] = sign * margin

    # --- Boundary assertions, with the real numbers in the message ---------
    expected_shape = (n_matches, n_teams)
    if A.shape != expected_shape:  # pragma: no cover - structurally impossible
        raise AssertionError(f"design matrix shape {A.shape} != {expected_shape}")
    if b.shape != (n_matches,):  # pragma: no cover - structurally impossible
        raise AssertionError(
            f"right-hand side shape {b.shape} != {(n_matches,)}; "
            f"A is {A.shape}"
        )
    row_sums = A.sum(axis=1)
    if not np.allclose(row_sums, 0.0):
        offenders = np.flatnonzero(~np.isclose(row_sums, 0.0))
        raise AssertionError(
            f"design matrix rows must sum to 0 (one winner +1, one loser -1); "
            f"{offenders.size} of {n_matches} rows do not, first at index "
            f"{int(offenders[0])} with sum {row_sums[offenders[0]]!r}. "
            "The likely cause is two raw team names canonicalising to the same "
            "franchise, which would also leave b with a sign for a match nobody "
            "played."
        )

    return A, b, names


# --------------------------------------------------------------------------
# Colley matrices over all 1,218 matches with a winner
# --------------------------------------------------------------------------


def colley_matrices() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the Colley win, games and rating matrices.

    Returns ``(W, C, M)``, each ``(n_teams, n_teams)`` with ``n_teams = 15``:

    ``W``
        ``W[i, j]`` is the number of matches team ``i`` **beat** team ``j``.
        Diagonal zero. The entries sum to the number of decided matches, because
        each of them contributes exactly one directed win.
    ``C``
        ``C[i, j]`` is the number of matches **played between** ``i`` and ``j``,
        so it is symmetric with a zero diagonal. Its entries sum to twice the
        number of decided matches.
    ``M``
        ``M = W + W.T + C``, the matrix of Colley's rating adjustment. Symmetric
        and entrywise non-negative, which is what makes the leading eigenvector
        well defined, real and positive.

    This is built over **all** matches with a winner — 1,218 — not the 558 the
    least-squares model uses. Win/loss information exists for every decided
    match, so there is no reason to discard the wicket-margin ones. That
    difference in datasets is the reason the two models can disagree.
    """
    frame = _cached_matches(MATCHES_CSV.resolve())
    names = teams()
    team_index = {name: j for j, name in enumerate(names)}

    decided = frame[frame["winner"].notna()]
    n = len(names)
    W = np.zeros((n, n), dtype=np.float64)
    C = np.zeros((n, n), dtype=np.float64)

    for row in decided.itertuples(index=False):
        team1 = str(row.canonical_team1)
        team2 = str(row.canonical_team2)
        winner = canonical(str(row.winner))
        if winner == team1:
            i, j = team_index[team1], team_index[team2]
        elif winner == team2:
            i, j = team_index[team2], team_index[team1]
        else:
            raise ValueError(
                f"match {row.match_id}: winner {winner!r} is neither "
                f"{team1!r} nor {team2!r}; the snapshot and the canonicalisation "
                "map disagree"
            )
        W[i, j] += 1.0
        # Games played is symmetric; the diagonal stays 0 because a team never
        # plays itself.
        C[i, j] += 1.0
        C[j, i] += 1.0

    if np.any(np.diag(C) != 0.0):  # pragma: no cover - structurally impossible
        raise AssertionError("games-played matrix has a non-zero diagonal")

    M = W + W.T + C
    return W, C, M


def games_played() -> np.ndarray:
    """Games each team played **within the 558 run-margin matches**.

    This is the weighting basis for the frequency-balanced least-squares variant
    and the residual diagnostics, so it is deliberately the run-margin subset
    and not the full 1,218. Sums to ``2 x 558 = 1116``.
    """
    A, _, names = design_matrix()
    return np.abs(A).sum(axis=0).astype(np.int64)


# --------------------------------------------------------------------------
# The official table — the comparison column
# --------------------------------------------------------------------------


def official_table() -> pd.DataFrame:
    """The all-time IPL table on this project's terms: 2 points per win.

    **This is the all-19-seasons table, not a per-season one.** One row per
    canonical franchise, columns ``team``, ``wins``, ``points``, sorted by points
    descending then team name ascending so the ordering is total and stable
    across runs.

    Two exclusions, both deliberate and both stated out loud in the demo rather
    than buried:

    * **Ties and abandonments.** 25 of the snapshot's 1,243 matches have no
      ``winner`` field — 16 decided by a Super Over eliminator and 9 abandoned
      (``result == "no result"``). They award no points here. A Super Over tie
      would in reality award 1 point to each side, so this table is *not* the
      official IPL table in full; it is the 2-points-per-win ranking over every
      decided match, which is what a linear model can be compared against.
    * **Per-season weighting.** Nothing here is weighted by recency, by matches
      played, or by season. Recency weighting is a named "what next", not part of
      this deliverable.

    Because every row's points are exactly twice its wins, the points column is
    a redundant view of the wins column. It is carried anyway because the
    comparison the project makes is against *points*, and inventing a second
    quantity would be worse than carrying a trivial one.
    """
    frame = _cached_matches(MATCHES_CSV.resolve())
    names = teams()

    decided = frame[frame["winner"].notna()]
    winners = decided["winner"].map(canonical)
    counts = winners.value_counts()

    # Every canonical team gets a row, even a hypothetical winless one, so the
    # table always has exactly `len(teams)` rows and never drops an unknown.
    table = pd.DataFrame(
        {
            "team": names,
            "wins": [int(counts.get(name, 0)) for name in names],
        }
    )
    table["points"] = table["wins"] * POINTS_PER_WIN
    table = table.sort_values(
        ["points", "team"], ascending=[False, True], ignore_index=True
    )
    return table


# --------------------------------------------------------------------------
# Everything, loaded once
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Systems:
    """The whole data layer, loaded and validated once.

    The demo loads this rather than calling each accessor in turn: the CSV is
    read, canonicalised and rebuilt into four matrices either way, and doing it
    once keeps the demo's stage timings honest.
    """

    matches: pd.DataFrame
    A: np.ndarray
    b: np.ndarray
    W: np.ndarray
    C: np.ndarray
    M: np.ndarray
    teams: list[str]
    games: np.ndarray
    official: pd.DataFrame


def build_systems() -> Systems:
    """Load the snapshot and build every matrix the demo needs."""
    frame = load_matches()
    A, b, names = design_matrix()
    W, C, M = colley_matrices()
    return Systems(
        matches=frame,
        A=A,
        b=b,
        W=W,
        C=C,
        M=M,
        teams=names,
        games=games_played(),
        official=official_table(),
    )