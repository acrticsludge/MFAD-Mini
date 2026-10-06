"""Design-matrix and Colley-matrix tests.

These pin the two linear objects the whole project stands on:

* ``(A, b)`` — the Massey design matrix. ``A`` is ``(558, 15)``: one row per
  match that carries a **run** margin, one column per canonical franchise. The
  558 is not a modelling choice, it is what the data allows — the other 660
  matches carry a wicket margin and no run figure at all, and manufacturing a
  run equivalent for them was refused on integrity grounds.
* ``(W, C, M)`` — the Colley matrices over all **1,218** matches that have a
  winner. Two models, two datasets, and their divergence is the finding.

Row order of ``A`` is the committed CSV's row order, filtered to the run-margin
subset. Every figure asserted here was measured 2026-10-04.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from iplranking.data import (
    colley_matrices,
    design_matrix,
    games_played,
    load_matches,
    official_table,
    teams,
)

# --- The measured figures, pinned -----------------------------------------
EXPECTED_DESIGN_SHAPE = (558, 15)
EXPECTED_WINNER_MATCHES = 1218
EXPECTED_TOTAL_POINTS = 2436
EXPECTED_GAMES_TOTAL = 1116
EXPECTED_TABLE_ROWS = 15


@pytest.fixture(scope="module")
def A_b() -> tuple[np.ndarray, np.ndarray, list[str]]:
    return design_matrix()


@pytest.fixture(scope="module")
def A(A_b: tuple[np.ndarray, np.ndarray, list[str]]) -> np.ndarray:
    return A_b[0]


@pytest.fixture(scope="module")
def b(A_b: tuple[np.ndarray, np.ndarray, list[str]]) -> np.ndarray:
    return A_b[1]


@pytest.fixture(scope="module")
def WCM() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return colley_matrices()


# --------------------------------------------------------------------------
# Shape and alphabet
# --------------------------------------------------------------------------


def test_teams_are_fifteen_and_alphabetically_sorted() -> None:
    """n = 15. Order is alphabetical so every downstream index is stable."""
    names = teams()
    assert len(names) == EXPECTED_TABLE_ROWS
    assert names == sorted(names)
    assert len(set(names)) == len(names)


def test_design_matrix_shape(A: np.ndarray) -> None:
    assert A.shape == EXPECTED_DESIGN_SHAPE


def test_design_matrix_is_float(A: np.ndarray) -> None:
    assert A.dtype == np.float64


def test_b_matches_the_row_count(b: np.ndarray) -> None:
    assert b.shape == (EXPECTED_DESIGN_SHAPE[0],)


def test_column_labels_line_up_with_rows(A_b) -> None:
    """The third return value is the column order, matching A's columns."""
    A, b, names = A_b
    assert len(names) == A.shape[1]
    assert len(b) == A.shape[0]


# --------------------------------------------------------------------------
# The +-1 convention
# --------------------------------------------------------------------------


def test_design_matrix_entries_are_plus_or_minus_one(A: np.ndarray) -> None:
    """A is a {0, +1, -1} incidence matrix whose **nonzero** entries are +-1.

    The dispatch for this slice reads "A values in {-1, +1}". Taken literally
    that assertion is unachievable, and not merely unachievable-by-us: `A` has
    one column per franchise (15) and one row per match, of which only two teams
    play, so 13 of every 15 entries are necessarily 0. The definition two
    sections earlier — "+1 if team j won, -1 if it lost" — pins the *nonzero*
    entries; the zeros follow from 15 teams and 2 participants. So the claim
    tested here is the one the dispatch means: **no nonzero entry is anything
    other than +-1**, and the sparsity is pinned too, which the original
    assertion could not even express. Both values must occur, so the test cannot
    pass on a degenerate constant matrix.
    """
    nonzero = A[A != 0.0]
    assert nonzero.size > 0
    assert set(np.unique(nonzero).tolist()) == {-1.0, 1.0}
    assert set(np.unique(A).tolist()) == {-1.0, 0.0, 1.0}
    # 15 franchises, 2 participants: exactly 13 zeros and 2 nonzeros per row.
    n_teams = A.shape[1]
    assert n_teams == EXPECTED_DESIGN_SHAPE[1]
    assert np.all((A != 0.0).sum(axis=1) == 2)
    assert np.all((A == 0.0).sum(axis=1) == n_teams - 2)
    assert int((A != 0.0).sum()) == 2 * EXPECTED_DESIGN_SHAPE[0]


def test_every_row_sums_to_zero(A: np.ndarray) -> None:
    """Row sum 0: a match contributes +1 to the winner and -1 to the loser.

    This is also the shape of the system's null direction — adding a constant to
    every team strength changes no predicted margin (AGENTS.md section 3).
    """
    assert np.allclose(A.sum(axis=1), 0.0)
    assert np.abs(A.sum(axis=1)).max() == 0.0


def test_every_row_has_exactly_one_winner_and_one_loser(A: np.ndarray) -> None:
    assert np.all((A == 1.0).sum(axis=1) == 1)
    assert np.all((A == -1.0).sum(axis=1) == 1)


def test_no_row_is_all_zero(A: np.ndarray) -> None:
    """Guards the one real failure mode: two raw names canonicalising to the
    same franchise would leave an all-zero row and a zero margin prediction."""
    assert np.all(np.abs(A).sum(axis=1) > 0)


# --------------------------------------------------------------------------
# The right-hand side: signed run margins
# --------------------------------------------------------------------------


def test_b_has_no_zero_entries(b: np.ndarray) -> None:
    """A run margin of 0 is legal in principle; on this snapshot none occurs.

    Measured: the 558 run margins span 1 to 146 runs. If this assertion ever
    fails the cause is upstream — a missing margin coerced to 0, not cricket.
    """
    assert not (b == 0).any()
    assert np.count_nonzero(b) == len(b)


def test_b_never_carries_a_missing_margin(b: np.ndarray) -> None:
    """The wicket-only matches contribute no NaN to the right-hand side."""
    assert np.isfinite(b).all()


def test_b_magnitudes_match_margin_runs_exactly() -> None:
    """|b| is the unsigned margin, row for row, in CSV order."""
    frame = load_matches()
    run_rows = frame[frame["margin_runs"].notna() & frame["winner"].notna()]
    assert len(run_rows) == EXPECTED_DESIGN_SHAPE[0]
    _, b, _ = design_matrix()
    assert np.array_equal(np.abs(b), run_rows["margin_runs"].to_numpy(dtype=float))


def test_b_uses_only_run_margin_rows_not_wicket_rows() -> None:
    """The 660 wicket-only matches must not reach A or b at all."""
    frame = load_matches()
    _, b, names = design_matrix()
    assert len(b) == EXPECTED_DESIGN_SHAPE[0]
    assert len(names) == EXPECTED_TABLE_ROWS
    # 558 + 660 + 25 = 1243: the three populations partition the snapshot.
    assert 558 + 660 + 25 == len(frame)


# --------------------------------------------------------------------------
# Sign convention, hand-checked
# --------------------------------------------------------------------------


def design_row_index(match_id: str) -> int:
    """Row of the design matrix holding ``match_id``.

    ``A`` and ``b`` have one row per *run-margin* match, so their row index is
    the match's position among the run-margin rows of the committed CSV — **not**
    its CSV row number. The two diverge as soon as a wicket-only match appears,
    which happens at CSV row 2. Each test below therefore states both, so a
    change in either ordering is visible rather than silent.
    """
    frame = load_matches()
    run_rows = frame[frame["margin_runs"].notna() & frame["winner"].notna()]
    hits = np.flatnonzero(run_rows["match_id"].to_numpy() == match_id)
    assert hits.size == 1, f"{match_id} is not a unique run-margin row"
    return int(hits[0])


def test_sign_convention_when_team2_won() -> None:
    """Design row 1 (CSV row 1): Chennai beat Kings XI Punjab by 33 runs.

    `team2` won, so b is **-33**: the sign is the loser's minus the winner's.
    Read back from ``ipl_json/335983.json``, where `info.teams` is
    ``['Kings XI Punjab', 'Chennai Super Kings']`` and `info.outcome.winner` is
    ``'Chennai Super Kings'`` by 33 runs.

    This is the row that catches a flipped convention, because the winner is the
    team named second in the fixture.
    """
    frame = load_matches()
    row = frame.iloc[1]
    assert row["match_id"] == "335983"
    assert row["canonical_team1"] == "Punjab Kings"
    assert row["canonical_team2"] == "Chennai Super Kings"
    assert row["winner"] == "Chennai Super Kings"
    assert int(row["margin_runs"]) == 33

    i = design_row_index("335983")
    assert i == 1

    A, b, names = design_matrix()
    assert b[i] == -33.0
    assert A[i, names.index("Chennai Super Kings")] == 1.0
    assert A[i, names.index("Punjab Kings")] == -1.0


def test_sign_convention_when_team1_won() -> None:
    """Design row 2 (CSV row **7**): Chennai Super Kings beat Mumbai by 6 runs.

    `team1` won, so b is **+6**. Read back from ``ipl_json/335989.json``, where
    `info.teams` is ``['Chennai Super Kings', 'Mumbai Indians']`` and
    `info.outcome` is ``{'by': {'runs': 6}, 'winner': 'Chennai Super Kings'}``.

    Note the row indices differ: CSV rows 2 to 6 are wicket-only and never reach
    the design matrix, so this match is CSV row 7 but design row 2.
    """
    frame = load_matches()
    row = frame.iloc[7]
    assert row["match_id"] == "335989"
    assert row["team1"] == "Chennai Super Kings"
    assert row["team2"] == "Mumbai Indians"
    assert row["winner"] == "Chennai Super Kings"
    assert int(row["margin_runs"]) == 6

    i = design_row_index("335989")
    assert i == 2

    A, b, names = design_matrix()
    assert b[i] == 6.0
    assert A[i, names.index("Chennai Super Kings")] == 1.0
    assert A[i, names.index("Mumbai Indians")] == -1.0


def test_sign_convention_uses_canonicalised_teams_on_both_sides() -> None:
    """Design row 3 (CSV row 9): the winner is recorded under a *pre-rename* name.

    ``ipl_json/335991.json`` lists ``['Kings XI Punjab', 'Mumbai Indians']`` with
    an outcome winner of ``'Kings XI Punjab'``, but the design matrix indexes the
    canonical column ``'Punjab Kings'``. So the winner string must be
    canonicalised before it can be matched to a column, and the ``+1`` must land
    under ``'Punjab Kings'`` — there is no ``'Kings XI Punjab'`` column to land
    in.

    This is the row that catches a loader which compares the raw winner against
    canonical team names, and which would therefore either raise or fall through
    to the wrong sign.
    """
    frame = load_matches()
    row = frame.iloc[9]
    assert row["match_id"] == "335991"
    assert row["team1"] == "Kings XI Punjab"          # raw, pre-rename
    assert row["canonical_team1"] == "Punjab Kings"   # canonical
    assert row["winner"] == "Kings XI Punjab"          # raw, pre-rename
    assert int(row["margin_runs"]) == 66

    i = design_row_index("335991")
    assert i == 3

    A, b, names = design_matrix()
    assert "Kings XI Punjab" not in names
    assert b[i] == 66.0
    assert A[i, names.index("Punjab Kings")] == 1.0
    assert A[i, names.index("Mumbai Indians")] == -1.0


def test_row_order_is_the_csvs_row_order() -> None:
    """Row i of A is the i-th run-margin match in the committed CSV, not a
    re-sorted or re-shuffled order."""
    frame = load_matches()
    run_rows = frame[frame["margin_runs"].notna() & frame["winner"].notna()]
    A, b, names = design_matrix()
    for i in (0, 1, 2, 100, 557):
        row = run_rows.iloc[i]
        winner = str(row["winner"])
        if winner == row["team1"] or winner == row["canonical_team1"]:
            assert b[i] == float(row["margin_runs"])
        else:
            assert b[i] == -float(row["margin_runs"])


# --------------------------------------------------------------------------
# Games played in the 558 subset
# --------------------------------------------------------------------------


def test_games_played_sums_to_twice_the_run_margin_matches() -> None:
    """Each of the 558 matches contributes one game to each of two teams."""
    games = games_played()
    assert games.shape == (EXPECTED_TABLE_ROWS,)
    assert int(games.sum()) == EXPECTED_GAMES_TOTAL
    assert EXPECTED_GAMES_TOTAL == 2 * EXPECTED_DESIGN_SHAPE[0]


def test_games_played_is_nonzero_for_every_team() -> None:
    """Every franchise appears in the run-margin subset, so no coefficient is
    undefined and no team can be silently dropped."""
    assert (games_played() > 0).all()


def test_games_played_agrees_with_the_design_matrix() -> None:
    """Games per team is exactly the row-sum of |A| — one nonzero per game."""
    A, _, names = design_matrix()
    games = games_played()
    assert np.array_equal(np.abs(A).sum(axis=0), games.astype(float))
    assert len(names) == len(games)


# --------------------------------------------------------------------------
# Colley matrices over all 1,218 winner matches
# --------------------------------------------------------------------------


def test_colley_shapes(WCM) -> None:
    W, C, M = WCM
    assert W.shape == (EXPECTED_TABLE_ROWS, EXPECTED_TABLE_ROWS)
    assert C.shape == (EXPECTED_TABLE_ROWS, EXPECTED_TABLE_ROWS)
    assert M.shape == (EXPECTED_TABLE_ROWS, EXPECTED_TABLE_ROWS)


def test_W_entries_sum_to_the_winner_match_count(WCM) -> None:
    """Every match with a winner contributes exactly one directed win."""
    W, _, _ = WCM
    assert W.sum() == EXPECTED_WINNER_MATCHES


def test_W_has_zero_diagonal(WCM) -> None:
    """A team never plays itself, so W[i, i] must be 0."""
    W, _, _ = WCM
    assert np.all(np.diag(W) == 0)


def test_C_is_symmetric_with_zero_diagonal(WCM) -> None:
    """Games played between i and j does not depend on the order."""
    _, C, _ = WCM
    assert np.array_equal(C, C.T)
    assert np.all(np.diag(C) == 0)


def test_C_diagonal_free_games_sum_to_twice_the_winner_matches(WCM) -> None:
    """Each winner match contributes 1 to C[i, j] and 1 to C[j, i]."""
    _, C, _ = WCM
    assert C.sum() == 2 * EXPECTED_WINNER_MATCHES


def test_M_is_the_colley_matrix(WCM) -> None:
    """M = W + W.T + C, the rating-shift matrix."""
    W, C, M = WCM
    assert np.array_equal(M, W + W.T + C)


def test_M_is_entrywise_non_negative(WCM) -> None:
    """A negative entry would mean the rating update is not a convex
    combination, and the Colley fixed point would not be one."""
    _, _, M = WCM
    assert (M >= 0).all()


def test_M_is_symmetric(WCM) -> None:
    """M is symmetric because M = W + W.T + C and C is symmetric. Symmetry is
    what makes the eigenvector well defined and real."""
    _, _, M = WCM
    assert np.allclose(M, M.T)


def test_colley_uses_the_winner_matches_not_the_run_margin_subset(WCM) -> None:
    """The two models run on deliberately different datasets.

    Colley uses win/loss, which every winner match has, so it sees 1,218 where
    Massey sees 558. This is the project's central constraint, asserted.
    """
    _, C, _ = WCM
    assert C.sum() // 2 == EXPECTED_WINNER_MATCHES
    assert EXPECTED_WINNER_MATCHES > EXPECTED_DESIGN_SHAPE[0]


# --------------------------------------------------------------------------
# Official table — the all-time comparison
# --------------------------------------------------------------------------


def test_official_table_columns() -> None:
    table = official_table()
    assert list(table.columns) == ["team", "wins", "points"]


def test_official_table_has_one_row_per_canonical_team() -> None:
    assert len(official_table()) == EXPECTED_TABLE_ROWS


def test_official_table_points_sum_to_twice_the_winner_matches() -> None:
    """2 points per win over all 19 seasons, so 2 x 1218 = 2436."""
    table = official_table()
    assert int(table["points"].sum()) == EXPECTED_TOTAL_POINTS
    assert EXPECTED_TOTAL_POINTS == 2 * EXPECTED_WINNER_MATCHES


def test_official_table_points_are_twice_wins() -> None:
    table = official_table()
    assert (table["points"] == 2 * table["wins"]).all()


def test_official_table_wins_sum_to_the_winner_match_count() -> None:
    """Each match with a winner is a win for exactly one team."""
    assert int(official_table()["wins"].sum()) == EXPECTED_WINNER_MATCHES


def test_official_table_is_sorted_by_points_then_team() -> None:
    """Points descending, then team name ascending. A total order, so the table
    is byte-stable across runs."""
    table = official_table()
    keys = list(zip(-table["points"].to_numpy(), table["team"].to_numpy()))
    assert keys == sorted(keys)


def test_official_table_teams_match_the_design_matrix_columns() -> None:
    table = official_table()
    _, _, names = design_matrix()
    assert set(table["team"]) == set(names)


def test_official_table_excludes_no_winner_matches() -> None:
    """Ties and abandonments have no winner and so award no points.

    This is the exclusion the demo states out loud: 25 of 1,243 matches
    contribute nothing to the comparison column.
    """
    frame = load_matches()
    table = official_table()
    excluded = int(frame["winner"].isna().sum())
    assert excluded == 25
    assert int(table["wins"].sum()) + excluded == len(frame)


# --------------------------------------------------------------------------
# Assembled systems
# --------------------------------------------------------------------------


def test_build_systems_returns_one_consistent_bundle() -> None:
    from iplranking.data import build_systems

    systems = build_systems()
    assert systems.matches.shape == (1243, 12)
    assert systems.A.shape == EXPECTED_DESIGN_SHAPE
    assert systems.b.shape == (EXPECTED_DESIGN_SHAPE[0],)
    assert len(systems.teams) == EXPECTED_TABLE_ROWS
    assert len(systems.games) == EXPECTED_TABLE_ROWS
    assert int(systems.official["points"].sum()) == EXPECTED_TOTAL_POINTS
    assert systems.W.shape == systems.C.shape == systems.M.shape


def test_build_systems_agrees_with_the_individual_accessors() -> None:
    from iplranking.data import build_systems

    systems = build_systems()
    A, b, names = design_matrix()
    W, C, M = colley_matrices()
    assert np.array_equal(systems.A, A)
    assert np.array_equal(systems.b, b)
    assert systems.teams == names
    assert np.array_equal(systems.W, W)
    assert np.array_equal(systems.C, C)
    assert np.array_equal(systems.M, M)
    assert np.array_equal(systems.games, games_played())


def test_load_matches_returns_the_committed_schema() -> None:
    """The exact column set of the committed snapshot, in order."""
    expected = [
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
    ]
    frame = load_matches()
    assert list(frame.columns) == expected
    assert isinstance(frame, pd.DataFrame)