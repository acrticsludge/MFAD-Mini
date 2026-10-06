"""The two linear models, and the three variants that do not fix them.

Where ``data.py`` stops at matrices, this module fits them. Two models on **two
different datasets** (`AGENTS.md` section 3), whose divergence is the project's
result:

======================  ====================  ===================================
fit                      dataset                what it believes
======================  ====================  ===================================
:func:`massey`           **558** run margins    strength difference *is* the margin
:func:`colley`           **1,218** decided      strength *orders* outcomes only
======================  ====================  ===================================

**Attribution, stated precisely because the shorthand was too loose.** The second
fit is a **Colley-style Perron eigenvector** of the rating matrix ``M = W + W' +
C``, normalised to shares. Colley's 2002 paper is a *linear* system for adjusted
ratings, not this eigenvector problem, so calling this "Colley's method" is loose
attribution and the demo, the report and the README all label it *Colley-style*
for that reason. The idea -- pull a team's rating toward the average of the teams
it beat, in proportion to how often it met them -- is Colley's; the system solved
here is the eigenvector form of it, and the numbers below are new measurements on
IPL data, not anything a published source reports.

Everything here is deterministic: no random start, no tolerance guess, no
iteration-order dependence. Two runs are bit-identical.

The measured figures this module reproduces
-------------------------------------------
All measured 2026-10-04 against ``data/matches.csv``::

    ||r||^2 = 928185.2      ||r|| = 963.4237       ||b||^2 = 948444.0
    ||b - mean(b)||^2 = 766931.3
    three LS routes agree to 4.796e-14   (worst pair: normal-equations vs constrained)
    winner accuracy = 0.5502 = 307 / 558
    majority-class baseline = 0.7796 = 435 / 558   (always the first-listed team)
    cond(A.T@A + 1*1.T) = 31.5476        cond(A.T@A) = 5.63e16  (numerically singular)
    Colley lam1 = 469.1757   lam2 = 14.8064   9 iterations
    frequency-balanced max|x| 17.43 -> 25.64     R^2 centred -0.2103 -> -0.2113
    held out (last 3 seasons): 463 train / 95 test, accuracy 0.432,
                                RMSE 46.71 vs mean-baseline RMSE 35.35
                                -- on a DEGENERATE split, see item 4

Three things measurement corrected, recorded here rather than smoothed over
-------------------------------------------------------------------------
``AGENTS.md`` section 4 makes an unmeasured number a defect, so each of these
is a place where the inherited expectation was wrong and the data was believed.

1. **The Colley matrix is indefinite, and that breaks the obvious way to get
   ``lam2``.** ``M = W + W.T + C`` has eigenvalue ``469.1757`` at the top but
   ``-86.7200`` at the bottom, so the spectral radius is set by the *positive*
   end and the power method is fine for ``lam1`` (9 iterations) -- but a second
   power run, even one correctly projected onto the complement of the leading
   eigenvector, converges to the eigenvector of **-86.72**, not to ``lam2``:
   measured ``|cos| = 0.99999999998`` against the most negative eigenvector, and
   ``||M x|| -> 86.7200``. ``||M x||`` estimates spectral *radius*, not the
   second algebraic eigenvalue. :func:`colley` therefore reads ``lam2`` from
   ``np.linalg.eigvalsh`` -- which the plan explicitly allows ("NumPy where the
   book uses it (``lstsq``, ``svd``, ``eigh``)") -- while the leading eigenpair,
   the part that carries the finding, stays hand-iterated. Both are tested
   against ``np.linalg.eigh``.

2. **Ridge does not leave R^2 unchanged. It degrades it.** The dispatch for this
   node expected "R2 centred unchanged to 4 dp (-0.2103)" for
   ``lam in [1, 1000]``. Measured, it is not unchanged -- it falls monotonically
   from ``-0.210259`` to ``-0.232369``, a span of **2.211e-2**, twenty
   thousand times the 1e-6 the inherited test asked for::

       lam       1        10        50       200      1000
       R2_c  -0.210357 -0.212150 -0.216264 -0.223703 -0.232369

   The *theorem* in :func:`ridge`'s docstring survives untouched and is what the
   data actually shows: ``x_hat`` is the minimiser of ``||A x - b||``, so no
   re-fit can lower that residual, and shrinkage cannot improve R^2 -- it can
   only make it worse. Measured strictly: the residual sum of squares rises by
   ``+75.3, +1450.8, +4605.5, +10310.8, +16957.4`` at those five values of
   ``lam``. That is the assertion the test suite pins, in place of the
   invariance claim, which measurement refutes. See
   ``test_ridge_never_improves_r_squared_because_it_cannot``.

3. **Frequency balancing *does* make the short-history extremity worse**, as
   the inherited plan's correction predicted -- but only if the weight uses the
   games each team played *in the run-margin subset*, not the per-row total of
   appearances. Both ``A`` rows and ``|A|`` row sums are ``2`` on every match, so
   a weight derived from ``A`` alone is the constant ``1/2`` and the "balanced"
   fit is bit-identical to OLS. With ``w_i = 1 / (games(t1) + games(t2))`` on
   ``data.games_played()``, the pair totals run 44 to 266 and Kochi's five
   matches are up-weighted by ~3x against a Mumbai-Chennai match. Result:
   Kochi ``17.43 -> 25.64``, ``max|x| 17.43 -> 25.64``, R^2 centred
   ``-0.2103 -> -0.2113``. The refutation stands, and it is the *direction* of
   the effect that refutes it: balancing amplifies the few matches the thin
   franchise played.

4. **The held-out split is degenerate, and saying so changes what its number
   means.** Refit on the first 16 seasons and scored on ``['2024', '2025',
   '2026']``, the fit gets **0.4316** of the winners right -- which reads as "worse
   than a coin flip". The first-listed team won **95 of those 95** matches. The
   split's target does not vary once, so the accuracy is being scored on a coin
   that has already landed: a constant "always predict team1" scores **1.000**
   there. Measured by :func:`diagnostics.team1_share_by_season`, the first-listed
   team won **every** run-margin match from **2018** onward, share exactly 1.000
   in all nine seasons, so the held-out era sits entirely inside the degenerate
   one. The 43.2% is reported with that attached rather than dropped, and the
   per-season table is printed so the reader can see the drift instead of taking
   it on trust.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .data import design_matrix
from .linalg_kit import power_iteration

__all__ = [
    "BalancedFit",
    "ColleyFit",
    "HeldOutResult",
    "MasseyFit",
    "SvdResult",
    "colley",
    "frequency_balanced",
    "held_out_fit",
    "ridge",
    "massey",
    "svd_of_A",
]

#: Entries below this magnitude are structurally zero on a real matrix and are
#: reported as such rather than as a computed ``-9.2e-15``. One order of
#: magnitude below the smallest genuine singular value of ``A`` (2.2216), so a
#: real direction can never be rounded away by it.
ZERO_CUTOFF = 1e-11


def _as_system(A: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Validate a ``(A, b)`` pair and return them as 2-D / 1-D float arrays."""
    M = np.asarray(A, dtype=np.float64)
    rhs = np.asarray(b, dtype=np.float64)
    if M.ndim != 2:
        raise ValueError(f"A must be 2-D, got shape {M.shape}")
    if rhs.ndim != 1:
        raise ValueError(f"b must be 1-D, got shape {rhs.shape}")
    if M.shape[0] != rhs.shape[0]:
        raise ValueError(
            f"A has {M.shape[0]} rows but b has {rhs.shape[0]} entries; the "
            "design matrix and its right-hand side must come from the same "
            "system. data.design_matrix() builds them together for this reason."
        )
    return M, rhs


def _centre(v: np.ndarray) -> np.ndarray:
    """Subtract the mean, i.e. fix the gauge at **zero sum**.

    Least squares on this ``A`` cannot determine the level, only the differences:
    every row of ``A`` sums to zero, so ``A @ (x + c*1) == A @ x`` exactly and
    the null direction is the constant vector (``tests/test_structure.py`` pins
    ``A @ ones == 0`` to the last bit). Centring is the convention that makes two
    runs comparable, and it is the gauge the constrained route produces natively.
    """
    return v - float(np.mean(v))


def _constrained(A: np.ndarray) -> np.ndarray:
    """``A.T @ A + 1 * 1.T`` -- the gauge-pinned normal equations, 15x15.

    Adding the outer product of the null vector pins the one direction the
    system cannot see, which makes the matrix **nonsingular**: measured
    ``rank(A.T@A) = 14`` and ``rank(A.T@A + 1*1.T) = 15``. Measured condition
    number ``31.5476`` -- five orders of magnitude *better* than
    ``cond(A.T@A) = 5.63e16``, which is what a single ``1e-16`` eigenvalue does
    to a condition number. This is the honest way to invert a near-singular
    normal-equation matrix: perturb it along the direction you know is null
    rather than hoping ``lstsq`` picks it out.
    """
    n = A.shape[1]
    ones = np.ones(n, dtype=np.float64)
    return A.T @ A + np.outer(ones, ones)


def _match_endpoints(A: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-row indices of the two teams in each row of the Massey design matrix.

    Row ``i`` is ``+1`` under the team that won and ``-1`` under the team that
    lost, so the winner is the row maximum and the loser the row minimum. Every
    other entry is ``0``.

    The *order* the two teams played in is not recoverable from ``A`` and is not
    needed: the frequency weight ``1 / (games(t1) + games(t2))`` is symmetric in
    its two teams, so the unordered pair identifies it completely.

    The validation is not decoration. A row of all zeros -- which is what two
    raw team names collapsing onto one franchise would produce, per the note in
    ``data.design_matrix`` -- has no argmax/argmin to speak of, so it is caught
    here with the offending row index instead of silently weighting a match no
    team played.
    """
    winner = np.argmax(A, axis=1)
    loser = np.argmin(A, axis=1)
    rows = np.arange(A.shape[0])
    bad = (A[rows, winner] != 1.0) | (A[rows, loser] != -1.0)
    if bad.any():  # pragma: no cover - data.design_matrix() guards this first
        offenders = np.flatnonzero(bad)
        raise AssertionError(
            f"{offenders.size} row(s) of A are not a +1/-1 winner-loser pair; "
            f"first at index {int(offenders[0])} with entries "
            f"{A[offenders[0]].tolist()}. Every row must hold exactly one +1 and "
            "one -1, or the frequency weight for that match is undefined."
        )
    return winner, loser


# --------------------------------------------------------------------------
# Massey: least squares on the 558 run margins
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MasseyFit:
    """One least-squares fit of the run margins, computed three ways.

    Attributes
    ----------
    x
        ``(n,)`` team strengths in **runs**, centred to zero sum. This is the
        SVD route's answer, which is the one the rest of the project uses,
        because ``lstsq`` on a rank-deficient matrix is the numerically
        trustworthy route: it truncates the numerically-zero direction instead
        of dividing by it.
    resid
        ``(m,)`` residuals ``b - A @ x``, so ``resid @ A ~= 0`` exactly by the
        normal equations. That orthogonality is a real, checkable consequence of
        the fit and it is pinned by a test.
    routes
        All three solutions, each centred the same way, keyed by name:
        ``"lstsq"`` (SVD, rank-aware), ``"normal_equations"``
        (``lstsq`` on the *singular* ``A.T@A``) and ``"constrained"``
        (the nonsingular gauge-pinned system).
    max_route_diff
        The measured largest absolute difference between any two routes.
        **4.796e-14** on this snapshot, between the normal-equation and
        constrained routes. Carried in the result so the demo prints a measured
        number rather than asserting agreement in prose.
    worst_pair
        Which pair produced ``max_route_diff``. Present so the printed number is
        attributable.
    cond_constrained
        ``cond(A.T@A + 1*1.T)``, measured **31.5476**.
    singular_values
        ``(n,)`` singular values of ``A``: ``12.4779`` down to ``2.2216``, then
        one at ``5e-15``.
    rank
        ``rank(A)``, measured **14**.
    """

    x: np.ndarray
    resid: np.ndarray
    routes: dict[str, np.ndarray]
    max_route_diff: float
    worst_pair: tuple[str, str]
    cond_constrained: float
    singular_values: np.ndarray
    rank: int


def massey(A: np.ndarray, b: np.ndarray) -> MasseyFit:
    """Least squares on the run margins, by **three independent routes**.

    The design matrix ``A`` is ``(558, 15)`` with ``rank(A) = 14`` and
    ``nullity(A) = 1`` -- the single null direction being the constant vector --
    so there is no unique ``x``, only an equivalence class ``x + c*1``. Three
    routes, three ways of dealing with that, and a measurement of how far apart
    they land:

    1. ``"lstsq"`` -- ``numpy.linalg.lstsq(A, b)``. SVD-based, and told
       ``rcond=None`` so it decides for itself which singular values are noise.
       This is the reference answer.
    2. ``"normal_equations"`` -- ``lstsq(A.T@A, A.T@b)``. The textbook route, and
       a trap: ``A.T@A`` is *also* rank 14, so naively inverting it would divide
       by a ``1e-16``. Solving it with ``lstsq`` is honest, and squaring the
       condition number (``5.63e16`` against ``31.5476`` for the constrained
       form) is the price of the detour.
    3. ``"constrained"`` -- ``solve(A.T@A + 1*1.T, A.T@b)``. Nonsingular, because
       the added rank-one term is exactly the null direction. Summing the
       equation over all teams gives ``0 + 15*(1.T x) = 0``, so this route lands
       on the zero-sum gauge natively -- which is why its output is already the
       centred one to machine precision.

    Measured, on this snapshot: the three agree to **4.796e-14**, the largest gap
    being between routes 2 and 3. They must: they solve the same normal equations
    and differ only in how the null direction is handled.

    Returns
    -------
    MasseyFit
        ``x`` is the SVD route, centred. All three are also returned so the
        agreement can be *displayed*, which is the point of computing three.
    """
    A, rhs = _as_system(A, b)
    m, n = A.shape

    AtA = A.T @ A
    Atb = A.T @ rhs
    K = _constrained(A)

    x_svd, _, rank, _ = np.linalg.lstsq(A, rhs, rcond=None)
    x_normal = np.linalg.lstsq(AtA, Atb, rcond=None)[0]
    x_constrained = np.linalg.solve(K, Atb)

    routes = {
        "lstsq": _centre(x_svd),
        "normal_equations": _centre(x_normal),
        "constrained": _centre(x_constrained),
    }

    names = list(routes)
    max_diff = 0.0
    worst = (names[0], names[1])
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            gap = float(np.abs(routes[names[i]] - routes[names[j]]).max())
            if gap > max_diff:
                max_diff = gap
                worst = (names[i], names[j])

    x = routes["lstsq"]
    return MasseyFit(
        x=x,
        resid=rhs - A @ x,
        routes=routes,
        max_route_diff=max_diff,
        worst_pair=worst,
        cond_constrained=float(np.linalg.cond(K)),
        singular_values=np.linalg.svd(A, compute_uv=False),
        rank=int(rank),
    )


# --------------------------------------------------------------------------
# Colley: eigenvector on the 1,218 decided matches
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ColleyFit:
    """The dominant eigenpair of the Colley rating matrix, as a share vector.

    Attributes
    ----------
    r
        ``(n,)`` rating **shares**, summing to exactly ``1.0``, so it reads
        directly as a percentage of the "league". Normalising the eigenvector to
        sum 1 is what makes it comparable with a points table at all; an
        eigenvector is otherwise only defined up to scale.
    lam1
        Leading eigenvalue, measured **469.1757**.
    lam2
        Second eigenvalue, measured **14.8064**. From ``eigvalsh``, not from a
        power run -- see the module docstring, item 1, for the measurement that
        forces this.
    iterations
        Multiply-and-normalise steps to the tolerance, measured **9**.
    history
        The full ``||M x||`` trace, one entry per step, so the demo can draw a
        live sparkline instead of asserting convergence. Measured:
        ``391.308 -> 469.095 -> 469.1746 -> 469.1757 -> ...`` -- monotone up from
        16.6% low.
    min_entry
        Smallest share, measured **0.0058173** (Rising Pune Supergiant, 15 wins).
    all_positive
        ``True`` iff every entry is strictly positive. Verified, never assumed:
        :func:`colley` raises rather than returning a fit with a non-positive
        entry, so reaching ``False`` is impossible by construction and the flag
        exists so the demo can *print* the fact rather than trust it.
    """

    r: np.ndarray
    lam1: float
    lam2: float
    iterations: int
    history: list[float]
    min_entry: float
    all_positive: bool


def colley(W: np.ndarray, C: np.ndarray) -> ColleyFit:
    """**Colley-style** Perron eigenvector of the rating matrix, hand-iterated.

    Over all 1,218 decided matches. The model says one thing only: **rank, not
    margin**. Team ``i``'s rating is pulled toward the average of the teams it
    beat, with the pull proportional to how often it met them. That is the
    eigenvector problem

    ``M r = lam1 r``   with   ``M = W + W.T + C``,

    where ``W[i, j]`` counts wins by ``i`` over ``j`` and ``C[i, j]`` counts
    matches played between them. ``M`` is symmetric and entrywise non-negative, so
    the leading eigenpair is real and simple (Perron-Frobenius) -- and positivity of
    the *entries* is the part worth checking rather than trusting, because the
    theorem needs irreducibility and the snapshot's win/loss graph is measured to
    have exactly **one** connected component, so it is irreducible.

    **Attribution: style, not the paper.** Colley's 2002 method solves a *linear*
    system of adjusted ratings; this is the eigenvector form of the same intuition.
    Calling it "Colley's method" without qualification would credit the paper
    with a system it does not contain. The demo, the report and the README all say
    *Colley-style* for that reason, and no coefficient vector published anywhere is
    being reproduced -- these are new measurements.

    The iteration is ``r <- M r / ||M r||`` and it is **hand-written**, in
    :func:`linalg_kit.power_iteration` -- reused rather than duplicated, because
    the dispatch for this module names that file finished and correct, and one
    convergence trace is better than two that can drift apart. The start is the
    normalised all-ones vector, fixed: there is no randomness anywhere in this
    project, so two calls are bit-identical, and a positive start cannot land on
    the negation of a positive eigenvector.

    Measured, 9 iterations: ``391.308 -> 469.095 -> ... -> 469.175700``,
    ``lam1 = 469.1757``, agreeing with ``np.linalg.eigh`` to 1e-12.

    ``lam2 = 14.8064`` is read from ``eigvalsh`` and **not** from a second power
    run, because ``M`` is indefinite -- its eigenvalues run down to ``-86.7200``
    -- so ``||M x||`` estimates spectral radius, and after removing the leading
    direction the radius is set by ``-86.72``, not by ``+14.81``. Measured: a
    correctly-projected second run converges to ``|cos| = 0.99999999998`` of the
    most *negative* eigenvector and reports ``86.7200``.

    Raises
    ------
    ValueError
        If ``W``/``C`` are not square, not the same size, or if ``M`` is not
        symmetric.
    AssertionError
        If any share is not strictly positive. This is a real guard, not a
        formality: it is the difference between "Perron-Frobenius applies here"
        and "we assumed it did". The message carries the offending value and its
        index.
    """
    wins = np.asarray(W, dtype=np.float64)
    games = np.asarray(C, dtype=np.float64)
    if wins.ndim != 2 or wins.shape[0] != wins.shape[1]:
        raise ValueError(f"W must be square, got shape {wins.shape}")
    if games.shape != wins.shape:
        raise ValueError(
            f"W is {wins.shape} but C is {games.shape}; the win and games "
            "matrices must index the same teams in the same order"
        )

    M = wins + wins.T + games
    if not np.allclose(M, M.T, atol=1e-12):
        raise ValueError(
            "M = W + W.T + C is not symmetric, so the dominant eigenpair need "
            "not be real and the power iteration below would be meaningless"
        )

    vector, lam1, history = power_iteration(M)

    # A positive start lands on a positive eigenvector for a non-negative M, but
    # "should" is not a measurement, so the sign is fixed by the data and then
    # the sign of the result is confirmed rather than assumed.
    if float(vector.sum()) < 0.0:  # pragma: no cover - unreachable for this M
        vector = -vector
    share = vector / float(vector.sum())

    min_entry = float(share.min())
    if not bool(np.all(share > 0.0)):  # pragma: no cover - M is irreducible
        offenders = np.flatnonzero(share <= 0.0)
        raise AssertionError(
            f"Perron-Frobenius positivity FAILED: {offenders.size} of "
            f"{share.size} Colley shares are not strictly positive; first at "
            f"index {int(offenders[0])} with value {share[offenders[0]]!r}, "
            f"smallest overall {min_entry!r}. M must be entrywise non-negative "
            "and irreducible (one connected component) for the leading "
            "eigenvector to be strictly positive. Either condition failing is a "
            "finding, not something to paper over."
        )

    return ColleyFit(
        r=share,
        lam1=float(lam1),
        lam2=float(np.linalg.eigvalsh(M)[-2]),
        iterations=len(history),
        history=[float(value) for value in history],
        min_entry=min_entry,
        all_positive=True,
    )


# --------------------------------------------------------------------------
# The refuted hypothesis: frequency-balanced least squares
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BalancedFit:
    """The weighted fit, the weights that produced it, and what they were built on.

    Attributes
    ----------
    x
        ``(n,)`` weighted solution, centred to zero sum, in runs. On this
        snapshot Kochi Tuskers Kerala moves from ``+17.43`` to **``+25.64``**.
    w
        ``(m,)`` per-match weight ``1 / (games(t1) + games(t2))``, from
        :func:`data.games_played`.
    match_games
        ``(m,)`` the pair totals the weights are the reciprocals of. Kept
        because it is the whole mechanism: measured, these run from **44** (the
        two five-season franchises meeting) to **266**.
    """

    x: np.ndarray
    w: np.ndarray
    match_games: np.ndarray


def frequency_balanced(
    A: np.ndarray, b: np.ndarray, games_per_team: np.ndarray
) -> BalancedFit:
    """Frequency-balanced least squares -- **the refuted hypothesis. It is worse.**

    The inherited build audit predicted that weighting each match by
    ``1 / (games(t1) + games(t2))`` would stop the short-history franchises
    dominating the fit. Measured 2026-10-04, it does the opposite:

    ==========================  =======  ===========  ===========
    team                        games    OLS x        balanced x
    ==========================  =======  ===========  ===========
    Kochi Tuskers Kerala        5        ``+17.43``   ``+25.64``
    Gujarat Lions               5        ``-13.70``   ``-13.24``
    ``max|x|`` over 15 teams             ``17.43``    ``25.64``
    ==========================  =======  ===========  ===========

    R^2 centred also slips, ``-0.2103 -> -0.2113``.

    **Why, and this is the finding rather than a footnote.** The diagnosis is
    right and the proposed repair inverts it. Kochi's extremity is *caused* by
    having 5 run-margin matches; those 5 matches are what the weight divides by,
    so they are up-weighted roughly threefold against a Mumbai-Chennai match,
    whose pair total is 266. Balancing amplifies the very matches it was meant to
    discount. Fewer games is not a reason to trust a franchise's games more --
    it is a reason to trust them *less*.

    So this function exists to **refute** the hypothesis, not to support it. Do
    not "repair" the number, and do not quietly swap in a different weighting
    until it looks better: the prediction being tested is precisely that this
    weighting, on this data, does not work.

    Parameters
    ----------
    A, b
        The Massey system, from :func:`data.design_matrix`.
    games_per_team
        ``(n,)`` games each team played **within the run-margin subset**, i.e.
        :func:`data.games_played` (sums to ``2 x 558 = 1116``).

        The basis matters and is easy to get wrong. Because every row of ``A``
        holds exactly two entries and ``|A|`` row sums to 2 throughout, a weight
        derived from ``A`` itself is the constant ``1/2`` and the "balanced" fit
        comes back bit-identical to OLS. Passing the per-team counts is what
        makes the pair totals differ.

    Returns
    -------
    BalancedFit
        The weighted solution **and** the weight vector, so the demo can show
        which matches were up-weighted rather than only that the answer moved.
    """
    A, rhs = _as_system(A, b)
    counts = np.asarray(games_per_team, dtype=np.float64)
    if counts.shape != (A.shape[1],):
        raise ValueError(
            f"games_per_team has shape {counts.shape} but A has "
            f"{A.shape[1]} columns. Pass data.games_played(), one count per team "
            "in the same (alphabetical) order as A's columns."
        )
    if np.any(counts <= 0.0):
        raise ValueError(
            f"games_per_team has {int((counts <= 0.0).sum())} non-positive "
            "entries, so the reciprocal weight is undefined or infinite"
        )

    winner, loser = _match_endpoints(A)
    match_games = counts[winner] + counts[loser]
    w = 1.0 / match_games
    root = np.sqrt(w)

    # Weighted least squares by the square-root-weight trick: weighting the rows
    # of A and b by sqrt(w) turns min ||A x - b||_W into an ordinary unweighted
    # least-squares problem in (A_w, b_w), with no explicit matrix square root.
    A_w = root[:, None] * A
    b_w = root * rhs
    x = _centre(np.linalg.lstsq(A_w, b_w, rcond=None)[0])

    return BalancedFit(x=x, w=w, match_games=match_games)


# --------------------------------------------------------------------------
# Ridge: the theorem, and what it actually costs
# --------------------------------------------------------------------------


def ridge(A: np.ndarray, b: np.ndarray, lam: float) -> np.ndarray:
    """Ridge shrinkage on ``A.T@A + lam*I``, centred to zero sum.

    **The narrow, true statement.** ``x_hat`` is *the* minimiser of
    ``||A x - b||``, so **no other unregularised least-squares fit can beat it** --
    that is arithmetic, not a finding about IPL data. Ridge is a different
    objective (it shrinks toward zero), so it is a *constrained* fit rather than a
    least-squares one, and the guarantee above says nothing about it either way.
    Measured, it is strictly worse here: the residual sum of squares rises by
    ``+75.3, +1450.8, +4605.5, +10310.8, +16957.4`` at
    ``lam = 1, 10, 50, 200, 1000``, and ``R^2`` falls monotonically.

    **What was retracted, so it is recorded here.** An earlier version of this
    project asserted that ridge "cannot change R^2 on this problem, and this is a
    theorem", and a dispatch asked for a test pinning ``R^2`` unchanged to ``1e-6``
    across ``lam in [1, 1000]``. Both were wrong. Ridge **does** change ``R^2``,
    monotonically downward, by ``2.211e-2`` over that range -- twenty thousand
    times the tolerance the claim wanted, and already in the fourth decimal at
    ``lam = 1``. An "obvious theorem" asserted without measurement was wrong in
    exactly the way `AGENTS.md` section 4 warns about, so the refuted claim is
    named in the demo output too, next to the measured table.

    What ridge *does* do is trade variance for bias, and on 15 unknowns with
    ``m = 558`` rows there is almost nothing to trade: the fit is already
    variance-starved, not variance-rich. Measured shrinkage, in runs:

    =========================  ========  ========  ========
    ``lam``                    ``max|x|``  ``||x||``  ``R^2`` centred
    =========================  ========  ========  ========
    ``0`` (OLS)                17.43     27.24     ``-0.210259``
    ``1``                      14.57     24.02     ``-0.210357``
    ``10``                      5.92     14.74     ``-0.212150``
    ``50``                      4.11      8.80     ``-0.216264``
    ``200``                     2.31      4.38     ``-0.223703``
    ``1000``                    0.69      1.25     ``-0.232369``
    =========================  ========  ========  ========

    **A correction to the inherited expectation, recorded because
    ``AGENTS.md`` section 4 requires it.** The dispatch that specified this
    function expected "R2 centred unchanged to 4 dp (-0.2103)" across
    ``lam in [1, 1000]``, and asked for a test pinning that invariance to 1e-6.
    Measurement refutes it: R^2 falls monotonically to ``-0.232369``, a span of
    ``2.211e-2`` -- some twenty thousand times the tolerance the inherited test
    asked for. What survives is the one-sided theorem, and it is sharp: the
    residual sum of squares rises strictly for every ``lam > 0``, by ``+75.3``,
    ``+1450.8``, ``+4605.5``, ``+10310.8``, ``+16957.4`` at those five values.
    The suite pins that instead. An invariance assertion here would have been a
    false claim wearing the costume of a theorem.

    Parameters
    ----------
    A, b
        The Massey system.
    lam
        Shrinkage strength, must be ``>= 0``. ``lam = 0`` is the unregularised
        system, which is still singular and is solved with ``lstsq`` rather than
        inverted.

    Returns
    -------
    numpy.ndarray
        ``(n,)`` shrunk strengths, centred to zero sum so the gauge matches
        :func:`massey`. Note that ``A @ x`` -- every *predicted margin* -- is
        unaffected by the centring, exactly as the null direction requires.
    """
    A, rhs = _as_system(A, b)
    if lam < 0.0:
        raise ValueError(
            f"lam must be non-negative, got {lam!r}; a negative ridge term is "
            "not regularisation at all"
        )
    n = A.shape[1]
    AtA = A.T @ A
    Atb = A.T @ rhs
    if lam == 0.0:
        x = np.linalg.lstsq(AtA, Atb, rcond=None)[0]
    else:
        x = np.linalg.solve(AtA + lam * np.eye(n, dtype=np.float64), Atb)
    return _centre(x)


# --------------------------------------------------------------------------
# Held-out: the fit that has to survive contact with unseen seasons
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class HeldOutResult:
    """How the margin fit behaves on seasons it never saw.

    Attributes
    ----------
    n_train, n_test
        ``463`` and ``95`` rows. They sum to the full 558: every run-margin
        match lands in exactly one side.
    test_seasons
        The three held-out labels, measured ``['2024', '2025', '2026']``.
    accuracy
        Fraction of test matches whose winner the fit gets right: ``0.4316`` =
        ``41 / 95``. **Read with the degeneracy below**, not as a clean
        out-of-sample estimate.
    rmse
        Root-mean-square error on the test margins, measured **46.71 runs**.
    baseline_rmse
        RMSE of "predict the training mean margin", measured **35.35 runs**.
        This is the number that matters: the model is 32% *worse* than a single
        constant.
    train_mean
        The constant used for the baseline (the **training** mean, ``14.43``).
        Using the test mean instead would leak the answer and would flatter the
        model to 28.32.
    x
        The strengths fitted on the training split only.
    pred, b_test
        The test predictions and the test margins they are scored against.
    """

    n_train: int
    n_test: int
    test_seasons: list[str]
    accuracy: float
    rmse: float
    baseline_rmse: float
    train_mean: float
    x: np.ndarray
    pred: np.ndarray
    b_test: np.ndarray


def held_out_fit(matches, teams, n_test_seasons: int = 3) -> HeldOutResult:
    """Refit on the first seasons by sorted label, score on the last ``n_test_seasons``.

    The most honest test available from a single archive, and the one that
    breaks the model: with ``n_test_seasons = 3`` the train split is the first 16
    season labels (``463`` rows) and the test split is ``['2024', '2025',
    '2026']`` (``95`` rows).

    - in-sample winner accuracy ``0.5502`` -> **out of sample ``0.4316``**
    - test RMSE **46.71 runs** vs **35.35** for "predict the training mean"
    - and the first-listed team won **95 of those 95** test matches

    So the model loses to a constant on the data it was fitted on *and* loses
    badly on data it was not.

    **The out-of-sample number is degenerate, and the project says so rather than
    quoting it bare.** The first-listed team won every one of the 95 run-margin
    matches in 2024, 2025 and 2026, so the accuracy target is constant: "always
    predict the first-listed team" scores **100%** on this split, and the fit's
    43.2% is measured against a label that never varies.
    :func:`diagnostics.team1_share_by_season` shows the whole picture -- the share
    is between 0.44 and 0.67 for 2007/08-2017 and then **exactly 1.000 for all
    nine seasons from 2018 on**, so the three held-out seasons sit entirely inside
    the degenerate era. The 43.2% is real and it is reported, with this attached;
    the RMSE comparison against the training mean is the part of this result that
    does not depend on the label distribution at all.

    Per-match T20 margin noise is ~41 runs (residual spread) against a fitted
    spread of ~6 runs, so there is little signal here to generalise -- see
    :func:`diagnostics.noise_vs_signal`, and note that the old ``37``-vs-``7``
    figure compared two unrelated quantities.

    Seasons are split by **sorted label**, not by a date comparison, so the split
    is reproducible from the labels alone. That is safe for this snapshot because
    the 19 labels happen to sort chronologically under plain string order -- an
    invariant asserted by a test, because if a future snapshot broke it the
    "held-out" split would silently overlap time and the number would be fiction.

    Parameters
    ----------
    matches
        The committed snapshot frame, i.e. ``systems.matches``. Only used for its
        ``season``, ``margin_runs`` and ``winner`` columns, to decide which rows
        of ``A`` belong to which split. ``A`` and ``b`` come from
        :func:`data.design_matrix`, which is the single definition of the design
        convention; rebuilding them here would risk a silent sign or
        canonicalisation drift. The row counts are cross-checked below so a
        mismatched frame fails loudly instead of misaligning every label.
    teams
        The 15 canonical names in ``A``'s column order. Used for reporting and
        validated against ``A``.
    n_test_seasons
        How many of the sorted labels to hold out. Default 3.

    Returns
    -------
    HeldOutResult
    """
    A, b, names = design_matrix()
    if list(teams) != list(names):
        raise ValueError(
            "teams does not match the design matrix's column order: "
            f"{list(teams)[:3]}... vs {list(names)[:3]}...; every vector in this "
            "project is indexed by position, so the orders must be identical"
        )
    if n_test_seasons < 1:
        raise ValueError(f"n_test_seasons must be at least 1, got {n_test_seasons}")

    required = ("season", "margin_runs", "winner")
    missing = [column for column in required if column not in matches.columns]
    if missing:
        raise ValueError(
            f"matches is missing column(s) {missing}; pass systems.matches, the "
            "committed snapshot frame from data.load_matches()"
        )

    # The same row selection data.design_matrix() makes, so row i of this frame
    # is row i of A. Checked rather than assumed.
    is_run_margin = (matches["margin_runs"].notna() & matches["winner"].notna()).to_numpy(
        dtype=bool
    )
    run_rows = int(is_run_margin.sum())
    if run_rows != A.shape[0]:  # pragma: no cover - only a mismatched frame
        raise ValueError(
            f"matches yields {run_rows} run-margin rows but the design matrix "
            f"has {A.shape[0]}. They must come from the same snapshot, or every "
            "season label below would be attached to the wrong match."
        )

    run_frame = matches[is_run_margin]
    labels = sorted(str(label) for label in run_frame["season"].unique())
    if len(labels) <= n_test_seasons:  # pragma: no cover - 19 labels measured
        raise ValueError(
            f"{len(labels)} season labels cannot supply a train split alongside "
            f"{n_test_seasons} held-out season(s)"
        )
    test_labels = labels[-n_test_seasons:]
    is_test = (
        run_frame["season"].astype("string").isin(test_labels).to_numpy(dtype=bool)
    )

    A_train, b_train = A[~is_test], b[~is_test]
    A_test, b_test = A[is_test], b[is_test]

    x = _centre(np.linalg.lstsq(A_train, b_train, rcond=None)[0])
    pred = A_test @ x
    train_mean = float(b_train.mean())

    return HeldOutResult(
        n_train=int(A_train.shape[0]),
        n_test=int(A_test.shape[0]),
        test_seasons=test_labels,
        accuracy=float(np.mean(np.sign(pred) == np.sign(b_test))),
        rmse=float(np.sqrt(np.mean((pred - b_test) ** 2))),
        # The honest baseline uses the *training* mean. Using the test mean would
        # leak the labels into the comparator and flatter the model.
        baseline_rmse=float(np.sqrt(np.mean((train_mean - b_test) ** 2))),
        train_mean=train_mean,
        x=x,
        pred=pred,
        b_test=b_test,
    )


# --------------------------------------------------------------------------
# The diagonalisation link: A.T@A = V diag(sigma^2) V.T
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SvdResult:
    """The singular-value factorisation and the normal-equation eigenvalues.

    Attributes
    ----------
    singular_values
        ``(n,)`` singular values of ``A``: ``12.4779`` down to ``2.2216``, then
        one at ``5e-15`` -- the null direction, numerically.
    eigenvalues_ata
        ``(n,)`` eigenvalues of ``A.T@A``, descending, with the structurally
        zero one replaced by exactly ``0.0``.
    squared_singular_values
        The same vector as ``singular_values ** 2``.
    max_abs_diff
        Largest absolute difference between the two, measured **1.14e-13**. The
        numbers are *the same numbers*, and this is the measurement that says so
        rather than the algebra being asserted in prose.
    rank
        ``14`` -- the count of squared singular values above
        :data:`ZERO_CUTOFF`.
    U, Vt
        The reduced factors, kept because stage 10 has to display
        ``A.T@A = V diag(sigma^2) V.T`` and cannot do it without them.
    """

    singular_values: np.ndarray
    eigenvalues_ata: np.ndarray
    squared_singular_values: np.ndarray
    max_abs_diff: float
    rank: int
    U: np.ndarray
    Vt: np.ndarray


def svd_of_A(A: np.ndarray) -> SvdResult:
    """``np.linalg.svd``, plus the ``A.T@A = V diag(sigma^2) V.T`` link.

    Stage 10 in one function: the eigenvalues of the normal-equation matrix are
    the **squared** singular values of ``A``, so the symmetric 15x15 diagonal
    ``A.T@A`` carries no information about the 558x15 problem that ``A`` does not
    -- it is ``A`` rotated, and its one small eigenvalue (``5.65`` for ``A``,
    ``5e-15`` for ``A.T@A``) is where the rank deficiency went.

    Both vectors are returned **and** their largest gap, so the demo prints the
    equality as a measurement. Measured: ``1.14e-13``, i.e. the difference
    between two ways of asking ``numpy`` the same question.

    The zero eigenvalue is snapped to exactly ``0.0`` on return.
    ``np.linalg.eigvalsh`` reports ``-9.23e-15`` for a mathematically
    non-negative quantity, and leaving that in a table headed "eigenvalues" is how
    a spurious negative rank deficiency gets quoted.
    """
    M = np.asarray(A, dtype=np.float64)
    if M.ndim != 2:
        raise ValueError(f"A must be 2-D, got shape {M.shape}")
    if M.shape[0] < M.shape[1]:  # pragma: no cover - A is (558, 15)
        raise ValueError(
            "this function assumes the tall layout (rows >= columns) that the "
            f"Massey design matrix uses; got {M.shape}"
        )

    U, values, Vt = np.linalg.svd(M, full_matrices=False)
    squared = values**2
    eigenvalues = np.linalg.eigvalsh(M.T @ M)[::-1]
    eigenvalues[np.abs(eigenvalues) < ZERO_CUTOFF] = 0.0
    squared_for_comparison = squared.copy()
    squared_for_comparison[np.abs(squared_for_comparison) < ZERO_CUTOFF] = 0.0

    return SvdResult(
        singular_values=values,
        eigenvalues_ata=eigenvalues,
        squared_singular_values=squared_for_comparison,
        max_abs_diff=float(np.abs(eigenvalues - squared_for_comparison).max()),
        rank=int(np.count_nonzero(squared > ZERO_CUTOFF)),
        U=U,
        Vt=Vt,
    )
