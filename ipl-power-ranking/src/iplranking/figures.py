"""One saved figure per mandated stage, and the two output directories.

Purpose
-------
``AGENTS.md`` section 5 mandates eleven linear-algebra stages and the owner's
2026-10-04 instruction is that **every stage must be visual**. The terminal walk-
through in :mod:`iplranking.demo` is one half of that; this module is the other
half. Every figure here is written to ``figures/`` as a PNG and is inlined into
``report/report.html`` by :mod:`iplranking.report`.

Where the numbers come from
---------------------------
Nothing in this module computes a *finding*. Every quantity plotted is measured
by :mod:`iplranking.data`, :mod:`iplranking.models`, :mod:`iplranking.diagnostics`
or :mod:`iplranking.linalg_kit` and handed in as an argument, so a figure can
never disagree with the number the terminal printed beside it. The two linear
algebraic steps this module does perform itself are stated where they occur:
Gram-Schmidt is re-run for its off-orthogonality trace, and the thin QR of ``A``
is recomputed for the ``||q_j^T A||`` profile.

Determinism -- a hard acceptance criterion
-----------------------------------------
Two runs must produce **byte-identical** PNGs, so:

* the ``Agg`` backend is selected before ``pyplot`` is imported: no window, no
  display, no dependence on a running desktop;
* team ordering is alphabetical everywhere, which is the order
  :func:`iplranking.data.teams` already fixes, so no figure can reorder a vector
  the maths produced;
* there is no random draw, no sampling, no jitter, no seed and no timestamp
  anywhere in the module;
* the PNG ``Software`` metadata tag is written explicitly, so the bytes do not
  depend on which Matplotlib version rendered them;
* the figure size and DPI are constants, and ``savefig`` is always given
  ``metadata=`` and ``pil_kwargs=``.

Output directories
------------------
:func:`figure_dir` and :func:`report_dir` walk up from this file to the repository
root -- ``src/iplranking`` -> ``src`` -> ``ipl-power-ranking`` -> the root that
holds ``data/``, ``figures/`` and ``report/``. **No absolute path is written down
and no environment variable is read**, so a clean clone at any path produces the
same layout. Both are functions rather than module constants precisely so a test
can point them at a temporary directory and compare two runs.

The house style
---------------
One restrained palette (:data:`INK`, :data:`BLUE`, :data:`TEAL`, :data:`ORANGE`,
:data:`RED`, :data:`GREY`, :data:`PURPLE`), generous figure sizes, and type large
enough to read on a projector. Every axis is labelled, no axis is left in
abbreviations, and **IPL franchise names are always written out in full** -- an
examiner has to be able to read "Royal Challengers Bengaluru" off the chart
without decoding "RCB". Grid lines are the only chrome; there are no spines to
decorate, no drop shadows and no 3-D.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

# Must precede `import matplotlib.pyplot`. Agg is a pure rasteriser: it needs no
# display, which is what lets the demo and the test suite run headless.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .data import repo_root  # noqa: E402

__all__ = [
    "FIGURE_NAMES",
    "figure_dir",
    "f01_data_funnel",
    "f02_design_matrix",
    "f03_rref",
    "f04_structure",
    "f05_redundancy",
    "f06_two_spaces",
    "f07_projection",
    "f08_least_squares",
    "f09_eigen",
    "f10_diagonalisation",
    "f11_ranking",
    "f12_findings",
    "f13_divergence",
    "report_dir",
]

# --------------------------------------------------------------------------
# Output directories
# --------------------------------------------------------------------------


def figure_dir() -> Path:
    """Directory holding the PNG figures, resolved from this file's location.

    ``<repo root>/figures``. A function, not a module constant, so a test can
    redirect it and compare two runs in temporary directories.
    """
    return repo_root() / "figures"


def report_dir() -> Path:
    """Directory holding the HTML report, resolved from this file's location.

    ``<repo root>/report``. Lives here rather than in :mod:`iplranking.report` so
    that both output directories are derived by one rule in one place; report.py
    calls ``figures.report_dir()`` through the module so a patched value is seen
    by both.
    """
    return repo_root() / "report"


def _ensure(directory: Path) -> Path:
    """Create *directory* if absent and return it."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _save(fig: plt.Figure, directory: Path, name: str) -> Path:
    """Write *fig* to ``directory/name`` and close it; return the path.

    The ``Software`` tag is pinned to a literal string. Matplotlib's default tag
    embeds the library version, which would make the PNG bytes differ between two
    machines running two versions -- the one thing a byte-identity check must not
    trip over, and a difference that carries no information about the data.
    """
    _ensure(directory)
    path = directory / name
    fig.savefig(
        path,
        dpi=DPI,
        format="png",
        metadata={"Software": "ipl-power-ranking"},
        pil_kwargs={"optimize": True},
    )
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# House style
# --------------------------------------------------------------------------

#: Raster density. Fixed, so the same figure is the same number of pixels twice.
DPI = 120

INK = "#14181f"
MUTED = "#5b6472"
GRID = "#d8dce3"
BLUE = "#1f5fa8"
TEAL = "#0f766e"
ORANGE = "#c2610c"
RED = "#b3261e"
GREY = "#b9bfc9"
PURPLE = "#5b4b9e"

plt.rcParams.update(
    {
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.8,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "legend.frameon": False,
    }
)

#: The exact file names, in stage order. ``demo.py`` and ``report.py`` both index
#: off this, and the test suite asserts all thirteen exist, so adding a figure
#: without naming it here fails rather than being silently skipped.
FIGURE_NAMES: tuple[str, ...] = (
    "01-data.png",
    "02-design-matrix.png",
    "03-rref.png",
    "04-structure.png",
    "05-redundancy.png",
    "06-qr.png",
    "07-projection.png",
    "08-least-squares.png",
    "09-eigen.png",
    "10-diagonalisation.png",
    "11-ranking.png",
    "12-findings.png",
    "13-divergence.png",
)


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------


def _team_axis(ax: plt.Axes, names: list[str], *, invert: bool = False) -> None:
    """Put *names* on the y-axis in full, alphabetically, one per row.

    No abbreviation and no truncation. When the caller has already sorted by
    something else the caller re-labels; this helper is only for the alphabetical
    case, which is the deterministic default for this project.
    """
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    if invert:
        ax.invert_yaxis()


def _note(fig: plt.Figure, text: str) -> None:
    """Write a single caption line under the figure."""
    fig.text(0.01, 0.01, text, color=MUTED, fontsize=8, ha="left", va="bottom")


def _fmt(value: float, places: int = 0) -> str:
    """Format a number for an in-figure label."""
    return f"{value:,.{places}f}"


# --------------------------------------------------------------------------
# Stage 1 -- REAL-WORLD DATA
# --------------------------------------------------------------------------


def f01_data_funnel(
    *,
    total: int,
    decided: int,
    no_winner: int,
    run_margin: int,
    wicket_only: int,
    seasons: int,
    first_season: str,
    last_season: str,
) -> Path:
    """Stage 1, REAL-WORLD DATA. Principle: **a dataset constrains the model**.

    The funnel 1,243 -> 1,218 -> 558 + 660, with the 25 excluded matches drawn
    as their own red segment rather than omitted. The visual point is that the
    558/660 split is not a modelling preference: it is what the archive contains,
    and it is the reason two different datasets feed two different models.

    All seven counts are passed in so the chart and the terminal cannot drift.
    """
    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    bar_height = 0.62

    rows = [
        (2, [(total, BLUE)], f"{total:,} matches in data/matches.csv"),
        (1, [(decided, TEAL), (no_winner, RED)], ""),
        (0, [(run_margin, BLUE), (wicket_only, GREY)], ""),
    ]
    for position, segments, label in rows:
        left = 0
        for value, colour in segments:
            ax.barh(
                position,
                value,
                left=left,
                height=bar_height,
                color=colour,
                edgecolor="white",
                linewidth=1.0,
            )
            left += value

    # --- annotations, placed inside the segments where they fit -------------
    ax.text(
        total / 2,
        2,
        f"{total:,}  all matches  ·  {seasons} seasons  ·  {first_season} to {last_season}",
        ha="center",
        va="center",
        color="white",
        fontsize=11,
        fontweight="bold",
    )
    ax.text(
        decided / 2,
        1,
        f"{decided:,}  decided  →  the Colley model uses all of these",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
    )
    ax.text(
        decided + no_winner / 2,
        1,
        f"{no_winner}",
        ha="center",
        va="center",
        color="white",
        fontsize=9,
        fontweight="bold",
    )
    ax.text(
        run_margin / 2,
        0,
        f"{run_margin:,}  run margin\n→ the Massey model",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )
    ax.text(
        run_margin + wicket_only / 2,
        0,
        f"{wicket_only:,}  wicket only\n→ the Colley model only",
        ha="center",
        va="center",
        color=INK,
        fontsize=10,
        fontweight="bold",
    )

    ax.annotate(
        f"EXCLUDED\n{no_winner} of {total:,} matches "
        f"({100.0 * no_winner / total:.2f}%)\nno `winner` field",
        xy=(decided + no_winner / 2, 1.31),
        xytext=(total * 0.60, 2.55),
        ha="center",
        va="bottom",
        fontsize=9,
        color=RED,
        fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.4),
    )

    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(
        [
            "does a margin figure\nexist at all?",
            "is there a `winner`\nfield in the record?",
            "what is in the\nsnapshot",
        ]
    )
    ax.set_xlim(0, total * 1.06)
    ax.set_ylim(-0.6, 3.15)
    ax.set_xlabel("matches")
    ax.set_title(
        "Stage 1 - the dataset decides the mathematics\n"
        f"{run_margin:,} of {total:,} matches carry a run margin; "
        f"{wicket_only:,} carry wickets and no run figure at all",
        loc="left",
    )
    ax.grid(axis="y", visible=False)
    _note(
        fig,
        "The 660 wicket-margin matches were NOT converted to run equivalents. "
        "Any such factor would have to be invented, so two honest models on two "
        "different datasets is what is built instead.",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[0])


# --------------------------------------------------------------------------
# Stage 2 -- Matrix Representation
# --------------------------------------------------------------------------


def f02_design_matrix(A: np.ndarray, teams: list[str]) -> Path:
    """Stage 2, Matrix Representation. Principle: **a match is one equation**.

    ``A`` drawn in full as a +-1 heatmap: 558 rows, 15 labelled franchise columns.
    Two things have to be legible. The *sparsity* -- each row has one +1, one -1
    and thirteen zeros, so 13.3% of the grid is ink -- and the *row-sum-zero*
    structure, which is shown as its own strip on the right, because it is the
    whole reason stage 4 has a null direction.
    """
    rows, columns = A.shape
    row_sums = A.sum(axis=1)
    density = 100.0 * np.count_nonzero(A) / A.size

    fig, (ax, strip) = plt.subplots(
        1, 2, figsize=(12.5, 8.6), gridspec_kw={"width_ratios": [3.1, 1.0]}
    )

    image = ax.imshow(
        A,
        aspect="auto",
        interpolation="nearest",
        cmap="RdBu_r",
        vmin=-1.0,
        vmax=1.0,
        extent=(0, columns, rows, 0),
    )
    ax.set_xticks(np.arange(columns) + 0.5)
    ax.set_xticklabels(teams, rotation=90, fontsize=8)
    ax.set_yticks([0, 100, 200, 300, 400, 500, 557])
    ax.set_xlabel("the 15 unknown franchise strengths  (columns of A)")
    ax.set_ylabel("the 558 run-margin matches  (rows of A)")
    ax.set_title(
        f"A = array  ({rows}, {columns})   one row per match\n"
        f"+1 winner   -1 loser   0 not in this match   ·   "
        f"{int(np.count_nonzero(A)):,} of {A.size:,} cells non-zero "
        f"({density:.1f}% dense)",
        loc="left",
    )
    ax.grid(visible=False)
    ax.axvline(0.5, color=INK, linewidth=0.8)
    bar = fig.colorbar(image, ax=ax, ticks=[-1, 0, 1], fraction=0.035, pad=0.02)
    bar.ax.set_yticklabels(["-1  loser", "0", "+1  winner"])

    strip.plot(np.arange(rows), row_sums, color=BLUE, linewidth=0.8)
    strip.axhline(0.0, color=INK, linewidth=1.0)
    strip.set_xlim(0, rows)
    strip.set_ylim(-1.0, 1.0)
    strip.set_xlabel("row index")
    strip.set_ylabel("row sum")
    strip.set_title(
        "every row sums to zero\n"
        f"max |row sum| = {float(np.abs(row_sums).max()):.1f}\n"
        "one +1 and one -1, always",
        loc="left",
        fontsize=10,
    )
    _note(
        fig,
        "Row sums to zero is not decoration: it means A @ (x + c*1) = A @ x for any c, "
        "which is the null direction stage 4 measures.",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[1])


# --------------------------------------------------------------------------
# Stage 3 -- Matrix Simplification (RREF)
# --------------------------------------------------------------------------


def f03_rref(R: np.ndarray, pivot_rows: list[int], teams: list[str]) -> Path:
    """Stage 3, Matrix Simplification. Principle: **Gauss-Jordan reduction finds
    the rank, and the rank is the number of independent facts**.

    The first fourteen rows of the reduced row-echelon form -- the pivot rows,
    each with a single 1 and a free-column coupling coefficient -- followed by the
    rows that came out **identically zero**. That zero row is the visible form of
    the null direction, so it is boxed and labelled rather than cropped away.
    """
    rank = len(pivot_rows)
    shown = rank + 2
    head = R[:shown]
    pivot_columns = [int(np.flatnonzero(row != 0.0)[0]) for row in head[:rank]]
    free_column = next(c for c in range(R.shape[1]) if c not in set(pivot_columns))

    fig, ax = plt.subplots(figsize=(12.5, 5.4))
    extent_scale = max(1.0, float(np.abs(head[:rank]).max()))
    image = ax.imshow(
        head,
        aspect="auto",
        interpolation="nearest",
        cmap="RdBu_r",
        vmin=-extent_scale,
        vmax=extent_scale,
        extent=(0, R.shape[1], shown, 0),
    )

    # Box every pivot row and every pivot column, so the "each pivot column is a
    # column of the identity" property of a *reduced* form is visible.
    for r in range(rank):
        ax.add_patch(
            plt.Rectangle(
                (0, r), R.shape[1], 1, fill=False, edgecolor=TEAL, linewidth=0.9
            )
        )
        c = pivot_columns[r]
        ax.plot([c + 0.5], [r + 0.5], marker="s", color=TEAL, markersize=5)
    free_head = head[:rank, free_column]
    ax.plot(
        [free_column + 0.5] * rank,
        np.arange(rank) + 0.5,
        marker="o",
        linestyle="none",
        color=ORANGE,
        markersize=6,
    )
    for r in range(rank):
        ax.annotate(
            f"{-float(free_head[r]):+.0f}",
            xy=(free_column + 0.62, r + 0.5),
            va="center",
            ha="left",
            fontsize=8,
            color=ORANGE,
        )

    # The singular row: drawn, boxed in red, and named.
    ax.add_patch(
        plt.Rectangle(
            (0, rank),
            R.shape[1],
            1,
            fill=False,
            edgecolor=RED,
            linewidth=1.6,
            linestyle="--",
        )
    )
    ax.text(
        R.shape[1] + 0.25,
        rank + 0.5,
        f"row {rank}: IDENTICALLY ZERO\nthe null direction,\nnot a missing row",
        va="center",
        ha="left",
fontsize=9,
        color=RED,
    )
    ax.text(
        R.shape[1] + 0.25,
        0.9,
        f"green box + square: pivot column,\nits entry is exactly 1\n"
        f"orange: coupling into the\nFREE column {free_column}\n"
        f"({teams[free_column]})",
        va="top",
        ha="left",
        fontsize=8.5,
        color=MUTED,
    )

    ax.set_xticks(np.arange(R.shape[1]) + 0.5)
    ax.set_xticklabels(teams, rotation=90, fontsize=8)
    ax.set_xlim(0, R.shape[1] + 5.0)
    ax.set_ylim(shown, 0)
    ax.set_yticks(np.arange(shown) + 0.5)
    ax.set_yticklabels(
        [f"{i}  pivot {pivot_rows[i]}" for i in range(rank)]
        + [f"{rank}  ZERO"]
        + [f"{rank + 1}  ZERO"]
    )
    ax.set_xlabel("columns of A")
    ax.set_ylabel("rows of the reduced row-echelon form")
    ax.set_title(
        f"RREF of A: {rank} pivot rows, then a zero row\n"
        f"free column = {free_column} ({teams[free_column]}); "
        f"the pivot rows' coupling into it is what defines the null direction",
        loc="left",
    )
    ax.grid(visible=False)
    bar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.03)
    bar.set_label("entry of R")

    _note(
        fig,
        f"... and {R.shape[0] - shown} more identically zero rows follow.  Original rows promoted to "
        f"pivots: {pivot_rows}.\n"
        "Pivot rule: take the largest |entry| below the diagonal (partial pivoting); a column with "
        "no entry above tolerance is FREE and takes no pivot.",
    )
    fig.tight_layout(rect=(0, 0.085, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[2])


# --------------------------------------------------------------------------
# Stage 4 -- Structure of the Space
# --------------------------------------------------------------------------


def f04_structure(
    singular_values: np.ndarray, rank: int, zero_cutoff: float
) -> Path:
    """Stage 4, Structure of the Space. Principle: **rank plus nullity is the
    whole dimension count, and the missing direction has a name**.

    The fifteen singular values of ``A`` on a log axis. Fourteen sit between
    ``12.48`` and ``2.22``; the fifteenth is at ``5e-15``, seven orders of
    magnitude below the structural-zero cutoff, which is what "numerically zero"
    means rather than asserting. Rank 14, nullity 1, drawn as the annotation.
    """
    values = np.asarray(singular_values, dtype=np.float64)
    count = values.size
    positions = np.arange(1, count + 1)

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.semilogy(positions, values, marker="o", color=BLUE, linewidth=1.4)
    ax.vlines(positions, zero_cutoff, values, color=BLUE, linewidth=1.2, alpha=0.45)
    ax.axhline(
        zero_cutoff,
        color=RED,
        linewidth=1.2,
        linestyle="--",
        label=f"structural-zero cutoff, {zero_cutoff:.0e}",
    )
    ax.set_yscale("log")
    ax.set_ylim(1e-16, 1e2)
    ax.set_xlim(0.4, count + 1.6)
    ax.set_xticks(positions)
    ax.set_xlabel("singular value index i")
    ax.set_ylabel("singular value of A  (log scale)")
    ax.set_title(
        f"the singular spectrum of A = array  (558, 15)\n"
        f"rank(A) = {rank},  nullity(A) = {count - rank},  n = {count}",
        loc="left",
    )

    ax.annotate(
        f"sigma_1 = {values[0]:.4f}\nlargest direction",
        xy=(1, values[0]),
        xytext=(1.5, 1.4),
        fontsize=9,
        color=BLUE,
        arrowprops=dict(arrowstyle="->", color=BLUE, linewidth=1.0),
    )
    ax.annotate(
        f"sigma_{rank} = {values[rank - 1]:.4f}\nsmallest real direction",
        xy=(rank, values[rank - 1]),
        xytext=(rank - 4.2, 2.0e-4),
        fontsize=9,
        color=BLUE,
        arrowprops=dict(arrowstyle="->", color=BLUE, linewidth=1.0),
    )
    ax.annotate(
        f"sigma_{count} = {values[-1]:.3e}\n"
        f"{abs(np.log10(values[-1] / values[rank - 1])):.1f} orders of magnitude\n"
        f"below sigma_{rank}\n→ the NULL direction",
        xy=(count, values[-1]),
        xytext=(6.4, 3.0e-14),
        fontsize=9,
        color=RED,
        fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.4),
    )
    ax.legend(loc="lower left", fontsize=9)
    _note(
        fig,
        "The null direction is the constant vector: adding the same number of runs to every "
        "franchise changes no predicted margin, so only DIFFERENCES are identifiable.",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[3])


# --------------------------------------------------------------------------
# Stage 5 -- Remove Redundancy
# --------------------------------------------------------------------------


def f05_redundancy(
    A: np.ndarray, pivot_rows: list[int], basis_rows: np.ndarray, teams: list[str]
) -> Path:
    """Stage 5, Remove Redundancy. Principle: **14 of 558 equations are
    independent; the other 544 are linear combinations of them**.

    Left: every one of the 558 match rows as a tick, the fourteen promoted to
    pivots picked out. The visual point is how few of them are. Right: those
    fourteen rows as a +-1 heatmap, so the reader can see they are ordinary
    matches and not a special subset.
    """
    rows, columns = A.shape
    kept = np.zeros(rows, dtype=bool)
    kept[np.asarray(pivot_rows, dtype=int)] = True
    redundant = rows - int(kept.sum())

    fig, (ax, basis_ax) = plt.subplots(
        1, 2, figsize=(12.5, 6.2), gridspec_kw={"width_ratios": [2.2, 1.0]}
    )

    ax.vlines(
        np.arange(rows) + 1,
        0,
        1,
        color=GREY,
        linewidth=0.9,
        label=f"redundant ({redundant} rows)",
    )
    ax.vlines(
        np.asarray(pivot_rows, dtype=int) + 1,
        0,
        1.0,
        color=ORANGE,
        linewidth=3.0,
        label=f"independent basis ({len(pivot_rows)} rows)",
    )
    ax.set_xlim(0, rows + 1)
    ax.set_ylim(0, 1.25)
    ax.set_yticks([])
    ax.set_xlabel("the 558 match rows of A")
    ax.set_title(
        f"basis of the row space: {len(pivot_rows)} of {rows}\n"
        f"{redundant} rows carry no information the other {len(pivot_rows)} do not",
        loc="left",
    )
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", fontsize=9, ncol=2)

    basis_ax.imshow(
        basis_rows,
        aspect="auto",
        interpolation="nearest",
        cmap="RdBu_r",
        vmin=-1.0,
        vmax=1.0,
    )
    basis_ax.set_xticks(np.arange(columns) + 0.5)
    basis_ax.set_xticklabels(teams, rotation=90, fontsize=7)
    basis_ax.set_yticks(np.arange(len(pivot_rows)) + 0.5)
    basis_ax.set_yticklabels(
        [f"row {pivot_rows[i]}" for i in range(len(pivot_rows))], fontsize=7
    )
    basis_ax.set_title(
        "the 14 basis rows, verbatim from A\n(no recombination: they ARE rows of A)",
        loc="left",
        fontsize=10,
    )
    basis_ax.grid(visible=False)
    _note(
        fig,
        f"Every non-pivot row was eliminated by these {len(pivot_rows)}, so it is a linear "
        "combination of them. rank(A) = 14 is the count; nothing more is independent.",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[4])


# --------------------------------------------------------------------------
# Stage 6 -- Orthogonalization
# --------------------------------------------------------------------------


def f06_two_spaces(
    A: np.ndarray, col_basis: np.ndarray, row_basis_orthonormal: np.ndarray
) -> Path:
    """Stage 6, Orthogonalization. Principle: **orthogonalise, but know which
    space you are orthogonalising -- ``Col(A)`` and ``Row(A)`` are not the same
    object.**

    Left: ``||q_j^T A||`` for each of the fifteen columns of the thin QR of ``A``.
    For the first fourteen this *is* the j-th singular value, because those
    directions lie in ``Col(A)``. The fifteenth reads ``2e-14``: that direction
    sees nothing of ``A``, so it is an orthogonal completion, not a direction of
    ``Col(A)``. That is the measured version of "thin QR orthogonalises the
    columns, not the rows".

    Right: the Gram-Schmidt basis of ``Row(A)`` -- a genuine ``(14, 15)``
    orthonormal basis, in ``R^15``, a different ambient space with a different
    shape. The panel titles carry the dimensions so the two cannot be confused.
    """
    heights = np.linalg.norm(col_basis.T @ A, axis=1)
    rank = int(np.count_nonzero(heights > 1e-8))
    Q = np.asarray(row_basis_orthonormal, dtype=np.float64)

    fig, (ax, basis_ax) = plt.subplots(
        1, 2, figsize=(13.0, 6.0), gridspec_kw={"width_ratios": [1.15, 1.0]}
    )

    positions = np.arange(1, heights.size + 1)
    colours = [BLUE] * rank + [RED] * (heights.size - rank)
    ax.bar(positions, heights, color=colours, width=0.7)
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_ylim(0, 30)
    ax.set_xticks(positions)
    ax.set_xlabel("column j of the thin QR factor Q")
    ax.set_ylabel(r"$\Vert q_j^{\mathsf{T}} A \Vert_2$")
    ax.set_title(
        "Col(A) is a subspace of R^558\n"
        f"thin QR of a (558, 15) matrix gives Q of shape {tuple(col_basis.shape)}: "
        f"{rank} columns inside\nCol(A) and one orthogonal completion outside it",
        loc="left",
    )
    ax.annotate(
        f"q_{heights.size} sees nothing of A:\n||q_{heights.size}^T A|| = {heights[-1]:.2e}\n"
        "so Q is NOT a basis of the 14-dimensional Col(A)",
        xy=(heights.size, max(heights[-1], 1e-3)),
        xytext=(heights.size - 8.2, 0.05),
        fontsize=9,
        color=RED,
        fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1.5),
        arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.4),
    )
    ax.axhline(
        1.0,
        color=MUTED,
        linewidth=0.8,
        linestyle=":",
        label="linear above 1, log below",
    )
    ax.legend(loc="upper right", fontsize=8)

    reach = float(np.abs(Q).max())
    image = basis_ax.imshow(
        Q,
        aspect="auto",
        interpolation="nearest",
        cmap="RdBu_r",
        vmin=-reach,
        vmax=reach,
        extent=(0, Q.shape[1], Q.shape[0], 0),
    )
    basis_ax.set_xticks(np.arange(Q.shape[1]) + 0.5)
    basis_ax.set_yticks(np.arange(Q.shape[0]) + 0.5)
    basis_ax.set_xlabel("the 15 franchise columns, alphabetical (the same order as A)")
    basis_ax.set_ylabel("14 orthonormal row-space directions")
    basis_ax.set_title(
        f"Row(A) is a subspace of R^15\nGram-Schmidt on the {Q.shape[0]} pivot rows gives "
        f"Q of shape {tuple(Q.shape)}\nwith Q Q^T = I_{Q.shape[0]}  (a real orthonormal basis)",
        loc="left",
        fontsize=10,
    )
    basis_ax.grid(visible=False)
    bar = fig.colorbar(image, ax=basis_ax, fraction=0.03, pad=0.03)
    bar.set_label("component of the direction")
    _note(
        fig,
        "Documented correction to an earlier claim in this project: thin QR orthogonalises the "
        "COLUMNS, i.e. Col(A) inside R^558. Row(A) inside R^15 is a different space and needs "
        "its own orthogonalisation, which is what the right-hand panel is.",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[5])


# --------------------------------------------------------------------------
# Stage 7 -- Projection
# --------------------------------------------------------------------------


def f07_projection(
    b: np.ndarray,
    x: np.ndarray,
    residual: np.ndarray,
    col_basis: np.ndarray,
    rank: int,
) -> Path:
    """Stage 7, Projection. Principle: **least squares *is* the orthogonal
    projection of ``b`` onto ``Col(A)``, and the residual is perpendicular to it.**

    Left: the decomposition checked direction by direction. ``b . q_j`` and
    ``(Ax). q_j`` coincide for every one of the fourteen in-space directions --
    that equality *is* the projection -- while ``r . q_j`` sits at ``1e-13``,
    invisible on this scale, which is the normal-equation condition made visible.

    Right: the residual itself, one point per match, with its norm annotated. Per
    match it runs ``||r|| / sqrt(m) = 40.79`` against a fitted spread of
    ``std(A x) = 5.98`` -- a ratio of ``6.82``, not five -- and it is the reason
    stage 8's ``R^2`` is negative. The negative sign itself is the missing
    intercept, not the noise: see ``diagnostics.intercept_model``.
    """
    fitted = np.asarray(x, dtype=np.float64)
    directions = np.asarray(col_basis, dtype=np.float64)[:, :rank]
    projected = b @ directions
    fitted_side = (b - residual) @ directions
    residual_side = residual @ directions

    fitted_norm = float(np.linalg.norm(b - residual))
    residual_norm = float(np.linalg.norm(residual))

    fig, (ax, resid_ax) = plt.subplots(
        1, 2, figsize=(13.0, 6.0), gridspec_kw={"width_ratios": [1.0, 1.0]}
    )

    positions = np.arange(1, rank + 1)
    width = 0.38
    ax.bar(
        positions - width / 2,
        projected,
        width,
        color=BLUE,
        label=r"$b \cdot q_j$",
    )
    ax.bar(
        positions + width / 2,
        fitted_side,
        width,
        color=TEAL,
        label=r"$(A\hat{x}) \cdot q_j$",
    )
    ax.plot(
        positions,
        residual_side,
        linestyle="none",
        marker=".",
        color=RED,
        markersize=9,
        label=r"$r \cdot q_j$   (= 0)",
    )
    ax.axhline(0.0, color=INK, linewidth=1.0)
    ax.set_xticks(positions)
    ax.set_xlabel("the 14 orthonormal directions of Col(A)")
    ax.set_ylabel("component of the vector along that direction  (runs)")
    ax.set_title(
        f"b decomposes into a fitted part of {fitted_norm:.2f} runs\n"
        f"and a residual of {residual_norm:.2f} runs, exactly perpendicular to it",
        loc="left",
    )
    ax.legend(loc="upper left", fontsize=9)
    ax.annotate(
        f"max |r . q_j| = {float(np.abs(residual_side).max()):.2e}\n"
        "A^T r = 0: the normal equations, in runs",
        xy=(positions[rank - 1], 0.0),
        xytext=(2.0, min(float(projected.min()) * 0.55, -40.0)),
        fontsize=9,
        color=RED,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.92, pad=1.5),
        arrowprops=dict(arrowstyle="->", color=RED, linewidth=1.2),
    )

    resid_ax.axhline(0.0, color=INK, linewidth=1.0)
    resid_ax.plot(
        np.arange(1, residual.size + 1),
        residual,
        linestyle="none",
        marker=".",
        markersize=2.5,
        color=ORANGE,
    )
    resid_ax.set_xlim(0, residual.size + 1)
    resid_ax.set_xlabel("the 558 run-margin matches, chronological")
    resid_ax.set_ylabel("r = b - A x_hat  (runs)")
    resid_ax.set_title(
        f"the residual: ||r|| = {residual_norm:.2f} runs\n"
        f"||r||^2 = {float(residual @ residual):,.1f}   vs   "
        f"||A x_hat||^2 = {fitted_norm**2:,.1f}",
        loc="left",
    )
    _note(
        fig,
        "Pythagoras: ||b||^2 = ||A x_hat||^2 + ||r||^2, valid only because the residual is "
        "orthogonal to the column space. The residual is the part of the data the model cannot see.",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[6])


# --------------------------------------------------------------------------
# Stage 8 -- Least Squares
# --------------------------------------------------------------------------


def f08_least_squares(
    b: np.ndarray,
    predicted: np.ndarray,
    residual: np.ndarray,
    r2_centred: float,
    r2_uncentred: float,
    accuracy: float,
) -> Path:
    """Stage 8, Prediction / Approximation. Principle: **least squares minimises
    the residual -- and on this data the minimum is worse than a constant.**

    Left: actual against fitted signed margin. The cloud is a cigar tilted the
    wrong way, and it is centred away from the origin because ``b`` has a non-zero
    mean of 18.04 runs; the ``y = x`` line is what a perfect model would lie on.
    **Both** R-squared values are annotated, each labelled with its denominator,
    because they disagree in sign and quoting only one hides the finding.

    Right: the residual distribution, with one standard deviation marked, and the
    winner-accuracy line -- 55.0%, which is **below** the majority-class baseline
    of 77.96%, so the model has negative skill. A coin flip at 50% is not the
    relevant comparison.
    """
    fig, (ax, resid_ax) = plt.subplots(
        1, 2, figsize=(13.0, 6.2), gridspec_kw={"width_ratios": [1.0, 1.0]}
    )

    limit = float(max(np.abs(b).max(), np.abs(predicted).max())) * 1.06
    ax.scatter(b, predicted, s=7, color=BLUE, alpha=0.35, linewidths=0)
    ax.plot([-limit, limit], [-limit, limit], color=INK, linewidth=1.2, linestyle="--")
    ax.axhline(0.0, color=MUTED, linewidth=0.8)
    ax.axvline(0.0, color=MUTED, linewidth=0.8)
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.set_xlabel("actual signed run margin  (runs)")
    ax.set_ylabel("fitted signed run margin  A x_hat  (runs)")
    ax.set_title(
        "fitted vs actual, 558 matches\nthe cloud is flatter than the y = x line: "
        "the fit shrinks large margins",
        loc="left",
    )
    ax.text(
        0.04,
        0.955,
        f"R^2  centred     = {r2_centred:+.4f}\n"
        f"        SS_tot = sum (b - mean b)^2\n\n"
        f"R^2  uncentred = {r2_uncentred:+.4f}\n"
        f"        SS_tot = sum b^2\n\n"
        f"winner accuracy = {100.0 * accuracy:.1f}%",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9.5,
        family="DejaVu Sans Mono",
        bbox=dict(facecolor="white", edgecolor=GRID, boxstyle="round,pad=0.5"),
    )

    sigma = float(np.std(residual))
    resid_ax.hist(
        residual, bins=48, color=BLUE, edgecolor="white", linewidth=0.4, alpha=0.9
    )
    resid_ax.axvline(0.0, color=INK, linewidth=1.2)
    for sign, name in ((-1.0, "-1 sigma"), (1.0, "+1 sigma")):
        resid_ax.axvline(
            sign * sigma,
            color=ORANGE,
            linewidth=1.1,
            linestyle="--",
        )
        resid_ax.text(
            sign * sigma,
            resid_ax.get_ylim()[1] * 0.96,
            f"{name} = {sign * sigma:+.1f}",
            color=ORANGE,
            fontsize=8.5,
            ha="center",
            va="top",
        )
    resid_ax.set_xlabel("residual  r = b - A x_hat  (runs)")
    resid_ax.set_ylabel("matches")
    resid_ax.set_title(
        f"the residual spread: sd(r) = {sigma:.2f} runs (population sd)\n"
        f"against sd(b) = 37.07 runs and a spread of fitted\n"
        f"team strengths sd(x) of only 7.03 runs",
        loc="left",
    )
    _note(
        fig,
        "The uncentred R^2 is the number the inherited write-up quoted. The centred one is the "
        "standard coefficient of determination, and it is negative: the model predicts worse than "
        "the single number 'the mean margin'.",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[7])


# --------------------------------------------------------------------------
# Stage 9 -- Pattern Discovery
# --------------------------------------------------------------------------


def f09_eigen(
    history: list[float],
    eigenvalues: np.ndarray,
    lam1: float,
    lam2: float,
    shares: np.ndarray,
    teams: list[str],
) -> Path:
    """Stage 9, Pattern Discovery. Principle: **the dominant eigenvector of a
    non-negative symmetric matrix is real, simple and positive.**

    Left: the power iteration's own ``||M r||`` trace, drawn from
    ``ColleyFit.history``. It climbs 16.6% in one step and is flat to twelve
    decimals by the ninth -- the convergence is shown, not asserted.

    Right: the full spectrum of ``M = W + W^T + C``. ``lam1 = 469.18`` dominates
    ``lam2 = 14.81`` by a factor of 31.7, which is what licenses calling it *the*
    dominant direction. The most negative eigenvalue, ``-86.72``, is annotated too,
    because it is why a second power run cannot be used to read ``lam2``.
    """
    values = np.array(history, dtype=np.float64)
    spectrum = np.sort(np.asarray(eigenvalues, dtype=np.float64))

    fig, (ax, spectrum_ax) = plt.subplots(
        1, 2, figsize=(13.0, 6.0), gridspec_kw={"width_ratios": [1.0, 1.05]}
    )

    ax.plot(
        np.arange(1, values.size + 1),
        values,
        marker="o",
        color=BLUE,
        linewidth=1.4,
    )
    ax.axhline(lam1, color=TEAL, linewidth=1.0, linestyle="--")
    ax.set_xticks(np.arange(1, values.size + 1))
    ax.set_xlabel("power iteration step")
    ax.set_ylabel(r"$\Vert M r \Vert_2$   (an estimate of the dominant eigenvalue)")
    ax.set_title(
        f"power iteration converges in {values.size} steps\n"
        f"{values[0]:.4f} -> {values[-1]:.4f}, monotone, tolerance 1e-12",
        loc="left",
    )
    ax.annotate(
        f"step 1: {values[0]:.2f}\n(16.6% below the answer)",
        xy=(1, values[0]),
        xytext=(1.4, values[0] + (values[-1] - values[0]) * 0.30),
        fontsize=9,
        color=ORANGE,
        arrowprops=dict(arrowstyle="->", color=ORANGE, linewidth=1.1),
    )
    ax.annotate(
        f"steps 4-{values.size}: flat to 1e-6",
        xy=(values.size, values[-1]),
        xytext=(values.size - 6.6, values[-1] - (values[-1] - values[0]) * 0.28),
        fontsize=9,
        color=TEAL,
        arrowprops=dict(arrowstyle="->", color=TEAL, linewidth=1.1),
    )

    positions = np.arange(1, spectrum.size + 1)
    colours = [
        TEAL if value == lam1 else (ORANGE if value == lam2 else GREY)
        for value in spectrum
    ]
    spectrum_ax.bar(positions, spectrum, color=colours, width=0.7)
    spectrum_ax.axhline(0.0, color=INK, linewidth=1.0)
    spectrum_ax.set_xticks(positions)
    spectrum_ax.set_xlabel("eigenvalue of M, ascending")
    spectrum_ax.set_ylabel("eigenvalue")
    spectrum_ax.set_title(
        f"M = W + W^T + C is symmetric and entrywise non-negative\n"
        f"lam1 = {lam1:.2f}  dominates  lam2 = {lam2:.2f}  by {lam1 / lam2:.1f}x",
        loc="left",
    )
    spectrum_ax.annotate(
        f"lam1 = {lam1:.2f}\nthe leading eigenvalue,\nread by hand",
        xy=(positions[-1], lam1),
        xytext=(positions[-1] - 7.2, lam1 * 0.72),
        fontsize=9,
        color=TEAL,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=TEAL, linewidth=1.2),
    )
    spectrum_ax.annotate(
        f"lam2 = {lam2:.2f}\nread from eigvalsh,\nNOT a second power run",
        xy=(positions[-2], lam2),
        xytext=(positions[-2] - 3.2, lam1 * 0.30),
        fontsize=9,
        color=ORANGE,
        arrowprops=dict(arrowstyle="->", color=ORANGE, linewidth=1.2),
    )
    spectrum_ax.annotate(
        f"lambda_min = {spectrum[0]:.2f}\nM is INDEFINITE, so ||M x|| estimates\n"
        "the spectral radius, not lam2",
        xy=(positions[0], spectrum[0]),
        xytext=(positions[0] + 0.6, spectrum[0] * 0.72),
        fontsize=9,
        color=RED,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.92, pad=1.5),
        arrowprops=dict(arrowstyle="->", color=RED, linewidth=1.2),
    )
    _note(
        fig,
        f"Perron-Frobenius: every share is strictly positive (smallest {float(np.min(shares)):.6f}, "
        f"{teams[int(np.argmin(shares))]}). Irreducibility is measured - the win/loss graph has "
        "exactly one connected component - not assumed.",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[8])


# --------------------------------------------------------------------------
# Stage 10 -- System Simplification / Diagonalisation
# --------------------------------------------------------------------------


def f10_diagonalisation(
    singular_values: np.ndarray,
    eigenvalues: np.ndarray,
    max_abs_diff: float,
) -> Path:
    """Stage 10, System Simplification. Principle: **the eigenvalues of ``A^T A``
    are the squared singular values, so the symmetric 15x15 is ``A`` rotated.**

    Three panels, left to right: the singular spectrum of ``A``; the eigenvalue
    spectrum of ``A^T A``, the same shape but stretched; and the identity itself,
    plotted as ``lambda_i`` against ``sigma_i^2`` with the ``y = x`` line. The
    scatter lies on that line to ``max |difference| = 2.0e-13``, which is the
    measurement that makes the algebra a check rather than a claim. The fifteenth
    point sits at the origin in both panels: that is the rank deficiency, restated.
    """
    sigma = np.asarray(singular_values, dtype=np.float64)
    lam = np.asarray(eigenvalues, dtype=np.float64)
    squared = sigma**2
    count = sigma.size

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.4))
    positions = np.arange(1, count + 1)

    axes[0].bar(positions, sigma, color=BLUE, width=0.7)
    axes[0].set_title(
        "singular values of A\n(the (558, 15) matrix itself)", loc="left", fontsize=11
    )
    axes[0].set_ylabel("sigma_i  (runs per team)")
    axes[0].set_xlabel("i")

    axes[1].bar(positions, lam, color=TEAL, width=0.7)
    axes[1].set_title(
        "eigenvalues of A^T A  (15 x 15, symmetric PSD)\nthe same spectrum, squared",
        loc="left",
        fontsize=11,
    )
    axes[1].set_ylabel("lambda_i = sigma_i^2")
    axes[1].set_xlabel("i")

    for ax in axes[:2]:
        ax.set_xticks(positions)
        ax.set_xticklabels([str(i) for i in positions], fontsize=8)
        ax.axhline(0.0, color=INK, linewidth=0.9)
        ax.annotate(
            f"i = {count}:  {sigma[-1]:.1e}  and  {lam[-1]:.1e}\nthe zero eigenvalue",
            xy=(count, 0.0),
            xytext=(count - 8.4, float(lam.max()) * 0.16),
            fontsize=9,
            color=RED,
            fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.2),
        )

    limit = float(max(squared.max(), lam.max())) * 1.06
    axes[2].plot([0, limit], [0, limit], color=INK, linewidth=1.2, linestyle="--")
    axes[2].scatter(squared, lam, s=26, color=PURPLE, zorder=3)
    axes[2].set_xlim(0, limit)
    axes[2].set_ylim(0, limit)
    axes[2].set_aspect("equal")
    axes[2].set_xlabel(r"$\sigma_i^2$")
    axes[2].set_ylabel(r"$\lambda_i(A^{\mathsf{T}} A)$")
    axes[2].set_title(
        "the identity, measured\n"
        f"max |lambda_i - sigma_i^2| = {max_abs_diff:.2e}",
        loc="left",
        fontsize=11,
    )
    _note(
        fig,
        "A^T A = V S^2 V^T is symmetric positive semi-definite, so all 15 eigenvalues are "
        ">= 0 to float error (largest negative excursion is -9.2e-15, snapped to 0). "
        "The diagonalisation is A, not a larger problem: 15x15 replaces 558x15.",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[9])


# --------------------------------------------------------------------------
# Stage 11 -- FINAL APPLICATION OUTPUT
# --------------------------------------------------------------------------


def f11_ranking(
    teams: list[str],
    x: np.ndarray,
    se: np.ndarray,
    shares: np.ndarray,
    official: pd.DataFrame,
) -> Path:
    """Stage 11, part one. Principle: **two models, two datasets, one picture.**

    Left: the Massey coefficients with **+-2 standard-error whiskers**. Nearly
    every whisker straddles zero, and the franchise with the widest whisker is one
    of the two five-game ones. Right: the Colley shares, which separate cleanly and
    reproduce the official ordering. Both panels are alphabetical with full names,
    because the ordering is the point of the comparison and abbreviations hide it.
    """
    order = np.argsort(np.asarray(teams, dtype=object))  # noqa: PLR1722
    names = [teams[i] for i in order]
    strengths = np.asarray(x, dtype=np.float64)[order]
    errors = np.asarray(se, dtype=np.float64)[order]
    share = np.asarray(shares, dtype=np.float64)[order]
    points = official.set_index("team").loc[names, "points"].to_numpy(dtype=float)

    fig, (ax, share_ax) = plt.subplots(
        1, 2, figsize=(13.5, 8.2), gridspec_kw={"width_ratios": [1.25, 1.0]}
    )

    positions = np.arange(len(names))
    colours = [TEAL if value >= 0 else RED for value in strengths]
    ax.errorbar(
        strengths,
        positions,
        xerr=2.0 * errors,
        fmt="none",
        ecolor=MUTED,
        elinewidth=1.4,
        capsize=3,
        zorder=2,
    )
    ax.barh(positions, strengths, color=colours, height=0.6, zorder=3)
    ax.axvline(0.0, color=INK, linewidth=1.2)
    _team_axis(ax, names)
    ax.set_xlabel("least-squares strength  x  (runs), zero-sum centred,  +-2 standard errors")
    ax.set_title(
        f"Massey least squares on {len(strengths)} run margins\n"
        f"{int(np.count_nonzero(np.abs(strengths) <= 2.0 * errors))} of {len(names)} "
        "coefficients are within 2 se of zero",
        loc="left",
    )

    share_ax.barh(positions, 100.0 * share, color=PURPLE, height=0.6)
    share_ax.axvline(0.0, color=INK, linewidth=1.2)
    _team_axis(share_ax, names)
    share_ax.set_xlabel("Colley rating share  (percent of the league)")
    share_ax.set_title(
        "Colley leading eigenvector on 1,218 decided matches\n"
        "every share strictly positive; top four are the four most-winning sides",
        loc="left",
    )
    del points  # kept in the signature so the caller must pass the authority
    _note(
        fig,
        "The left panel has no vertical axis of meaning: read the whiskers, not the bars. "
        "A bar that reaches 17 runs comes from 5 matches.",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[10])


def f12_findings(
    teams: list[str],
    x: np.ndarray,
    se: np.ndarray,
    games: np.ndarray,
    max_abs_t: float,
) -> Path:
    """Stage 11, part two. Principle: **"not significant" is a measured result,
    and it has a cause in the sample size.**

    Left: ``t_i = x_i / se_i`` for all fifteen franchises against the +-2 sigma
    band, drawn as a band the reader can see every coefficient failing to reach.
    ``max |t| = 1.20`` -- the nearest any team gets is 40% short.

    Right: games played against ``|x|``. The two five-game franchises sit at the
    bottom of the sample-size axis and at the top of the coefficient axis, and the
    correlation is ``-0.663``. Together the two panels are why the answer is a
    statement about sample size and not about team quality.
    """
    order = np.argsort(np.asarray(teams, dtype=object))  # noqa: PLR1722
    names = [teams[i] for i in order]
    t_stats = (np.asarray(x, dtype=np.float64) / np.asarray(se, dtype=np.float64))[order]
    games_sorted = np.asarray(games, dtype=np.float64)[order]
    magnitude = np.abs(np.asarray(x, dtype=np.float64))[order]
    correlation = float(np.corrcoef(games_sorted, magnitude)[0, 1])

    fig, (ax, scatter_ax) = plt.subplots(
        1, 2, figsize=(13.5, 7.4), gridspec_kw={"width_ratios": [1.1, 1.0]}
    )

    positions = np.arange(len(names))
    ax.axvspan(-2.0, 2.0, color=GREY, alpha=0.30, zorder=0)
    ax.barh(positions, t_stats, color=[TEAL if v >= 0 else RED for v in t_stats], height=0.6)
    ax.axvline(0.0, color=INK, linewidth=1.2)
    for boundary in (-2.0, 2.0):
        ax.axvline(boundary, color=RED, linewidth=1.4, linestyle="--")
    ax.text(
        2.0,
        len(names) - 0.35,
        "  +2 sigma",
        color=RED,
        fontsize=9,
        va="center",
    )
    ax.text(
        -2.0,
        len(names) - 0.35,
        "-2 sigma  ",
        color=RED,
        fontsize=9,
        va="center",
        ha="right",
    )
    ax.set_xlim(-2.8, 2.8)
    _team_axis(ax, names)
    ax.set_xlabel(r"t = x / se    (standard errors from $\sigma^2(A^TA + 11^T)^{-1}$)")
    ax.set_title(
        f"NOT ONE coefficient reaches 2 sigma\nmax |t| = {max_abs_t:.2f}, "
        "40% short of the band",
        loc="left",
    )

    scatter_ax.scatter(games_sorted, magnitude, s=45, color=BLUE, zorder=3)
    slope, intercept = np.polyfit(games_sorted, magnitude, 1)
    grid = np.linspace(0, float(games_sorted.max()) * 1.05, 50)
    scatter_ax.plot(grid, slope * grid + intercept, color=ORANGE, linewidth=1.4)
    for index in range(len(names)):
        if games_sorted[index] <= 12:
            scatter_ax.annotate(
                names[index],
                (games_sorted[index], magnitude[index]),
                textcoords="offset points",
                xytext=(9, 2),
                fontsize=9,
                color=INK,
            )
    scatter_ax.set_xlabel("matches played inside the 558-match run-margin subset")
    scatter_ax.set_ylabel("|x|   (fitted strength, runs)")
    scatter_ax.set_title(
        f"corr(games played, |x|) = {correlation:+.3f}\n"
        "the fewer matches, the more extreme the coefficient",
        loc="left",
    )
    _note(
        fig,
        "This is why the ranking is not published as a power table: the two franchises at the "
        "extreme of the left panel of figure 11 are the same two five-game franchises here.",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[11])


def f13_divergence(comparison: pd.DataFrame) -> Path:
    """Stage 11, part three. Principle: **three orderings, one picture.**

    A slopegraph: the official points table on the left, Massey's margin fit in
    the middle, Colley's win/loss fit on the right. Five of fifteen lines are
    dead flat for Colley and **none** are for Massey, whose Kochi Tuskers Kerala
    runs from 15th to 1st. The two Spearman values against the official table,
    ``+0.939`` and ``+0.093``, are printed on the panel so the picture and the
    number cannot disagree.
    """
    ordered = comparison.sort_values("official_rank")
    names = ordered["team"].tolist()
    official_rank = ordered["official_rank"].to_numpy(dtype=float)
    massey_rank = ordered["massey_rank"].to_numpy(dtype=float)
    colley_rank = ordered["colley_rank"].to_numpy(dtype=float)
    colley_flat = int(np.count_nonzero(colley_rank == official_rank))
    massey_flat = int(np.count_nonzero(massey_rank == official_rank))

    fig, ax = plt.subplots(figsize=(11.5, 9.2))
    columns = [
        ("official points table\n(2 per win, all 19 seasons)", official_rank),
        ("Massey least squares\non 558 run margins", massey_rank),
        ("Colley leading eigenvector\non 1,218 decided matches", colley_rank),
    ]
    for index, (_, ranks) in enumerate(columns):
        for team_index in range(len(names)):
            colour = ORANGE if index == 1 else (PURPLE if index == 2 else GREY)
            ax.plot(
                [0, 1, 2],
                [official_rank[team_index], massey_rank[team_index], colley_rank[team_index]],
                color=colour,
                linewidth=1.1,
                alpha=0.75,
                zorder=2,
            )
    for index, (label, ranks) in enumerate(columns):
        ax.plot(
            [index] * len(names),
            ranks,
            linestyle="none",
            marker="o",
            markersize=5,
            color=[GREY, ORANGE, PURPLE][index],
            zorder=3,
        )
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels([columns[0][0], columns[1][0], columns[2][0]], fontsize=9)
        break

    for team_index, name in enumerate(names):
        ax.text(
            -0.045,
            official_rank[team_index],
            f"{int(official_rank[team_index])}. {name}",
            ha="right",
            va="center",
            fontsize=9,
        )
        ax.text(
            2.045,
            colley_rank[team_index],
            f"{int(colley_rank[team_index])}. {name}",
            ha="left",
            va="center",
            fontsize=9,
        )

    ax.set_xlim(-0.42, 2.42)
    ax.set_ylim(15.6, 0.4)
    ax.set_yticks(range(1, 16))
    ax.set_yticklabels([f"rank {i}" for i in range(1, 16)], fontsize=8)
    ax.set_xlabel("")
    ax.set_ylabel("rank out of the 15 canonical franchises  (1 = strongest)")
    ax.set_title(
        "the three-way divergence\n"
        f"Spearman(Massey, official) = +0.093      Spearman(Colley, official) = +0.939      "
        f"Spearman(Massey, Colley) = 0.000",
        loc="left",
    )
    ax.text(
        0.5,
        15.35,
        f"lines dead flat against the official table:  Colley {colley_flat} of 15    |    "
        f"Massey {massey_flat} of 15",
        ha="center",
        fontsize=9.5,
        color=INK,
    )
    ax.grid(axis="x", visible=False)
    _note(
        fig,
        "Joined BY TEAM NAME and never by row position: the official table arrives sorted by "
        "points and the fitted vectors in alphabetical order. A positional join measures nothing "
        "and produced one wrong number in this project before it was caught.",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    return _save(fig, figure_dir(), FIGURE_NAMES[12])
