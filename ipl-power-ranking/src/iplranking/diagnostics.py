"""Diagnostics: the numbers that decide whether the fit is any good.

``models.py`` produces two rankings. This module asks the questions that matter,
and answers every one of them in the negative:

1. **Does the fit explain anything?** Barely. Centred ``R^2 = -0.2103`` for the
   no-intercept design, ``+0.0181`` once the intercept it was never allowed is
   added. See :func:`intercept_model` -- the negative number is a *specification*
   artefact, not a noise finding, and this module is where that is measured.
2. **Is any team's strength distinguishable from zero?** No. The largest
   ``|x/se|`` over all 15 franchises is **1.20**, so not one coefficient reaches
   2 sigma.
3. **Does either ranking agree with the official points table?** Only the one
   that never saw a margin. Spearman ``+0.939`` for Colley, ``+0.093`` for
   Massey.

Two denominators, both reported
-------------------------------
``R^2`` has two standard-looking definitions and they disagree **in sign**:

===================  ================  ==========  ==========================
denominator          sum of squares   measured    meaning
===================  ================  ==========  ==========================
``sum(b^2)``         948,444.0        ``+0.0214`` uncentred: looks positive
``sum((b-b)^2)``     766,931.3        ``-0.2103`` centred: the real one
===================  ================  ==========  ==========================

**The inherited build audit, the handoff and the old spec all headline
``+0.0214`` and none of them headline ``-0.2103``.** That is how a model worse
than a constant shipped with a positive-sounding fit statistic, and it is the
same class of error as the two wrong dataset counts this repository has already
paid for. ``r_squared`` therefore takes ``centred`` as a **keyword argument with
no default**: ``r_squared(b, pred)`` does not merely default, it does not
compile. A silent default is how this error survived.

**And then ``-0.2103`` itself was retracted as a *cause*.** It is not evidence
that noise beats signal; it is what a model that is *forbidden* from fitting a
constant looks like. ``A @ 1 = 0`` (stage 4) means ``A x`` cannot represent a
constant, so the fit sits ``17.30`` runs low on every single match and is
guaranteed to lose the comparison with the mean. :func:`intercept_model` adds the
one column ``A`` was not allowed to have and the number moves to ``+0.0181`` --
still nothing, but for an honest reason. Stages 4 and 8 are one argument.

The measured figures, all 2026-10-04
------------------------------------
============================  =========  ==================================
quantity                      value      note
============================  =========  ==================================
``||r||^2``                   928185.2   558 run margins
``sigma2 = ||r||^2/544``      1706.2228  544 = m - rank, ``rank(A) = 14``
``se`` range                  4.68-17.63 two teams at ~17.63, both 5-game
                                         franchises
``max |x/se|``                1.20       Rajasthan Royals; nothing at 2 sigma
winner accuracy               0.5502     ``307 / 558``, in sample
majority-class baseline       0.7796     ``435 / 558`` -- see the warning
held-out accuracy             0.4316     ``41 / 95``, on a degenerate split
majority share, test seasons  1.0000     ``95 / 95``: never varies at all
intercept (one extra column)  18.1369    moves centred ``R^2`` to ``+0.0181``
``mean(b) - mean(A x_hat)``    17.3014    the bias, in runs
residual spread               40.7850    ``||r|| / sqrt(m)``
fitted spread                 5.9805     ``std(A x_hat)``
noise over signal             6.8196     the two spreads above, ratioed
Spearman(Massey, Colley)      0.000      *exactly* zero -- pinned, see below
Pearson(Massey, Colley)      -0.1217
Spearman(Massey, official)   +0.093
Spearman(Colley, official)   +0.939
``corr(games, |x|)``          -0.663     short history -> extreme coefficient
============================  =========  ==================================

A measured correction to the majority-class baseline, recorded here because it is
the second time this project has nearly published a wrong percentage
-------------------------------------------------------------------------------
An adversarial review reported the majority class at **77.96%**; the correction
that reached this module claimed the reviewer was wrong and gave **62.19%**
(``347 / 558``). **The reviewer was right.** Measured on the snapshot:

===================================  ======  ===========================
comparison                           wins    share
===================================  ======  ===========================
``canonical(winner) == team1``       435     ``0.77956989``  **77.96%**
raw ``winner`` string == ``team1``   347     ``0.62186380``  62.19%
``sign(b) > 0``                      435     ``0.77956989``
===================================  ======  ===========================

The 62.19% comes from comparing the **raw** ``winner`` string against the
**canonical** ``team1`` column. Those differ for the 88 run-margin matches
involving a renamed franchise -- ``Delhi Daredevils`` vs ``Delhi Capitals``,
``Kings XI Punjab`` vs ``Punjab Kings``, and so on -- so all 88 are scored as
losses for a team that won. It is the same canonicalisation mismatch
:func:`data.design_matrix` carries an explicit row-sum guard against, and the
correct figure is the one that agrees with ``sign(b)``, because ``sign(b)`` is
the convention the model's predictions are scored in.

The **direction** of the finding survives either way and is what is reported:
``0.5502 < 0.6219`` and ``0.5502 < 0.7796``, so the model has **negative skill**
against the relevant baseline under both numbers. :func:`majority_class_accuracy`
now *requires* the two conventions to agree and raises otherwise, so this exact
error cannot recur silently.

``Spearman(Massey, Colley)`` being exactly ``0.0`` is a property of the data, not
a bug: neither vector has a tie, so both have ranks ``1..15`` with no averaging,
and the Pearson correlation of the two rank vectors cancels to zero on the last
bit. It is pinned by a test so a future dataset that moves it off zero is
noticed rather than explained away.

Two deviations from the dispatch, both forced and both recorded
---------------------------------------------------------------
1. :func:`standard_errors` takes ``x`` as a **required keyword**. The dispatch
   wrote the signature as ``standard_errors(A, resid, rank)`` and asked it to
   return ``t = x / se``, but ``x`` cannot be recovered from ``A`` and
   ``resid``: ``resid = b - A x`` needs ``b`` to invert. Rather than guess ``x``
   inside the function -- which is the exact silent-default failure
   :func:`r_squared` is built to prevent -- the caller supplies it and a
   three-argument call raises.
2. :func:`official_comparison` takes ``se`` as a required fourth argument, for
   the same reason: its ``massey_se`` column must describe the ``x`` passed in,
   and re-deriving standard errors internally would silently report the errors of
   a *different* fit whenever a caller passed some other ``x``.

No SciPy. :func:`spearman` is hand-rolled, average-tie ranks and all.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = [
    "InterceptFit",
    "SignalNoise",
    "average_ranks",
    "intercept_model",
    "majority_class_accuracy",
    "noise_vs_signal",
    "official_comparison",
    "r_squared",
    "spearman",
    "standard_errors",
    "summary_table",
    "team1_share_by_season",
    "team1_win_share",
    "team1_won_flags",
    "winner_accuracy",
]


# --------------------------------------------------------------------------
# R^2, with the denominator spelled out
# --------------------------------------------------------------------------


def r_squared(b: np.ndarray, pred: np.ndarray, *, centred: bool) -> float:
    """Coefficient of determination, with the denominator chosen **explicitly**.

    ``1 - SSres / SS_tot``, and ``SS_tot`` has two legitimate denominators that
    do not agree:

    ``centred=True``
        ``SS_tot = sum((b - mean(b))**2)``, i.e. the variance of the outcome
        being explained. This is the standard definition, and it compares the
        model against the best constant predictor.
    ``centred=False``
        ``SS_tot = sum(b**2)``, the total squared magnitude, correct only when
        the outcome is already mean-centred.

    **Measured on this project: ``-0.2103`` centred, ``+0.0214`` uncentred.**
    The sign flips because ``sum(b^2) = 948,444`` is larger than
    ``sum((b-b)^2) = 766,931``, so the uncentred ratio is smaller and the
    subtraction leaves a small positive number.

    The inherited build audit, the handoff and the earlier spec headline the
    uncentred figure and never print the centred one. Read alone, ``+0.0214``
    says "the model explains 2% of the variation"; the centred figure says the
    model is **worse than predicting the mean margin**, which is the true
    statement about this data and the reason the whole project is framed around
    signal-to-noise rather than around a fit.

    Parameters
    ----------
    b, pred
        The observed margins and the model's predictions on them. Same length.
    centred
        **Keyword-only and required, with no default.** ``r_squared(b, pred)``
        raises ``TypeError``. There is no safe default here: ``True`` and
        ``False`` produce numbers of opposite sign, so guessing one would put a
        quietly wrong claim into a printed table. Every call site in this project
        names the denominator.

    Returns
    -------
    float
        The coefficient of determination, negative on this data under both
        denominators.
    """
    observed = np.asarray(b, dtype=np.float64).ravel()
    predicted = np.asarray(pred, dtype=np.float64).ravel()
    if observed.shape != predicted.shape:
        raise ValueError(
            f"b has {observed.size} entries but pred has {predicted.size}; R^2 "
            "needs the predictions for exactly the outcomes being scored"
        )
    if observed.size == 0:
        raise ValueError("R^2 is undefined for an empty sample")

    ss_res = float(np.sum((observed - predicted) ** 2))
    if centred:
        ss_tot = float(np.sum((observed - observed.mean()) ** 2))
    else:
        ss_tot = float(np.sum(observed**2))
    if ss_tot == 0.0:  # pragma: no cover - impossible on the committed snapshot
        raise ValueError(
            "the total sum of squares is zero, so R^2 is undefined; the outcome "
            "vector is constant"
        )
    return 1.0 - ss_res / ss_tot


# --------------------------------------------------------------------------
# The intercept the design matrix is not allowed to have
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SignalNoise:
    """The three spreads, and the one ratio between them that is well defined.

    The old project compared ``std(b) = 37.07`` against ``std(x) = 7.03`` and
    called the quotient ``0.19`` a signal-to-noise ratio. That compared the
    spread of the **data** with the spread of the **coefficients** -- two
    different objects in two different units-of-meaning -- and the ratio was not
    a quantity anyone could act on. These three are all spreads of the *fitted
    and observed margins*, in the same units, so the ratio is meaningful:

    =================  ==============  =========  =========================
    field              measured        unit       what it is
    =================  ==============  =========  =========================
    ``margin_spread``  ``37.0733``    runs       ``std(b)``: how much the
                                                    signed margins vary
                                                    overall
    ``residual_spread`` ``40.7850``   runs       ``||r|| / sqrt(m)``: what
                                                    the model cannot explain
    ``fitted_spread``  ``5.9805``     runs       ``std(A x_hat)``: what it can
    ``ratio``          ``6.8196``     dimensionless, the two above
    =================  ==============  =========  =========================

    ``std(b)`` is still reported, because "the margins run from -146 to +146 with
    a spread of 37 runs" is a true and useful thing to know. It is just not "the
    noise": it contains both the team signal and the mean offset, and it is not
    the residual.
    """

    margin_spread: float
    residual_spread: float
    fitted_spread: float
    ratio: float


def noise_vs_signal(A: np.ndarray, b: np.ndarray, x: np.ndarray) -> SignalNoise:
    """Residual spread against fitted spread, in runs, and their ratio.

    ``residual_spread = ||b - A x|| / sqrt(m)`` -- the RMS residual, i.e. the
    typical size of the margin the model fails to explain, measured **40.7850**
    runs.

    ``fitted_spread = std(A x)`` -- the RMS fitted margin, i.e. the typical size of
    the difference between two teams as the model sees it, measured **5.9805**
    runs.

    Their quotient is measured **6.8196**: the unexplained margin is about **6.8x**
    the team signal. That is the diagnosis, and it is a comparison of like with
    like.

    ``std(b) = 37.0733`` is returned too, as ``margin_spread``, under the name it
    actually deserves. Note it is *smaller* than ``residual_spread``, which is not
    a contradiction: ``b`` has a mean of ``+18.04`` and the residual is measured
    about that mean.

    Parameters
    ----------
    A, b
        The Massey system and its signed margins.
    x
        The fitted strengths. Any member of the equivalence class ``x + c*1``
        gives the same answer, because ``A @ 1 == 0`` -- so this is not a
        gauge-sensitive argument and no particular gauge is imposed.

    Returns
    -------
    SignalNoise
    """
    M = np.asarray(A, dtype=np.float64)
    rhs = np.asarray(b, dtype=np.float64).ravel()
    estimates = np.asarray(x, dtype=np.float64).ravel()
    if M.ndim != 2:
        raise ValueError(f"A must be 2-D, got shape {M.shape}")
    if M.shape[0] != rhs.size:
        raise ValueError(
            f"A has {M.shape[0]} rows but b has {rhs.size} entries; the spreads "
            "are computed over matched rows"
        )
    if estimates.size != M.shape[1]:
        raise ValueError(
            f"x has {estimates.size} entries but A has {M.shape[1]} columns"
        )
    m = M.shape[0]
    if m == 0:  # pragma: no cover - A is (558, 15)
        raise ValueError("a 0-row system has no spread to report")

    residual = rhs - M @ estimates
    fitted = M @ estimates
    residual_spread = float(np.linalg.norm(residual) / np.sqrt(m))
    fitted_spread = float(fitted.std())
    if fitted_spread == 0.0:  # pragma: no cover - A is not a zero matrix
        raise ValueError(
            "the fitted margins are constant, so the signal spread is zero and "
            "noise over signal is infinite; there is nothing to ratio"
        )
    return SignalNoise(
        margin_spread=float(rhs.std()),
        residual_spread=residual_spread,
        fitted_spread=fitted_spread,
        ratio=residual_spread / fitted_spread,
    )


@dataclass(frozen=True)
class InterceptFit:
    """The same model, with the one column ``A`` was never allowed to have.

    ``A`` has ``A @ 1 = 0`` exactly -- every row has one ``+1`` and one ``-1`` --
    so ``A x`` can never equal a constant vector, no matter what ``x`` is. The
    consequence is arithmetic, not statistical: with ``mean(b) = +18.04`` and
    ``mean(A x_hat) = +0.73``, the fit is **17.30 runs low on every one of the
    558 matches**, and is therefore guaranteed to lose the centred ``R^2``
    comparison with a single constant. Measured, with one extra column of ones:

    ============================  ==============  ==============
    quantity                     no intercept    with intercept
    ============================  ==============  ==============
    ``SS_res``                   928,185.2       **753,087.7**
    ``R^2`` centred              ``-0.2103``     **``+0.0181``**
    ``R^2`` uncentred            ``+0.0214``     ``+0.2060``
    mean of the fitted margins   ``+0.7344``     ``+18.8713``
    ============================  ==============  ==============

    So the negative number was **structural, not empirical**: the rank deficiency
    that stage 4 proves is the reason the stage-8 statistic looks the way it does.
    And the corrected number is not a rescue -- ``+0.0181`` is still no signal.
    Both are reported, each labelled.

    Attributes
    ----------
    intercept
        The constant column's coefficient, measured **18.1369** runs. It is *not*
        the mean margin (``18.0358``); the difference is what the 15 team
        coefficients still have to absorb, and it is small because the intercept
        absorbs almost all of the level.
    x
        The 15 team strengths from the augmented fit, in runs. Not equal to the
        no-intercept fit even after recentring: adding a column raises the rank
        from 14 to 15, so this is a genuinely different estimate, not a shifted
        copy.
    r_squared_centred, r_squared_uncentred
        Both denominators again, for the augmented fit.
    ss_res, ss_tot_centred
        The sums of squares behind them.
    mean_b, mean_fitted, bias
        ``mean(b) = 18.0358``; the **no-intercept** fit's mean fitted margin
        ``0.7344``; and their difference, ``17.3014`` runs, which is the whole
        finding in one subtraction.
    spread
        The :class:`SignalNoise` measured on the **no-intercept** fit: residual
        ``40.7850``, fitted ``5.9805``, ratio ``6.8196``. ``fitted_spread`` and
        ``residual_spread`` are also exposed directly on this object.
    """

    intercept: float
    x: np.ndarray
    r_squared_centred: float
    r_squared_uncentred: float
    ss_res: float
    ss_tot_centred: float
    mean_b: float
    mean_fitted: float
    bias: float
    spread: SignalNoise

    @property
    def residual_spread(self) -> float:
        """``||r|| / sqrt(m)`` on the no-intercept fit, measured **40.7850**."""
        return self.spread.residual_spread

    @property
    def fitted_spread(self) -> float:
        """``std(A x_hat)``, measured **5.9805**. Unchanged by the intercept."""
        return self.spread.fitted_spread


def intercept_model(A: np.ndarray, b: np.ndarray) -> InterceptFit:
    """Append one constant column to ``A``, refit, and report what changes.

    This is the correction to the project's most-misreported number, and it is
    **not** an alternative model -- it is the *same* model with the one degree of
    freedom ``A @ 1 = 0`` forbids. Adding the column lifts ``rank(A)`` from 14 to
    15, so the augmented normal equations are nonsingular and the augmented fit
    can represent a constant. What it measures is whether the stage-8 headline
    survives being allowed to do that.

    Measured answer: **no.** ``SS_res`` falls from ``928,185.2`` to
    ``753,087.7`` and centred ``R^2`` rises from ``-0.2103`` to ``+0.0181`` -- a
    genuine improvement of 22.9% of the residual sum of squares, and still a fit
    that explains **1.8% of the centred variation**.

    ``x`` is *not* a parameter. The no-intercept least-squares fit is recovered
    internally because it is needed to state ``mean_fitted`` and ``bias``, and it
    is recovered by ``lstsq`` rather than accepted from a caller for a reason:
    ``A @ x`` is **gauge-invariant** here (``A @ (x + c*1) == A @ x``), so there is
    no choice of gauge that could change the answer. Nothing is being guessed.

    Parameters
    ----------
    A, b
        The Massey system, ``(558, 15)`` and ``(558,)``.

    Returns
    -------
    InterceptFit
    """
    M = np.asarray(A, dtype=np.float64)
    rhs = np.asarray(b, dtype=np.float64).ravel()
    if M.ndim != 2:
        raise ValueError(f"A must be 2-D, got shape {M.shape}")
    if M.shape[0] != rhs.size:
        raise ValueError(
            f"A has {M.shape[0]} rows but b has {rhs.size} entries; the "
            "intercept model is the same system with one column appended"
        )
    if rhs.size == 0:  # pragma: no cover - A is (558, 15)
        raise ValueError("an empty sample has no intercept fit to report")

    m, n = M.shape
    augmented = np.hstack([M, np.ones((m, 1), dtype=np.float64)])
    solution = np.linalg.lstsq(augmented, rhs, rcond=None)[0]
    fitted = augmented @ solution

    no_intercept = np.linalg.lstsq(M, rhs, rcond=None)[0]
    mean_fitted = float((M @ no_intercept).mean())

    return InterceptFit(
        intercept=float(solution[-1]),
        x=np.asarray(solution[:-1], dtype=np.float64),
        r_squared_centred=r_squared(rhs, fitted, centred=True),
        r_squared_uncentred=r_squared(rhs, fitted, centred=False),
        ss_res=float(np.sum((rhs - fitted) ** 2)),
        ss_tot_centred=float(np.sum((rhs - rhs.mean()) ** 2)),
        mean_b=float(rhs.mean()),
        mean_fitted=mean_fitted,
        bias=float(rhs.mean()) - mean_fitted,
        spread=noise_vs_signal(M, rhs, no_intercept),
    )


# --------------------------------------------------------------------------
# Standard errors
# --------------------------------------------------------------------------


def standard_errors(
    A: np.ndarray,
    resid: np.ndarray,
    rank: int,
    *,
    x: np.ndarray,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Per-team standard errors, the residual variance, and the t statistics.

    ``sigma2 = ||r||^2 / (m - rank)`` -- measured **1706.2228** for
    ``m = 558``, ``rank(A) = 14``, so ``544`` degrees of freedom and not ``558``.
    Spending one per estimated coefficient is the standard correction and here it
    is not cosmetic: it raises ``sigma2`` by 2.8% over ``||r||^2/558``.

    The covariance used is the one the dispatch prescribes,
    ``Cov = sigma2 * inv(A.T@A + 1*1.T)``, giving ``se`` from **4.68 to 17.63**
    runs and ``max|x/se| = 1.20``.

    **What that covariance is, measured rather than asserted.** It is *not* the
    exact covariance of the constrained estimator, and the difference is worth
    stating because the numbers are quoted in the demo. Writing ``K = A.T@A +
    11.T``, one computes and this project pins

        ``K^-1 == (A.T@A)^+ + (1/15^2) * 1*1.T``    (to 5.7e-16, measured)

    because ``1.T @ K = 15 * 1.T``, which forces ``1.T @ K^-1 = (1/15) * 1.T``.
    So ``sigma2 * K^-1`` is the **minimum-norm** estimator's covariance
    ``sigma2 * (A.T@A)^+`` -- the right covariance for the SVD route
    :func:`models.massey` actually returns -- plus a rank-one term that adds the
    same ``sigma2/225 = 7.5832`` to every variance. The exact covariance of the
    *constrained* estimator would instead be ``sigma2 * (I - 1*1.T/15)``, whose
    diagonal is constant, giving a flat 39.91 for all fifteen.

    None of that changes the finding, and the difference is measured rather than
    left implicit:

    ==================================  ==========  ============
    covariance                           ``max|t|``  2 sigma?
    ==================================  ==========  ============
    ``sigma2 * K^-1`` (dispatched)       **1.2017**  no
    ``sigma2 * (A.T@A)^+`` (exact)      1.4329      no
    ``sigma2 * (I - 11.T/15)``          0.4367      no
    ==================================  ==========  ============

    The dispatched figure is the one reported, because it is the one the measured
    targets pin. The other two are computed in the test suite so the claim "not
    one coefficient is significant at 2 sigma" is shown to be a property of the
    data rather than of a debatable covariance formula.

    Parameters
    ----------
    A, resid
        The design matrix and its residual ``b - A x``. Only the residual's norm
        and ``A`` are used, so a caller cannot get the variance and the
        covariance out of step.
    rank
        The rank of ``A``, passed in rather than recomputed so the degrees of
        freedom are the same ``544`` that were used to state them.
    x
        **Required keyword.** ``t = x / se`` needs it and it is not recoverable
        from ``A`` and ``resid``; see the module docstring. A call omitting it
        raises rather than defaulting.

    Returns
    -------
    ``(se, sigma2, t_stats)``
        ``se`` is ``(n,)`` in runs, ``sigma2`` a float, ``t_stats`` is
        ``x / se``, dimensionless.
    """
    M = np.asarray(A, dtype=np.float64)
    r = np.asarray(resid, dtype=np.float64).ravel()
    estimates = np.asarray(x, dtype=np.float64).ravel()
    if M.ndim != 2:
        raise ValueError(f"A must be 2-D, got shape {M.shape}")
    n = M.shape[1]
    if r.size != M.shape[0]:
        raise ValueError(
            f"A has {M.shape[0]} rows but resid has {r.size} entries; the "
            "degrees of freedom are computed from these two and must match"
        )
    if estimates.size != n:
        raise ValueError(
            f"x has {estimates.size} entries but A has {n} columns; one "
            "coefficient is fitted per team"
        )
    dof = M.shape[0] - int(rank)
    if dof <= 0:
        raise ValueError(
            f"m - rank = {M.shape[0]} - {rank} = {dof} degrees of freedom; the "
            "residual variance is undefined with none left"
        )

    sigma2 = float(r @ r) / dof
    ones = np.ones(n, dtype=np.float64)
    covariance = sigma2 * np.linalg.inv(M.T @ M + np.outer(ones, ones))
    se = np.sqrt(np.diag(covariance))
    return se, sigma2, estimates / se


# --------------------------------------------------------------------------
# Rank correlation, by hand
# --------------------------------------------------------------------------


def average_ranks(values: np.ndarray) -> np.ndarray:
    """Ranks ``1..n``, with tied values sharing the **average** of their ranks.

    Hand-rolled because there is no SciPy in this project's stack, and because
    the tie rule is a decision worth being able to see rather than import.

    A tie does not get an arbitrary side rank, which would make the answer depend
    on the sort order. Tied entries get the mean of the ranks they span:
    ``[10, 20, 20, 30] -> [1, 2.5, 2.5, 4]``. Measured, and asserted in the suite.

    This matters whenever ties exist. In this project they do **not** -- all 15
    Massey coefficients and all 15 Colley shares are distinct, and the official
    points table has no tie either -- so ``average_ranks`` returns a clean
    permutation of ``1..15`` here and Spearman reduces to Pearson on the ranks.
    The tie path is still exercised by a hand-checked example, because a ranking
    routine that has never been given a tie has never been tested.
    """
    data = np.asarray(values, dtype=np.float64).ravel()
    if data.size == 0:
        raise ValueError("cannot rank an empty vector")
    if not np.all(np.isfinite(data)):
        raise ValueError("cannot rank a vector containing NaN or infinity")

    order = np.argsort(data, kind="stable")
    ordered = data[order]
    ranks = np.empty(data.size, dtype=np.float64)

    start = 0
    while start < data.size:
        stop = start
        while stop + 1 < data.size and ordered[stop + 1] == ordered[start]:
            stop += 1
        # `ordered[start:stop+1]` all carry the same value, so they take the mean
        # of the 1-based ranks they occupy.
        ranks[order[start : stop + 1]] = 0.5 * (start + stop) + 1.0
        start = stop + 1
    return ranks


def spearman(u: np.ndarray, v: np.ndarray) -> float:
    """Spearman rank correlation: average ranks, then Pearson on the ranks.

    ``pearson(average_ranks(u), average_ranks(v))``, which is the standard
    definition of Spearman's rho and also equals ``1 - 6*sum(d^2)/(n^3-n)`` when
    there are no ties. The closed form is *not* used here: it is wrong the moment
    a tie appears, and it is the tie path that has to be right.

    Ties are averaged (see :func:`average_ranks`). This project has none in
    either ranking, so both vectors here are clean permutations of ``1..15``.

    Measured, on this project:

    ==========================  ========
    pair                        rho
    ==========================  ========
    Massey vs Colley            ``0.000``
    Massey vs official points   ``+0.093``
    Colley vs official points   ``+0.939``
    ==========================  ========

    The zero is exact and it is the headline: the two models, fitted on the same
    15 franchises, are **uncorrelated to three decimal places**. One reproduces
    the official table at ``+0.939``; the other, which used the margin the
    official table ignores, does not manage ``+0.093``.

    Note the indexing trap, which cost this project one wrong measurement before
    it was caught: both arguments must be in the **same** team order. The
    official table arrives sorted by points; the fitted vectors arrive in
    alphabetical team order. Comparing them positionally measures nothing.
    """
    left = average_ranks(u)
    right = average_ranks(v)
    if left.size != right.size:  # pragma: no cover - average_ranks sizes both
        raise ValueError(f"cannot correlate {left.size} and {right.size} values")

    left_c = left - left.mean()
    right_c = right - right.mean()
    denominator = float(
        np.sqrt(float(left_c @ left_c) * float(right_c @ right_c))
    )
    if denominator == 0.0:
        raise ValueError(
            "at least one input is constant, so its ranks have zero variance "
            "and Spearman's rho is undefined"
        )
    return float(left_c @ right_c) / denominator


# --------------------------------------------------------------------------
# Winner accuracy
# --------------------------------------------------------------------------


def winner_accuracy(pred: np.ndarray, b: np.ndarray) -> float:
    """Fraction of matches whose **winner** the fitted ranking predicts.

    Not ``sign(pred - b)`` and not a margin comparison: the question is only
    which team was stronger, so the magnitudes are discarded and the two signs
    compared. Measured **0.5502** = ``307 / 558`` in sample.

    A prediction of exactly zero is counted as a **miss**, not a win: it names no
    team. Measured, the closest any prediction comes to zero on this snapshot is
    ``0.1995`` runs, so the convention never fires here -- it is fixed anyway so
    a future dataset cannot quietly decide the answer by comparison to zero.

    Out of sample the same measure gives **0.4316** (``41 / 95``); see
    :func:`models.held_out_fit`.

    **The relevant baseline is not 0.50.** ``0.5502`` is only a little above a coin
    flip, but the first-listed team won **77.96%** of these 558 matches, so the
    comparison that says anything is against *that*. See
    :func:`majority_class_accuracy` and :func:`team1_win_share`.
    """
    predicted = np.asarray(pred, dtype=np.float64).ravel()
    observed = np.asarray(b, dtype=np.float64).ravel()
    if predicted.shape != observed.shape:
        raise ValueError(
            f"pred has {predicted.size} entries but b has {observed.size}; "
            "winner accuracy compares signs on matched pairs"
        )
    if observed.size == 0:
        raise ValueError("accuracy is undefined on an empty sample")
    return float(np.mean(np.sign(predicted) == np.sign(observed)))


# --------------------------------------------------------------------------
# The baseline that actually matters: which team was listed first
# --------------------------------------------------------------------------


def team1_won_flags(matches: pd.DataFrame) -> np.ndarray:
    """Boolean: did the **first-listed** team win, on the 558 run-margin rows?

    The one place the "first-listed team" target is built, and it canonicalises
    the winner before comparing. That step is not cosmetic -- see the module
    docstring. Measured on the committed snapshot:

    ==============================  ======  =========
    comparison                      wins    share
    ==============================  ======  =========
    ``canonical(winner) == team1``  435     ``0.7796``
    raw ``winner`` string == team1  347     ``0.6219``
    ==============================  ======  =========

    The raw comparison undercounts by **88 of 558** matches -- every run-margin
    match involving one of the four renamed franchises -- and produced a majority
    class of 62.19% that is simply wrong. :func:`majority_class_accuracy` asserts
    this function against ``sign(b)`` so the two conventions can never drift.

    Parameters
    ----------
    matches
        The committed snapshot frame, i.e. :func:`data.load_matches`. Only the
        run-margin subset is used, in the frame's own row order, which is the
        order :func:`data.design_matrix` uses.

    Returns
    -------
    numpy.ndarray
        ``(m,)`` boolean, one per run-margin match.
    """
    from .canon import canonical

    required = ("margin_runs", "winner", "canonical_team1")
    missing = [column for column in required if column not in matches.columns]
    if missing:
        raise ValueError(
            f"matches is missing column(s) {missing}; pass data.load_matches(), "
            "the committed snapshot frame"
        )
    rows = matches[
        matches["margin_runs"].notna() & matches["winner"].notna()
    ]
    if len(rows) == 0:  # pragma: no cover - the snapshot has 558
        raise ValueError(
            "no run-margin matches with a winner in this frame, so there is no "
            "first-listed-team target to build"
        )
    winners = rows["winner"].astype(str).map(canonical)
    first = rows["canonical_team1"].astype(str)
    return (winners == first).to_numpy(dtype=bool)


def team1_win_share(matches: pd.DataFrame) -> float:
    """**0.7796** -- the majority-class baseline, ``435`` of ``558``.

    The accuracy of the do-nothing classifier "always predict the first-listed
    team". It is the number the fitted ranking has to beat, and it does not:
    :func:`winner_accuracy` measures **0.5502** on the same rows.

    A two-sided coin flip gives 0.50, which is why the 55% used to be reported
    against one. That was the wrong comparator: it is beaten by *any* function of
    the fixture ordering, and this dataset's fixture ordering is strongly
    non-random (see :func:`team1_share_by_season`). The model is **22.9 points
    below** the relevant baseline, which is negative skill rather than weak skill.

    Parameters
    ----------
    matches
        The committed snapshot frame.

    Returns
    -------
    float
        ``float(mean(team1_won_flags(matches)))``.
    """
    return float(team1_won_flags(matches).mean())


def team1_share_by_season(matches: pd.DataFrame) -> pd.Series:
    """Per-season first-listed-team win share, on the run-margin rows.

    This is where the held-out split stops being a clean test. Measured:

    ==========  =====  =======  =========
    season      wins   of       share
    ==========  =====  =======  =========
    2007/08     13     24       0.542
    2009        14     27       0.519
    2009/10     18     31       0.581
    2011        22     33       0.667
    2012        15     34       0.441
    2013        24     37       0.649
    2014        12     22       0.545
    2015        21     32       0.656
    2016        12     21       0.571
    2017        13     26       0.500
    2018        28     28       **1.000**
    2019        22     22       **1.000**
    2020/21     27     27       **1.000**
    2021        22     22       **1.000**
    2022        37     37       **1.000**
    2023        40     40       **1.000**
    2024        35     35       **1.000**
    2025        33     33       **1.000**
    2026        27     27       **1.000**
    ==========  =====  =======  =========

    **The first-listed team won every single run-margin match from 2018 onward** --
    nine seasons, 281 matches, share exactly 1.000. The held-out split is the last
    three of those, so its 43.2% is being scored against a target that never
    varies: a model that always answered "the first-listed team" would score
    **100%** there. The number is real and it is reported, with the caveat
    attached rather than in a footnote.

    (An earlier correction to this module put the table at 0.29-0.88 for
    2007/08-2023 by using the raw, un-canonicalised winner string. The direction
    -- degeneracy at the end of the archive -- was right and the numbers were
    wrong; see the module docstring.)

    Parameters
    ----------
    matches
        The committed snapshot frame.

    Returns
    -------
    pandas.Series
        Share per season label, indexed by the ``str`` season label in ascending
        label order. A ``float`` Series, so the demo can print it and the report
        can embed it without re-deriving anything.
    """
    from .canon import canonical

    required = ("margin_runs", "winner", "canonical_team1", "season")
    missing = [column for column in required if column not in matches.columns]
    if missing:
        raise ValueError(
            f"matches is missing column(s) {missing}; pass data.load_matches(), "
            "the committed snapshot frame"
        )
    rows = matches[
        matches["margin_runs"].notna() & matches["winner"].notna()
    ]
    winners = rows["winner"].astype(str).map(canonical)
    frame = pd.DataFrame(
        {
            "season": rows["season"].astype("string").to_numpy(),
            "first_listed_won": (
                winners == rows["canonical_team1"].astype(str)
            ).to_numpy(dtype=bool),
        }
    )
    grouped = frame.groupby("season", sort=True)["first_listed_won"].agg(["sum", "count"])
    share = grouped["sum"].astype(float) / grouped["count"].astype(float)
    share.index = share.index.astype(str)
    share.name = "team1_win_share"
    return share


def majority_class_accuracy(
    pred: np.ndarray,
    b: np.ndarray,
    team1_won: np.ndarray,
) -> float:
    """The model's winner accuracy, **scored in the majority class's own convention**.

    Returns the fraction of matches where the fitted ranking's predicted winner
    agrees with "the first-listed team won". Measured **0.5502** = ``307 / 558``.

    It equals :func:`winner_accuracy` here, and the reason it exists separately is
    the *convention check*: ``b``'s sign **is** the first-listed-team indicator,
    because :func:`data.design_matrix` builds ``b[i] = +margin`` exactly when the
    first-listed team won. This function asserts that equality and raises if it
    does not hold, which is what stops the two conventions drifting apart.

    That is not hypothetical. A correction to this module computed the majority
    class by comparing the **raw** ``winner`` string to the **canonical** team
    column, got ``347`` of ``558`` instead of ``435``, and published a 62.19%
    baseline that 88 matches contradict. The guard below is the fix for that
    class of error: an indicator that disagrees with ``sign(b)`` is a bug and now
    raises rather than producing a plausible wrong percentage.

    **Read the result against the baseline, not against 0.50.** ``0.5502`` against
    :func:`team1_win_share`'s ``0.7796`` is **negative skill** against the only
    classifier this data rewards.

    Parameters
    ----------
    pred
        ``(m,)`` fitted margins from ``A @ x``.
    b
        ``(m,)`` the signed margins, in the order ``pred`` was computed on.
    team1_won
        ``(m,)`` boolean first-listed-team indicator, from
        :func:`team1_won_flags` over the same rows in the same order.

    Returns
    -------
    float
    """
    predicted = np.asarray(pred, dtype=np.float64).ravel()
    observed = np.asarray(b, dtype=np.float64).ravel()
    flags = np.asarray(team1_won).ravel().astype(bool)
    if predicted.shape != observed.shape:
        raise ValueError(
            f"pred has {predicted.size} entries but b has {observed.size}; "
            "winner accuracy compares signs on matched pairs"
        )
    if flags.size != predicted.size:
        raise ValueError(
            f"team1_won has {flags.size} entries but pred has {predicted.size}; "
            "the indicator and the predictions must describe the same matches, "
            "in the same order"
        )
    if predicted.size == 0:
        raise ValueError("accuracy is undefined on an empty sample")

    from_sign = observed > 0.0
    if not np.array_equal(from_sign, flags):
        disagreements = int(np.count_nonzero(from_sign != flags))
        raise ValueError(
            f"team1_won disagrees with sign(b) on {disagreements} of "
            f"{flags.size} matches, so the two conventions are not the same "
            "classification. b[i] is positive exactly when the FIRST-LISTED team "
            "won, so any disagreement means the indicator was built against the "
            "raw winner string while b was built against the canonical one -- the "
            "renamed franchises (Delhi Daredevils/Delhi Capitals, Kings XI "
            "Punjab/Punjab Kings, Royal Challengers Bangalore/Bengaluru, Rising "
            "Pune Supergiant/Supergiants) make the two differ. Build the "
            "indicator with diagnostics.team1_won_flags(), which canonicalises."
        )
    return float(np.mean(np.sign(predicted) == np.where(flags, 1.0, -1.0)))


# --------------------------------------------------------------------------
# The two comparison tables
# --------------------------------------------------------------------------


def _ordered_ranks(values: np.ndarray, names: list[str]) -> np.ndarray:
    """Ranks 1..n by descending value, ties broken by ascending name.

    A **total** order, deliberately. ``rank(method="min")`` would give two
    equally-performing teams the same rank and leave the numbering non-consecutive
   ; ``method="average"`` would give half-integers that are awkward to print next
    to a points table. Here every ordering is a permutation of ``1..15``, so rank
    movement is a plain integer difference and the demo can print it directly.

    The name tiebreak is what makes it deterministic: without it, two runs whose
    sort is stable but whose input order differed would print different rankings
    for identical data. The project has no ties in either ranking today, so the
    tiebreak never fires -- it is here so that cannot change.
    """
    if len(values) != len(names):
        raise ValueError(
            f"{len(values)} values but {len(names)} names; they must be the same "
            "length and in the same order"
        )
    order = sorted(range(len(values)), key=lambda i: (-float(values[i]), names[i]))
    ranks = np.empty(len(values), dtype=np.int64)
    for position, index in enumerate(order, start=1):
        ranks[index] = position
    return ranks


def _official_points(official_df: pd.DataFrame, names: list[str]) -> np.ndarray:
    """Official points per team, re-indexed onto the **team** order of ``names``.

    ``data.official_table()`` returns its rows sorted by points, and the fitted
    vectors are in alphabetical team order, so the two must be joined on ``team``
    before anything is compared. Getting this wrong silently correlates two
    unrelated orderings; see the note on :func:`spearman`.
    """
    if "team" not in official_df.columns or "points" not in official_df.columns:
        raise ValueError(
            "official_df must have 'team' and 'points' columns, got "
            f"{sorted(official_df.columns)}; pass data.official_table()"
        )
    lookup = official_df.set_index("team")["points"]
    missing = [name for name in names if name not in lookup.index]
    if missing:
        raise ValueError(
            f"official_df has no row for {missing}; it must carry one row per "
            "canonical franchise"
        )
    return lookup.loc[names].to_numpy(dtype=np.float64)


@dataclass(frozen=True)
class _Comparison:
    """Shared plumbing for the two tables, so they cannot drift apart."""

    names: list[str]
    massey_x: np.ndarray
    massey_se: np.ndarray
    colley_share: np.ndarray
    points: np.ndarray


def _comparison(
    massey_x: np.ndarray,
    se: np.ndarray,
    colley_r: np.ndarray,
    official_df: pd.DataFrame,
    names: list[str],
) -> _Comparison:
    """Validate four aligned vectors and join them onto the official points."""
    x = np.asarray(massey_x, dtype=np.float64).ravel()
    errors = np.asarray(se, dtype=np.float64).ravel()
    share = np.asarray(colley_r, dtype=np.float64).ravel()
    widths = {x.size, errors.size, share.size, len(names)}
    if len(widths) != 1:
        raise ValueError(
            f"massey_x has {x.size}, se has {errors.size}, colley_r has "
            f"{share.size} and there are {len(names)} teams; every vector must "
            "be in the same team order and the same length"
        )
    if np.any(errors < 0.0):
        raise ValueError("a standard error is negative, so it is not one")
    return _Comparison(
        names=list(names),
        massey_x=x,
        massey_se=errors,
        colley_share=share,
        points=_official_points(official_df, list(names)),
    )


def official_comparison(
    x: np.ndarray,
    colley_r: np.ndarray,
    official_df: pd.DataFrame,
    se: np.ndarray,
) -> pd.DataFrame:
    """Both models beside the official all-time table, one row per franchise.

    Nine columns, and the point of the table is what sits next to what:

    =================  =========================================================
    column             meaning
    =================  =========================================================
    ``team``           canonical franchise name
    ``points``         official all-time points (2 per win), the authority
    ``official_rank``  1..15 by points descending, ties by name
    ``massey_x``       least-squares strength, runs, zero-sum centred
    ``massey_se``      its standard error, runs
    ``massey_rank``    1..15 by ``massey_x`` descending
    ``colley_share``   Colley rating share, summing to 1 across the 15
    ``colley_rank``    1..15 by ``colley_share`` descending
    ``rank_movement``  ``massey_rank - official_rank``; **positive means Massey
                       ranks that team worse than the official table does**
    =================  =========================================================

    Sorted by ``points`` descending then ``team`` ascending, so it reads as the
    official table with the two fits annotated onto it -- and the annotation is
    what shows the split: Colley's ``colley_rank`` runs 1..15 almost alongside
    ``official_rank`` (Spearman **+0.939**), while Massey's column is close to
    unrelated (**+0.093**). Read down the ``rank_movement`` column and the margin
    fit visibly scatters its own winners and losers.

    Parameters
    ----------
    x, colley_r
        Fitted values in **team order** (alphabetical, i.e. ``data.teams()``),
        from :func:`models.massey` and :func:`models.colley`. That order is
        recovered here by sorting ``official_df``'s names, so a caller passing the
        vectors in the points-sorted order of the table below will misalign them
        -- which is a mistake worth making impossible to make silently, and the
        module docstring says why.
    official_df
        From :func:`data.official_table`; joined on ``team``, never on row
        position.
    se
        **Required.** Standard errors for ``x``; a fourth argument the dispatch
        omitted. Deriving them here instead would mean reporting the errors of a
        *different* fit than the one passed in, which is the kind of quiet
        mismatch this project has already been bitten by. See the module
        docstring.
    """
    # The fitted vectors are in alphabetical team order -- `data.teams()` -- and
    # `official_df` arrives sorted by *points*, which is a different order. The
    # team order is therefore recovered by sorting the names, not by reading
    # `official_df`'s row order, or every fitted value would be attributed to the
    # wrong franchise. The output is re-sorted by points at the end.
    names = sorted(str(name) for name in official_df["team"])
    comparison = _comparison(x, se, colley_r, official_df, names)

    massey_rank = _ordered_ranks(comparison.massey_x, comparison.names)
    colley_rank = _ordered_ranks(comparison.colley_share, comparison.names)
    official_rank = _ordered_ranks(comparison.points, comparison.names)

    frame = pd.DataFrame(
        {
            "team": comparison.names,
            "points": comparison.points.astype(np.int64),
            "official_rank": official_rank,
            "massey_x": comparison.massey_x,
            "massey_se": comparison.massey_se,
            "massey_rank": massey_rank,
            "colley_share": comparison.colley_share,
            "colley_rank": colley_rank,
            "rank_movement": massey_rank - official_rank,
        }
    )
    return frame.sort_values(
        ["points", "team"], ascending=[False, True], ignore_index=True
    )


def summary_table(
    teams,
    massey_x: np.ndarray,
    se: np.ndarray,
    colley_r: np.ndarray,
    official_df: pd.DataFrame,
    games: np.ndarray,
) -> pd.DataFrame:
    """The headline table, sorted by fitted strength, with games **shown**.

    Columns: ``team``, ``games_played``, ``massey_x``, ``massey_se``,
    ``colley_share``, ``points`` -- six, of which one is not a ranking at all.

    ``games_played`` is in the table and is not decorative. Measured on this
    snapshot, ``corr(games_played, |massey_x|) = -0.663``: the fewer matches a
    franchise played, the more extreme its fitted strength. The top row is Kochi
    Tuskers Kerala with 5 run-margin games and ``x = +17.43``, three times the
    spread of the well-measured teams; the second is Rising Pune Supergiant with
    12. Hide that column and the table reads as a statement about team quality.
    With it, the same numbers read as a statement about **sample size**, which is
    what they are -- and the two five-game franchises at the top are the whole
    diagnosis in two rows.

    Every row keeps ``games_played`` adjacent to ``massey_se``, so the reader sees
    "how uncertain is this number" and "why is it uncertain" in one glance.

    Parameters
    ----------
    teams
        The canonical names in the order of every vector below.
    massey_x, se, colley_r
        Fitted values and standard errors, in team order.
    official_df
        From :func:`data.official_table`.
    games
        ``(n,)`` matches played per team, from :func:`data.games_played`.

    Returns
    -------
    pandas.DataFrame
        ``len(teams)`` rows, sorted by ``massey_x`` descending then ``team``
        ascending.
    """
    names = [str(name) for name in teams]
    played = np.asarray(games).ravel()
    if played.size != len(names):
        raise ValueError(
            f"games has {played.size} entries but there are {len(names)} teams; "
            "pass data.games_played()"
        )

    comparison = _comparison(massey_x, se, colley_r, official_df, names)
    frame = pd.DataFrame(
        {
            "team": names,
            "games_played": played.astype(np.int64),
            "massey_x": comparison.massey_x,
            "massey_se": comparison.massey_se,
            "colley_share": comparison.colley_share,
            "points": comparison.points.astype(np.int64),
        }
    )
    return frame.sort_values(
        ["massey_x", "team"], ascending=[False, True], ignore_index=True
    )