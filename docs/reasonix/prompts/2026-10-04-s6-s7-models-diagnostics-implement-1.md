# Dispatch — S6/S7 (remainder): `models.py`, `diagnostics.py` and their tests

**Context:** a previous node was interrupted after landing `linalg_kit.py` and `tests/test_structure.py`. Those are done and **127 tests pass**. Do not rewrite them.

**Read first:** `AGENTS.md` (§4 honesty, §6 the two binding corrections), `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` §3 and §4, `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` §3.

**Read these before writing** — they are finished, correct, and you must use their real APIs: `src/iplranking/data.py`, `src/iplranking/linalg_kit.py`, `src/iplranking/canon.py`, and `tests/test_structure.py`. Do **not** modify any of them.

**Blast radius — you may create/modify ONLY these four files:**
- `ipl-power-ranking/src/iplranking/models.py`
- `ipl-power-ranking/src/iplranking/diagnostics.py`
- `ipl-power-ranking/tests/test_models.py`
- `ipl-power-ranking/tests/test_diagnostics.py`

Touching anything else is a breach — stop and report. Do NOT run `git add`/`commit`/`push`. Do NOT edit anything under `docs/`. Do NOT touch `console.py`, `figures.py`, `report.py`, `demo.py` (other nodes own them) or `data.py`/`linalg_kit.py`/`canon.py`/`parse.py` (finished).

**Environment:** system Python 3.14.7, numpy 2.5.2, pandas 3.0.5, pytest 9.1.1. **No SciPy** — implement Spearman by hand from numpy. **No venv, no pip install.**

Run tests from `C:\Anubhav\MFAD-Mini\ipl-power-ranking` with `python -m pytest -q`.

## THE most important rule

**NEVER make a test pass by editing, skipping, deleting or weakening an assertion.** Every number below was measured on 2026-10-04 against this exact snapshot. If your implementation produces a different number, **STOP and report the discrepancy with both values.** Do not loosen a tolerance and continue — a silently widened tolerance is precisely the failure this repository has already paid for twice. Pin to the precision stated and nothing looser.

## Targets — measured 2026-10-04, reproduce these

```text
||r||^2 = 928185.2      ||r|| = 963.4237
||b||^2 = 948444.0      ||b - mean(b)||^2 = 766931.3
R2 uncentred = +0.0214          R2 centred = -0.2103
three least-squares routes agree to ~4.8e-14
in-sample winner accuracy = 0.5502
sigma^2 = ||r||^2/544 = 1706.2      se range 4.68 .. 17.63
max |x/se| over 15 teams = 1.20
Colley: lambda1 = 469.1757, lambda2 = 14.8064, all 15 entries > 0, r sums to 1
Spearman(Massey, Colley) = 0.000      Pearson = -0.1217
Spearman(Massey, official) = +0.093   Spearman(Colley, official) = +0.939
corr(games_played, |x|) = -0.663
held-out: train = first 16 seasons by sorted label (463 rows), test = last 3 (95 rows)
          accuracy 0.432, RMSE 46.71   vs  "predict the mean" baseline RMSE 35.35
frequency-balanced: max|x| 17.43 -> 25.64  (WORSE — the refuted hypothesis)
                     Kochi 17.43 -> 25.64, Gujarat Lions 13.70 -> 13.24
                     R2 centred -0.2103 -> -0.2113
ridge lam in [1, 10, 50, 200, 1000]: R2 centred unchanged to 4 dp (-0.2103)
eigenvalues of A.T@A == squared singular values of A, to 1e-8
```

## 1. `models.py`

- `massey(A, b) -> MasseyFit` — least squares, dataclass result carrying `x` (centred to **zero-sum**), `resid`, `routes` dict, `max_route_diff`, `cond_constrained`, `singular_values`, `rank`.
  Compute **three independent routes** and assert they agree:
  1. `numpy.linalg.lstsq` (SVD-based, handles rank deficiency)
  2. the **singular** normal equations `A.T@A x = A.T@b`, solved via `np.linalg.lstsq` because `A.T@A` is rank 14 too
  3. the **constrained** form `A.T@A x + 1*1.T@x = A.T@b` — nonsingular, pins the null direction explicitly
  `max_route_diff` must record the measured maximum absolute difference across the three so the demo can print it.
- `colley(W, C) -> ColleyFit` — **hand-written power iteration** on `M = W + W.T + C`: `r <- M r / ||M r||`. Deterministic start (all ones, normalised) — **no randomness anywhere**. Normalise the final `r` to **sum 1** so it reads as a percentage share. **Assert, do not assume, Perron–Frobenius positivity**: every entry strictly `> 0`. Return `r`, `lam1`, `lam2`, `iterations`, `history` (full convergence trace so the demo can draw a live sparkline), `min_entry`, `all_positive`.
  Cross-check against `np.linalg.eigh` in the tests.
- `frequency_balanced(A, b, games_per_team) -> BalancedFit` — weight match `i` by `w_i = 1/(games(t1) + games(t2))`, solve `min ||A.T @ W^{1/2} x - W^{1/2} b||`. Return the weighted solution **and** the weight vector.
  **This is the refuted hypothesis from the inherited plan, and your docstring must say so.** Measured: it makes the short-history extremity *worse* (Kochi 17.43 → 25.64) because balancing **up-weights** the few matches Kochi played. A reader must not be able to open this file and conclude the fix works.
- `ridge(A, b, lam) -> np.ndarray` — `lam` shrinkage on `A.T@A + lam*I`.
  Docstring must record **why ridge cannot improve R² here, as a theorem not an observation**: `x̂` is *the* minimiser of `‖Ax − b‖`, so no re-fit by least squares can lower that residual sum of squares. Measured: unchanged to 4 dp for `lam ∈ [1, 1000]`.
- `held_out_fit(matches, teams, n_test_seasons=3) -> HeldOutResult` — split seasons by **sorted label**, last 3 as test; build systems from each split via `data.py`'s own helpers; fit; report `n_train`, `n_test`, `accuracy`, `rmse`, and the **`predict the mean margin` baseline RMSE** for comparison.
- `svd_of_A(A) -> SvdResult` — `np.linalg.svd` plus the `A.T@A = V Σ² Vᵀ` link: return the eigenvalues of `A.T@A` and the squared singular values so the demo can show they are the same numbers.

## 2. `diagnostics.py`

- `r_squared(b, pred, *, centred: bool) -> float` — **two denominators, explicitly named, no default.** `centred=True` → `1 − SSres/Σ(b−b̄)²`; `centred=False` → `1 − SSres/Σb²`.
  Docstring must state the measured values (**−0.2103** centred, **+0.0214** uncentred) and record that the inherited build-audit headline reported **only the uncentred one**, which hid a negative R² — i.e. that the model is *worse than predicting the mean margin*.
  **`centred` is keyword-only with no default**, so `r_squared(b, pred)` is not callable. A silent default here is how the inherited error survived.
- `standard_errors(A, resid, rank) -> (se, sigma2, t_stats)` — `sigma2 = ‖r‖²/(m − rank) = ‖r‖²/544`, `Cov = sigma2 * inv(A.T@A + 1*1.T)`, `se = sqrt(diag(Cov))`, `t = x/se`.
- `spearman(u, v) -> float` — **hand-rolled, no SciPy**: average-tie ranks both inputs, then Pearson on the ranks. Document the tie-averaging. Must reproduce `0.000`, `+0.093`, `+0.939` from the target list.
- `winner_accuracy(pred, b) -> float`
- `official_comparison(x, colley_r, official_df) -> pd.DataFrame` — one row per canonical team: `team, points, official_rank, massey_x, massey_se, massey_rank, colley_share, colley_rank, rank_movement`. Sorted by points desc, then team asc for determinism.
- `summary_table(teams, massey_x, se, colley_r, official_df, games) -> pd.DataFrame` — the headline table sorted by `massey_x` desc, with a **`games_played` column that is visible**, because short-history leverage is the diagnosis and hiding it would hide the finding.

## 3. Tests

`tests/test_models.py`:
- three LS routes agree to **1e-10**; `max_route_diff` is measured and recorded
- centred `x` sums to 0; `resid` orthogonality `resid @ A ≈ 0` (the normal-equation condition, worth pinning explicitly)
- `colley` all entries `> 0`, sums to 1, `lam1 > lam2 > 0`, and matches `np.linalg.eigh`'s dominant eigenvector to 1e-8
- **`frequency_balanced` *increases* `max|x|`** — assert the direction, with a comment stating this is the refuted hypothesis so a future agent does not "fix" the assertion
- ridge `R²` invariance across `lam ∈ [1, 1000]` to 1e-6 — correct and deliberate here because it is a **theorem**; say so in the comment
- `held_out` RMSE **strictly greater** than the mean-baseline RMSE
- eigenvalues of `A.T@A` equal squared singular values to 1e-8

`tests/test_diagnostics.py`:
- both `R²` variants to 4 dp (**−0.2103** and **+0.0214**), plus the underlying sum-of-squares identities
- `sigma2 == ‖r‖²/544`; `se` min/max to 2 dp (4.68 / 17.63)
- **`max|t| < 1.25`** — the finding: not one coefficient is significant at 2σ. Comment must state that this is a result, not a loose bound.
- Spearman to 3 dp for all three pairs; `pearson(massey, colley) ≈ −0.122`; `corr(games, |x|) ≈ −0.663`
- winner accuracy 0.5502 to 3 dp
- `r_squared` **cannot** be called without an explicit `centred=` — test via `inspect.signature`, asserting it is keyword-only and has no default
- `summary_table` has 15 rows, is sorted by `massey_x` desc, and contains `games_played`

## 4. Verification before reporting

Run and paste **verbatim**:
```
cd C:\Anubhav\MFAD-Mini\ipl-power-ranking
python -m pytest -q
```
then:
```
python -c "import sys;sys.path.insert(0,'src');from iplranking.data import build_systems;from iplranking import models,diagnostics as d;s=build_systems();m=models.massey(s.A,s.b);c=models.colley(s.W,s.C);print('routes maxdiff',m.max_route_diff);print('colley pos',c.all_positive,'lam1',round(c.lam1,4),'iters',c.iterations);print('R2c',round(d.r_squared(s.b,s.A@m.x,centred=True),4),'R2u',round(d.r_squared(s.b,s.A@m.x,centred=False),4));print('spearman',round(d.spearman(m.x,c.r),4))"
```

Then **mutation-check at least three assertions**: break something deliberately, confirm a named test catches it, restore. Report each mutation and what caught it. A suite never shown to fail is not evidence.

## 5. Report back
1. Verbatim pytest final line and verbatim second-command output.
2. **Every measured number that disagreed with the target list, with both values.** If none did, say so explicitly.
3. Mutations tried and what caught them.
4. Confirmation you touched only the four files in the blast radius.