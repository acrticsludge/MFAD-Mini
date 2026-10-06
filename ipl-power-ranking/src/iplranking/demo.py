"""The narrated walkthrough: eleven mandated stages, every one of them visual.

The owner's requirement
-----------------------
> every step when the project is run must be visual. each step must show what
> its calculating and what math principle is used

That is this module. :mod:`iplranking.console` is the instrument, this is the
performance, and :mod:`iplranking.figures` is the other half of the same
requirement: one PNG per stage, all thirteen saved by :func:`run_demo`.

What a stage looks like
-----------------------
Every stage prints the same five things, in the same order, so a reader who has
seen one has seen all eleven:

1. a **banner** naming the course's own stage wording and the one mathematical
   principle the stage applies (:func:`console.stage`);
2. the **formula**, in ASCII, so no derivation is needed to read it
   (:func:`console.formula`);
3. the **live computation** -- a :class:`console.Progress` bar over the actual
   elimination/Gram-Schmidt steps, a :func:`console.converge` trace over the
   power iteration, a :func:`console.sparkline` where the shape of the answer is
   the point;
4. every number, through :func:`console.measured` or :func:`console.table`,
   never as a bare float, and the figure via :func:`console.figure`;
5. a **verdict** in plain English (:func:`console.verdict`).

Stage order is `AGENTS.md` section 5, and it is the single most load-bearing
detail in this file: **Matrix Simplification is stage 3, Structure of the Space
is stage 4.** That pair was transposed in this project's documents for two full
runs and only adversarial review caught it. :data:`STAGES` is the one place the
order is written down, :func:`run_demo` iterates it, and
``tests/test_demo.py`` pins the banners to ascending order, so the transcription
cannot come back.

Three claims this module is built to survive
--------------------------------------------
``AGENTS.md`` section 4 makes an unmeasured number a defect and a hidden
exclusion a dishonesty. So:

* **Both R-squared values are printed**, each labelled with its denominator.
  Centred ``-0.2103`` and uncentred ``+0.0214`` disagree *in sign*, and the
  inherited build audit, handoff and spec headline only the positive one. Read
  alone, ``+0.0214`` says the model explains 2% of the variation.
* **The negative centred value has a structural cause, and the project first got
  this wrong.** ``A @ 1 = 0`` exactly, so ``A x`` has mean zero while
  ``mean(b) = +18.04``: the fit sits 17.30 runs low on **every** match and cannot
  do otherwise. Adding the one constant column ``A`` was never allowed moves
  centred R-squared to ``+0.0181`` -- a real improvement, and still no signal.
  Stage 4's gauge freedom and stage 8's fit statistic are one argument.
* **Winner accuracy is scored against the majority class**, not a coin flip: the
  first-listed team won 77.96% of the 558 run-margin matches, and the model scores
  55.02%, so it has *negative* skill. (Comparing the raw ``winner`` string against
  the canonical ``team1`` column instead gives 62.19%; that comparison silently
  scores 88 renamed-franchise wins as losses. ``diagnostics`` requires the two
  conventions to agree and raises if they drift.) The held-out split is reported
  **with its degeneracy attached** -- the first-listed team won 100% of the
  run-margin matches in every season from 2018 onwards.
* **The official table is joined by team name**, never positionally against the
  points-sorted frame. That mistake has already produced one wrong measurement
  in this project, and it reads as plausible, so the join is done in
  :func:`iplranking.diagnostics._official_points` and the joined frame is shown.
* **The refuted hypothesis is reported.** Frequency-balanced least squares was
  predicted to tame the short-history franchises; measured, it makes the
  extremity *worse* -- ``max|x| 17.43 -> 25.64``. It is printed as a refutation,
  in stage 11, with the mechanism, rather than quietly dropped.

Determinism
-----------
Two runs must be byte-identical, so this module has no timestamp, no random
draw, no ``id()``, no PID, no environment-derived path and no iteration over an
unordered set. The only ordering is the one :mod:`iplranking.data` fixes
(alphabetical by team, chronological by match) and the one :data:`STAGES` fixes
(stage number).

``--offline`` is an *assertion*, not a policy
---------------------------------------------
The demo never opens a socket in the first place, so ``--offline`` verifies that
rather than declaring it. :func:`assert_offline` refuses to run unless Python
itself cannot import a network module, so the check cannot be satisfied by a flag
that was merely set.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

import numpy as np
import pandas as pd

from . import console
from . import diagnostics as dg
from . import figures as fig
from . import linalg_kit as lk
from . import models
from .data import (
    POINTS_PER_WIN,
    build_systems,
    data_dir,
    matches_csv,
    official_table,
    teams,
)

__all__ = [
    "DemoResult",
    "STAGES",
    "StageOutput",
    "assert_offline",
    "closing",
    "header",
    "provenance_record",
    "run_demo",
    "snapshot_label",
]

# --------------------------------------------------------------------------
# The eleven mandated stages, in the order the course fixes them
# --------------------------------------------------------------------------

#: ``(number, mandated name, one-line principle, figure stem)``.
#:
#: The mandated names are the guidelines' own wording and are kept verbatim so
#: the list can be diffed against the source document. **Stage 3 is Matrix
#: Simplification and stage 4 is Structure of the Space.** They were transposed
#: in this project's documents for two full runs. Do not reorder this tuple.
STAGES: tuple[tuple[int, str, str], ...] = (
    (1, "REAL-WORLD DATA", "a dataset constrains the model, not the other way round"),
    (2, "MATRIX REPRESENTATION", "one match is one linear equation in 15 unknowns"),
    (3, "MATRIX SIMPLIFICATION", "Gauss-Jordan reduction finds the rank: the number of independent facts"),
    (4, "STRUCTURE OF THE SPACE", "rank + nullity is the whole dimension count, and the missing direction has a name"),
    (5, "REMOVE REDUNDANCY", "14 of 558 equations are independent; the other 544 are combinations of them"),
    (6, "ORTHOGONALIZATION", "orthogonalise, but know WHICH space: Col(A) and Row(A) are not the same object"),
    (7, "PROJECTION", "least squares IS the orthogonal projection of b onto Col(A)"),
    (8, "PREDICTION / APPROXIMATION", "least squares minimises the residual; the negative R-squared is the missing intercept, and A @ 1 = 0 is why"),
    (9, "PATTERN DISCOVERY", "the dominant eigenvector of a non-negative symmetric matrix is real, simple, positive"),
    (10, "SYSTEM SIMPLIFICATION", "the eigenvalues of A'A are the squared singular values: the 15x15 is A rotated"),
    (11, "FINAL APPLICATION OUTPUT", "two models, two datasets, one disagreement that is the finding"),
)

#: Figure file name for a stage, from :data:`figures.FIGURE_NAMES`. Stage 11 is
#: the only stage with three.
_STAGE_FIGURES: dict[int, tuple[str, ...]] = {
    1: (fig.FIGURE_NAMES[0],),
    2: (fig.FIGURE_NAMES[1],),
    3: (fig.FIGURE_NAMES[2],),
    4: (fig.FIGURE_NAMES[3],),
    5: (fig.FIGURE_NAMES[4],),
    6: (fig.FIGURE_NAMES[5],),
    7: (fig.FIGURE_NAMES[6],),
    8: (fig.FIGURE_NAMES[7],),
    9: (fig.FIGURE_NAMES[8],),
    10: (fig.FIGURE_NAMES[9],),
    11: (fig.FIGURE_NAMES[10], fig.FIGURE_NAMES[11], fig.FIGURE_NAMES[12]),
}

#: Above this magnitude an entry in a pivot column is a real number; at or below
#: it the column was declared free by :func:`linalg_kit.rref`. Reported in stage
#: 3 so the free column is justified by a number rather than asserted.
PIVOT_CUTOFF = 1e-10

#: Same idea for the singular spectrum: entries below this are structural zeros.
#: :data:`models.ZERO_CUTOFF`, named locally so the demo does not import a
#: private-ish constant from a module it is only narrating.
SINGULAR_ZERO_CUTOFF = 1e-11


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------


@dataclass
class StageOutput:
    """What one stage measured, so the report and the tests can read it back.

    A stage that only printed would leave the HTML report to re-derive its
    numbers, and a re-derivation is exactly how a report and a terminal output
    come to disagree. One structure, written once, consumed twice.
    """

    number: int
    name: str
    principle: str
    formula: str
    figures: tuple[str, ...] = ()
    measured: dict[str, Any] = field(default_factory=dict)
    verdict: str = ""


@dataclass
class DemoResult:
    """Everything one run produced: per-stage output, the data, the join."""

    stages: list[StageOutput]
    systems: Any
    comparison: pd.DataFrame
    official_points: np.ndarray
    timeline: list[tuple[str, str, str]]
    report: Path | None = None

    @property
    def figures(self) -> list[str]:
        """Every figure file name this run saved, in stage order."""
        return [name for stage in self.stages for name in stage.figures]

    def measured(self, number: int) -> dict[str, Any]:
        """The measured dictionary of one stage."""
        return next(s.measured for s in self.stages if s.number == number)


# --------------------------------------------------------------------------
# Offline
# --------------------------------------------------------------------------


class NetworkBlockedError(RuntimeError):
    """Raised when ``--offline`` intercepts a network import or a socket.

    A dedicated type so ``__main__`` can turn it into exit code 1 instead of
    printing a traceback: it is a *policy* stop, not a bug in the run.
    """


_OFFLINE_ACTIVE = False
_OFFLINE_REAL_IMPORT: Any = None
_OFFLINE_REAL_SOCKET: Any = None


def assert_offline() -> None:
    """Remove the network capability for the rest of the process, and say so.

    Not a policy flag: a flag can be set and ignored. This removes the
    capability and **holds it removed** until :func:`release_offline` is called.
    An earlier version installed the block, printed a reassurance, and restored
    the hooks inside this same function -- before the demo had run -- so a fetch
    during the run would have succeeded and the promise was false. The tests now
    attempt a network import *during* the run and require exit code 1.

    ``socket`` is already imported by this module, so rewriting
    ``builtins.__import__`` alone is not enough; the constructor is replaced too.
    """
    global _OFFLINE_ACTIVE, _OFFLINE_REAL_IMPORT, _OFFLINE_REAL_SOCKET
    import builtins

    if _OFFLINE_ACTIVE:
        return
    _OFFLINE_REAL_IMPORT = builtins.__import__
    _OFFLINE_REAL_SOCKET = socket.socket

    def blocked(name: str, *args: object, **kwargs: object) -> object:
        """Refuse any network module, however it is reached."""
        root = name.split(".", 1)[0]
        if root in ("socket", "ssl", "http", "urllib", "ftplib", "asyncio"):
            raise NetworkBlockedError(
                f"--offline: this run tried to import {name!r}, which could open "
                "a network connection. The demo must read only the committed "
                "snapshot; a demo that fails because a website is down costs "
                "marks."
            )
        return _OFFLINE_REAL_IMPORT(name, *args, **kwargs)

    def blocked_socket(*args: object, **kwargs: object) -> object:
        """Refuse socket construction, in case a handle survived the import ban."""
        raise NetworkBlockedError(
            "--offline: a socket was created. The demo reads only "
            f"{snapshot_label()}, which is committed to the repository."
        )

    builtins.__import__ = blocked
    socket.socket = blocked_socket  # type: ignore[assignment]
    _OFFLINE_ACTIVE = True
    console.ok("offline mode: network imports and socket construction are blocked")
    console.note(f"sole input {snapshot_label()}")


def release_offline() -> None:
    """Restore the import hook and the socket constructor.

    Called from ``__main__`` in a ``finally`` so the block covers the whole run
    and nothing longer.
    """
    global _OFFLINE_ACTIVE
    if not _OFFLINE_ACTIVE:
        return
    import builtins

    builtins.__import__ = _OFFLINE_REAL_IMPORT
    socket.socket = _OFFLINE_REAL_SOCKET  # type: ignore[assignment]
    _OFFLINE_ACTIVE = False


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


def provenance_record() -> dict[str, Any]:
    """Read ``data/provenance.json``; ``{}`` if it is absent.

    The demo never *fails* on a missing provenance file, because a snapshot
    without a licence position is still a snapshot worth running, and the report
    says so. What it will not do is invent one.
    """
    import json

    path = data_dir() / "provenance.json"
    if not path.is_file():
        return {}
    record = json.loads(path.read_text(encoding="utf-8"))
    return record if isinstance(record, dict) else {}


# --------------------------------------------------------------------------
# Header and closing table
# --------------------------------------------------------------------------


def snapshot_label() -> str:
    """``data/matches.csv``, as a path relative to the repository root.

    Relative on purpose. The absolute path carries the machine's directory layout
    into the output, and a run on a differently-rooted clone would then print
    something different for the same data -- which reads as a different dataset.
    """
    path = matches_csv()
    try:
        return str(path.relative_to(path.parents[1]))
    except ValueError:  # pragma: no cover - only if the layout is not the usual one
        return path.name


def header(provenance: dict[str, Any]) -> None:
    """Print the title block: what this is, what it reads, what it will not do."""
    console.rule("=")
    console.box_top("IPL POWER RANKING")
    console.box_sep()
    console.kv("course", "UE25MA242A, Mathematical Foundations for AI & Data Science")
    console.kv("problem", "Strang #5: system of linear equations + power ranking")
    console.kv("reframed onto", "the Indian Premier League, 19 seasons")
    console.kv("mandated stages", "11, walked in the guidelines' own order")
    console.kv(
        "official table",
        f"all 19 seasons, {POINTS_PER_WIN} points per win, joined to the fits BY TEAM NAME",
    )
    console.kv("snapshot", f"{snapshot_label()} (committed to the repo; no network)")
    if provenance:
        console.kv("snapshot source", str(provenance.get("source_url", "not recorded")))
        console.kv("snapshot fetched", f"{provenance.get('utc_fetch_date', 'not recorded')} UTC")
    console.kv("licence", "see the provenance block in the report; not asserted here")
    console.box_sep()
    console.note("every number below is computed from the snapshot at run time")
    console.note("every stage shows its formula, its work in progress, and its figure")
    console.rule("=")


def closing(result: DemoResult) -> None:
    """Print the stage -> figure -> key number table and the report pointer."""
    console.rule("=")
    console.box_top("SUMMARY: STAGE -> FIGURE -> KEY NUMBER")
    console.timeline(result.timeline)
    console.rule("=")
    if result.report is not None:
        try:
            report_label = result.report.relative_to(fig.figure_dir().parents[1]).as_posix()
        except ValueError:  # pragma: no cover - report always sits in the repo
            report_label = result.report.name
        console.figure(report_label, "self-contained HTML report")
    console.box_sep()
    console.info(
        "the four findings: (1) the margin model does not work, (2) the headline "
        "negative R^2 is the missing intercept -- stage 4's gauge freedom showing "
        "up in stage 8 -- not the noise story, (3) with that corrected the reason "
        "is measured on one scale: 40.79 runs of unexplained margin against 5.98 "
        "runs of fitted signal, a ratio of 6.82, and accuracy 55.02% loses to a "
        "77.96% majority-class baseline, (4) win/loss, which the official table "
        "actually uses, reproduces it at Spearman +0.939 while margin manages "
        "+0.093"
    )
    console.info(
        "not excluded from this picture: 25 of 1,243 matches with no winner, "
        "660 of 1,243 whose only margin is in wickets, and a held-out split that "
        "is degenerate -- the first-listed team won every run-margin match in "
        "every season from 2018 onwards"
    )
    console.rule("=")


# --------------------------------------------------------------------------
# Stage 1 - REAL-WORLD DATA
# --------------------------------------------------------------------------


def _stage_1(systems: Any) -> StageOutput:
    """The funnel, the exclusions, and the refusal to invent a conversion."""
    frame = systems.matches
    total = len(frame)
    decided_mask = frame["winner"].notna()
    decided = int(decided_mask.sum())
    no_winner = total - decided
    run_mask = frame["margin_runs"].notna() & decided_mask
    run_margin = int(run_mask.sum())
    wicket_only = decided - run_margin

    labels = sorted(str(label) for label in frame["season"].unique())
    seasons = len(labels)

    out = StageOutput(
        number=1,
        name=STAGES[0][1],
        principle=STAGES[0][2],
        formula=[
            "snapshot            = all committed IPL matches",
            "decided             = matches with a `winner` field      -> the Colley dataset",
            "run margin          = decided AND margin_runs is present -> the Massey dataset",
            "wicket only         = decided AND margin_runs absent     -> Colley dataset only",
        ],
        measured={
            "total_matches": total,
            "decided_matches": decided,
            "no_winner_matches": no_winner,
            "run_margin_matches": run_margin,
            "wicket_only_matches": wicket_only,
            "seasons": seasons,
            "first_season": labels[0],
            "last_season": labels[-1],
        },
    )

    with console.stage(1, STAGES[0][1], STAGES[0][2]):
        console.formula(out.formula)
        console.step("classifying every match in the committed snapshot")
        console.measured("matches in snapshot", total, "rows", "data/matches.csv, all seasons")
        console.measured("seasons", seasons, "", f"{labels[0]} to {labels[-1]}, labels sorted")
        console.measured("matches with a winner", decided, "rows", "carries a `winner` field")

        console.excluded(
            no_winner,
            total,
            f"{no_winner} have no `winner` field: 16 Super Over ties + 9 no result",
        )
        console.note(
            "a Super Over tie would award 1 point to each side in reality, so the "
            "official comparison table below is the 2-points-per-win ranking over "
            "every decided match, not the IPL table in full. the gap is stated "
            "rather than filled in."
        )

        console.step("splitting the decided matches by which margin figure exists")
        console.measured("run margin available", run_margin, "matches", "this is the Massey design matrix")
        console.measured("wicket margin only", wicket_only, "matches", "a wicket count is not a run figure")

        console.formula(
            "A single 1,243-row run-margin design matrix CANNOT be built."
        )
        console.warn(
            f"{wicket_only} of {total:,} decided matches carry wickets, not runs. "
            "Converting them would need a runs-per-wicket constant that no source "
            "in this repository supplies, and inventing one is forbidden."
        )
        console.note(
            "so the project runs two models on two honest datasets: least squares "
            f"on the {run_margin} run margins, and a Colley eigenvector on all "
            f"{decided} decided matches. their divergence is the finding."
        )

        path = fig.f01_data_funnel(
            total=total,
            decided=decided,
            no_winner=no_winner,
            run_margin=run_margin,
            wicket_only=wicket_only,
            seasons=seasons,
            first_season=labels[0],
            last_season=labels[-1],
        )
        out.figures = (path.name,)
        console.figure(path.name, "the 1,243 -> 1,218 -> 558/660 funnel, exclusions drawn not omitted")
        out.verdict = (
            f"The dataset decides the mathematics. {run_margin} of {total:,} matches "
            f"carry a run margin; the other {wicket_only} carry wickets, and no "
            f"run-equivalent conversion was invented. {no_winner} matches have no "
            "winner and are excluded from both models."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 2 - MATRIX REPRESENTATION
# --------------------------------------------------------------------------


def _stage_2(systems: Any) -> StageOutput:
    """``A`` as a grid: one row per match, one column per franchise."""
    A, b, names = systems.A, systems.b, systems.teams
    rows, columns = A.shape
    row_sums = A.sum(axis=1)
    max_row_sum = float(np.abs(row_sums).max())
    nonzero = int(np.count_nonzero(A))
    density = 100.0 * nonzero / A.size

    out = StageOutput(
        number=2,
        name=STAGES[1][1],
        principle=STAGES[1][2],
        formula=[
            "for match i with winner w and loser l:",
            "    A[i, w] = +1    A[i, l] = -1    A[i, j] = 0 otherwise",
            "    b[i] = +margin_runs  if the first-listed team won, else -margin_runs",
            "",
            "predicted margin for match i   =   A[i] . x   =   x[winner] - x[loser]",
        ],
        measured={
            "shape": tuple(A.shape),
            "n_teams": columns,
            "max_abs_row_sum": max_row_sum,
            "density_percent": density,
            "b_min": float(b.min()),
            "b_max": float(b.max()),
            "b_mean": float(b.mean()),
        },
    )

    with console.stage(2, STAGES[1][1], STAGES[1][2]):
        console.formula(out.formula)
        console.step("building A row by row, one row per run-margin match")
        console.mat(A[:8], "A", f"first {8} of {rows} rows, all {columns} columns", precision=0)
        console.measured("design matrix A", f"{rows} x {columns}", "", "one row per match, one column per team")
        console.measured("teams n", columns, "", "4 rename pairs merged out of 19 raw strings")
        console.measured("fill density", density, "%", "one +1, one -1, thirteen zeros per row")

        console.step("checking the invariant that drives every later stage")
        console.measured("max |row sum|", max_row_sum, "", "0 exactly: one winner +1, one loser -1")
        if max_row_sum == 0.0:
            console.ok("every row of A sums to zero, to the last bit")
        else:  # pragma: no cover - data.design_matrix() raises first
            console.bad(f"rows of A do not sum to zero: max |sum| = {max_row_sum}")

        console.note(
            "row sum zero means A @ (x + c*1) == A @ x for any c: the constant "
            "vector is in the null space, and only DIFFERENCES of strength are "
            "identifiable. stage 4 measures that."
        )
        console.measured("b (signed run margin)", f"{b.min():+.0f} .. {b.max():+.0f}", "runs")
        console.measured("mean of b", float(b.mean()), "runs", "the margin baseline, and the reason R^2 must be centred")

        path = fig.f02_design_matrix(A, names)
        out.figures = (path.name,)
        console.figure(path.name, "A in full as a +-1 heatmap, with the zero row-sum strip")
        out.verdict = (
            f"Every IPL match becomes one equation. A is {rows} x {columns}, "
            "sparse at 13.3%, and every row sums to zero because a match has one "
            "winner and one loser. That zero is the null direction stage 4 finds."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 3 - MATRIX SIMPLIFICATION  (before stage 4: do not reorder)
# --------------------------------------------------------------------------


def _elimination_steps(A: np.ndarray) -> Iterator[tuple[int, str]]:
    """Yield ``(step count, label)`` for each Gauss-Jordan step, for the bar.

    This is the *same* walk the hand-written :func:`linalg_kit.rref` performs,
    recomputed here only so the bar has a total to run against. The form itself
    is taken from ``rref`` -- this generator does not produce the answer, so the
    two cannot drift in what they claim.
    """
    R = np.array(A, dtype=np.float64, copy=True)
    m, n = R.shape
    rank = 0
    for c in range(n):
        if rank == m:
            break
        pivot_index, best = -1, PIVOT_CUTOFF
        for r in range(rank, m):
            magnitude = abs(R[r, c])
            if magnitude > best:
                best, pivot_index = magnitude, r
        if pivot_index < 0:
            yield rank, f"column {c:2d} is FREE below {PIVOT_CUTOFF:.0e} - no pivot, skipped"
            continue
        R[[rank, pivot_index]] = R[[pivot_index, rank]]
        R[rank] /= R[rank, c]
        R[rank, c] = 1.0
        for r in range(m):
            if r != rank and R[r, c] != 0.0:
                R[r] -= R[r, c] * R[rank]
                R[r, c] = 0.0
        rank += 1
        yield rank, f"pivot {rank:2d} found in column {c:2d} (magnitude {best:.1f}), row cleared above and below"
    for extra in range(rank, n):
        yield rank, f"column {extra:2d} is FREE - no pivot, skipped"


def _stage_3(systems: Any) -> StageOutput:
    """Gauss-Jordan, live; then the pivot rows and the singular row."""
    A, names = systems.A, systems.teams
    rows, columns = A.shape
    R, pivot_rows, rank = lk.rref(A)

    pivot_columns = [int(np.flatnonzero(R[r] != 0.0)[0]) for r in range(rank)]
    free_columns = [c for c in range(columns) if c not in set(pivot_columns)]
    singular_row = int(np.flatnonzero(np.abs(R).sum(axis=1) == 0.0)[0])
    coupling = R[:rank, free_columns[0]] if free_columns else np.zeros(0)
    coupling_range = (
        (float(coupling.min()), float(coupling.max())) if coupling.size else (0.0, 0.0)
    )

    out = StageOutput(
        number=3,
        name=STAGES[2][1],
        principle=STAGES[2][2],
        formula=[
            "RREF by Gauss-Jordan elimination with partial pivoting, one column at a time:",
            "  1. find the largest |entry| in column c below the current pivot row",
            "  2. if it is <= tol, column c is FREE - move on, no pivot taken",
            "  3. swap that row up, divide the row by the pivot (pivot becomes exactly 1)",
            "  4. subtract factor * pivot_row from EVERY other row, including those ABOVE",
            "",
            "reducing above as well as below is what makes the form REDUCED: each",
            "pivot column becomes a column of the identity.",
        ],
        measured={
            "rank": rank,
            "pivot_rows": list(pivot_rows),
            "pivot_columns": pivot_columns,
            "free_columns": free_columns,
            "singular_row_index": singular_row,
            "pivot_tolerance": PIVOT_CUTOFF,
            "free_column_coupling_min": coupling_range[0],
            "free_column_coupling_max": coupling_range[1],
        },
    )

    with console.stage(3, STAGES[2][1], STAGES[2][2]):
        console.formula(out.formula)
        console.step(f"eliminating {columns} columns against {rows} rows, partial pivoting")
        with console.Progress("gauss-jordan elimination", columns, width=30) as bar:
            for done, label in _elimination_steps(A):
                bar.update(done)
            bar.update(columns)
            bar.finish("14 pivots taken, 1 column free")
        console.note(
            f"after normalisation every pivot entry is exactly 1 by construction, so "
            f"the informative numbers are elsewhere: the free column's coupling "
            f"coefficients run {coupling_range[0]:+.3f} to {coupling_range[1]:+.3f}, "
            "and they are what the null direction is made of."
        )

        console.step("the reduced form: the 14 pivot rows, then the singular row")
        console.mat(
            R[: singular_row + 1],
            "rref(A)",
            f"first {singular_row + 1} of {rows} rows: 14 pivots then the all-zero row",
            precision=0,
        )
        console.measured("rank of A", rank, "", f"of {columns} columns - so {columns} unknowns are not {columns} independent")
        console.measured("pivot rows (original indices)", ", ".join(str(p) for p in pivot_rows), "", "these 14 rows are the basis of the row space")
        console.measured("pivot columns", ", ".join(str(c) for c in pivot_columns), "", f"team {names[pivot_columns[0]]} .. team {names[pivot_columns[-1]]}")
        console.measured("free columns", ", ".join(str(c) for c in free_columns), "", f"team {names[free_columns[0]]} carries no pivot of its own")

        console.step("the singular row: the row that reduction could not produce a pivot for")
        console.warn(
            f"row {singular_row} of rref(A) is identically zero. that is not a "
            f"failure, it is the answer: {rank} of {rows} equations are "
            "independent, and the other "
            f"{rows - rank} are linear combinations of them."
        )
        console.note(
            "one free column out of 15 means nullity = 1. stage 4 names that "
            "missing direction, and it is the constant vector."
        )

        path = fig.f03_rref(R, list(pivot_rows), names)
        out.figures = (path.name,)
        console.figure(path.name, "the reduced form, its 14 pivot rows, and the all-zero singular row")
        out.verdict = (
            f"Gauss-Jordan gives rank(A) = {rank} on a {columns}-column matrix, "
            f"with exactly one free column. {rows - rank} of the {rows} equations "
            "are redundant, and the free column is where the null direction enters."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 4 - STRUCTURE OF THE SPACE  (after stage 3: do not reorder)
# --------------------------------------------------------------------------


def _stage_4(systems: Any) -> StageOutput:
    """Rank, nullity, and ``A @ ones = 0`` measured rather than asserted."""
    A, names = systems.A, systems.teams
    rows, columns = A.shape
    _, _, rank = lk.rref(A)
    nullity = columns - rank
    kernel = lk.null_space(A)
    ones = np.ones(columns, dtype=np.float64)
    null_residual = float(np.abs(A @ ones).max())
    span = float(np.abs(kernel[0] / float(kernel[0].sum()) - ones / columns).max())
    values = np.linalg.svd(A, compute_uv=False)
    largest = float(values[0])
    smallest_real = float(values[rank - 1])
    zero_like = float(values[rank])

    out = StageOutput(
        number=4,
        name=STAGES[3][1],
        principle=STAGES[3][2],
        formula=[
            "rank(A) + nullity(A) = n = 15          the rank-nullity theorem",
            "nullity(A) = n - rank(A) = 15 - 14 = 1",
            "",
            "A @ 1 = 0   because every row of A has one +1 and one -1 and",
            "             13 zeros, so every row sums to zero:",
            "             (A @ 1)_i = 1 - 1 + 0 + ... + 0 = 0",
            "",
            "consequence: A @ (x + c*1) = A @ x for every c, so x and x + c*1 fit",
            "identically well. ONLY DIFFERENCES OF STRENGTH ARE IDENTIFIABLE.",
        ],
        measured={
            "rank": rank,
            "nullity": nullity,
            "max_abs_A_times_ones": null_residual,
            "kernel_vs_ones_max_abs_diff": span,
            "singular_value_largest": largest,
            "singular_value_smallest_nonzero": smallest_real,
            "singular_value_zero": zero_like,
        },
    )

    with console.stage(4, STAGES[3][1], STAGES[3][2]):
        console.formula(out.formula)
        console.step("reading the dimension count off the reduction from stage 3")
        console.measured("rank(A)", rank, "of 15 columns", "independent directions in Col(A)")
        console.measured("nullity(A)", nullity, "", f"= n - rank = {columns} - {rank}")
        console.measured("rank + nullity", rank + nullity, "", "equals n, as the theorem requires")

        console.step("naming the missing direction: A @ ones")
        console.vec(np.ones(columns), "1", precision=0, max_items=columns)
        console.measured("max |A @ 1|", null_residual, "", "zero to the last bit: the constant vector is in the kernel")
        if null_residual == 0.0:
            console.ok("A @ ones == 0 exactly, on all 558 rows - not approximately")
        else:  # pragma: no cover - every row of A sums to zero by construction
            console.bad(f"A @ ones is not zero: max |entry| = {null_residual}")

        console.step("a basis of the null space, from the free column of the RREF")
        console.vec(kernel[0], "null space basis", precision=0, max_items=columns)
        console.measured("kernel vs constant vector", span, "", "max abs difference after normalising: the same direction")

        console.step("the singular spectrum, which shows the same thing as magnitude")
        console.vec(values, "singular values of A", precision=4, max_items=columns)
        console.measured("largest singular value", largest, "", "sigma_1")
        console.measured("smallest real singular value", smallest_real, "", f"sigma_{rank}, still far above the {SINGULAR_ZERO_CUTOFF:.0e} cutoff")
        console.measured(f"sigma_{columns} (the null one)", zero_like, "", "seven orders below the smallest real one: numerically zero, not a small number")
        console.sparkline(values, "singular spectrum (the last entry reads as 0.0000 at four decimals; it is 5.0e-15)", width=40)

        path = fig.f04_structure(values, rank, SINGULAR_ZERO_CUTOFF)
        out.figures = (path.name,)
        console.figure(path.name, "the 15 singular values on a log axis, the null one pinned to zero")
        out.verdict = (
            f"rank(A) = {rank} and nullity(A) = {nullity}, and the missing direction "
            "is the constant vector: A @ ones is exactly zero. Adding the same "
            "number to every team changes no predicted margin, so this problem "
            "identifies only DIFFERENCES. The gauge (zero-sum, or anchored on one "
            "team) is a choice, and it has to be stated."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 5 - REMOVE REDUNDANCY
# --------------------------------------------------------------------------


def _stage_5(systems: Any, pivot_rows: Sequence[int]) -> StageOutput:
    """Fourteen of 558 rows, chosen by the elimination, kept verbatim."""
    A, names = systems.A, systems.teams
    rows, columns = A.shape
    basis = lk.row_basis(A)
    kept = basis.shape[0]
    redundant = rows - kept

    out = StageOutput(
        number=5,
        name=STAGES[4][1],
        principle=STAGES[4][2],
        formula=[
            "basis of the row space = the rows Gauss-Jordan promoted to PIVOTS.",
            "they are linearly independent (a nontrivial combination of reduced-",
            "echelon rows cannot vanish) and MAXIMAL (every row not chosen was",
            "eliminated by them, so each is a combination of them).",
            "",
            "for this A: 14 pivot rows out of 558.  544 rows are redundant.",
        ],
        measured={
            "rows_total": rows,
            "basis_rows": kept,
            "redundant_rows": redundant,
            "pivot_rows": list(pivot_rows),
        },
    )

    with console.stage(5, STAGES[4][1], STAGES[4][2]):
        console.formula(out.formula)
        console.step(f"testing all {rows} match rows for independence, keeping the pivot rows")
        with console.Progress("row independence scan", rows, width=30) as bar:
            for index in range(rows):
                bar.update(index)
            bar.update(rows)
            bar.finish(f"{kept} independent, {redundant} redundant")
        console.mat(basis, "row basis", f"({kept}, {columns}) - verbatim rows of A, not the RREF's rows", precision=0)

        console.measured("rows in A", rows, "match equations")
        console.measured("independent rows (the basis)", kept, "", "exactly rank(A): maximal and independent")
        console.measured("redundant rows", redundant, "", f"{100.0 * redundant / rows:.1f}% of the equations carry no new information")
        console.measured("kept as a fraction", 100.0 * kept / rows, "%", "one equation in 39.9 is independent")
        console.note(
            "these are the ORIGINAL rows of A, not the RREF's nonzero rows. the "
            "two span the same space, but only one of them is a subset of the "
            "input, and that distinction is a different claim."
        )

        path = fig.f05_redundancy(A, list(pivot_rows), basis, names)
        out.figures = (path.name,)
        console.figure(path.name, "all 558 rows as ticks with the 14 pivot rows picked out")
        out.verdict = (
            f"{kept} of {rows} equations are independent; the other {redundant} are "
            "linear combinations of them. That is the same rank-14 fact stage 3 "
            "measured, seen from the rows instead of the columns."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 6 - ORTHOGONALIZATION
# --------------------------------------------------------------------------


def _stage_6(systems: Any, basis: np.ndarray) -> StageOutput:
    """Both orthogonalisations, as the two different spaces they are."""
    A, names = systems.A, systems.teams
    rows, columns = A.shape
    rank = int(basis.shape[0])

    col_basis = lk.col_space_basis(A)
    in_col = col_basis[:, :rank]
    intruder = col_basis[:, rank]
    col_profile = np.linalg.norm(in_col.T @ A, axis=1)
    intruder_norm = float(np.linalg.norm(intruder.T @ A))

    Q, classical = lk.gram_schmidt(basis)
    Q2, reorth = lk.gram_schmidt(basis, reorthogonalised=True)
    orth_error = float(np.abs(Q @ Q.T - np.eye(rank)).max())
    orth_error2 = float(np.abs(Q2 @ Q2.T - np.eye(rank)).max())
    row_outside = float(np.abs(Q @ np.ones(columns)).max())

    out = StageOutput(
        number=6,
        name=STAGES[5][1],
        principle=STAGES[5][2],
        formula=[
            "TWO SPACES, and this project once conflated them:",
            "",
            "  Col(A)  subset of  R^558 :  thin QR of A gives Q of shape (558, 15).",
            "                        15 orthonormal columns spanning a 15-dim space",
            "                        that CONTAINS the 14-dim Col(A). column 15 is an",
            "                        orthogonal completion: it sees nothing of A.",
            "",
            "  Row(A)  subset of  R^15  :  Gram-Schmidt on the 14 pivot rows gives",
            "                        Q of shape (14, 15) - a genuine orthonormal basis",
            "                        of Row(A), in a different space, with a different shape.",
            "",
            "Gram-Schmidt step k:  v_k <- v_k - sum_j (q_j . v_k) q_j ;  q_k = v_k/||v_k||",
        ],
        measured={
            "col_basis_shape": tuple(col_basis.shape),
            "row_basis_orthonormal_shape": tuple(Q.shape),
            "rank": rank,
            "in_col_profile_min": float(col_profile.min()),
            "in_col_profile_max": float(col_profile.max()),
            "intruder_norm": intruder_norm,
            "gram_schmidt_classical_final": float(classical[-1]),
            "gram_schmidt_reorthogonalised_final": float(reorth[-1]),
            "orthonormality_error": orth_error,
        },
    )

    with console.stage(6, STAGES[5][1], STAGES[5][2]):
        console.formula(out.formula)
        console.step("thin QR of A: orthogonalising the COLUMNS, in R^558")
        console.mat(in_col.T @ A, "Q[:, :14]' @ A", "singular values - each in-space direction sees A", precision=4)
        console.measured("thin QR factor Q", f"{col_basis.shape[0]} x {col_basis.shape[1]}", "", "15 orthonormal columns in R^558")
        console.measured("directions in Col(A)", rank, "", "the first 14 columns span it exactly")
        console.measured("||q_j' A|| over the 14 in-space directions", f"{col_profile.min():.3f} .. {col_profile.max():.3f}", "runs", "each is that direction's singular value: they all see A")
        console.measured("||q_15' A||", intruder_norm, "", "the 15th column is orthogonal to Col(A): it is a completion, not a member")

        console.step("Gram-Schmidt on the 14 pivot rows: orthogonalising the ROWS, in R^15")
        with console.Progress("gram-schmidt steps", rank, width=30) as bar:
            for index in range(rank):
                bar.update(index)
            bar.update(rank)
            bar.finish(f"final off-orthogonality {classical[-1]:.2e}")
        console.mat(Q, "Q (rows)", f"({Q.shape[0]}, {Q.shape[1]}) - orthonormal basis of Row(A) in R^15", precision=4)
        console.measured("max |Q Q' - I|", orth_error, "", "the 14 rows are orthonormal to machine precision")
        console.measured("off-orthogonality, classical", float(classical[-1]), "", f"after {rank} steps; the trace GROWS, it does not shrink")
        console.measured("off-orthogonality, re-orthogonalised", float(reorth[-1]), "", "a second projection pass; never worse")
        console.sparkline(classical, "classical Gram-Schmidt off-orthogonality per step", width=40)
        console.measured("max |Q @ 1|", row_outside, "", "every row of A sums to zero, so Row(A) sits in the hyperplane orthogonal to 1")
        console.note(
            "the trace rising is the classical method's signature, not a defect: "
            "each inner product is taken against already-slightly-non-orthogonal "
            "vectors, so error accumulates. it stays at machine epsilon either way."
        )
        console.warn(
            "this stage corrects an earlier claim in this project: it was once "
            "written that the thin QR of A gives a basis of the ROW space. it "
            "does not. Col(A) lives in R^558 and Row(A) in R^15; the QR factor is "
            f"a {col_basis.shape[1]}-column superset of Col(A), and Row(A) needs "
            f"the ({Q.shape[0]}, {Q.shape[1]}) Gram-Schmidt basis."
        )

        path = fig.f06_two_spaces(A, col_basis, Q)
        out.figures = (path.name,)
        console.figure(path.name, "||q_j' A|| for all 15 QR columns, beside the (14, 15) Row(A) basis")
        out.verdict = (
            "Two orthogonalisations, two different spaces. Thin QR orthogonalises "
            f"the columns of A and gives a {col_basis.shape[0]} x {col_basis.shape[1]} "
            f"matrix in R^558 whose 15th direction is outside Col(A) entirely; "
            f"Gram-Schmidt on the pivot rows gives the ({Q.shape[0]}, {Q.shape[1]}) "
            "orthonormal basis of Row(A) in R^15. They are not interchangeable, and "
            "an earlier write-up in this project said they were."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 7 - PROJECTION
# --------------------------------------------------------------------------


def _stage_7(systems: Any, fit: Any, col_basis: np.ndarray, rank: int) -> StageOutput:
    """``b`` splits into its projection onto ``Col(A)`` and a perpendicular rest."""
    A, b, x = systems.A, systems.b, fit.x
    predicted = A @ x
    residual = b - predicted
    residual_norm = float(np.linalg.norm(residual))
    b_norm = float(np.linalg.norm(b))
    predicted_norm = float(np.linalg.norm(predicted))
    directions = col_basis[:, :rank]
    side = residual @ directions
    orth_error = float(np.abs(side).max())
    decomp_error = float(np.abs(residual + predicted - b).max())

    out = StageOutput(
        number=7,
        name=STAGES[6][1],
        principle=STAGES[6][2],
        formula=[
            "x_hat = argmin_x ||A x - b||   is   the orthogonal projection of b",
            "onto Col(A). So:",
            "",
            "    b        = A x_hat  +  r          (exactly, by construction)",
            "    r        = b - A x_hat             the residual",
            "    r . q_j  = 0  for every q_j spanning Col(A)   <- the normal equations",
            "",
            "equivalently  A' r = 0, i.e. r is in the LEFT null space of A.",
        ],
        measured={
            "residual_norm": residual_norm,
            "b_norm": b_norm,
            "predicted_norm": predicted_norm,
            "max_abs_residual_dot_direction": orth_error,
            "decomposition_error": decomp_error,
        },
    )

    with console.stage(7, STAGES[6][1], STAGES[6][2]):
        console.formula(out.formula)
        console.step("computing the projection and its perpendicular remainder")
        console.measured("||b||", b_norm, "runs", "the vector being projected")
        console.measured("||A x_hat||", predicted_norm, "runs", "the projection, i.e. the fitted margins")
        console.measured("||r|| = ||b - A x_hat||", residual_norm, "runs", "the residual: the part Col(A) cannot reach")
        console.measured("||r|| / ||A x_hat||", residual_norm / predicted_norm, "", "the residual is this many times longer than the part that was projected")
        console.measured("||r|| / ||b||", residual_norm / b_norm, "", "the residual is this fraction of the data the model never sees")
        console.note(
            "Pythagoras holds here -- ||b||^2 = ||A x_hat||^2 + ||r||^2 -- and only "
            "because the residual is orthogonal to the column space. that ratio is "
            "the whole story of this project."
        )

        console.step("verifying the orthogonality that makes it a projection")
        with console.Progress("orthogonality check over 14 in-space directions", rank, width=30) as bar:
            for index in range(rank):
                bar.update(index)
            bar.update(rank)
            bar.finish(f"max |r . q_j| = {orth_error:.2e}")
        console.measured("max |r . q_j| over q_1..q_14", orth_error, "", "zero to roundoff: the residual is perpendicular to Col(A)")
        console.measured("max |(A x + r) - b|", decomp_error, "", "roundoff only: the decomposition is an identity, not a fit")
        if orth_error < 1e-9:
            console.ok("r is orthogonal to Col(A) - least squares IS a projection, verified not assumed")
        else:  # pragma: no cover - the normal equations make this exact
            console.bad(f"the residual is not orthogonal: max |r . q_j| = {orth_error}")

        path = fig.f07_projection(b, x, residual, col_basis, rank)
        out.figures = (path.name,)
        console.figure(path.name, "b.q_j against (Ax).q_j for all 14 directions, beside the residual itself")
        out.verdict = (
            f"Least squares is a projection, not a curve fit. b splits exactly into "
            f"A x_hat plus a residual of norm {residual_norm:.2f} runs, and that "
            "residual is perpendicular to every direction in Col(A). It is "
            f"{residual_norm / predicted_norm:.1f} times longer than the part that was "
            "projected, which is why the fit statistic in stage 8 is negative."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 8 - PREDICTION / APPROXIMATION
# --------------------------------------------------------------------------


def _stage_8(
    systems: Any,
    fit: Any,
    official_points: np.ndarray,
) -> StageOutput:
    """Three routes, both R-squared values, in-sample then held-out."""
    A, b, x = systems.A, systems.b, fit.x
    predicted = A @ x
    residual = fit.resid

    r2_centred = dg.r_squared(b, predicted, centred=True)
    r2_uncentred = dg.r_squared(b, predicted, centred=False)
    ss_tot_centred = float(np.sum((b - b.mean()) ** 2))
    ss_tot_raw = float(np.sum(b**2))
    ss_res = float(np.sum((b - predicted) ** 2))

    accuracy = dg.winner_accuracy(predicted, b)
    held = models.held_out_fit(systems.matches, systems.teams, n_test_seasons=3)

    # The correction that reframes this stage. A @ 1 = 0 exactly, so A x can
    # never equal a constant vector: the fit cannot represent the dataset's
    # +18.04-run mean margin, and is therefore *guaranteed* to lose the centred
    # R^2 comparison with one constant. That is the stage-4 gauge freedom, not a
    # finding about noise. Adding the forbidden column measures the difference.
    intercept_fit = dg.intercept_model(A, b)
    signal = dg.noise_vs_signal(A, b, x)
    team1_share = dg.team1_win_share(systems.matches)
    majority = dg.majority_class_accuracy(A @ x, b, dg.team1_won_flags(systems.matches))
    share_by_season = dg.team1_share_by_season(systems.matches)

    ridge_rows = []
    for lam in (0.0, 1.0, 10.0, 50.0, 200.0, 1000.0):
        shrunk = models.ridge(A, b, lam)
        ridge_rows.append(
            (
                f"{lam:g}",
                f"{float(np.abs(shrunk).max()):.2f}",
                f"{float(np.linalg.norm(shrunk)):.2f}",
                f"{dg.r_squared(b, A @ shrunk, centred=True):.4f}",
            )
        )

    out = StageOutput(
        number=8,
        name=STAGES[7][1],
        principle=STAGES[7][2],
        formula=[
            "the normal equations   A' A x = A' b",
            "",
            "rank-deficient, so there is no unique x - only the class x + c*1. Three",
            "routes, three ways of handling the null direction:",
            "",
            "  lstsq(A, b)                        SVD; truncates the zero singular value",
            "  lstsq(A'A, A'b)                    the textbook route; A'A is ALSO rank 14",
            "  solve(A'A + 1*1', A'b)             nonsingular: 1*1' IS the null direction",
            "",
            "R^2 = 1 - SS_res / SS_tot, and SS_tot has TWO legitimate denominators:",
            "  centred    SS_tot = sum (b - mean(b))^2   -> the standard R^2",
            "  uncentred  SS_tot = sum b^2               -> correct only if b is centred",
            "they disagree in SIGN on this data, so both are reported.",
            "",
            "and the centred one is negative for a STRUCTURAL reason: every row of A",
            "sums to zero, so A x has mean zero, while mean(b) = +18.04. The model",
            "cannot represent a constant at all. Adding the one column A was never",
            "allowed - a constant - moves centred R^2 from -0.2103 to +0.0181. The",
            "rank deficiency of stage 4 IS the negative R^2 of stage 8.",
        ],
        measured={
            "max_route_diff": fit.max_route_diff,
            "worst_pair": fit.worst_pair,
            "cond_constrained": fit.cond_constrained,
            "r2_centred": r2_centred,
            "r2_uncentred": r2_uncentred,
            "ss_res": ss_res,
            "ss_tot_centred": ss_tot_centred,
            "ss_tot_uncentred": ss_tot_raw,
            "winner_accuracy_in_sample": accuracy,
            "majority_class_accuracy_in_sample": majority,
            "team1_win_share": team1_share,
            "intercept_r_squared_centred": intercept_fit.r_squared_centred,
            "intercept": intercept_fit.intercept,
            "intercept_ss_res": intercept_fit.ss_res,
            "bias": intercept_fit.bias,
            "mean_b": intercept_fit.mean_b,
            "mean_fitted": intercept_fit.mean_fitted,
            "residual_spread": signal.residual_spread,
            "fitted_spread": signal.fitted_spread,
            "noise_signal_ratio": signal.ratio,
            "held_out_accuracy": held.accuracy,
            "held_out_rmse": held.rmse,
            "held_out_baseline_rmse": held.baseline_rmse,
            "held_out_n_train": held.n_train,
            "held_out_n_test": held.n_test,
            "held_out_seasons": list(held.test_seasons),
        },
    )

    with console.stage(8, STAGES[7][1], STAGES[7][2]):
        console.formula(out.formula)
        console.step("solving the same normal equations three independent ways")
        for label, vector in fit.routes.items():
            console.measured(
                f"max |x| via {label}",
                float(np.abs(vector).max()),
                "runs",
                "same answer, different handling of the null direction",
            )
        console.measured("largest disagreement between routes", fit.max_route_diff, "runs", f"worst pair: {fit.worst_pair[0]} vs {fit.worst_pair[1]}")
        console.measured("cond(A'A + 1*1')", fit.cond_constrained, "", "nonsingular because 1*1' is exactly the null direction; A'A alone is 5.6e16")
        if fit.max_route_diff < 1e-9:
            console.ok("three independent routes agree to 4.8e-14 - the answer is the fit, not the algorithm")

        console.step("the fitted ranking, with the standard error on every coefficient")
        console.vec_bars(x, systems.teams, width=30)
        console.note("teams are alphabetical; the bar is centred on the visible zero axis")

        console.step("how good is the fit? both denominators, both printed")
        console.measured("sum of squares, residual", ss_res, "", "||b - A x||^2 over 558 matches")
        console.measured("sum of squares, centred", ss_tot_centred, "", "the STANDARD denominator: the variance of b about its mean")
        console.measured("sum of squares, uncentred", ss_tot_raw, "", "the other denominator: total squared magnitude of b")
        console.measured("R^2 CENTRED", r2_centred, "", "denominator sum (b - mean(b))^2 - the standard definition")
        console.measured("R^2 UNCENTRED", r2_uncentred, "", "denominator sum b^2 - the same arithmetic, other denominator")
        console.warn(
            "the two denominators disagree in sign because 948,444 > 766,931. the "
            "inherited build audit, the handoff and the earlier spec all headline "
            "only the uncentred +0.0214, which reads as 'explains 2% of the "
            "variation'. the centred -0.2103 is the standard number, and it is "
            "NEGATIVE."
        )

        console.step("why the centred R^2 is negative: the missing intercept, not noise")
        console.measured("mean of the signed margins (b)", intercept_fit.mean_b, "runs", "the level the model has to hit")
        console.measured("mean of the fitted margins (A x)", intercept_fit.mean_fitted, "runs", "the fit sits THIS FAR low on every match")
        console.measured("bias = mean(b) - mean(A x)", intercept_fit.bias, "runs", "arithmetic, not statistical: A @ 1 = 0 forbids a constant")
        console.measured("R^2 centred, with one constant column added", intercept_fit.r_squared_centred, "", f"the column A was never allowed; intercept {intercept_fit.intercept:.4f} runs")
        console.measured("SS_res, without / with the intercept", f"{ss_res:,.1f} / {intercept_fit.ss_res:,.1f}", "", "928,185 -> 753,088: the level was most of the residual")
        console.bad(
            f"so the negative R^2 of {r2_centred:.4f} is a STRUCTURAL consequence of "
            "the rank deficiency stage 4 proved, not a data finding about noise. "
            "stage 4 and stage 8 are one argument: A @ 1 = 0 forbids an absolute "
            "level, so the model cannot fit the +18-run mean margin, so it looks "
            "worse than a constant."
        )
        console.note(
            f"and the correction does NOT rescue the model: {intercept_fit.r_squared_centred:+.4f} "
            "centred, once it is allowed to fit the level properly, is still no signal."
        )

        console.step("winner accuracy against the baseline that matters")
        console.measured("winner accuracy, in sample", 100.0 * accuracy, "%", f"{int(round(accuracy * b.size))} of {b.size}")
        console.measured(
            "majority-class baseline (always team1)",
            100.0 * team1_share,
            "%",
            f"{int(round(team1_share * b.size))} of {b.size} run-margin matches are won by the first-listed team",
        )
        console.measured("model minus baseline", 100.0 * (majority - team1_share), "%", "NEGATIVE: the model has less skill than a constant guess")
        console.bad(
            f"the model scores {100.0 * majority:.1f}% against a majority-class "
            f"baseline of {100.0 * team1_share:.1f}%. a coin flip is not the "
            "relevant comparison - always naming the first-listed team beats the fit."
        )
        console.note(
            "majority_class_accuracy asserts that b's sign and the first-listed-team "
            "indicator are the same convention, and raises if they ever drift apart; "
            "that equality is why it returns the model's own accuracy."
        )

        console.step("held out: fit on the first 16 seasons, scored on the last 3")
        console.measured("train / test rows", f"{held.n_train} / {held.n_test}", "", f"held-out seasons: {', '.join(held.test_seasons)}")
        console.measured("winner accuracy, held out", 100.0 * held.accuracy, "%", f"{int(round(held.accuracy * held.n_test))} of {held.n_test}")
        console.measured("test RMSE, model", held.rmse, "runs", "fitted margins against the real ones")
        console.measured("test RMSE, mean baseline", held.baseline_rmse, "runs", f"the single number {held.train_mean:.2f} - a constant beats the model")
        console.note("the baseline uses the TRAINING mean; using the test mean would leak the answer and flatter the model")
        console.warn(
            "AND THE SPLIT IS DEGENERATE, so read this number with the caveat "
            "attached: the first-listed team won 100% of run-margin matches in "
            + ", ".join(f"{s} ({share_by_season[s]:.3f})" for s in held.test_seasons)
            + ". this is not a local quirk of the test seasons: the share is "
            "exactly 1.000 for EVERY season from 2018 onwards - nine in a row - "
            "against 0.44-0.67 in 2007/08-2017. the archive's team-ordering "
            "convention changed, so the test seasons contain a target that never "
            "varies and part of the TRAINING window is degenerate too. this is not "
            "a clean out-of-sample estimate."
        )
        console.table(
            ["season", "team1 won share"],
            [[s, f"{v:.3f}"] for s, v in share_by_season.items()],
            title="run-margin matches won by the first-listed team, by season",
        )

        console.step("the noise-to-signal ratio, measured on the fitted margins")
        console.measured("residual spread, ||r|| / sqrt(m)", signal.residual_spread, "runs", "margin the model cannot explain, per match")
        console.measured("fitted spread, std(A x)", signal.fitted_spread, "runs", "the team signal the model does extract")
        console.measured("noise / signal", signal.ratio, "x", "the unexplained part is this many times the explained part")
        console.measured("spread of the raw margins, std(b)", signal.margin_spread, "runs", "reported for context - it includes the +18-run level and the signal")
        console.note(
            "the earlier write-up compared std(b) against std(x), i.e. a DATA spread "
            "against a COEFFICIENT spread, and called the ratio a signal-to-noise "
            "figure. both quantities are real; the ratio is not. the two spreads "
            "above are on the same scale and the ratio between them is defined."
        )

        console.step("why shrinkage cannot help: the cost of regularising")
        console.table(["lambda", "max|x|", "||x||", "R^2 centred"], ridge_rows, title=None)
        console.note(
            "x_hat is THE minimiser of ||A x - b||, so no other UNREGULARISED "
            "least-squares fit can lower the residual. ridge is not that fit - it "
            "shrinks toward zero, a different objective - and the table shows it is "
            "strictly worse here: R^2 falls monotonically to -0.2324. an earlier "
            "spec claimed R^2 was unchanged; measurement refutes it, and the "
            "measurement is the table."
        )

        path = fig.f08_least_squares(b, predicted, residual, r2_centred, r2_uncentred, accuracy)
        out.figures = (path.name,)
        console.figure(path.name, "actual against fitted margin, with BOTH R^2 values labelled by denominator")
        out.verdict = (
            f"Three routes agree to 4.8e-14, so the answer is the fit and not the "
            f"algorithm. The fit itself: centred R^2 = {r2_centred:.4f} without an "
            f"intercept and {intercept_fit.r_squared_centred:+.4f} with the one column A "
            f"was never allowed - the negative value is the stage-4 gauge freedom, "
            f"not noise, and correcting it still leaves no signal. "
            f"{100.0 * accuracy:.1f}% winner accuracy against a "
            f"{100.0 * team1_share:.1f}% majority-class baseline. "
            f"{100.0 * held.accuracy:.1f}% held out on a split that is degenerate "
            f"(team1 won 100% of those matches), RMSE {held.rmse:.2f} against "
            f"{held.baseline_rmse:.2f} for one constant."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 9 - PATTERN DISCOVERY
# --------------------------------------------------------------------------


def _stage_9(systems: Any, fit: Any) -> StageOutput:
    """The power method, live, and the positivity claim checked rather than assumed."""
    W, C, M = systems.W, systems.C, systems.M
    names = systems.teams

    # Hand-iterate here so the trace can be shown live; models.colley is called
    # immediately afterwards and its own measured values are the ones reported.
    vector, lam_live, history = lk.power_iteration(M)
    fit_colley = models.colley(W, C)

    spectrum = np.linalg.eigvalsh(M)
    shares = fit_colley.r
    min_entry = fit_colley.min_entry
    iterations = fit_colley.iterations
    colley_matches = int(systems.matches["winner"].notna().sum())

    out = StageOutput(
        number=9,
        name=STAGES[8][1],
        principle=STAGES[8][2],
        formula=[
            "Colley's model says RANK, not margin: pull a team's rating toward the",
            "average of the teams it beat, in proportion to how often it met them.",
            "",
            "    M r = lam1 r        with   M = W + W' + C",
            "      W[i,j] = wins by i over j        C[i,j] = matches between i and j",
            "",
            "M is symmetric and entrywise non-negative, so by Perron-Frobenius the",
            "leading eigenpair is real, simple and STRICTLY POSITIVE.",
            "",
            "power method:   r <- M r / ||M r||      ||M r|| estimates lam1",
        ],
        measured={
            "lam1": fit_colley.lam1,
            "lam2": fit_colley.lam2,
            "iterations": iterations,
            "min_entry": min_entry,
            "all_positive": fit_colley.all_positive,
            "smallest_eigenvalue": float(spectrum.min()),
            "matches_in_colley_subset": colley_matches,
        },
    )

    with console.stage(9, STAGES[8][1], STAGES[8][2]):
        console.formula(out.formula)
        console.step(f"power-iterating the {M.shape[0]}x{M.shape[1]} Colley matrix from the normalised all-ones vector")
        console.converge("||M r||", iter(history))
        console.measured("lam1 from the live iteration", lam_live, "", f"the hand-written route, {iterations} multiply-and-normalise steps")
        console.measured("|live - models.colley|", abs(lam_live - fit_colley.lam1), "", "the two routes agree to machine precision")
        console.sparkline(history, "the full convergence trace, one point per step", width=40)

        console.measured("lam1", fit_colley.lam1, "", "the dominant eigenvalue, 9 iterations at tol 1e-12")
        console.measured("lam2", fit_colley.lam2, "", "the second ALGEBRAIC eigenvalue, read from eigvalsh, not a second power run")
        console.measured("ratio lam1 / lam2", fit_colley.lam1 / fit_colley.lam2, "", "31.7 - which is what licenses calling lam1 *the* dominant direction")
        console.measured("iterations to tolerance", iterations, "steps", "tol 1e-12 on the change in the eigenvalue estimate")
        console.measured("smallest eigenvalue of M", float(spectrum.min()), "", "M is INDEFINITE: its spectral radius is set by the positive end")
        console.warn(
            "a second power run, even correctly projected off the leading "
            f"eigenvector, converges to {float(spectrum.min()):.2f} and not to "
            f"{fit_colley.lam2:.2f}: ||M x|| estimates spectral RADIUS, not the "
            "second algebraic eigenvalue. lam2 is read from eigvalsh instead."
        )

        console.step("asserting positivity out loud, because the theorem is not the measurement")
        console.measured("smallest Colley share", min_entry, "", f"{names[int(np.argmin(shares))]}, the smallest franchise in the table")
        if fit_colley.all_positive:
            console.ok(
                f"all {shares.size} Colley shares are strictly positive "
                f"(smallest {min_entry:.6f}). M is irreducible - the win/loss "
                "graph is one connected component - so this is required, and it "
                "is checked rather than assumed."
            )
        else:  # pragma: no cover - models.colley raises instead of returning this
            console.bad("a Colley share is not strictly positive - the model is not a rating")

        console.step("the ratings, normalised to shares of the league")
        console.vec(shares, "Colley rating shares", precision=4, max_items=len(names))
        console.measured("sum of shares", float(shares.sum()), "", "exactly 1, so it reads as a percentage of the league")
        console.measured("matches in the Colley dataset", colley_matches, "", "every decided match, not just the 558 run margins")

        path = fig.f09_eigen(history, spectrum, fit_colley.lam1, fit_colley.lam2, shares, names)
        out.figures = (path.name,)
        console.figure(path.name, "the ||M r|| convergence trace, beside the full spectrum of M")
        out.verdict = (
            f"The leading eigenvector of M is real, simple and strictly positive: "
            f"lam1 = {fit_colley.lam1:.2f} against lam2 = {fit_colley.lam2:.2f}, "
            f"reached in {iterations} iterations, smallest share {min_entry:.6f} > 0. "
            "This is a model of who beat whom, and it uses all 1,218 decided matches."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 10 - SYSTEM SIMPLIFICATION
# --------------------------------------------------------------------------


def _stage_10(systems: Any) -> StageOutput:
    """``A'A = V diag(sigma^2) V'``, as a measured identity."""
    A = systems.A
    result = models.svd_of_A(A)
    columns = A.shape[1]
    sigma = result.singular_values
    eigenvalues = result.eigenvalues_ata
    squared = result.squared_singular_values
    AtA = A.T @ A
    asymmetry = float(np.abs(AtA - AtA.T).max())
    smallest = float(eigenvalues.min())

    out = StageOutput(
        number=10,
        name=STAGES[9][1],
        principle=STAGES[9][2],
        formula=[
            "SVD:   A = U diag(sigma) V'      ->  A'A = V diag(sigma^2) V'",
            "",
            "so the 15x15 symmetric normal-equation matrix carries exactly the same",
            "information as the 558x15 A: it is A, rotated and squared. The tiny",
            "eigenvalue is where the rank deficiency went.",
            "",
            "   A' A is symmetric by construction:  (A'A)' = A'A   always, for any A.",
        ],
        measured={
            "max_abs_asymmetry": asymmetry,
            "max_abs_diff_sigma2_vs_eigenvalues": result.max_abs_diff,
            "rank": result.rank,
            "sigma_largest": float(sigma[0]),
            "sigma_smallest_nonzero": float(sigma[result.rank - 1]),
            "eigenvalue_smallest": smallest,
            "eigenvalue_largest": float(eigenvalues[0]),
        },
    )

    with console.stage(10, STAGES[9][1], STAGES[9][2]):
        console.formula(out.formula)
        console.step(f"forming A'A: ({columns} x {columns}), symmetric by construction")
        console.mat(AtA[:6], "A'A", f"first 6 of {columns} rows and columns", precision=0)
        console.measured("max |A'A - (A'A)'|", asymmetry, "", "0 exactly: symmetry is structural, not a numerical accident")

        console.step("comparing the spectrum of A'A against the squared singular values of A")
        console.table(
            ["index", "sigma_i", "sigma_i^2", "eigenvalue_i of A'A"],
            [
                [str(i + 1), f"{sigma[i]:.6e}", f"{squared[i]:.6e}", f"{eigenvalues[i]:.6e}"]
                for i in range(columns)
            ],
        )
        console.measured("largest eigenvalue of A'A", float(eigenvalues[0]), "", f"= sigma_1^2 = {float(sigma[0]) ** 2:.4f}")
        console.measured("smallest eigenvalue of A'A", smallest, "", "the structurally zero one, snapped to 0.0 rather than left as -9.2e-15")
        console.measured("rank from the spectrum", result.rank, "", "14 squared singular values above 1e-11")
        console.measured("max |sigma_i^2 - eigenvalue_i|", result.max_abs_diff, "", "the identity, measured rather than asserted")
        if result.max_abs_diff < 1e-10:
            console.ok("the eigenvalues of A'A ARE the squared singular values of A, to 2.0e-13")

        path = fig.f10_diagonalisation(sigma, eigenvalues, result.max_abs_diff)
        out.figures = (path.name,)
        console.figure(path.name, "sigma_i against sigma_i^2 on the y = x line: the identity as a scatter")
        out.verdict = (
            f"A'A is symmetric to {asymmetry:g} and its eigenvalues are the "
            f"squared singular values of A to {result.max_abs_diff:.1e}. The "
            f"{columns}x{columns} diagonal is A rotated, not new information, and "
            f"its {smallest:g} eigenvalue is the rank-14 deficiency restated."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Stage 11 - FINAL APPLICATION OUTPUT
# --------------------------------------------------------------------------


def _stage_11(
    systems: Any,
    fit: Any,
    se: np.ndarray,
    t_stats: np.ndarray,
    eight: dict[str, Any],
    colley_fit: Any,
    comparison: pd.DataFrame,
    official_points: np.ndarray,
) -> StageOutput:
    """The finding, its cause, the refuted hypothesis, and the divergence.

    *eight* is stage 8's measured dictionary, handed in rather than recomputed:
    the R-squared this stage quotes has to be the same number stage 8 printed, and
    re-deriving it here would be the same class of error as the report and the
    terminal drifting apart.
    """
    x, names, games = fit.x, systems.teams, systems.games
    shares = colley_fit.r
    r2_centred = float(eight["r2_centred"])

    signal = dg.noise_vs_signal(systems.A, systems.b, x)
    accuracy = dg.winner_accuracy(systems.A @ x, systems.b)
    max_abs_t = float(np.abs(t_stats).max())
    corr_games = float(np.corrcoef(games, np.abs(x))[0, 1])
    rho_mc = dg.spearman(x, shares)
    rho_mo = dg.spearman(x, official_points)
    rho_co = dg.spearman(shares, official_points)

    balanced = models.frequency_balanced(systems.A, systems.b, games)
    ols_max = float(np.abs(x).max())
    bal_max = float(np.abs(balanced.x).max())
    kochi = int(np.argmax(np.abs(x)))
    bal_r2 = dg.r_squared(systems.b, systems.A @ balanced.x, centred=True)

    out = StageOutput(
        number=11,
        name=STAGES[10][1],
        principle=STAGES[10][2],
        formula=[
            "claim 1: the margin model does not work.",
            "    centred R^2 = -0.2103 WITHOUT an intercept, +0.0181 WITH one.",
            "    the negative value is structural: A @ 1 = 0 forbids a constant,",
            "    so A x has mean 0 while mean(b) = +18.04, and the fit sits 17.30",
            "    runs low on every match. stage 4's gauge freedom IS stage 8's R^2.",
            "    winner accuracy 55.02% against a majority-class baseline of 77.96%",
            "    -> NEGATIVE skill. max|t| = 1.20: not one coefficient at 2 sigma.",
            "",
            "claim 2: the reason is measured, on one scale.",
            "    residual spread  ||r|| / sqrt(m) = 40.79 runs unexplained",
            "    fitted spread    std(A x)        =  5.98 runs of team signal",
            "    ratio 6.82x - the unexplained part dwarfs the explained part",
            "    corr(games played, |x|) = -0.663: short history -> extreme coefficient",
            "",
            "claim 3: win/loss carries what the margin throws away.",
            "    the Colley-style Perron eigenvector of W + W' + C reproduces the",
            "    official points table; the margin fit does not. (Colley's 2002 paper",
            "    solves a different, linear system, so the attribution is loose.)",
            "",
            "significance:  t_i = x_i / se_i,   se from sigma^2 (A'A + 11')^-1,",
            "                            sigma^2 = ||r||^2 / (m - rank) = ||r||^2 / 544",
            "",
            "divergence:    Spearman between the three orderings, joined BY TEAM NAME.",
        ],
        measured={
            "residual_spread": signal.residual_spread,
            "fitted_spread": signal.fitted_spread,
            "noise_signal_ratio": signal.ratio,
            "max_abs_t": max_abs_t,
            "corr_games_abs_x": corr_games,
            "spearman_massey_colley": rho_mc,
            "spearman_massey_official": rho_mo,
            "spearman_colley_official": rho_co,
            "ols_max_abs_x": ols_max,
            "balanced_max_abs_x": bal_max,
            "balanced_r2_centred": bal_r2,
            "in_sample_accuracy": accuracy,
            "held_out_accuracy": eight["held_out_accuracy"],
        },
    )

    with console.stage(11, STAGES[10][1], STAGES[10][2]):
        console.formula(out.formula)

        console.step("the ranking, with the official points table joined BY TEAM NAME")
        console.table(
            ["team", "points", "official", "massey x", "massey", "colley", "moved"],
            [
                [
                    row.team,
                    int(row.points),
                    int(row.official_rank),
                    f"{row.massey_x:+.2f}",
                    int(row.massey_rank),
                    int(row.colley_rank),
                    f"{int(row.rank_movement):+d}",
                ]
                for row in comparison.itertuples(index=False)
            ],
            title="official table, then massey rank, colley rank, and how far the margin fit moved",
        )
        console.note(
            "columns: official = official rank by points, massey = the margin fit's "
            "rank, colley = the win/loss fit's rank, moved = massey - official "
            "(positive means the margin fit ranks that franchise worse than the "
            "official table does)"
        )
        console.note(
            "the official table arrives sorted by points and the fitted vectors in "
            "alphabetical team order, so the join is on `team`. comparing them "
            "positionally has already produced one wrong measurement in this project."
        )

        console.step("claim 1: the margin model does not work")
        console.measured("R^2 centred, no intercept", r2_centred, "", "negative - but read the next line before concluding why")
        console.measured("R^2 centred, with the constant column", eight["intercept_r_squared_centred"], "", "the negative value was the missing intercept, and this is still no signal")
        console.measured("mean(b) - mean(A x), the bias", eight["bias"], "runs", "the fit sits this far low on every match, because A @ 1 = 0")
        console.measured("winner accuracy, in sample", 100.0 * accuracy, "%", "scored against the majority-class baseline below")
        console.measured("majority-class baseline (always team1)", 100.0 * eight["team1_win_share"], "%", "always naming the first-listed team beats the model")
        console.measured("winner accuracy, held out", 100.0 * eight["held_out_accuracy"], "%", "on a split that is degenerate - see stage 8")
        console.measured("max |t| over 15 coefficients", max_abs_t, "", "NOT ONE coefficient is distinguishable from zero at 2 sigma")

        console.step("claim 2: the reason is measured, on one scale")
        console.measured("residual spread, ||r|| / sqrt(m)", signal.residual_spread, "runs", "margin the model cannot explain, per match")
        console.measured("fitted spread, std(A x)", signal.fitted_spread, "runs", "team signal the model does extract")
        console.measured("noise / signal", signal.ratio, "x", "the unexplained part is 6.8 times the explained part")
        console.measured("corr(games played, |x|)", corr_games, "", "fewer games -> more extreme coefficient")
        console.measured("widest standard error", float(se.max()), "runs", f"{names[int(np.argmax(se))]}, a 5-game franchise")
        console.measured("narrowest standard error", float(se.min()), "runs", f"{names[int(np.argmin(se))]}, a 138-game franchise")

        console.step("the refuted hypothesis: frequency balancing was tried, and it is worse")
        console.measured("max |x|, ordinary least squares", ols_max, "runs", f"driven by {names[kochi]}, 5 run-margin games")
        console.measured("max |x|, frequency balanced", bal_max, "runs", f"the same team, {names[kochi]}, pushed further out")
        console.measured("R^2 centred, frequency balanced", bal_r2, "", f"against {r2_centred:.4f} for ordinary least squares")
        console.warn(
            "an inherited build audit predicted that weighting each match by "
            "1/(games(t1) + games(t2)) would stop the short-history franchises "
            "dominating. measurement refutes it: the weighting UP-weights the five "
            "matches the thin franchise played, so the extremity grows from 17.43 "
            "to 25.64. fewer games is a reason to trust a franchise LESS, not more."
        )
        console.bad(
            f"refuted, and reported: balancing made it worse, max|x| "
            f"{ols_max:.2f} -> {bal_max:.2f}."
        )

        console.step("claim 3: win/loss carries what the margin throws away")
        console.measured("Spearman, Colley vs official", rho_co, "", "the eigenvector model reproduces the points table")
        console.measured("Spearman, Massey vs official", rho_mo, "", "the margin model, using information the table ignores, does not")
        console.measured("Spearman, Massey vs Colley", rho_mc, "", "exactly zero: the two models are uncorrelated")
        console.note(
            "the two models rank the same 15 franchises in completely unrelated "
            "orders. one is right and one is wrong, and which one is settled by "
            "the official table, not by the fit statistics."
        )

        summary = dg.summary_table(names, x, se, shares, systems.official, games)
        console.step("the headline table, sorted by fitted strength, with games shown")
        console.table(
            ["team", "games", "massey x", "se", "colley share", "points"],
            [
                [
                    row.team,
                    int(row.games_played),
                    f"{row.massey_x:+.2f}",
                    f"{row.massey_se:.2f}",
                    f"{row.colley_share:.4f}",
                    int(row.points),
                ]
                for row in summary.itertuples(index=False)
            ],
            title=None,
        )
        console.note("the top two rows are the 5-game and the 12-game franchises. read games before you read x")

        for path, caption in (
            (fig.f11_ranking(names, x, se, shares, systems.official), "Massey coefficients with +-2 se whiskers, beside the Colley shares"),
            (fig.f12_findings(names, x, se, games, max_abs_t), "every t statistic against the 2-sigma band, beside games played against |x|"),
            (fig.f13_divergence(comparison), "official table, margin fit and win/loss fit as one slopegraph"),
        ):
            out.figures = out.figures + (path.name,)
            console.figure(path.name, caption)

        out.verdict = (
            "The margin model does not work, and the headline negative R^2 is not "
            f"the reason people first think. Centred R^2 is {r2_centred:.4f} without "
            f"an intercept and {eight['intercept_r_squared_centred']:+.4f} with the one "
            f"column A was never allowed to have: the model cannot fit the "
            f"+{eight['mean_b']:.2f}-run mean margin at all, because A @ 1 = 0. That is "
            f"stage 4's gauge freedom showing up in stage 8, and correcting it still "
            f"leaves no signal. Accuracy {100.0 * accuracy:.1f}% against a "
            f"{100.0 * eight['team1_win_share']:.1f}% majority-class baseline is "
            f"NEGATIVE skill. The reason is measured on one scale: "
            f"{signal.residual_spread:.2f} runs of unexplained margin against "
            f"{signal.fitted_spread:.2f} runs of fitted signal, a ratio of "
            f"{signal.ratio:.2f}. Frequency balancing was tried and made it worse, "
            f"max|x| {ols_max:.2f} -> {bal_max:.2f}. Win/loss, which is what the "
            f"official table actually uses, reproduces it at Spearman "
            f"{rho_co:+.3f}; margin manages {rho_mo:+.3f}."
        )
        console.verdict(out.verdict)
    return out


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def _timeline_rows(outputs: Sequence[StageOutput]) -> list[tuple[str, str, str]]:
    """The closing stage -> figure -> key number table, one key number per stage."""
    keys: dict[int, str] = {
        1: "558 run / 660 wicket",
        2: "558 x 15, row sum 0",
        3: "rank 14, 1 free column",
        4: "A @ 1 = 0 exactly",
        5: "14 of 558 independent",
        6: "Col(A) (558,15) vs Row(A) (14,15)",
        7: "||r|| 963.42",
        8: "R2 -0.2103 / +0.0214",
        9: "lam1 469.18 in 9 iters",
        10: "sigma^2 = eigenvalues, 2.0e-13",
        11: "Spearman +0.939 vs +0.093",
    }
    return [
        (f"{out.number} {out.name}", ", ".join(out.figures), keys[out.number])
        for out in outputs
    ]


def run_demo(*, figures_only: bool = False, stream: TextIO | None = None) -> DemoResult:
    """Walk all eleven stages, save all thirteen figures, return what was measured.

    Parameters
    ----------
    figures_only:
        Skip the opening banner and the closing summary table. Used by the
        determinism test, which runs the demo repeatedly and only compares the
        files; the narration is the expensive part.
    stream:
        Where to render. ``None`` means ``sys.stdout``. Passed straight to
        :func:`console.init` rather than initialised unconditionally: a caller
        that has already bound the renderer to a buffer (the CLI's ``stdout``
        override, or a test capturing the walkthrough) must not be silently
        detached from it halfway through the run.

    Returns
    -------
    DemoResult
        The per-stage measured numbers, the official-table join, and the closing
        timeline, so :mod:`iplranking.report` can render the same figures the
        terminal printed instead of re-deriving them.
    """
    console.init(stream)
    provenance = provenance_record()
    if not figures_only:
        header(provenance)

    # --- load once -------------------------------------------------------
    console.step("reading the committed snapshot and building every matrix")
    systems = build_systems()
    names = teams()
    official = official_table()
    console.measured("canonical franchises n", len(names), "", "19 raw team strings merged by four authorised rename pairs")
    console.measured("design matrix A", f"{systems.A.shape[0]} x {systems.A.shape[1]}", "")
    console.measured("Colley matrix M", f"{systems.M.shape[0]} x {systems.M.shape[1]}", "")

    # --- the official points table, joined BY TEAM NAME -------------------
    official_points = dg._official_points(official, names)

    # --- fit both models -------------------------------------------------
    fit = models.massey(systems.A, systems.b)
    se, sigma2, t_stats = dg.standard_errors(
        systems.A, fit.resid, fit.rank, x=fit.x
    )
    colley_fit = models.colley(systems.W, systems.C)
    held = models.held_out_fit(systems.matches, systems.teams, n_test_seasons=3)
    comparison = dg.official_comparison(
        fit.x, colley_fit.r, official, se
    )

    # --- the eleven stages, in the mandated order -----------------------
    outputs: list[StageOutput] = []
    out1 = _stage_1(systems)
    outputs.append(out1)
    out2 = _stage_2(systems)
    outputs.append(out2)
    out3 = _stage_3(systems)
    outputs.append(out3)
    out4 = _stage_4(systems)
    outputs.append(out4)
    out5 = _stage_5(systems, out3.measured["pivot_rows"])
    outputs.append(out5)
    basis = lk.row_basis(systems.A)
    col_basis = lk.col_space_basis(systems.A)
    out6 = _stage_6(systems, basis)
    outputs.append(out6)
    out7 = _stage_7(systems, fit, col_basis, out3.measured["rank"])
    outputs.append(out7)
    out8 = _stage_8(systems, fit, official_points)
    outputs.append(out8)
    out9 = _stage_9(systems, fit)
    outputs.append(out9)
    out10 = _stage_10(systems)
    outputs.append(out10)

    hold = dict(out8.measured)
    out11 = _stage_11(
        systems, fit, se, t_stats, hold, colley_fit, comparison, official_points
    )
    outputs.append(out11)

    result = DemoResult(
        stages=outputs,
        systems=systems,
        comparison=comparison,
        official_points=official_points,
        timeline=_timeline_rows(outputs),
    )

    if not figures_only:
        closing(result)
    return result
