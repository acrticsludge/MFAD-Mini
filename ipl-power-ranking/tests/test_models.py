"""Model tests: the three least-squares routes, Colley's eigenvector, the SVD
link, the held-out split, and the two variants that are here to be **refuted**.

`AGENTS.md` section 4 is the rule this file exists to enforce: every number is
measured by the code in front of it, never written down in prose and trusted.
Where the dispatch for this module expected something and measurement disagreed,
the measured value is pinned *and the disagreement is pinned*, so neither can be
quietly undone -- see `test_ridge_r_squared_is_not_invariant_contrary_to_the_
inherited_claim` and `test_frequency_balancing_increases_max_abs_x`.

All figures measured 2026-10-04 against the committed snapshot.

How to read the tolerances
--------------------------
Every tolerance here is stated *beside* the measured value, and is one or two
orders of magnitude below it -- never merely "close enough". A tolerance widened
to make a test pass is the specific failure this repository has already paid for
twice, so where a measured number is quoted to 4 decimals the assertion is to 4
decimals, and where it is quoted to 2 the assertion is to 2.
"""

from __future__ import annotations

import numpy as np
import pytest

from iplranking import diagnostics as dg
from iplranking import models
from iplranking.data import build_systems

# --- The measured figures, pinned ------------------------------------------
EXPECTED_SHAPE = (558, 15)
EXPECTED_RANK = 14
EXPECTED_NUM_TEAMS = 15
#: Largest absolute difference across the three least-squares routes. Measured
#: 4.796e-14, between the normal-equations route and the constrained one.
EXPECTED_MAX_ROUTE_DIFF = 4.796e-14
#: The three routes must agree far tighter than this; the measured gap is 4.8e-14.
ROUTE_AGREEMENT_TOL = 1e-10
#: ||r||^2 = 928185.2 and ||r|| = 963.4237.
EXPECTED_SS_RES = 928185.2
EXPECTED_RESID_NORM = 963.4237
#: cond(A.T@A + 1*1.T). cond(A.T@A) is 5.63e16 -- numerically singular.
EXPECTED_COND_CONSTRAINED = 31.5476
#: Colley: lam1 = 469.1757, lam2 = 14.8064, 9 multiply-and-normalise steps.
EXPECTED_LAM1 = 469.1757
EXPECTED_LAM2 = 14.8064
EXPECTED_ITERATIONS = 9
#: Smallest Colley share, 0.0058173 (Rising Pune Supergiant, 15 wins).
EXPECTED_MIN_ENTRY = 0.0058173
#: Frequency balancing: max|x| 17.43 -> 25.64, Kochi 17.43 -> 25.64,
#: Gujarat Lions 13.70 -> 13.24, R^2 centred -0.2103 -> -0.2113.
EXPECTED_OLS_MAX_ABS_X = 17.4283
EXPECTED_BALANCED_MAX_ABS_X = 25.6355
EXPECTED_OLS_KOCHI = 17.4283
EXPECTED_BALANCED_KOCHI = 25.6355
EXPECTED_OLS_GUJARAT_LIONS = -13.703
EXPECTED_BALANCED_GUJARAT_LIONS = -13.2379
EXPECTED_R2_CENTRED = -0.2103
EXPECTED_BALANCED_R2_CENTRED = -0.2113
#: Held out on the last 3 season labels: 463 train / 95 test.
EXPECTED_N_TRAIN = 463
EXPECTED_N_TEST = 95
EXPECTED_TEST_SEASONS = ["2024", "2025", "2026"]
EXPECTED_HELD_OUT_ACCURACY = 0.432
EXPECTED_HELD_OUT_RMSE = 46.71
EXPECTED_BASELINE_RMSE = 35.35
#: ridge at lam = 1000: R^2 centred falls to -0.232369 from -0.210259.
EXPECTED_RIDGE_R2_C = -0.2324

RIDGE_LAMBDAS = (1.0, 10.0, 50.0, 200.0, 1000.0)


@pytest.fixture(scope="module")
def systems():
    return build_systems()


@pytest.fixture(scope="module")
def fit(systems):
    return models.massey(systems.A, systems.b)


@pytest.fixture(scope="module")
def colley_fit(systems):
    return models.colley(systems.W, systems.C)


@pytest.fixture(scope="module")
def balanced(systems):
    return models.frequency_balanced(systems.A, systems.b, systems.games)


# --------------------------------------------------------------------------
# Massey: three routes, one answer
# --------------------------------------------------------------------------


def test_massey_shape_and_rank(fit, systems) -> None:
    assert fit.x.shape == (EXPECTED_NUM_TEAMS,)
    assert fit.resid.shape == (systems.A.shape[0],)
    assert fit.rank == EXPECTED_RANK
    assert fit.singular_values.size == EXPECTED_NUM_TEAMS


def test_three_least_squares_routes_agree(fit) -> None:
    """Three independent routes, agreeing to 1e-10.

    Route 1 inverts nothing (``lstsq`` on the SVD), route 2 squares the condition
    number (``lstsq`` on the singular ``A.T@A``), route 3 pins the null direction
    and becomes nonsingular. Measured gap between any two of them: **4.796e-14**,
    four orders inside the tolerance asserted here.

    The tolerance is not tighter than it needs to be for appearance's sake: three
    genuinely different algorithms on a rank-deficient 558x15 system cannot agree
    to machine epsilon, because the SVD truncates the 5e-15 singular value while
    the constrained route keeps it exactly. 1e-10 is the honest bound, and it is
    ~2000x above the measured gap, so a route that actually diverged by 1e-9
    would be caught.
    """
    assert set(fit.routes) == {"lstsq", "normal_equations", "constrained"}
    for name, route in fit.routes.items():
        assert route.shape == (EXPECTED_NUM_TEAMS,), name
    stacked = np.stack(list(fit.routes.values()))
    assert np.abs(stacked - fit.routes["lstsq"]).max() < ROUTE_AGREEMENT_TOL


def test_max_route_diff_is_measured_not_claimed(fit) -> None:
    """The number the demo prints is carried in the result, and it is real.

    Measured **4.796e-14**, worst pair ``normal_equations`` vs ``constrained`` --
    the two routes that both go through ``A.T@A`` but pin the null direction
    differently. Asserting the value *and* the pair means a change in the code
    that silently swaps in a worse route shows up as a failed test rather than as
    a slightly different number nobody reads.
    """
    assert fit.max_route_diff == pytest.approx(EXPECTED_MAX_ROUTE_DIFF, rel=1e-3)
    assert fit.max_route_diff < ROUTE_AGREEMENT_TOL
    assert fit.worst_pair == ("normal_equations", "constrained")
    # And the recorded gap really is the gap: recomputing it from `routes` gives
    # the same number, so `max_route_diff` cannot be a stale constant.
    recomputed = max(
        float(np.abs(fit.routes[p] - fit.routes[q]).max())
        for p in fit.routes
        for q in fit.routes
        if p < q
    )
    assert recomputed == fit.max_route_diff


def test_centred_x_sums_to_zero(fit) -> None:
    """The gauge is fixed at zero sum.

    ``A`` has the constant vector in its kernel (``A @ ones == 0`` exactly, pinned
    in ``test_structure.py``), so ``A x = b`` cannot determine the level of ``x``
    and every solution is an equivalence class. Centring is the convention, and
    the measured sum is ``1.78e-15`` -- three orders below the bound asserted
    here, which is the residual of summing 15 doubles that each round to about 7.
    """
    assert abs(float(fit.x.sum())) < 1e-12
    for name, route in fit.routes.items():
        assert abs(float(route.sum())) < 1e-12, name


def test_the_constrained_route_is_already_zero_sum(systems) -> None:
    """Why the third route is the honest one, tested directly.

    Summing ``(A.T@A + 1*1.T) x = A.T@b`` over all 15 teams: the first term
    vanishes because ``A @ 1 == 0``, leaving ``15 * (1.T x) = 0``. The
    constrained route therefore lands on the zero-sum gauge *natively*, needing
    no centring step to agree with the others -- so their agreement is a real
    agreement and not an artefact of three identical post-processing steps.

    Measured before centring: the constrained solution sums to ``1e-14`` of zero,
    the same order as the SVD route's.
    """
    n = systems.A.shape[1]
    ones = np.ones(n)
    raw = np.linalg.solve(
        systems.A.T @ systems.A + np.outer(ones, ones), systems.A.T @ systems.b
    )
    assert abs(float(raw.sum())) < 1e-12


def test_residual_is_orthogonal_to_the_column_space(fit, systems) -> None:
    """``resid @ A ~= 0`` -- the normal-equation condition, pinned explicitly.

    Worth its own test because it is the defining property of a least-squares
    solution and it is **falsifiable**: a solution that minimised something else,
    or one fitted on the wrong rows, would not be orthogonal to the column space.

    Measured, largest entry of ``resid @ A``: ``7.46e-13``, against a residual of
    norm 963.4 -- i.e. ``7.7e-16`` relative, which is machine epsilon. The bound
    is ``1e-9``, four orders above the measurement and four below anything that
    would indicate a real residual trend.
    """
    assert np.abs(fit.resid @ systems.A).max() < 1e-9
    assert np.allclose(systems.A @ fit.x + fit.resid, systems.b, atol=1e-9)


def test_massey_reproduces_the_measured_residual_norm(fit) -> None:
    """``||r||^2 = 928185.2``, ``||r|| = 963.4237``.

    Quoted to one decimal and four decimals respectively; asserted to those.
    """
    ss_res = float(fit.resid @ fit.resid)
    assert round(ss_res, 1) == EXPECTED_SS_RES
    assert round(float(np.linalg.norm(fit.resid)), 4) == EXPECTED_RESID_NORM


def test_constrained_system_is_nonsingular_where_the_plain_one_is_not(
    fit, systems
) -> None:
    """The whole reason route 3 exists, as a measured contrast.

    ``rank(A.T@A) = 14`` and ``cond = 5.63e16``: a single ``1e-16`` eigenvalue
    makes the matrix numerically singular, and inverting it would divide by that
    noise. Adding ``1*1.T`` -- the null direction, known exactly -- makes it rank
    15 with ``cond = 31.55``. Five and a half orders of magnitude of difference,
    from a one-term change.
    """
    n = systems.A.shape[1]
    plain = systems.A.T @ systems.A
    constrained = plain + np.ones((n, n))
    assert np.linalg.matrix_rank(plain) == EXPECTED_RANK
    assert np.linalg.matrix_rank(constrained) == EXPECTED_NUM_TEAMS
    assert np.linalg.cond(plain) > 1e15
    assert fit.cond_constrained == pytest.approx(EXPECTED_COND_CONSTRAINED, abs=1e-3)
    assert np.linalg.cond(constrained) == pytest.approx(fit.cond_constrained, rel=1e-12)


def test_winner_accuracy_in_sample(fit, systems) -> None:
    """0.5502 = 307 of 558, measured. The single best-looking number in the fit."""
    accuracy = dg.winner_accuracy(systems.A @ fit.x, systems.b)
    assert round(accuracy, 4) == 0.5502
    assert accuracy == pytest.approx(307 / 558, abs=1e-15)


# --------------------------------------------------------------------------
# Colley: the eigenvector that works
# --------------------------------------------------------------------------


def test_colley_shares_are_positive_and_sum_to_one(colley_fit) -> None:
    """Perron-Frobenius verified, not assumed, and the sum is exact.

    ``all_positive`` is True and every entry is strictly positive: smallest share
    ``0.0058173``, Rising Pune Supergiant. Sum is exactly ``1.0`` so the vector
    reads as a percentage share, which is the only reason it can be set beside a
    points table at all.

    The strictness is the point. ``>= 0`` would pass for a matrix Perron-Frobenius
    does not cover, and a zero entry would mean a franchise the win/loss graph
    cannot reach -- which would be a finding, not a formatting detail.
    """
    assert colley_fit.all_positive is True
    assert colley_fit.r.size == EXPECTED_NUM_TEAMS
    assert np.all(colley_fit.r > 0.0)
    assert colley_fit.r.sum() == 1.0
    assert round(colley_fit.min_entry, 7) == EXPECTED_MIN_ENTRY
    assert colley_fit.min_entry == float(colley_fit.r.min())


def test_colley_eigenvalues_are_ordered_and_measured(colley_fit) -> None:
    """``lam1 = 469.1757 > lam2 = 14.8064 > 0``, and the gap is the finding.

    A leading eigenvalue thirty times the second means the graph has one
    dominant block -- every franchise is comparable to every other through
    transitivity -- which is precisely why a single scalar per team is a
    reasonable summary here.
    """
    assert colley_fit.lam1 > colley_fit.lam2 > 0.0
    assert round(colley_fit.lam1, 4) == EXPECTED_LAM1
    assert round(colley_fit.lam2, 4) == EXPECTED_LAM2


def test_colley_matches_the_dominant_eigenvector_of_eigh(colley_fit, systems) -> None:
    """The hand-written iteration against ``np.linalg.eigh``, to 1e-8.

    The comparison is on ``|cos|`` because an eigenvector is defined only up to
    sign and nothing here fixes the sign. ``1e-8`` on the cosine is about 5e-17
    in angle -- far inside the 9 iterations the tolerance allows.

    This is the test that makes the power iteration evidence rather than
    decoration: two unrelated algorithms, SVD and repeated multiplication, landing
    on the same direction.
    """
    _, vectors = np.linalg.eigh(systems.M)
    reference = vectors[:, -1]
    cosine = abs(
        float(colley_fit.r @ reference) / (np.linalg.norm(colley_fit.r) * np.linalg.norm(reference))
    )
    assert cosine > 1.0 - 1e-8
    values = np.linalg.eigvalsh(systems.M)
    assert colley_fit.lam1 == pytest.approx(values[-1], rel=1e-12)
    assert colley_fit.lam2 == pytest.approx(values[-2], rel=1e-12)


def test_colley_convergence_trace_is_real_and_measured(colley_fit) -> None:
    """The sparkline the demo draws: 9 steps, monotone up from 16.6% low.

    ``history[0] = 391.308`` is the crude first estimate; the trace climbs to
    ``469.175700``. Monotone non-decreasing is the real content of a power
    iteration on a symmetric matrix; the length is pinned because 9 is what this
    data takes at ``tol = 1e-12`` and a change in it should be noticed.
    """
    history = np.asarray(colley_fit.history, dtype=float)
    assert colley_fit.iterations == EXPECTED_ITERATIONS
    assert len(history) == EXPECTED_ITERATIONS
    assert np.all(np.diff(history) > 0.0)
    assert history[0] < history[-1]
    assert np.isclose(history[0], colley_fit.lam1, rtol=0.2)
    assert abs(history[-1] - history[-2]) <= 1e-12 * max(1.0, abs(history[-1]))


def test_colley_is_deterministic(systems) -> None:
    """No randomness anywhere: the start is the normalised all-ones vector, so
    two calls are bit-identical. Determinism is a project rule, and a demo that
    printed different numbers on two runs would cost marks."""
    first = models.colley(systems.W, systems.C)
    second = models.colley(systems.W, systems.C)
    assert np.array_equal(first.r, second.r)
    assert first.lam1 == second.lam1
    assert first.history == second.history


def test_colley_needs_a_symmetric_matrix_and_says_so(systems) -> None:
    """``M = W + W.T + C`` is symmetric by construction; if it were not, the
    leading eigenpair need not be real and the iteration would be meaningless.
    Asserting the failure mode is what stops the guard being decoration."""
    assert np.allclose(systems.M, systems.M.T)
    with pytest.raises(ValueError):
        models.colley(systems.W, np.zeros((3, 3)))


# --------------------------------------------------------------------------
# SVD: the diagonalisation link
# --------------------------------------------------------------------------


def test_eigenvalues_of_ata_equal_squared_singular_values_to_1e_8(systems) -> None:
    """Stage 10 in one assertion: ``A.T@A = V diag(sigma^2) V.T``.

    Measured largest gap **1.99e-13**, four orders inside the 1e-8 asserted here.
    The 1e-8 is not slack for its own sake -- it is the meaningful threshold
    here, because the two are computed by genuinely different algorithms
    (``eigh`` vs ``svd``) and agree to roundoff. A tighter bound would be testing
    LAPACK's internal consistency, not this project's claim.
    """
    result = models.svd_of_A(systems.A)
    assert result.singular_values.size == EXPECTED_NUM_TEAMS
    assert result.eigenvalues_ata.size == EXPECTED_NUM_TEAMS
    assert result.max_abs_diff < 1e-8
    assert np.abs(result.eigenvalues_ata - result.squared_singular_values).max() < 1e-8


def test_the_null_direction_shows_up_as_one_exactly_zero_eigenvalue(systems) -> None:
    """14 nonzero squared singular values and one exactly zero, on both routes.

    ``5.01e-15`` squared becomes ``2.5e-29``, and ``-9.23e-15`` from ``eigvalsh``
    becomes ``0.0`` -- snapped on return, because a table headed "eigenvalues"
    showing a negative number is how a spurious second rank deficiency gets
    quoted. Asserted both ways so the snapping cannot be dropped.
    """
    result = models.svd_of_A(systems.A)
    assert result.rank == EXPECTED_RANK
    assert result.eigenvalues_ata[-1] == 0.0
    assert result.squared_singular_values[-1] == 0.0
    assert np.all(result.eigenvalues_ata[:-1] > 0.0)
    # The zero sits last: both vectors are in descending order.
    assert np.all(np.diff(result.eigenvalues_ata) <= 0.0)


def test_ata_is_rank_15_where_ata_squared_is_rank_14(systems) -> None:
    """A check that ``svd_of_A`` is measuring ``A`` and not its square.

    ``A.T@A`` is rank 14 with 15 eigenvalues, while its square root is rank 14
    with 15 singular values -- and ``cond(A.T@A) = 5.63e16`` against
    ``cond(A) = 2.49e15``, the squaring showing up exactly as the ratio of the
    two. This is the numerical argument for stage 10: the symmetric form is
    nothing new, and it is harder to solve.
    """
    n = systems.A.shape[1]
    assert np.linalg.matrix_rank(systems.A.T @ systems.A) == EXPECTED_RANK
    assert np.linalg.matrix_rank(np.eye(n)) == n
    result = models.svd_of_A(systems.A)
    assert result.U.shape == (systems.A.shape[0], EXPECTED_NUM_TEAMS)
    assert result.Vt.shape == (EXPECTED_NUM_TEAMS, EXPECTED_NUM_TEAMS)


# --------------------------------------------------------------------------
# The refuted hypothesis: frequency balancing
# --------------------------------------------------------------------------


def test_frequency_balancing_increases_max_abs_x(fit, balanced) -> None:
    """**THIS IS THE REFUTED HYPOTHESIS. DO NOT "FIX" THIS ASSERTION.**

    The inherited build audit predicted that frequency-balanced least squares
    would stop Kochi Tuskers Kerala and Gujarat Lions dominating the fit.
    Measured, it does the opposite: ``max|x|`` rises from **17.43 to 25.64**,
    Kochi from ``+17.43`` to ``+25.64``, and R^2 centred slips from ``-0.2103``
    to ``-0.2113``.

    The diagnosis was right and the proposed repair inverted it. Kochi's extreme
    coefficient is *caused* by having 5 run-margin matches, and the weight
    ``1/(games(t1) + games(t2))`` divides by exactly that -- so it up-weights
    Kochi's handful of matches about threefold against a Mumbai-Chennai match,
    whose pair total is 266, and amplifies the coefficient it was meant to tame.

    The direction of the inequality below is the finding. If someone later swaps
    in a different weighting and this test fails, the correct response is to
    report that the weighting changed -- **not** to flip the assertion. What
    would be dishonest is leaving ``abs(balanced) > abs(ols)`` in place after
    finding a weighting that improves the fit and calling that a fix: it would
    hide that the *original hypothesis* was tested and refuted.
    """
    balanced_max = float(np.abs(balanced.x).max())
    ols_max = float(np.abs(fit.x).max())
    assert round(ols_max, 4) == EXPECTED_OLS_MAX_ABS_X
    assert round(balanced_max, 4) == EXPECTED_BALANCED_MAX_ABS_X
    assert balanced_max > ols_max, (
        f"frequency balancing made max|x| *smaller* ({balanced_max!r} < {ols_max!r}); "
        "the refuted hypothesis is a directional claim and this is no longer the "
        "measurement. Report the weighting change; do not flip the sign here."
    )


def test_frequency_balancing_pins_the_two_refuted_teams(fit, balanced, systems) -> None:
    """Kochi ``17.43 -> 25.64``, Gujarat Lions ``13.70 -> 13.24``.

    Both measured to 4 decimals. Gujarat Lions moving *less* extreme while Kochi
    moves more is what makes the mechanism checkable: the five-game franchises
    are treated the same way by the weighting, and only Kochi's coefficient is
    amplified enough to change the story, because its matches are all against
    well-measured teams.
    """
    index = {name: i for i, name in enumerate(systems.teams)}
    kochi = index["Kochi Tuskers Kerala"]
    lions = index["Gujarat Lions"]
    assert round(float(fit.x[kochi]), 4) == EXPECTED_OLS_KOCHI
    assert round(float(balanced.x[kochi]), 4) == EXPECTED_BALANCED_KOCHI
    assert round(float(fit.x[lions]), 4) == EXPECTED_OLS_GUJARAT_LIONS
    assert round(float(balanced.x[lions]), 4) == EXPECTED_BALANCED_GUJARAT_LIONS
    assert balanced.x[kochi] > fit.x[kochi]
    assert abs(balanced.x[lions]) < abs(fit.x[lions])


def test_frequency_balancing_weights_are_the_pair_totals_not_a_constant(
    balanced,
) -> None:
    """The mechanism, pinned: the weights must actually vary.

    ``w_i = 1/(games(t1) + games(t2))`` and ``games`` is
    ``data.games_played()``. The pair totals run **44 to 266**, so the weights run
    1/266 to 1/44 -- a factor of six between the most and least trusted match.

    This test exists because the obvious wrong implementation is a *silent*
    no-op: every row of ``A`` holds exactly two entries and ``|A|`` row sums to 2
    throughout, so a weight derived from ``A`` itself is the constant ``1/2`` and
    the "balanced" fit comes back bit-identical to OLS. Someone reaching for
    ``np.abs(A).sum(axis=1)`` instead of the per-team counts would otherwise get
    a plausible, stable, wrong answer.
    """
    assert balanced.w.size == balanced.match_games.size
    assert float(balanced.match_games.min()) == 44.0
    assert float(balanced.match_games.max()) == 266.0
    assert np.allclose(balanced.w, 1.0 / balanced.match_games)
    assert np.ptp(balanced.w) > 0.01
    # 6x spread, and no row is the constant 1/2.
    assert float(balanced.w.max() / balanced.w.min()) == pytest.approx(6.045, abs=0.01)
    assert not np.allclose(balanced.w, 0.5)


def test_frequency_balancing_makes_the_fit_slightly_worse(fit, balanced, systems) -> None:
    """R^2 centred ``-0.2103 -> -0.2113``. Balancing moves the *direction* of the
    coefficient vector and leaves the fit just as bad -- marginally worse.

    Scored with the **unweighted** residual, the same denominator the OLS R^2
    uses, so the two numbers are comparable. (Scored on the weighted objective
    the balanced fit reads ``-0.182``, but that is a different quantity answering
    a different question and is not what "did balancing help" means.)
    """
    r2_ols = dg.r_squared(systems.b, systems.A @ fit.x, centred=True)
    r2_balanced = dg.r_squared(systems.b, systems.A @ balanced.x, centred=True)
    assert round(r2_ols, 4) == EXPECTED_R2_CENTRED
    assert round(r2_balanced, 4) == EXPECTED_BALANCED_R2_CENTRED
    assert r2_balanced < r2_ols
    # Both are negative: both models are worse than predicting the mean margin.
    assert r2_ols < 0.0
    assert r2_balanced < 0.0


def test_frequency_balancing_is_deterministic(systems) -> None:
    first = models.frequency_balanced(systems.A, systems.b, systems.games)
    second = models.frequency_balanced(systems.A, systems.b, systems.games)
    assert np.array_equal(first.x, second.x)
    assert np.array_equal(first.w, second.w)


# --------------------------------------------------------------------------
# Ridge: the theorem, and the claim measurement refuted
# --------------------------------------------------------------------------


def test_ridge_never_improves_r_squared_because_it_cannot(fit, systems) -> None:
    """**A theorem, not an observation**, and the direction it runs in is the
    whole content of this test.

    ``x_hat`` is *the* minimiser of ``||A x - b||``, so no re-fit -- least squares
    or otherwise -- can produce a smaller residual. ``R^2 = 1 - SSres/SS_tot`` and
    ``SS_tot`` does not depend on ``x``, so shrinkage can only move R^2 **down**.

    Measured strictly: the residual sum of squares *rises* at every one of the
    five lambdas, by ``+75.3, +1450.8, +4605.5, +10310.8, +16957.4``. Those
    deltas are asserted to be positive rather than merely non-negative, because
    a ridge penalty that left the residual untouched would mean the shrinkage was
    not applied and would also satisfy a ``>= 0`` test.
    """
    ss_res_ols = float(fit.resid @ fit.resid)
    baseline = dg.r_squared(systems.b, systems.A @ fit.x, centred=True)
    previous_delta = 0.0
    for lam in RIDGE_LAMBDAS:
        shrunk = models.ridge(systems.A, systems.b, lam)
        residual = systems.b - systems.A @ shrunk
        delta = float(residual @ residual) - ss_res_ols
        assert delta > 0.0, f"lam={lam}: ridge left the residual unchanged or lower"
        assert delta > previous_delta, f"lam={lam}: shrinkage effect is not monotone"
        previous_delta = delta
        assert dg.r_squared(systems.b, systems.A @ shrunk, centred=True) < baseline


def test_ridge_r_squared_is_not_invariant_contrary_to_the_inherited_claim(
    fit, systems
) -> None:
    """The dispatch expected R^2 *unchanged to 4 dp* across
    ``lam in [1, 1000]``, and wanted that pinned to 1e-6. **Measurement refutes
    it, and this test pins the refutation.**

    Measured R^2 centred: ``-0.210259`` at OLS, falling monotonically to
    ``-0.232369`` at ``lam = 1000``. The span is **2.211e-2** -- some twenty
    thousand times the tolerance the inherited claim wanted, and it changes in
    the *fourth* decimal at ``lam = 1`` already, so "unchanged to 4 dp" fails
    at the very first value of the grid.

    The reason is not a subtlety: ``A.T@A``'s eigenvalues run 155.7 down to 4.9 on
    the identifiable directions, so a penalty of ``lam = 1000`` dominates all of
    them and ``x`` is shrunk almost to zero (``max|x|`` 17.43 -> 0.69). What the
    inherited claim preserved was the *theorem* it was reaching for -- that ridge
    cannot help -- which is why it is kept and tested above, one assertion at a
    time, with the direction it actually runs in.

    The lower bound on the span is the load-bearing half. It says: the invariance
    claim is false *by at least three orders of magnitude*. A future agent
    rewriting the ridge term cannot reintroduce it.
    """
    baseline = dg.r_squared(systems.b, systems.A @ fit.x, centred=True)
    values = []
    for lam in RIDGE_LAMBDAS:
        shrunk = models.ridge(systems.A, systems.b, lam)
        values.append(dg.r_squared(systems.b, systems.A @ shrunk, centred=True))
    values = np.asarray(values, dtype=float)
    assert round(float(values[-1]), 4) == EXPECTED_RIDGE_R2_C
    assert np.all(np.diff(values) < 0.0), "R^2 must fall monotonically in lam"
    span = float(values.max() - values.min())
    assert span > 1e-3, f"span {span!r} is too small to refute the 1e-6 claim"
    assert span < 1e-1, f"span {span!r} is implausibly large; check the ridge term"
    # Even the mildest penalty already breaks "unchanged to 4 dp".
    assert abs(float(values[0]) - baseline) > 1e-5


def test_ridge_shrinks_towards_zero_and_never_below_it(systems) -> None:
    """What the penalty does to the coefficients themselves.

    ``lam = 0`` returns the unregularised solution -- still solved with ``lstsq``,
    because ``A.T@A`` is rank 14 and inverting it would divide by a ``1e-16``.
    Every larger ``lam`` shrinks the coefficients monotonically towards zero.

    The gauge survives: centring is applied after the solve, so ``sum(x) == 0``
    holds at every ``lam``. Without that, ``lam = 0`` would return a
    minimum-norm solution whose sum is only zero by luck, and the two routes
    would not be comparable at the gauge -- the whole point of the comparison.
    """
    unregularised = models.ridge(systems.A, systems.b, 0.0)
    previous = float(np.linalg.norm(unregularised))
    assert abs(float(unregularised.sum())) < 1e-12
    for lam in RIDGE_LAMBDAS:
        shrunk = models.ridge(systems.A, systems.b, lam)
        assert abs(float(shrunk.sum())) < 1e-12, "ridge must keep the gauge"
        current = float(np.linalg.norm(shrunk))
        assert current < previous, f"lam={lam} did not shrink the solution"
        previous = current
    # At lam = 1000 the penalty dominates every eigenvalue of A.T@A (155.7 down
    # to 4.9), so the solution is nearly annihilated -- measured norm 1.25
    # against 27.24 unregularised.
    assert float(np.linalg.norm(models.ridge(systems.A, systems.b, 1000.0))) == pytest.approx(
        1.2471, abs=1e-4
    )
    # Shrinkage is a contraction of the coefficient vector, so no entry can grow.
    heavy = models.ridge(systems.A, systems.b, 1000.0)
    assert np.all(np.abs(heavy) <= np.abs(unregularised) + 1e-12)


def test_ridge_rejects_a_negative_penalty(systems) -> None:
    """A negative ``lam`` is not regularisation; it is an unregularised solve with
    a deliberate bias. Rejected rather than silently solved."""
    with pytest.raises(ValueError):
        models.ridge(systems.A, systems.b, -1.0)


# --------------------------------------------------------------------------
# Held out: the fit meets seasons it never saw
# --------------------------------------------------------------------------


def test_held_out_split_is_the_last_three_seasons(systems) -> None:
    """463 train rows / 95 test rows, on ``['2024', '2025', '2026']``.

    They sum to the full 558: every run-margin match lands in exactly one split,
    which is asserted rather than assumed -- an overlapping split would make the
    held-out number fiction while still looking like a number.
    """
    result = models.held_out_fit(systems.matches, systems.teams)
    assert result.n_train == EXPECTED_N_TRAIN
    assert result.n_test == EXPECTED_N_TEST
    assert result.n_train + result.n_test == systems.A.shape[0]
    assert result.test_seasons == EXPECTED_TEST_SEASONS


def test_sorted_season_labels_are_chronological(systems) -> None:
    """The split is by *sorted label*, which is only a time split if string order
    coincides with chronological order on these 19 labels.

    It does, but that is a property of these particular labels, not of string
    comparison, so the whole list is pinned. Measured labels:

    ``2007/08, 2009, 2009/10, 2011..2019, 2020/21, 2021..2026``

    Two label families coexist -- a bare year and a ``yyyy/yy`` season -- and
    there is no ``2008`` or ``2011/12`` at all, which is worth pinning precisely
    because assuming the more regular spellings would have been wrong. The
    ordering facts that carry the time split are asserted explicitly: ``'2009' <
    '2009/10'`` (a prefix sorts before its extension) and ``'2019' <
    '2020/21' < '2021'`` (the crossing, where the ``yyyy/yy`` form for 2020 sits
    between the bare years 2019 and 2021).

    If a future snapshot broke any of these, the "held-out" split would silently
    overlap time and the accuracy below would quietly stop meaning anything.
    """
    labels = sorted(
        str(label) for label in systems.matches["season"].drop_duplicates()
    )
    assert len(labels) == 19
    assert labels == [
        "2007/08",
        "2009",
        "2009/10",
        "2011",
        "2012",
        "2013",
        "2014",
        "2015",
        "2016",
        "2017",
        "2018",
        "2019",
        "2020/21",
        "2021",
        "2022",
        "2023",
        "2024",
        "2025",
        "2026",
    ]
    # The crossing case: a `yyyy/yy` label sorting between two bare years.
    assert "2019" in labels and "2020/21" in labels and "2021" in labels
    assert labels.index("2019") < labels.index("2020/21") < labels.index("2021")
    # A prefix sorts before its own extension.
    assert labels.index("2009") < labels.index("2009/10")
    # The held-out three are the last three, so the split is genuinely the most
    # recent part of the archive and not an arbitrary tail.
    assert labels[-3:] == EXPECTED_TEST_SEASONS
    # No regular-spelling labels exist, so nothing here relies on one.
    assert "2008" not in labels
    assert "2011/12" not in labels


def test_held_out_rmse_is_worse_than_predicting_the_mean(systems) -> None:
    """**RMSE 46.71 vs 35.35.** The model loses to a constant by 32%.

    Strictly greater, and pinned to 2 decimals as measured. The baseline is the
    *training* mean: using the test mean would leak the answer into the
    comparator and would flatter the model to 28.32, i.e. to a number that looks
    like the model is losing only slightly.
    """
    result = models.held_out_fit(systems.matches, systems.teams)
    assert round(result.rmse, 2) == EXPECTED_HELD_OUT_RMSE
    assert round(result.baseline_rmse, 2) == EXPECTED_BASELINE_RMSE
    assert result.rmse > result.baseline_rmse
    assert result.rmse / result.baseline_rmse == pytest.approx(1.321, abs=0.005)


def test_held_out_accuracy_is_near_chance(systems) -> None:
    """0.432 = 41 of 95, down from 0.5502 in sample.

    A coin flip on a two-sided outcome is 0.50. The fit is *below* it on unseen
    seasons, and 12 points below it on the ones it was fitted to. Two numbers,
    both bad, and the second is the honest one.
    """
    result = models.held_out_fit(systems.matches, systems.teams)
    assert round(result.accuracy, 3) == EXPECTED_HELD_OUT_ACCURACY
    assert result.accuracy == pytest.approx(41 / 95, abs=1e-15)
    assert result.accuracy < 0.5


def test_held_out_baseline_uses_the_training_mean(systems) -> None:
    """Pinned because the leak is the easy mistake here.

    ``baseline_rmse`` must come from the mean of the **training** margins
    (14.43). From the test margins it would be 28.32 -- a flattering number that
    would still show the model losing, but by much less, and for a reason that
    is not about the model at all.
    """
    result = models.held_out_fit(systems.matches, systems.teams)
    assert round(result.train_mean, 2) == 14.43
    leaked = float(np.sqrt(np.mean((result.b_test.mean() - result.b_test) ** 2)))
    assert round(leaked, 2) == 28.32
    assert abs(result.baseline_rmse - leaked) > 1.0


def test_held_out_fit_is_deterministic(systems) -> None:
    first = models.held_out_fit(systems.matches, systems.teams)
    second = models.held_out_fit(systems.matches, systems.teams)
    assert first.accuracy == second.accuracy
    assert first.rmse == second.rmse
    assert first.baseline_rmse == second.baseline_rmse
    assert np.array_equal(first.x, second.x)


def test_held_out_rejects_a_mismatched_team_order(systems) -> None:
    """Every vector in this project is indexed by position, so a wrong order is a
    silent disaster: the fit is still a fit, it just attributes strengths to the
    wrong franchises. Guarded with the real numbers."""
    with pytest.raises(ValueError):
        models.held_out_fit(systems.matches, list(reversed(systems.teams)))
    with pytest.raises(ValueError):
        models.held_out_fit(systems.matches, systems.teams, n_test_seasons=0)