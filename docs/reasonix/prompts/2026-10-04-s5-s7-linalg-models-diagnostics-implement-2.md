# Dispatch — S5/S6/S7: the linear algebra, the models, the diagnostics

**Read first:** `AGENTS.md` (§4 honesty, §6 the two binding corrections), `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` (§3, §4 — these are your targets), `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` §3.

**`data.py`, `canon.py`, `parse.py` and the first 88 tests already exist and pass.** Read `data.py` before you write anything — it defines `load_matches`, `teams`, `design_matrix`, `colley_matrices`, `games_played`, `official_table`, `build_systems`. Do not modify it. If you believe it is wrong, report it; do not edit it.

**Blast radius — you may create/modify ONLY:**
`ipl-power-ranking/src/iplranking/linalg_kit.py`, `ipl-power-ranking/src/iplranking/models.py`, `ipl-power-ranking/src/iplranking/diagnostics.py`, `ipl-power-ranking/tests/test_structure.py`, `ipl-power-ranking/tests/test_models.py`, `ipl-power-ranking/tests/test_diagnostics.py`.
Six files. Touching anything else is a breach — stop and report. Do NOT run `git add`/`commit`/`push`. Do NOT edit anything under `docs/`. Do NOT touch `console.py`, `figures.py`, `report.py`, `demo.py` (other nodes own them) or the three existing data modules.

**Environment:** system Python 3.14.7, numpy 2.5.2, pandas 3.0.5, pytest 9.1.1. **No SciPy** — implement Spearman rank correlation by hand from `numpy`. Do NOT create a venv or pip install.

Run tests from `C:\Anubhav\MFAD-Mini\ipl-power-ranking` with `python -m pytest -q`.

## THE most important rule

**NEVER make a test pass by editing, skipping, deleting or weakening an assertion.** Every number below was measured on 2026-10-04. If your implementation produces a different number, **STOP and report the discrepancy with both values.** Do not "fix" it by loosening a tolerance to 1e-6 and moving on. This repository has already lost two full runs to unmeasured numbers; a silent tolerance widening is exactly that failure. Pin to the precision given and nothing looser.

## Targets — measured 2026-10-04, reproduce these

```text
A (558, 15)   rank 14   nullity 1   cond on rank 5.6167
singular values: largest 12.4779, smallest nonzero 2.2216, one value ~0 (1e-15)
||r||^2 = 928185.2      ||r|| = 963.4237
||b||^2 = 948444.0      ||b - mean(b)||^2 = 766931.3
R2 uncentred = +0.0214          R2 centred = -0.2103
in-sample winner accuracy = 0.5502
sigma^2 = ||r||^2/544 = 1706.2      se range 4.68 .. 17.63
max |x/se| over 15 teams = 1.20
Colley: lambda1 = 469.1757, lambda2 = 14.8064, all 15 entries > 0
Spearman(Massey, Colley) = 0.000      Pearson = -0.1217
Spearman(Massey, official) = +0.093   Spearman(Colley, official) = +0.939
corr(games_played, |x|) = -0.663
held-out: train = first 16 seasons by sorted label (463 rows), test = last 3 (95 rows)
          accuracy 0.432, RMSE 46.71   vs  "predict the mean" RMSE 35.35
frequency-balanced: Kochi |x| 17.43 -> 25.64, Gujarat Lions 13.70 -> 13.24
                     max|x| 17.43 -> 25.64, R2 centred -0.2103 -> -0.2113
ridge lam in [1, 10, 50, 200, 1000]: R2 centred unchanged to 4 dp (-0.2103)
```

## 1. `linalg_kit.py` — hand-written, because the examiner reads the machinery

`AGENTS.md` §5 mandates RREF, basis selection, Gram–Schmidt. Use NumPy for arrays; **write the algorithms yourself** so the steps are legible, and comment the mathematics as you go.

- `rref(M, tol=1e-10) -> (R, pivot_rows, rank)` — Gauss–Jordan with partial pivoting. `pivot_rows` must record **which original rows** became pivots (that is the row basis, needed by `row_basis` below). Return values rounded to a sensible tolerance — do not leave 1e-16 dust that makes `np.allclose` checks fragile.
- `null_space(M, tol=1e-10) -> np.ndarray` — basis of `ker(M)`, shape `(nullity, n)`.
- `row_basis(M) -> np.ndarray` — a **maximal linearly independent subset of the rows of `M`**, obtained from `rref`'s pivot rows. For `A` this must return exactly **14 rows out of 558**. `AGENTS.md` §5 stage 5.
- `gram_schmidt(rows) -> (Q, residuals)` — classical Gram–Schmidt on a matrix whose rows are vectors; `Q` orthonormal with `Q @ Q.T ≈ I`, and `residuals[k]` is the post-step off-orthogonality norm, so the demo can show it shrinking. Also provide a re-orthogonalised variant and report the difference.
- `power_iteration(M, x0=None, tol=1e-12, max_iter=5000) -> (x, lam, history)` — hand-written, returning the full convergence history so the demo can draw a live sparkline. Deterministic `x0` (all ones, normalised) — **no randomness**.

### The distinction you must not get wrong (`AGENTS.md` §6)
For `A` at 558×15 with rank 14:
- Thin QR of `A` gives `Q` of shape **(558, 15)** — 15 orthonormal columns spanning a **15-dimensional** space that *contains* the 14-dimensional `Col(A)`. It is **not** a basis of `Col(A)`, and it is **certainly not** a basis of `Row(A) ⊆ R^15`.
- `Row(A)` is a different space, in `R^15`, dimension 14, and needs its own orthogonalisation — `gram_schmidt` on the 14 basis rows from `row_basis`, or QR of `A.T`.
Expose `col_space_basis(A)` and `row_space_basis(A)` as separate functions returning the two different objects, and **write a test that distinguishes them**: `A @ col_basis == col_basis` up to the singular cutoff for 14 of the 15 directions, while the row basis satisfies `Q @ Q.T ≈ I_14` and lies in `R^15` with `rank(A) == Q.shape[0]`. A test that cannot tell these two spaces apart is a test that cannot fail.

## 2. `models.py`

- `massey(A, b) -> MasseyFit` — least squares. Compute **three independent routes** and assert they agree:
  1. `numpy.linalg.lstsq` (SVD-based, handles rank deficiency)
  2. the **singular** normal equations `A.T @ A @ x = A.T @ b`, solved by `np.linalg.lstsq` because `A.T @ A` is rank 14 too
  3. the **constrained** form `A.T @ A @ x + 1*1.T @ x = A.T @ b` — nonsingular, pins the null direction explicitly
  Measured: all three agree to ~4.8e-14. **Record the max absolute difference in the result object** so the demo can print it.
  Return a dataclass with `x` (centred to zero-sum), `resid`, `routes` dict, `max_route_diff`, `cond_constrained`, `singular_values`.
- `colley(W, C) -> ColleyFit` — **hand-written power iteration** on `M = W + W.T + C`, iterating `r ← M r / ‖M r‖`. Normalise the final `r` to **sum 1** (so it reads as a percentage share). **Assert, do not assume, Perron–Frobenius positivity**: every entry strictly `> 0`. Return `r`, `lam1`, `lam2`, `iterations`, `history`, `min_entry`, and a boolean `all_positive`.
- `frequency_balanced(A, b, games_per_team) -> np.ndarray` — weight match `i` by `w_i = 1/(games(t1) + games(t2))`, solve `min ‖A^T W^{1/2} x − W^{1/2} b‖`. Return the weighted solve plus the weights.
  **This is the refuted hypothesis from the inherited plan.** Measured: it makes the short-history extremity *worse* (Kochi 17.43 → 25.64), because balancing **up-weights** the few matches Kochi played. Docstring must say so.
- `ridge(A, b, lam) -> np.ndarray` — `lam` shrinkage on `A.T@A + lam*I`.
  Docstring must record **why ridge cannot improve R² here, and that it is a theorem not an observation**: `x̂` is *the* minimiser of `‖Ax − b‖`, so no re-fit by least squares can lower that residual sum of squares. Measured: R² centred is unchanged to 4 dp for `lam ∈ [1, 1000]`.
- `held_out_fit(matches, teams, n_test_seasons=3) -> HeldOutResult` — build the systems from a train split, fit, evaluate on the test split. Report accuracy, RMSE, and the **"predict the mean margin" baseline RMSE** for comparison.
- `svd_of_A(A) -> SvdResult` — `np.linalg.svd`, plus the `A.T@A = V Σ² V^T` link: return the eigenvalues of `A.T@A` and show they equal the squared singular values.

## 3. `diagnostics.py`

- `r_squared(b, pred, *, centred: bool) -> float` — **two denominators, explicitly named, never a default.** `centred=True` → `1 − SSres/Σ(b−b̄)²`. `centred=False` → `1 − SSres/Σb²`. Docstring must state the measured values (**−0.2103** and **+0.0214**) and that the inherited build-audit reported only the uncentred one, so a negative `R²` — "worse than predicting the mean" — was hidden. **Never expose an `r_squared` with a silent default.** A bare `r_squared(b, pred)` call must not be possible.
- `standard_errors(A, resid, rank) -> (se, sigma2, t_stats)` — `sigma2 = ‖r‖²/(m − rank) = ‖r‖²/544`, `Cov = sigma2 * inv(A.T@A + 1*1.T)`, `se = sqrt(diag)`, `t = x/se`.
- `spearman(u, v) -> float` — **hand-rolled, no SciPy**: rank both with average ranks for ties, then Pearson on the ranks. Document the tie-averaging.
- `winner_accuracy(pred, b) -> float`
- `official_comparison(x, colley_r, official_df) -> pd.DataFrame` — one table: team, official points, official rank, massey `x ± se`, massey rank, colley share %, colley rank, rank movement. Sorted by official points.
- `summary_table(teams, massey_x, se, colley_r, official_df, games) -> pd.DataFrame` — the headline table, sorted by massey `x` desc, with the games-played column **visible**, because the short-history leverage is the diagnosis.

## 4. Tests

`tests/test_structure.py` — pin `rank(A) == 14`, `nullity(A) == 1`, `A @ ones == 0` (the null direction is **exactly** the constant vector — this is the project's central insight, test it directly), `rref` correctness on small hand-checkable matrices (a 2×2, a 3×3 singular one, an all-zero-row one) **and** on `A` itself, `row_basis` returning exactly 14 rows that are genuinely independent (`matrix_rank == 14`), `gram_schmidt` orthonormality to 1e-10, `power_iteration` converging to the same vector as `np.linalg.eigh`, and the `Col(A)` vs `Row(A)` distinction test described above.

`tests/test_models.py` — three LS routes agree to **1e-10**; centred `x` sums to 0; `colley` all-positive and sums to 1; `colley` `lam1 > lam2 > 0`; `frequency_balanced` **increases** `max|x|` (the refutation — assert the direction, with a comment saying this is the refuted hypothesis so nobody "fixes" it later); ridge `R²` invariance across `lam ∈ [1, 1000]` to 1e-6 (a theorem, so a loose-but-meaningful tolerance is correct here — say why in a comment); `held_out` RMSE **greater** than the mean-baseline RMSE; `A.T@A` eigenvalues equal squared singular values to 1e-8.

`tests/test_diagnostics.py` — both `R²` variants to 4 dp (**−0.2103** and **+0.0214**) and their sum-of-squares identities; `sigma2 == ‖r‖²/544`; `se` min/max to 2 dp (4.68/17.63); `max|t| < 1.25` (the finding: not one coefficient significant at 2σ); Spearman to 3 dp for all three pairs (**0.000**, **+0.093**, **+0.939**); `pearson(massey, colley) ≈ −0.122`; `corr(games, |x|) ≈ −0.663`; winner accuracy 0.5502 to 3 dp; and that `r_squared` **cannot** be called without an explicit `centred=` argument — test that with `inspect.signature`.

## 5. Verification before reporting
Run and paste verbatim:
```
cd C:\Anubhav\MFAD-Mini\ipl-power-ranking
python -m pytest -q
python -c "import sys;sys.path.insert(0,'src');from iplranking.data import build_systems;from iplranking import models,diagnostics as d;s=build_systems();m=models.massey(s.A,s.b);c=models.colley(s.W,s.C);print('rank',s.A.shape,m.routes is not None,m.max_route_diff);print('colley all_pos',c.all_positive,c.lam1,c.iterations);print('R2c',d.r_squared(s.b,s.A@m.x,centred=True),'R2u',d.r_squared(s.b,s.A@m.x,centred=False));print('spearman',d.spearman(m.x,c.r))"
```
Also **mutation-check at least three** of your own assertions — break the code deliberately, confirm a test catches it, restore. Report which mutations you tried and what caught them. A test suite that has never been shown to fail is not evidence.

## Report back
1. Verbatim pytest final line, and the verbatim output of the second command.
2. **Every measured number that disagreed with the target list, with both values.** If none disagreed, say so explicitly.
3. Which mutations you tried and what caught them.
4. Confirmation you touched only the six files in the blast radius.