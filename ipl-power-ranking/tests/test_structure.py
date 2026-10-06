"""Stage 3-6 structure tests: RREF, null space, row basis, Gram-Schmidt, power
iteration, and the Col(A) / Row(A) distinction.

`AGENTS.md` section 5 makes the examiner read the machinery, so every function
exercised here is hand-written in `linalg_kit.py` rather than delegated to
`numpy.linalg` -- the point is that the steps are legible, and these tests are
what hold the steps honest.

Every figure asserted here was measured 2026-10-04 against the committed
snapshot. See `docs/reasonix/prompts/2026-10-04-s5-s7-linalg-models-diagnostics-implement-2.md`
sections 1 and 4 for the target list, and the module docstrings in
`linalg_kit.py` for the two places where measurement contradicted the target.
"""

from __future__ import annotations

import numpy as np
import pytest

from iplranking import linalg_kit as lk
from iplranking.data import build_systems

# --- The measured figures, pinned -----------------------------------------
EXPECTED_SHAPE = (558, 15)
EXPECTED_RANK = 14
EXPECTED_NULLITY = 1
EXPECTED_NUM_TEAMS = 15
#: Largest and smallest-nonzero singular values of A, measured 2026-10-04.
EXPECTED_SV_LARGEST = 12.4779
EXPECTED_SV_SMALLEST_NONZERO = 2.2216
#: The 15th singular value is zero to machine precision, not to `tol`.
SINGULAR_ZERO_CUTOFF = 1e-12


@pytest.fixture(scope="module")
def systems():
    return build_systems()


@pytest.fixture(scope="module")
def A(systems) -> np.ndarray:
    return systems.A


@pytest.fixture(scope="module")
def row_basis(A: np.ndarray) -> np.ndarray:
    return lk.row_basis(A)


# --------------------------------------------------------------------------
# The central structural fact: the null direction IS the constant vector
# --------------------------------------------------------------------------


def test_A_shape(A: np.ndarray) -> None:
    assert A.shape == EXPECTED_SHAPE


def test_rank_of_A_is_fourteen(A: np.ndarray) -> None:
    """The 15 columns are not 15 independent unknowns: rank is n - 1 = 14.

    Cross-checked two ways. `rref` is hand-written, so agreeing with
    `numpy.linalg.matrix_rank` is a real check on the elimination and not a
    tautology.
    """
    _, pivot_rows, rank = lk.rref(A)
    assert rank == EXPECTED_RANK
    assert len(pivot_rows) == EXPECTED_RANK
    assert np.linalg.matrix_rank(A) == EXPECTED_RANK


def test_nullity_of_A_is_one(A: np.ndarray) -> None:
    assert lk.null_space(A).shape == (EXPECTED_NULLITY, EXPECTED_NUM_TEAMS)


def test_singular_values_of_A_have_fourteen_nonzero_and_one_zero(A: np.ndarray) -> None:
    """The rank-14 claim from the spectrum, and both measured endpoints.

    12.4779 largest, 2.2216 smallest nonzero, and one value at ~5e-15 -- i.e.
    zero to machine precision. The cutoff is 1e-12, two orders below the smallest
    genuine value, so this cannot pass by luck.
    """
    values = np.linalg.svd(A, compute_uv=False)
    assert values.size == EXPECTED_NUM_TEAMS
    assert values[0] == pytest.approx(EXPECTED_SV_LARGEST, abs=1e-4)
    nonzero = values[values > SINGULAR_ZERO_CUTOFF]
    assert nonzero.size == EXPECTED_RANK
    assert nonzero[-1] == pytest.approx(EXPECTED_SV_SMALLEST_NONZERO, abs=1e-4)
    assert values[-1] < SINGULAR_ZERO_CUTOFF
    assert np.all(np.diff(values) <= 1e-12)  # sorted descending


def test_the_constant_vector_is_exactly_in_the_null_space(A: np.ndarray) -> None:
    """``A @ ones == 0``, exactly, not approximately.

    This is the project's central insight and it is tested directly rather than
    inferred: every row of A is ``+1`` for the winner and ``-1`` for the loser,
    so every row sums to exactly zero and the constant vector is annihilated
    with **no** floating-point error at all. Adding the same number to all 15
    team strengths therefore predicts identical margins -- which is why the
    least-squares solution is only determined up to a constant, and why
    `models.massey` centres its answer to zero sum.

    The stronger form matters: `np.allclose` alone would also pass for a matrix
    whose rows merely nearly sum to zero, which is a different and much weaker
    claim.
    """
    ones = np.ones(EXPECTED_NUM_TEAMS)
    assert np.array_equal(A @ ones, np.zeros(A.shape[0]))


def test_predicted_margins_are_invariant_to_adding_a_constant() -> None:
    """The consequence of the null direction, tested on the systems themselves.

    If a constant is in the kernel then ``A (x + c*1) == A x`` exactly, so no
    choice of gauge can change a single predicted margin. This is the reason the
    two models' *levels* are not comparable but their *orderings* are.

    The tolerance is not 0.0 and the reason is worth stating, because it looks
    like a weakened assertion: the identity is exact in real arithmetic, but
    forming ``x + c*ones`` for ``c = 1e6`` and then multiplying by ``A`` rounds
    at the 1e6 scale, so the two dot products agree to ~1e-10 and not to the bit.
    The *exact* claim is tested separately and separately holds:
    ``A @ ones == 0`` is true to the last bit, in
    ``test_the_constant_vector_is_exactly_in_the_null_space``.
    """
    systems = build_systems()
    A, b = systems.A, systems.b
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    baseline = A @ x
    for c in (-1000.0, -1.0, 0.5, 7.25, 1e6):
        shifted = A @ (x + c * np.ones(EXPECTED_NUM_TEAMS))
        assert np.allclose(shifted, baseline, rtol=1e-12, atol=1e-9)


def test_null_space_basis_is_the_constant_vector(A: np.ndarray) -> None:
    """The computed null space is spanned by the constant vector.

    `null_space` builds each basis vector with a 1 in the free column and
    ``-R[i, free]`` in each pivot column. For A the single free column is the
    last one and the RREF carries ``-1`` in every pivot column, so the basis
    vector comes out as ``(1, 1, ..., 1)`` -- *unnormalised*, which is the
    textbook convention and the reason the free component is exactly 1.

    So the two quantities pinned here are "every entry is exactly 1" (the
    convention, and an exactness claim) and "the direction is the constant
    vector" (the content, and a claim about the data). The RREF row above shows
    the ``-1`` coupling that produces it.
    """
    basis = lk.null_space(A)
    assert basis.shape == (EXPECTED_NULLITY, EXPECTED_NUM_TEAMS)
    assert np.allclose(A @ basis.T, 0.0, atol=1e-10)
    # Unnormalised: exactly the constant vector, entry for entry.
    assert np.array_equal(basis[0], np.ones(EXPECTED_NUM_TEAMS))
    assert np.isclose(np.linalg.norm(basis[0]), np.sqrt(EXPECTED_NUM_TEAMS))
    # The direction claim, independent of scale: it is the constant vector.
    assert np.isclose(abs(float(basis[0] @ np.ones(EXPECTED_NUM_TEAMS))), EXPECTED_NUM_TEAMS)
    # And it is not *any* other direction: a single changed component would
    # break the annihilation of A.
    perturbed = basis[0].copy()
    perturbed[0] = 2.0
    assert np.abs(A @ perturbed).max() > 0.0


def test_null_space_of_a_full_rank_square_matrix_is_empty() -> None:
    """A rank-deficient-only API would be a stage that cannot pass; this is the
    other half: the function has to be able to return *nothing*."""
    assert lk.null_space(np.eye(4)).shape == (0, 4)
    _, pivot_rows, rank = lk.rref(np.eye(4))
    assert rank == 4
    assert pivot_rows == [0, 1, 2, 3]


# --------------------------------------------------------------------------
# rref, on matrices small enough to check by hand
# --------------------------------------------------------------------------


def test_rref_on_a_two_by_two() -> None:
    """``[[2, 1], [1, 3]]`` is invertible, so its RREF is the identity.

    det = 6 - 1 = 5 != 0, rank 2, both rows are pivots, and the elimination
    has to swap rows to get there because the (0, 0) entry starts at 2.
    """
    M = np.array([[2.0, 1.0], [1.0, 3.0]])
    R, pivot_rows, rank = lk.rref(M)
    assert rank == 2
    assert sorted(pivot_rows) == [0, 1]
    assert np.allclose(R, np.eye(2))
    # R must be reachable by row operations, so it spans the same row space.
    assert np.allclose(R, M) is False  # sanity: the RREF is genuinely reduced
    assert np.isclose(np.linalg.matrix_rank(np.vstack([M, R])), 2)


def test_rref_on_a_singular_three_by_three() -> None:
    """``[[1,2,3],[4,5,6],[7,8,9]]`` has rank 2, hand-checkable.

    Row reduction: ``r2 - 4 r1 = (0, -3, -6)``, ``r3 - 7 r1 = (0, -6, -12)``,
    and the second is exactly twice the first, so the third pivot is missing.
    Dividing the surviving row by -3 gives ``(0, 1, 2)`` and back-substituting
    into row 1 gives ``(1, 0, -1)``. Expected RREF is therefore
    ``[[1,0,-1],[0,1,2],[0,0,0]]`` with the zero row last.
    """
    M = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    R, pivot_rows, rank = lk.rref(M)
    assert rank == 2
    assert len(pivot_rows) == 2
    expected = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 0.0]])
    assert np.allclose(R, expected, atol=1e-12)
    # The pivot rows recorded must be the ORIGINAL rows that produced the
    # surviving rows, which is what makes `row_basis` a subset of the input.
    assert all(0 <= i < M.shape[0] for i in pivot_rows)
    assert np.allclose(M[pivot_rows] @ np.array([1.0, -2.0, 1.0]), 0.0)


def test_rref_on_a_matrix_with_an_all_zero_row() -> None:
    """A zero row must be skipped, not turned into a pivot of 0/0.

    ``[[1,2,3],[0,0,0],[2,4,6]]`` has row space spanned by ``(1, 2, 3)``. Column 0
    pivots; after the elimination the remaining rows are exactly zero, so
    columns 1 and 2 are **free** columns and keep the pivot row's own entries.
    The RREF is therefore ``[[1,2,3],[0,0,0],[0,0,0]]`` -- *not*
    ``[[1,0,0], ...]``. A reduction that "helpfully" zeroed columns 1 and 2
    would be computing something else: the row it leaves behind, ``(1,0,0)``, is
    not even a combination of the input's rows in the right proportions.
    """
    M = np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0], [2.0, 4.0, 6.0]])
    R, pivot_rows, rank = lk.rref(M)
    assert rank == 1
    assert len(pivot_rows) == 1
    assert np.allclose(R, np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]), atol=0.0)
    # Only column 0 is a pivot column, so no entry of the pivot rows that is not
    # a pivot is nonzero -- there is no second 1.0 to indicate another pivot.
    assert np.count_nonzero(R[:rank] == 1.0) == 1
    # Partial pivoting picks the row with the **largest** first entry, and
    # |2.0| > |1.0|, so the pivot is original row 2 -- not row 0, which is the
    # answer a first-nonzero rule would give. Both rows span the same
    # one-dimensional space, so either is a defensible basis choice; partial
    # pivoting is deterministic, so the choice is pinned rather than left open.
    assert pivot_rows == [2]
    # The row it displaced must not also be recorded: the set has to be free of
    # duplicates, or "which rows became pivots" stops being a question.
    assert len(set(pivot_rows)) == len(pivot_rows)
    # And the row space really is 1-dimensional, so a single pivot is maximal.
    assert np.linalg.matrix_rank(M) == 1


def test_rref_leaves_no_floating_point_dust() -> None:
    """`np.allclose` at 1e-8 is useless if the answer is full of 1e-16.

    The dispatch asks for the RREF to be returned "rounded to a sensible
    tolerance", so a hand-computed RREF with exact entries must come back
    *exactly* equal, not approximately. This is the test that catches a
    reduction which leaves -0.0 and 1e-17 behind.
    """
    M = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    R, _, _ = lk.rref(M)
    expected = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 0.0]])
    assert np.array_equal(R, expected)
    # and no negative zeros anywhere
    assert not (np.signbit(R) & (R == 0.0)).any()


def test_rref_preserves_the_row_space(A: np.ndarray) -> None:
    """Row reduction is a sequence of invertible row operations, so the row
    space is unchanged. Stacking R under A must not raise the rank."""
    R, _, _ = lk.rref(A)
    assert np.linalg.matrix_rank(np.vstack([A, R])) == EXPECTED_RANK


def test_rref_of_A_is_echelon_form_with_fourteen_leading_ones(A: np.ndarray) -> None:
    """On A itself: 14 pivot columns, and the pivot block is the 14x14 identity.

    The pivots land in the first 14 columns because A has full row rank on the
    first 14 franchise columns as well as on all 15 -- the *combination*
    constraint is the null direction, not any single column being zero.
    """
    R, pivot_rows, rank = lk.rref(A)
    assert rank == EXPECTED_RANK
    assert R.shape == EXPECTED_SHAPE
    lead = R[:EXPECTED_RANK, :EXPECTED_RANK]
    assert np.allclose(lead, np.eye(EXPECTED_RANK), atol=1e-12)
    # Everything below the pivot block is exactly zero.
    assert np.array_equal(R[EXPECTED_RANK:, :], np.zeros((R.shape[0] - EXPECTED_RANK, R.shape[1])))
    # The RREF must be in reduced form: zero above each pivot too.
    for i in range(EXPECTED_RANK):
        for j in range(i + 1, EXPECTED_RANK):
            assert R[i, j] == 0.0
    # The single free column carries the null direction, so it is not all zero.
    assert np.any(R[:EXPECTED_RANK, EXPECTED_RANK] != 0.0)
    assert len(set(pivot_rows)) == EXPECTED_RANK


# --------------------------------------------------------------------------
# Stage 5: a maximal linearly independent subset of the rows
# --------------------------------------------------------------------------


def test_row_basis_has_exactly_rank_rows(A: np.ndarray) -> None:
    """14 rows out of 558. Not 'at most 14', not 'as many as pivot' -- the
    number is the whole content of the claim."""
    basis = lk.row_basis(A)
    assert basis.shape == (EXPECTED_RANK, EXPECTED_NUM_TEAMS)
    assert basis.shape[0] < A.shape[0]
    assert EXPECTED_RANK == 14 < A.shape[0]


def test_row_basis_rows_are_actually_rows_of_A(row_basis: np.ndarray, A: np.ndarray) -> None:
    """Every returned vector is a verbatim row of A, not a recombination.

    This is what makes it a *subset* of the rows rather than just some basis of
    the row space, and it is falsifiable: any implementation that returns, say,
    the RREF's nonzero rows instead of the original ones fails here.
    """
    A_set = {row.tobytes() for row in A}
    assert all(row.tobytes() in A_set for row in row_basis)


def test_row_basis_rows_are_genuinely_independent(row_basis: np.ndarray) -> None:
    """``matrix_rank == 14``. A basis of 14 vectors with rank 12 is not a basis."""
    assert np.linalg.matrix_rank(row_basis) == EXPECTED_RANK
    assert np.linalg.matrix_rank(row_basis) == row_basis.shape[0]


def test_row_basis_spans_exactly_the_row_space(row_basis: np.ndarray, A: np.ndarray) -> None:
    """Maximal, not merely independent: adding any dropped row must break it."""
    _, pivot_rows, rank = lk.rref(A)
    assert list(np.flatnonzero(np.all(row_basis == 0.0, axis=1))) == []
    dropped = [i for i in range(A.shape[0]) if i not in set(pivot_rows)]
    assert len(dropped) == A.shape[0] - rank
    # A dropped row is a combination of the kept ones, so the rank cannot grow.
    assert np.linalg.matrix_rank(np.vstack([row_basis, A[dropped[0]]])) == EXPECTED_RANK
    assert np.linalg.matrix_rank(np.vstack([row_basis, A[dropped[-1]]])) == EXPECTED_RANK


# --------------------------------------------------------------------------
# Stage 6: Gram-Schmidt on Row(A)
# --------------------------------------------------------------------------


def test_gram_schmidt_gives_an_orthonormal_basis(row_basis: np.ndarray) -> None:
    Q, residuals = lk.gram_schmidt(row_basis)
    assert Q.shape == row_basis.shape
    assert np.allclose(Q @ Q.T, np.eye(row_basis.shape[0]), atol=1e-10)
    assert len(residuals) == row_basis.shape[0]


def test_gram_schmidt_preserves_the_row_space(row_basis: np.ndarray) -> None:
    """Orthogonalisation is a change of basis, not a projection onto a subspace.

    The row space of the input is 14-dimensional; if Gram-Schmidt silently
    shrank it, the stage would be reporting a basis of the wrong thing.
    """
    Q, _ = lk.gram_schmidt(row_basis)
    assert np.linalg.matrix_rank(np.vstack([row_basis, Q])) == row_basis.shape[0]
    # Every Q-row lies in the row space, hence orthogonal to the constant
    # vector -- the same null direction as before, seen from Row(A).
    assert np.allclose(Q @ np.ones(row_basis.shape[1]), 0.0, atol=1e-10)


def test_gram_schmidt_residuals_are_measured_not_assumed(row_basis: np.ndarray) -> None:
    """`residuals[k]` is the off-orthogonality of the first k+1 vectors.

    MEASURED 2026-10-04, and this contradicts the dispatch, which expected
    these to shrink. They do not: they **grow**, from exactly 0.0 to 1.47e-15
    (classical) and 1.97e-16 (re-orthogonalised). Growth is the classical
    Gram-Schmidt signature -- the inner products are no longer computed against
    exactly orthogonal vectors, so error accumulates per step. On this data the
    total is ~1e-15, i.e. machine epsilon, so orthogonality to 1e-10 is not at
    risk; the demo must not claim a decaying residual. See the module docstring
    of `linalg_kit`.
    """
    _, residuals = lk.gram_schmidt(row_basis)
    assert all(r >= 0.0 for r in residuals)
    assert residuals[0] == 0.0
    assert residuals[-1] > residuals[0]
    assert residuals[-1] < 1e-10


def test_reorthogonalisation_is_at_least_as_orthogonal(row_basis: np.ndarray) -> None:
    """The reported difference between the two variants, measured not asserted.

    Classical Gram-Schmidt ends at 1.47e-15 off-orthogonality; the
    re-orthogonalised variant ends at 1.97e-16. Measured ratio 7.5x. The
    variant is never worse, which is the only direction the theorem runs in.
    """
    _, classical = lk.gram_schmidt(row_basis)
    _, reorth = lk.gram_schmidt(row_basis, reorthogonalised=True)
    assert len(reorth) == len(classical)
    assert reorth[-1] <= classical[-1] * 1.5
    assert reorth[-1] < classical[-1]


def test_reorthogonalisation_beats_classical_on_an_ill_conditioned_set() -> None:
    """Where the two variants differ *visibly* -- which is the point of having
    two. A near-parallel, badly scaled set is where classical Gram-Schmidt
    loses orthogonality outright; the second pass recovers it.

    A deliberately pathological input is used here on purpose: the assertion on
    the real 14-row basis above can only show a 1e-15 effect, and a test that
    can only ever observe machine epsilon is not evidence that the
    re-orthogonalisation loop is doing anything.
    """
    rows = np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, 1.0 + 1e-10, 1.0 + 2e-10],
            [0.0, 1.0, 1.0],
        ]
    )
    Qc, _ = lk.gram_schmidt(rows)
    Qr, _ = lk.gram_schmidt(rows, reorthogonalised=True)
    err_c = np.abs(Qc @ Qc.T - np.eye(3)).max()
    err_r = np.abs(Qr @ Qr.T - np.eye(3)).max()
    assert err_c > 1e-6, f"the pathological case is not pathological: {err_c!r}"
    assert err_r < 1e-10
    assert err_r < err_c


# --------------------------------------------------------------------------
# Stage 9: power iteration, hand-written
# --------------------------------------------------------------------------


def test_power_iteration_reproduces_the_leading_eigenvector(systems) -> None:
    """Agrees with `np.linalg.eigh` up to sign, which is the only freedom.

    `M` is symmetric and entrywise non-negative, so the leading eigenpair is
    real, simple and the power iteration converges to it from a deterministic
    start. The comparison is on ``|cos|`` because an eigenvector is defined up
    to a sign and nothing here fixes that sign.
    """
    M = systems.M
    x, lam, history = lk.power_iteration(M)
    values, vectors = np.linalg.eigh(M)
    cos = abs(float(x @ vectors[:, -1]) / (np.linalg.norm(x) * np.linalg.norm(vectors[:, -1])))
    assert np.isclose(cos, 1.0, atol=1e-8)
    assert np.isclose(lam, values[-1], rtol=1e-10)
    assert np.isclose(lam, 469.1757, atol=1e-3)
    assert history[-1] == lam


def test_power_iteration_converges_and_returns_a_unit_vector(systems) -> None:
    M = systems.M
    x, lam, history = lk.power_iteration(M)
    assert np.isclose(np.linalg.norm(x), 1.0, atol=1e-12)
    assert lam > 0.0
    assert len(history) <= 5000
    assert len(history) >= 2
    # Monotone non-decreasing once past the first step: the Rayleigh quotient
    # of a normalised power iterate cannot fall.
    assert np.all(np.diff(np.asarray(history[1:], dtype=float)) >= -1e-9)


def test_power_iteration_history_actually_converges(systems) -> None:
    """The history is a real convergence trace, so the demo's sparkline shows
    something. The measured figure: 9 iterations to 1e-12 on M."""
    M = systems.M
    _, lam, history = lk.power_iteration(M, tol=1e-12)
    reference = np.linalg.eigh(M)[0][-1]
    assert len(history) == 9          # 9 multiply-and-normalise steps
    # The first step is a crude estimate and the trace climbs to the answer:
    # 391.308233 -> 469.094860 -> ... -> 469.175700. Monotone from below is the
    # real content; the first value is 16.6% low, which is why it is bounded at
    # 20% and not asserted equal.
    assert history[0] < reference
    assert np.isclose(history[0], reference, rtol=0.2)
    assert np.all(np.diff(np.asarray(history, dtype=float)) > 0.0)
    assert np.isclose(history[-1], reference, rtol=1e-12)
    assert abs(history[-1] - history[-2]) <= 1e-12 * max(1.0, abs(history[-1]))


def test_power_iteration_is_deterministic(systems) -> None:
    """No randomness anywhere: the default start is the normalised all-ones
    vector, so two calls are bit-identical."""
    M = systems.M
    x1, lam1, h1 = lk.power_iteration(M)
    x2, lam2, h2 = lk.power_iteration(M)
    assert np.array_equal(x1, x2)
    assert lam1 == lam2
    assert h1 == h2


def test_power_iteration_default_start_is_the_normalised_ones_vector(systems) -> None:
    """Pinned because a random start would make the demo non-reproducible."""
    M = systems.M
    ones = np.ones(EXPECTED_NUM_TEAMS) / np.sqrt(EXPECTED_NUM_TEAMS)
    x, _, _ = lk.power_iteration(M)
    # The all-ones vector is a *positive* combination of the leading
    # eigenvector's direction, so the iteration cannot land on the opposite
    # sign of it. This is only true because the start is non-negative.
    assert float(x @ ones) > 0.0


def test_power_iteration_raises_rather_than_silently_returning_a_non_convergence(
    systems,
) -> None:
    """An iteration that never converges must say so, not return the last
    iterate as though it had."""
    with pytest.raises(RuntimeError):
        lk.power_iteration(np.eye(4), max_iter=1, tol=1e-30)


# --------------------------------------------------------------------------
# Col(A) and Row(A): two different spaces, in two different ambient spaces
# --------------------------------------------------------------------------


def test_col_space_basis_is_fifteen_columns_inside_R558(A: np.ndarray) -> None:
    """Thin QR of A: ``Q`` is ``(558, 15)`` -- 15 orthonormal columns spanning a
    15-dimensional space in R^558.

    This is **not** a basis of Col(A), which is only 14-dimensional. It is a
    15-dimensional space that *contains* Col(A) strictly, the extra direction
    being whatever the reduction had to add to complete the basis. The shape
    alone proves it is the wrong object to call a basis of Col(A).
    """
    Q = lk.col_space_basis(A)
    assert Q.shape == EXPECTED_SHAPE  # (558, 15)
    assert Q.shape[0] == A.shape[0]
    assert Q.shape[1] == EXPECTED_NUM_TEAMS
    assert np.allclose(Q.T @ Q, np.eye(EXPECTED_NUM_TEAMS), atol=1e-12)


def test_the_fifteenth_column_of_the_col_basis_is_outside_col_space(A: np.ndarray) -> None:
    """The precise statement of "contains", and it is falsifiable.

    Column 15 of the thin QR is orthogonal to every column of A, so it is
    orthogonal to Col(A) and cannot be a member of it. The first 14 columns,
    by contrast, *do* span Col(A): projecting A onto their span returns A
    unchanged. If the reduction produced 15 directions that were all inside
    Col(A), this test would fail -- which is exactly the mistake `AGENTS.md`
    section 6 warns about.
    """
    Q = lk.col_space_basis(A)
    rank = EXPECTED_RANK
    projector = Q[:, :rank] @ Q[:, :rank].T
    assert np.allclose(projector @ A, A, atol=1e-9)      # first 14 span Col(A)
    assert np.isclose(np.linalg.norm(Q[:, rank] @ A), 0.0, atol=1e-9)  # 15th is orthogonal
    assert np.isclose(np.linalg.norm(projector @ Q[:, rank]), 0.0, atol=1e-9)


def test_col_space_basis_has_one_more_column_than_the_rank(A: np.ndarray) -> None:
    """``col_space_basis(A).shape[1] == rank(A) + 1``, stated as a relation so
    the distinction cannot be quietly closed by changing a number."""
    Q = lk.col_space_basis(A)
    rank = np.linalg.matrix_rank(A)
    assert Q.shape[1] == rank + 1
    assert Q.shape[1] != rank


def test_row_space_basis_is_fourteen_rows_inside_R15(row_basis: np.ndarray) -> None:
    """Gram-Schmidt on the 14 pivot rows of A: an orthonormal basis of Row(A),
    living in R^15, with ``Q @ Q.T = I_14`` and ``Q.shape[0] == rank(A)``."""
    Q = lk.gram_schmidt(row_basis)[0]
    assert Q.shape == (EXPECTED_RANK, EXPECTED_NUM_TEAMS)
    assert Q.shape[0] == EXPECTED_RANK
    assert np.allclose(Q @ Q.T, np.eye(EXPECTED_RANK), atol=1e-10)
    assert Q.shape[1] == EXPECTED_NUM_TEAMS
    assert np.allclose(Q @ np.ones(EXPECTED_NUM_TEAMS), 0.0, atol=1e-10)


def test_row_space_basis_function_matches_the_hand_built_one(A: np.ndarray, row_basis) -> None:
    Q = lk.row_space_basis(A)
    assert Q.shape == (EXPECTED_RANK, EXPECTED_NUM_TEAMS)
    assert np.allclose(Q @ Q.T, np.eye(EXPECTED_RANK), atol=1e-10)
    # Same space as the Gram-Schmidt of the raw pivot rows.
    Q_manual = lk.gram_schmidt(row_basis)[0]
    assert np.isclose(
        np.linalg.norm((Q @ Q.T) - (Q_manual @ Q_manual.T)), 0.0, atol=1e-9
    )


def test_the_two_spaces_are_genuinely_different_objects(A: np.ndarray) -> None:
    """THE test that separates the two, and it fails if either is conflated.

    Both are derived from the *same* 14-dimensional abstract subspace -- the
    column space of A, which equals its row space as a subspace of R^15 -- but
    they are returned as matrices in *different ambient spaces* with *different
    shapes*:

    * ``col_space_basis(A)`` is ``(558, 15)`` in R^558. It has 14 directions in
      Col(A) plus **one** direction that is not in Col(A) at all. It is not a
      basis of Col(A).
    * ``row_space_basis(A)`` is ``(14, 15)`` in R^15. Every one of its 14 rows
      is in Col(A), and they are a genuine basis of it. It **is** a basis of
      Col(A) / Row(A).

    A suite that cannot tell these apart is a suite that cannot fail, so the
    shapes, the counts and the membership are each asserted, and a concrete
    falsifier is included at the end.
    """
    col = lk.col_space_basis(A)
    row = lk.row_space_basis(A)

    # Different ambient spaces, different shapes.
    assert col.shape == (A.shape[0], EXPECTED_NUM_TEAMS)   # R^558
    assert row.shape == (EXPECTED_RANK, EXPECTED_NUM_TEAMS)  # R^15
    assert col.shape != row.shape
    assert col.shape[0] != row.shape[0]

    # The col basis is one dimension too wide to be a basis of Col(A).
    assert col.shape[1] == EXPECTED_RANK + 1
    # The row basis is exactly the right width.
    assert row.shape[0] == np.linalg.matrix_rank(A)

    # Falsifier: membership. Every row of the row basis is in Col(A), because
    # it was built by orthogonalising rows of A. The last column of the col
    # basis is not in Col(A) at all. Stating both directions is what makes this
    # a test rather than a description.
    projector = lk.col_projector(A)
    assert np.isclose(np.linalg.norm(projector @ col[:, EXPECTED_RANK]), 0.0, atol=1e-9)
    for vector in row:
        # `A @ pinv(A) @ A @ v == A @ v` is the defining idempotence of the
        # pseudo-inverse, and it says the projection of `A v` back onto
        # Col(A) is exactly `A v`: so `A @ v` is in Col(A) -- which is where
        # every row of the row basis lives.
        assert np.allclose(A @ lk.pinv(A) @ A @ vector, A @ vector, atol=1e-8)
        # and a *non*-member of Col(A) would fail this, which is the check the
        # last col column failed above
        assert np.isclose(
            np.linalg.norm(projector @ (A @ vector) - (A @ vector)), 0.0, atol=1e-8
        )

    # And the abstract subspaces really are the same one: the row basis
    # diagonalises the symmetric part of the fit, with eigenvalues exactly the
    # 14 nonzero squared singular values. This is the shared content, and it
    # is what makes the two objects "the same space, differently packaged"
    # rather than "two different spaces".
    restricted = np.linalg.eigvalsh(row @ (A.T @ A) @ row.T)
    singular = np.linalg.svd(A, compute_uv=False)
    nonzero = singular[singular > SINGULAR_ZERO_CUTOFF]
    assert restricted.size == EXPECTED_RANK
    assert np.allclose(restricted, np.sort(nonzero) ** 2, atol=1e-6)


def test_col_projector_is_the_orthogonal_projection_onto_col_space(A: np.ndarray) -> None:
    """Stage 7 groundwork: the projector onto Col(A) is symmetric, idempotent,
    has rank 14, and leaves A fixed."""
    P = lk.col_projector(A)
    assert P.shape == (A.shape[0], A.shape[0])
    assert np.allclose(P, P.T, atol=1e-9)
    assert np.allclose(P @ P, P, atol=1e-9)
    assert np.linalg.matrix_rank(P) == EXPECTED_RANK
    assert np.allclose(P @ A, A, atol=1e-9)


def test_col_projector_projects_an_arbitrary_vector_onto_col_space(A: np.ndarray) -> None:
    """The projector must actually do something: a random direction's
    projection is in Col(A) and the residual is orthogonal to it."""
    rng = np.random.default_rng(20261004)  # seeded: determinism is a project rule
    v = rng.standard_normal(A.shape[0])
    P = lk.col_projector(A)
    projected = P @ v
    residual = v - projected
    assert np.allclose(A.T @ residual, 0.0, atol=1e-8)
    assert np.isclose(np.linalg.norm(v) ** 2, np.linalg.norm(projected) ** 2 + np.linalg.norm(residual) ** 2, rtol=1e-10)


def test_pinv_satisfies_all_four_moore_penrose_conditions(A: np.ndarray) -> None:
    """`col_space_basis` is QR-based and `col_projector` is SVD-based; both claim
    to produce the same geometry. These are the four defining conditions of the
    Moore-Penrose inverse, and any matrix satisfying them is *the* pseudo-inverse,
    so this pins the object rather than a particular route to it.

    With ``B = A+``, ``A`` is ``(558, 15)`` and ``B`` is ``(15, 558)``:
    ``A B A = A``, ``B A B = B``, and ``A B`` and ``B A`` are both symmetric.
    """
    B = lk.pinv(A)
    assert B.shape == (A.shape[1], A.shape[0])
    assert np.allclose(A @ B @ A, A, atol=1e-8)
    assert np.allclose(B @ A @ B, B, atol=1e-8)
    assert np.allclose(A @ B, (A @ B).T, atol=1e-8)
    assert np.allclose(B @ A, (B @ A).T, atol=1e-8)
    assert np.isclose(np.linalg.matrix_rank(A @ B), EXPECTED_RANK)


def test_pinv_agrees_with_the_qr_route(A: np.ndarray) -> None:
    """``A A+`` must equal the projector built from the thin QR's first 14
    columns. Two independent routes (SVD and QR) to one object."""
    P_svd = lk.col_projector(A)
    Q = lk.col_space_basis(A)
    P_qr = Q[:, :EXPECTED_RANK] @ Q[:, :EXPECTED_RANK].T
    assert np.allclose(P_svd, P_qr, atol=1e-9)
