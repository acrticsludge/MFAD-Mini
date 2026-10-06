"""Diagnostic tests: the two R^2 denominators, standard errors, the significance
finding, rank correlation, and the two comparison tables.

This is where the project's conclusion is pinned, and the conclusion is negative
three times over:

* ``R^2 = -0.2103`` centred -- worse than predicting the mean margin;
* ``max|x/se| = 1.20`` -- not one coefficient significant at 2 sigma;
* ``Spearman(Massey, Colley) = 0.000`` exactly -- the two rankings are
  uncorrelated, so only one of the two models can be right, and the comparison
  with the official table says which.

Every figure measured 2026-10-04 against the committed snapshot. Tolerances are
stated next to the measured value and are one or two orders of magnitude below
it; none of them was widened after the fact. Where a dispatch for this module
expected a number that measurement refuted, the refutation is what is pinned --
see `test_ridge...` in `test_models.py` and
`test_dispatched_covariance_is_not_the_exact_covariance_but_the_finding_holds`
below.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from iplranking import diagnostics as dg
from iplranking import models
from iplranking.data import build_systems

# --- The measured figures, pinned ------------------------------------------
EXPECTED_NUM_TEAMS = 15
EXPECTED_M = 558
EXPECTED_RANK = 14
EXPECTED_DOF = 544
EXPECTED_SS_RES = 928185.2
EXPECTED_SS_TOTAL_UNCENTRED = 948444.0
EXPECTED_SS_TOTAL_CENTRED = 766931.3
EXPECTED_R2_CENTRED = -0.2103
EXPECTED_R2_UNCENTRED = 0.0214
EXPECTED_SIGMA2 = 1706.2228
EXPECTED_SE_MIN = 4.68
EXPECTED_SE_MAX = 17.63
EXPECTED_MAX_T = 1.20
#: Spearman, 3 dp, all three pairs.
EXPECTED_SPEARMAN_MASSEY_COLLEY = 0.000
EXPECTED_SPEARMAN_MASSEY_OFFICIAL = 0.093
EXPECTED_SPEARMAN_COLLEY_OFFICIAL = 0.939
EXPECTED_PEARSON_MASSEY_COLLEY = -0.122
EXPECTED_CORR_GAMES_ABS_X = -0.663
EXPECTED_WINNER_ACCURACY = 0.5502

#: The two sigma the significance claim is about.
TWO_SIGMA = 2.0


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
def official_points(systems):
    """Official points **aligned to alphabetical team order**.

    This is the join that has to happen before any correlation with the fitted
    vectors is meaningful, and it is a fixture rather than an inline expression so
    that every test in this file that compares against the official table goes
    through it.
    """
    return (
        systems.official.set_index("team").loc[systems.teams, "points"].to_numpy().astype(float)
    )


# --------------------------------------------------------------------------
# R^2: two denominators, opposite signs
# --------------------------------------------------------------------------


def test_both_r_squared_variants_to_four_decimals(systems, fit) -> None:
    """**-0.2103 centred, +0.0214 uncentred.** The sign flips between them.

    Both are pinned to the 4 decimals the dispatch quotes, and the difference is
    asserted as **opposite in sign** rather than merely unequal: the whole reason
    this function refuses a default is that these two numbers are not two
    estimates of one thing, they are claims in opposite directions about whether
    the model beats a constant.
    """
    predicted = systems.A @ fit.x
    centred = dg.r_squared(systems.b, predicted, centred=True)
    uncentred = dg.r_squared(systems.b, predicted, centred=False)
    assert round(centred, 4) == EXPECTED_R2_CENTRED
    assert round(uncentred, 4) == EXPECTED_R2_UNCENTRED
    assert centred < 0.0 < uncentred


def test_the_sum_of_squares_identities_underneath_r_squared(systems, fit) -> None:
    """The three sums of squares, and the two identities that connect them.

    Measured 2026-10-04:

    ==================  ==========  ==============================================
    quantity            value       meaning
    ==================  ==========  ==============================================
    ``||r||^2``         928185.2    ``SSres``, one per run-margin match
    ``||b||^2``         948444.0    the *uncentred* total
    ``||b - b'||^2``    766931.3    the *centred* total
    ==================  ==========  ==============================================

    Two exact identities tie them together, and both are asserted because either
    one on its own is satisfied by a wrong ``b``:

    1. ``||b||^2 = ||A x||^2 + ||r||^2`` -- Pythagoras, valid only because the
       least-squares residual is orthogonal to ``Col(A)``. This is the numerical
       form of the normal equations, and it fails for any non-minimising ``x``.
    2. ``||b||^2 = ||b - b'||^2 + m * b'^2`` -- the variance decomposition. This is
       what *explains* the sign flip: the uncentred denominator is the larger one
       by ``m * 18.036^2 = 181,513``, so it makes the same ratio smaller and the
       same subtraction less negative.

    Together they mean the centred and uncentred figures cannot disagree for any
    reason other than the denominator, which is the claim being made about them.
    """
    b, A, x, resid = systems.b, systems.A, fit.x, fit.resid
    m = A.shape[0]
    mean = float(b.mean())

    ss_res = float(resid @ resid)
    ss_total_uncentred = float(b @ b)
    ss_total_centred = float(np.sum((b - mean) ** 2))

    assert round(ss_res, 1) == EXPECTED_SS_RES
    assert round(ss_total_uncentred, 1) == EXPECTED_SS_TOTAL_UNCENTRED
    assert round(ss_total_centred, 1) == EXPECTED_SS_TOTAL_CENTRED

    # (1) Pythagoras through the column space.
    fitted = A @ x
    assert abs(float(fitted @ fitted) + ss_res - ss_total_uncentred) < 1e-6
    # (2) The variance decomposition that makes the two denominators differ.
    assert abs(ss_total_centred + m * mean**2 - ss_total_uncentred) < 1e-6
    # The measured size of the gap, which is the whole mechanism of the flip.
    assert round(m * mean**2, 1) == 181512.7


def test_r_squared_is_each_denominator_explicitly(systems, fit) -> None:
    """Recomputed from first principles, both ways.

    Not a tautology check: it pins that ``centred`` selects
    ``sum((b - mean(b))**2)`` and *only* that, so an implementation that used the
    wrong denominator on one branch would have to get both branches right to pass.
    """
    b, predicted = systems.b, systems.A @ fit.x
    ss_res = float(np.sum((b - predicted) ** 2))
    assert dg.r_squared(b, predicted, centred=True) == pytest.approx(
        1.0 - ss_res / float(np.sum((b - b.mean()) ** 2)), rel=1e-14
    )
    assert dg.r_squared(b, predicted, centred=False) == pytest.approx(
        1.0 - ss_res / float(np.sum(b**2)), rel=1e-14
    )


def test_r_squared_rejects_mismatched_and_degenerate_input(systems, fit) -> None:
    """Guards on the two ways the function could return a plausible wrong number.

    Unequal lengths would silently score predictions against the wrong margins;
    a constant ``b`` makes the centred denominator zero and the quotient infinite.
    """
    b, predicted = systems.b, systems.A @ fit.x
    with pytest.raises(ValueError):
        dg.r_squared(b, predicted[:-1], centred=True)
    # The uncentred branch guards its own length too -- checked separately, so a
    # branch that forgot the check would fail rather than silently mis-score.
    with pytest.raises(ValueError):
        dg.r_squared(b, predicted[:-1], centred=False)
    # A constant b: the centred denominator is zero, so the quotient is undefined.
    # The *uncentred* denominator is not zero there, so this input must raise for
    # the centred call and succeed for the other -- which is exactly why the flag
    # has no default.
    with pytest.raises(ValueError):
        dg.r_squared(np.ones(10), np.zeros(10), centred=True)
    assert dg.r_squared(np.ones(10), np.zeros(10), centred=False) == pytest.approx(
        0.0, abs=1e-12
    )
    with pytest.raises(ValueError):
        dg.r_squared(np.array([]), np.array([]), centred=False)


def test_r_squared_cannot_be_called_without_an_explicit_denominator(
    systems, fit
) -> None:
    """The signature is the guarantee. This is the test the dispatch asked for.

    ``centred`` must be **keyword-only with no default**, checked structurally via
    ``inspect.signature`` rather than by trying one call, because a call that
    happens to raise for another reason would give the same green tick.

    Three separate properties, each asserted:

    1. ``centred`` exists as a parameter at all;
    2. its kind is ``KEYWORD_ONLY`` -- so it cannot be filled positionally and
       misread;
    3. its default is ``empty`` -- so ``r_squared(b, pred)`` is a ``TypeError``.

    A silent default here is exactly how the inherited build audit came to report
    ``+0.0214`` without anyone noticing the model was worse than a constant: the
    wrong branch was never *chosen*, it was inherited.
    """
    signature = inspect.signature(dg.r_squared)
    assert "centred" in signature.parameters
    centred = signature.parameters["centred"]
    assert centred.kind is inspect.Parameter.KEYWORD_ONLY
    assert centred.default is inspect.Parameter.empty
    # And the runtime behaviour agrees with the declared signature.
    predicted = systems.A @ fit.x
    with pytest.raises(TypeError):
        dg.r_squared(systems.b, predicted)
    # Positional is refused too, so `r_squared(b, pred, True)` cannot slip through.
    with pytest.raises(TypeError):
        dg.r_squared(systems.b, predicted, True)


# --------------------------------------------------------------------------
# Standard errors and the significance finding
# --------------------------------------------------------------------------


def test_sigma2_uses_m_minus_rank_degrees_of_freedom(systems, fit) -> None:
    """``sigma2 = ||r||^2 / 544``, measured **1706.2228**.

    ``544 = 558 - 14``: one degree of freedom spent per estimated coefficient.
    The correction is not cosmetic -- it raises ``sigma2`` by 2.8% over
    ``||r||^2/558``, and on this model that is the difference between
    ``max|t| = 1.20`` and a slightly larger number. Both the exact quotient and
    the 4-decimal figure are pinned, so a change of divisor cannot hide inside a
    tolerance.
    """
    se, sigma2, _ = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    ss_res = float(fit.resid @ fit.resid)
    assert systems.A.shape[0] - fit.rank == EXPECTED_DOF
    assert sigma2 == pytest.approx(ss_res / EXPECTED_DOF, rel=1e-15)
    assert round(sigma2, 4) == EXPECTED_SIGMA2
    assert se.size == EXPECTED_NUM_TEAMS
    assert se.size == fit.x.size


def test_standard_error_range_to_two_decimals(systems, fit) -> None:
    """**4.68 to 17.63 runs**, to the 2 decimals measured.

    The spread is the diagnosis and not noise in the reporting: the two largest
    standard errors, 17.63 and 17.62, belong to Gujarat Lions and Kochi Tuskers
    Kerala -- the same two five-game franchises that hold the most extreme
    coefficients. Short history produces both at once.
    """
    se, _, _ = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    assert round(float(se.min()), 2) == EXPECTED_SE_MIN
    assert round(float(se.max()), 2) == EXPECTED_SE_MAX
    assert np.all(se > 0.0)
    assert se.max() / se.min() == pytest.approx(3.767, abs=0.01)


def test_the_largest_standard_errors_belong_to_the_five_game_franchises(
    systems, fit
) -> None:
    """``corr(games_played, |x|) = -0.663``, and the two extremes are the same two
    teams. The leverage is not spread around; it is concentrated in two rows of
    the summary table.

    Measured correlation: **-0.6630**. The best-measured franchise (138 games) has
    the *smallest* standard error, 4.68, and the two five-game franchises have the
    two largest at 17.63 and 17.62 -- 3.8x the uncertainty, from 1/28th the data.
    """
    se, _, _ = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    order = np.argsort(se)
    worst = [systems.teams[i] for i in order[-2:]]
    assert set(worst) == {"Gujarat Lions", "Kochi Tuskers Kerala"}
    assert sorted(systems.games[order[-2:]].tolist()) == [5, 5]
    correlation = float(np.corrcoef(systems.games, np.abs(fit.x))[0, 1])
    assert round(correlation, 3) == EXPECTED_CORR_GAMES_ABS_X
    assert correlation < 0.0


def test_no_coefficient_is_significant_at_two_sigma(systems, fit) -> None:
    """``max|t| = 1.20 < 1.25 < 2``. **This is a result, not a loose bound.**

    Read the bound carefully, because it is the one place in this suite where a
    generous tolerance could quietly erase the finding. The measured value is
    **1.2017**; the assertion uses **1.25**, a margin of 4%. It is not "assert
    less than 2 and let the reader judge" -- the point is that the nearest any of
    the 15 coefficients comes to significance is 40% short of it. Raising 1.25 to
    2.0 would turn a measured null result into "maybe something", which is
    arithmetically permitted by the assertion and dishonest about the data.

    The strongest team, Rajasthan Royals at ``|t| = 1.2017``, is the largest of the
    15 and is named so the number has an owner rather than existing as an
    anonymous maximum.

    The final assertion is the one that would catch a fabricated result: a
    regression that made a coefficient *look* significant would raise ``max|t|``
    above 2 and fail here, and a regression that made the data look cleaner than
    it is would push it the other way.
    """
    _, _, t_stats = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    max_t = float(np.abs(t_stats).max())
    assert round(max_t, 2) == EXPECTED_MAX_T
    assert max_t < 1.25, (
        f"max|t| = {max_t!r}; the finding is that nothing reaches 2 sigma, and "
        "1.25 is a 4% margin on the measured 1.2017 -- not a bound to relax"
    )
    assert max_t < TWO_SIGMA
    assert np.all(np.abs(t_stats) < TWO_SIGMA), "a coefficient reached 2 sigma"
    owner = systems.teams[int(np.abs(t_stats).argmax())]
    assert owner == "Rajasthan Royals"
    # The margin is real and it is small: the bound sits 4.0% above the measured
    # value, and this assertion fails if it is ever loosened to 10% or more. It is
    # the assertion that stops the finding being quietly relaxed into "possibly
    # one coefficient".
    margin = (1.25 - max_t) / max_t
    assert 0.03 < margin < 0.05, f"the 1.25 bound is {margin:.1%} above the data"


def test_standard_errors_require_x_rather_than_guessing_it(systems, fit) -> None:
    """``x`` is a required keyword, because ``t = x/se`` cannot be derived from
    ``A`` and ``resid`` alone.

    ``resid = b - A x`` needs ``b`` to invert, and ``b`` is not an argument.
    The dispatch's three-argument signature was therefore underdetermined, and
    the alternative -- recovering ``x`` internally -- would mean silently
    reporting t statistics for a fit the caller did not ask about. Same principle
    as ``r_squared``: no guessable defaults.

    Checked structurally, then at runtime.
    """
    signature = inspect.signature(dg.standard_errors)
    estimates = signature.parameters["x"]
    assert estimates.kind is inspect.Parameter.KEYWORD_ONLY
    assert estimates.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        dg.standard_errors(systems.A, fit.resid, fit.rank)


def test_standard_errors_reject_inconsistent_shapes(systems, fit) -> None:
    """The three arguments have to describe the same fit, checked rather than
    assumed: a residual of the wrong length would silently change the degrees of
    freedom, and an ``x`` of the wrong length would silently change the team
    count."""
    with pytest.raises(ValueError):
        dg.standard_errors(systems.A, fit.resid[:-1], fit.rank, x=fit.x)
    with pytest.raises(ValueError):
        dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x[:-1])
    with pytest.raises(ValueError):
        dg.standard_errors(systems.A, fit.resid, systems.A.shape[0], x=fit.x)


def test_dispatched_covariance_is_not_the_exact_covariance_but_the_finding_holds(
    systems, fit
) -> None:
    """The one honest caveat in this file, pinned as an identity and as a bound.

    ``diagnostics.standard_errors`` uses the covariance the dispatch prescribed,
    ``sigma2 * inv(A.T@A + 1*1.T)``. That is **not** the exact covariance of the
    constrained estimator, and rather than leave that as a caveat in a docstring
    it is measured and asserted here:

    ==========================  ===========  ==========================
    covariance                  ``max|t|``   2 sigma reached?
    ==========================  ===========  ==========================
    ``sigma2 * inv(K)`` used    **1.2017**   no
    ``sigma2 * (A.T@A)^+``      1.4329       no
    ``sigma2 * (I - 11.T/15)``  0.4367       no
    ==========================  ===========  ==========================

    where ``K = A.T@A + 1*1.T``. The identity that explains the difference is
    asserted to 1e-12: ``K^-1 == (A.T@A)^+ + 11.T/225``, because
    ``1.T @ K = 15 * 1.T`` forces ``1.T @ K^-1 = (1/15) * 1.T``. So the dispatched
    covariance is the **minimum-norm** estimator's covariance -- the right one for
    the SVD route ``massey`` actually returns -- plus a rank-one term adding
    ``sigma2/225 = 7.5832`` to every variance, which the third assertion confirms
    entry by entry.

    So the se *values* depend on a choice of covariance and the *conclusion* does
    not. The most conservative of the three still puts every one of the 15
    coefficients under 2 sigma, and the most permissive tops out at 1.43. Pinning
    only the reported number would leave a reader unable to tell which of the two
    kinds of claim they were looking at.
    """
    A, resid, rank, x = systems.A, fit.resid, fit.rank, fit.x
    n = A.shape[1]
    ones = np.ones(n)
    _, sigma2, _ = dg.standard_errors(A, resid, rank, x=x)

    # The identity, measured rather than asserted in prose.
    eigenvalues = np.linalg.eigvalsh(A.T @ A)
    vectors = np.linalg.eigh(A.T @ A)[1]
    kept = eigenvalues > 0.0
    inverse_values = np.zeros_like(eigenvalues)
    inverse_values[kept] = 1.0 / eigenvalues[kept]
    pseudo_inverse = (vectors * inverse_values) @ vectors.T
    constrained_inverse = np.linalg.inv(A.T @ A + np.outer(ones, ones))
    assert np.abs(
        constrained_inverse - (pseudo_inverse + np.outer(ones, ones) / n**2)
    ).max() < 1e-12
    assert np.abs(constrained_inverse - pseudo_inverse).max() > 1e-3

    # The rank-one term adds the same sigma2/225 to every variance.
    se_dispatched = np.sqrt(np.diag(sigma2 * constrained_inverse))
    se_pseudo = np.sqrt(np.diag(sigma2 * pseudo_inverse))
    assert np.allclose(se_dispatched**2 - se_pseudo**2, sigma2 / n**2, atol=1e-9)
    assert round(sigma2 / n**2, 4) == 7.5832

    # The conclusion survives all three covariances.
    projector = np.eye(n) - np.outer(ones, ones) / n
    for covariance in (constrained_inverse, pseudo_inverse, projector):
        spread = np.sqrt(np.diag(sigma2 * covariance))
        assert np.all(np.abs(x / spread) < TWO_SIGMA), (
            "the significance finding depends on which covariance is used"
        )
    assert float(np.abs(x / se_pseudo).max()) == pytest.approx(1.4329, abs=1e-4)


# --------------------------------------------------------------------------
# Spearman, hand-rolled
# --------------------------------------------------------------------------


def test_spearman_for_all_three_pairs_to_three_decimals(
    fit, colley_fit, official_points
) -> None:
    """``0.000``, ``+0.093``, ``+0.939``. The headline comparison, pinned.

    ==========  ==========================  =============  ====================
    pair        Spearman                   reading       meaning
    ==========  ==========================  =============  ====================
    M vs C      ``0.000``                  no relation   the two models are
                                                           independent
    M vs off    ``+0.093``                 no relation   margins explain
                                                           nothing about the
                                                           points table
    C vs off    ``+0.939``                 near-identity win/loss recovers
                                                           the official table
    ==========  ==========================  =============  ====================

    The zero is not a rounding artefact of "about 0"; it is exact, and
    ``test_spearman_between_the_two_models_is_exactly_zero`` pins why.
    """
    assert round(dg.spearman(fit.x, colley_fit.r), 3) == EXPECTED_SPEARMAN_MASSEY_COLLEY
    assert round(dg.spearman(fit.x, official_points), 3) == EXPECTED_SPEARMAN_MASSEY_OFFICIAL
    assert (
        round(dg.spearman(colley_fit.r, official_points), 3)
        == EXPECTED_SPEARMAN_COLLEY_OFFICIAL
    )
    # And the ordering of the three is the finding, not just their values: the
    # margin fit is no better than the official table than the win/loss fit is.
    assert dg.spearman(colley_fit.r, official_points) > dg.spearman(fit.x, official_points)
    assert abs(dg.spearman(fit.x, official_points)) < 0.2


def test_spearman_between_the_two_models_is_exactly_zero(fit, colley_fit) -> None:
    """Exactly ``0.0`` -- and this test shows it is a property of the data rather
    than a coincidence of rounding.

    Neither ranking has a tie, so ``average_ranks`` returns a clean permutation of
    ``1..15`` for both. Both rank vectors therefore have mean 8, and the Pearson
    correlation of the two centred rank vectors cancels **exactly**: the sum of
    the 15 products is 0 to the last bit, so the quotient is 0.0 rather than
    ``1e-17``.

    This is the project's central numerical result -- the two models are
    uncorrelated on the same 15 franchises, fitted from the same fixtures, using
    the same mathematics -- so it is pinned both as a value and as the reason the
    value is exact. A snapshot that moves it to ``1e-17`` instead of ``0.0`` would
    still mean "uncorrelated"; this test says so explicitly rather than treating
    exactness as the claim.
    """
    rho = dg.spearman(fit.x, colley_fit.r)
    assert rho == 0.0
    assert rho == EXPECTED_SPEARMAN_MASSEY_COLLEY
    # No ties in either ranking, so the ranks are a permutation of 1..15.
    ranks_x = dg.average_ranks(fit.x)
    ranks_c = dg.average_ranks(colley_fit.r)
    assert sorted(ranks_x.tolist()) == list(range(1, 16))
    assert sorted(ranks_c.tolist()) == list(range(1, 16))
    centred_x = ranks_x - ranks_x.mean()
    centred_c = ranks_c - ranks_c.mean()
    assert float(centred_x @ centred_c) == 0.0
    # Pearson on the raw values, by contrast, is not zero -- so the two statistics
    # are genuinely different objects and reporting only one would mislead.
    assert round(float(np.corrcoef(fit.x, colley_fit.r)[0, 1]), 3) == (
        EXPECTED_PEARSON_MASSEY_COLLEY
    )


def test_average_ranks_handles_ties_by_averaging() -> None:
    """The tie path, checked against a hand-computed example.

    ``[10, 20, 20, 30] -> [1, 2.5, 2.5, 4]``. Ties get the mean of the ranks they
    span, never an arbitrary side -- otherwise the answer would depend on the sort
    order, and this snapshot happens to have no ties at all, so a tie-handling bug
    would be invisible here and would surface only on someone else's data.

    The paired Spearman is then hand-checkable too: ranks ``[1, 2.5, 2.5, 4]``
    against ``[1, 2, 4, 3]`` give ``3/sqrt(22.5) = 0.63246``.
    """
    assert dg.average_ranks(np.array([10.0, 20.0, 20.0, 30.0])).tolist() == [
        1.0,
        2.5,
        2.5,
        4.0,
    ]
    # All four equal: every rank is the mean of 1..4.
    assert dg.average_ranks(np.array([5.0, 5.0, 5.0, 5.0])).tolist() == [2.5] * 4
    # No ties: a clean permutation, independent of input order.
    assert dg.average_ranks(np.array([3.0, 1.0, 2.0])).tolist() == [3.0, 1.0, 2.0]
    assert dg.average_ranks(np.array([2.0, 3.0, 1.0])).tolist() == [2.0, 3.0, 1.0]
    # Leading and trailing ties both average: [7,7] span ranks 2 and 3 -> 2.5, and
    # [9,9] span ranks 4 and 5 -> 4.5, with the lone 1 taking rank 1.
    assert dg.average_ranks(np.array([7.0, 7.0, 1.0, 9.0, 9.0])).tolist() == [
        2.5,
        2.5,
        1.0,
        4.5,
        4.5,
    ]
    rho = dg.spearman(np.array([10.0, 20.0, 20.0, 30.0]), np.array([1.0, 2.0, 4.0, 3.0]))
    assert rho == pytest.approx(3.0 / np.sqrt(22.5), rel=1e-14)
    assert round(rho, 3) == 0.632


def test_spearman_reduces_to_the_closed_form_when_there_are_no_ties(
    fit, colley_fit
) -> None:
    """``1 - 6*sum(d^2)/(n^3-n)`` must agree with the implementation here.

    Independent verification of the hand-rolled code against the textbook
    one-liner. The agreement is asserted **only** on tie-free input, and that
    restriction is the point: the closed form is wrong the moment a tie appears,
    so running it as a cross-check everywhere would validate the tie handling
    against a formula that does not model it. Both rankings here are tie-free,
    which ``test_spearman_between_the_two_models_is_exactly_zero`` establishes.
    """
    n = EXPECTED_NUM_TEAMS
    ranks_x = dg.average_ranks(fit.x)
    ranks_c = dg.average_ranks(colley_fit.r)
    squared_difference = float(np.sum((ranks_x - ranks_c) ** 2))
    closed_form = 1.0 - 6.0 * squared_difference / (n**3 - n)
    assert dg.spearman(fit.x, colley_fit.r) == pytest.approx(closed_form, abs=1e-12)


def test_official_points_must_be_joined_on_team_not_read_in_row_order(
    fit, colley_fit, systems, official_points
) -> None:
    """The alignment trap, pinned because this project fell into it once.

    ``data.official_table()`` returns rows sorted by **points**; the fitted vectors
    are in **alphabetical team order**. Correlating them positionally measures a
    relationship between two different orderings and produces a plausible,
    stable, meaningless number.

    Measured both ways:

    ==================================  ==========
    pairing                             rho
    ==================================  ==========
    joined on ``team`` (correct)       ``+0.939``
    positional over ``official_df``     ``-0.121``
    ==================================  ==========

    The wrong one has the same sign and roughly the same magnitude as
    Spearman(Massey, Colley), so it would have passed a "these are unrelated"
    eyeball check. Only the joined figure is a statement about the models. The
    assertion is that they **differ**, so a future refactor cannot quietly swap
    the join for a positional read.
    """
    positional = systems.official["points"].to_numpy().astype(float)
    joined = dg.spearman(colley_fit.r, official_points)
    misaligned = dg.spearman(colley_fit.r, positional)
    assert round(joined, 3) == EXPECTED_SPEARMAN_COLLEY_OFFICIAL
    assert round(misaligned, 3) == -0.121
    assert abs(joined - misaligned) > 1.0
    # And the contract that makes the join possible: alphabetical order is
    # recoverable from the official table alone.
    assert sorted(systems.official["team"].tolist()) == list(systems.teams)


def test_winner_accuracy_to_three_decimals(systems, fit) -> None:
    """**0.5502**, the best-looking number in the margin fit.

    Asserted to 4 decimals (tighter than the 3 asked for) *and* as the exact
    fraction ``307 / 558``, because "0.550 to 3 dp" on its own would be satisfied
    by a wide band of wrong answers. The exact count is what makes this a
    measurement rather than a decimal.

    The context is asserted alongside it, because the number on its own is
    misleading: a two-sided coin flip is 0.50, so 55% is barely above chance, and
    out of sample the same measure falls to **0.4316** -- below chance.
    """
    accuracy = dg.winner_accuracy(systems.A @ fit.x, systems.b)
    assert round(accuracy, 4) == EXPECTED_WINNER_ACCURACY
    assert accuracy == pytest.approx(307 / 558, abs=1e-15)
    assert accuracy > 0.5
    assert accuracy < 0.6


def test_winner_accuracy_treats_a_zero_prediction_as_a_miss(systems) -> None:
    """A prediction of exactly zero names no team, so it cannot be a win.

    Fixed by convention rather than left to a comparison that happens not to fire
    on this data -- the closest any prediction comes to zero here is 0.1995 runs,
    so an implementation using ``>= 0`` would agree with the correct one today and
    silently diverge on someone else's.
    """
    assert np.abs(systems.A @ models.massey(systems.A, systems.b).x).min() == pytest.approx(
        0.1995, abs=1e-4
    )
    b = np.array([5.0, -5.0, 5.0])
    assert dg.winner_accuracy(np.array([1.0, -1.0, 0.0]), b) == pytest.approx(2 / 3)
    with pytest.raises(ValueError):
        dg.winner_accuracy(np.array([1.0, -1.0]), b)


# --------------------------------------------------------------------------
# The two tables
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def official_table_frame(systems, fit, colley_fit):
    se, _, _ = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    return dg.official_comparison(fit.x, colley_fit.r, systems.official, se)


@pytest.fixture(scope="module")
def summary(systems, fit, colley_fit):
    se, _, _ = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    return dg.summary_table(
        systems.teams, fit.x, se, colley_fit.r, systems.official, systems.games
    )


def test_summary_table_has_fifteen_rows_sorted_by_massey_desc(summary) -> None:
    """15 rows, one per canonical franchise, ordered by fitted strength.

    The sort is the table's argument: descending ``massey_x`` puts the two
    five-game franchises at the top, where the diagnosis is. A reader who only
    skims sees "Kochi Tuskers Kerala, by a mile" and the ``games_played`` column
    next to it says "from 5 matches".
    """
    assert list(summary.columns) == [
        "team",
        "games_played",
        "massey_x",
        "massey_se",
        "colley_share",
        "points",
    ]
    assert len(summary) == EXPECTED_NUM_TEAMS
    assert summary["team"].nunique() == EXPECTED_NUM_TEAMS
    strengths = summary["massey_x"].to_numpy()
    assert np.all(np.diff(strengths) < 0.0), "not sorted by massey_x descending"
    assert set(summary["team"]) == set(summary["team"])


def test_summary_table_carries_a_visible_games_played_column(summary, systems) -> None:
    """The column is present **and** it is the diagnosis.

    ``corr(games_played, |massey_x|) = -0.663``: the fewer matches a franchise
    played, the more extreme its fitted strength. Hiding that column would turn
    the table from a statement about sample size into a statement about team
    quality, which is the specific misreading this project exists to correct.

    Asserted structurally (the column is there, per-team, integral) *and*
    substantively (the top row is a 5-game franchise, and the most-measured
    franchise is nowhere near the top).
    """
    assert "games_played" in summary.columns
    played = summary["games_played"].to_numpy()
    assert played.size == EXPECTED_NUM_TEAMS
    assert np.array_equal(np.sort(played), np.sort(systems.games))
    assert int(played.sum()) == 2 * EXPECTED_M
    top = summary.iloc[0]
    assert top["team"] == "Kochi Tuskers Kerala"
    assert int(top["games_played"]) == 5
    assert round(float(top["massey_x"]), 4) == 17.4283
    # The best-measured franchise is mid-table, not the top.
    best_measured = summary.loc[
        summary["games_played"] == int(systems.games.max()), "team"
    ].iloc[0]
    assert best_measured == "Mumbai Indians"
    assert int(
        summary.index[summary["team"] == best_measured][0]
    ) > 0


def test_summary_table_massey_values_are_not_misaligned(summary, systems, fit) -> None:
    """Each team's coefficient sits on **that team's row**.

    The guard against the alignment trap of
    ``test_official_points_must_be_joined_on_team_not_read_in_row_order``: a
    misaligned table is still a well-formed table with 15 rows and a correct
    sort, so only comparing values against ``fit.x`` by name catches it.
    """
    for index, team in enumerate(systems.teams):
        row = summary.loc[summary["team"] == team].iloc[0]
        assert float(row["massey_x"]) == pytest.approx(float(fit.x[index]), rel=1e-12)


def test_official_comparison_shape_columns_and_sort(official_table_frame) -> None:
    """Nine columns in the specified order, sorted by points then team.

    Sorted by **official** points, so it reads as the authority with the two fits
    annotated onto it -- the visual claim being that Colley's rank column runs
    alongside the official one while Massey's does not.
    """
    assert list(official_table_frame.columns) == [
        "team",
        "points",
        "official_rank",
        "massey_x",
        "massey_se",
        "massey_rank",
        "colley_share",
        "colley_rank",
        "rank_movement",
    ]
    assert len(official_table_frame) == EXPECTED_NUM_TEAMS
    points = official_table_frame["points"].to_numpy()
    assert np.all(np.diff(points) <= 0), "not sorted by points descending"
    top_two = official_table_frame["team"].tolist()[:2]
    assert top_two == ["Mumbai Indians", "Chennai Super Kings"]
    # Within a points tie the team name breaks it, so the ordering is total.
    for (_, left), (_, right) in zip(
        official_table_frame.iterrows(), official_table_frame.iloc[1:].iterrows()
    ):
        if left["points"] == right["points"]:
            assert left["team"] < right["team"]


def test_official_comparison_ranks_are_permutations_and_movement_is_consistent(
    official_table_frame,
) -> None:
    """All three rank columns are permutations of ``1..15``, and
    ``rank_movement == massey_rank - official_rank`` exactly.

    A permutation, not a competition ranking: ties are broken by name so every
    column is consecutive and a movement is a plain integer difference. And the
    sign convention is pinned by two named rows rather than left to the reader:
    Kochi is 15th officially and 1st in the Massey fit (**-14**), Mumbai Indians
    is 1st officially and 7th in the fit (**+6**). Positive means the margin fit
    ranks a team worse than the official table does.
    """
    for column in ("official_rank", "massey_rank", "colley_rank"):
        assert sorted(official_table_frame[column].tolist()) == list(range(1, 16))
    assert np.array_equal(
        official_table_frame["rank_movement"].to_numpy(),
        (
            official_table_frame["massey_rank"].to_numpy()
            - official_table_frame["official_rank"].to_numpy()
        ),
    )
    named = official_table_frame.set_index("team")
    assert int(named.loc["Kochi Tuskers Kerala", "rank_movement"]) == -14
    assert int(named.loc["Mumbai Indians", "rank_movement"]) == 6
    # Colley's ordering is much closer to the official one, which is the point of
    # the table: 5 of the 15 teams land on exactly the official rank, against 0 of
    # 15 for the margin fit.
    colley_movement = np.abs(
        official_table_frame["colley_rank"].to_numpy()
        - official_table_frame["official_rank"].to_numpy()
    )
    massey_movement = np.abs(
        official_table_frame["rank_movement"].to_numpy()
    )
    assert int((colley_movement == 0).sum()) == 5
    assert int((massey_movement == 0).sum()) == 0
    # And the spread of the two is the finding in one comparison.
    assert int(colley_movement.max()) == 4
    assert int(massey_movement.max()) == 14


def test_official_comparison_keeps_each_team_on_its_own_values(
    official_table_frame, systems, fit, colley_fit
) -> None:
    """Values checked against the source vectors **by name**, not by row.

    This is the specific failure the table is vulnerable to: it takes fitted
    vectors in one order and an official table in another, so a positional mix-up
    would produce a table that looks completely normal.
    """
    for index, team in enumerate(systems.teams):
        row = official_table_frame.loc[official_table_frame["team"] == team].iloc[0]
        assert float(row["massey_x"]) == pytest.approx(float(fit.x[index]), rel=1e-12)
        assert float(row["colley_share"]) == pytest.approx(
            float(colley_fit.r[index]), rel=1e-12
        )
        assert int(row["points"]) == int(
            systems.official.set_index("team").loc[team, "points"]
        )


def test_both_tables_reject_misaligned_input(systems, fit, colley_fit) -> None:
    """Mismatched lengths must fail loudly. Both tables index everything by
    position, so a vector of the wrong length is a silent misattribution."""
    se, _, _ = dg.standard_errors(systems.A, fit.resid, fit.rank, x=fit.x)
    with pytest.raises(ValueError):
        dg.summary_table(
            systems.teams, fit.x[:-1], se, colley_fit.r, systems.official, systems.games
        )
    with pytest.raises(ValueError):
        dg.summary_table(
            systems.teams, fit.x, se, colley_fit.r, systems.official, systems.games[:-1]
        )
    with pytest.raises(ValueError):
        dg.official_comparison(
            fit.x, colley_fit.r, systems.official.rename(columns={"points": "pts"}), se
        )
    with pytest.raises(ValueError):
        dg.official_comparison(fit.x, colley_fit.r, systems.official.iloc[:-1], se)