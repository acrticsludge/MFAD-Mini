# 04 — The eleven stages

What the demo computes at each of the 11 stages, in the order `AGENTS.md` §5
mandates. Every number is measured at run time from `data/matches.csv`. None is
hard-coded, and `tests/` pins each one.

The order matters: **Matrix Simplification is stage 3 and Structure of the Space
is stage 4**. Documents in this repo had that pair swapped for two runs.
`tests/test_demo.py` now pins the banner order
(`test_stage_banners_appear_in_ascending_order`,
`test_matrix_simplification_precedes_structure_of_the_space`).

> **Open audit finding:** the design-matrix sign convention behind stages 2, 8
> and 11 looks wrong, and several headline numbers below may come from it. Read
> [10-known-issues.md](10-known-issues.md) before you rely on any Massey
> number.

## Before stage 1: what `run_demo()` loads once

`demo.run_demo()` (`src/iplranking/demo.py`) does this, in order:

1. `provenance_record()` reads `data/provenance.json`. If the file is missing it
   gets `{}` and the run continues.
2. `header()` prints the banner (skipped with `--figures-only`).
3. `data.build_systems()` loads the CSV once and returns a frozen `Systems`
   bundle: `matches`, `A`, `b`, `W`, `C`, `M`, `teams`, `games`, `official`.
4. Both models are fitted up front: `models.massey(A, b)`,
   `diagnostics.standard_errors(...)`, `models.colley(W, C)`,
   `models.held_out_fit(..., n_test_seasons=3)`, and
   `diagnostics.official_comparison(...)`.
5. It calls `_stage_1` … `_stage_11` explicitly, in order. `demo.STAGES` holds
   only each stage's number, mandated name and one-line principle, and
   `_stage_N` reads its banner text from there.
6. `closing()` prints the summary timeline (skipped with `--figures-only`). The
   result goes back to `__main__`, which passes it to `report.build_report()`.

Each stage prints the same five things: a banner (name + principle), an ASCII
formula, the live computation (progress bar, convergence trace or sparkline),
the measured values, and a plain-English verdict. It also saves a figure.

## Stage by stage

| # | Stage | What runs | Code | Figure |
|---|-------|-----------|------|--------|
| 1 | Real-world data | Sorts all 1,243 matches into 558 run-margin, 660 wicket-only and 25 with no winner (16 Super Over, 9 no result), and states the exclusions out loud | `demo._stage_1` | `01-data.png` (data funnel) |
| 2 | Matrix representation | Builds `A` (558 × 15) and `b` row by row, one equation per run-margin match, then checks that every row sums to 0 | `data.design_matrix` | `02-design-matrix.png` |
| 3 | Matrix simplification | Hand-written Gauss–Jordan RREF with partial pivoting and a progress bar over the columns. Shows the 14 pivot rows and the one row that gets no pivot | `linalg_kit.rref` | `03-rref.png` |
| 4 | Structure of the space | Reads rank 14 / nullity 1 off the RREF, shows `A @ 1 = 0`, gets the null-space basis from the free column, and gives the singular spectrum as magnitudes | `linalg_kit.null_space`, `np.linalg.svd` | `04-structure.png` |
| 5 | Remove redundancy | Tests all 558 rows for independence and keeps the 14 pivot rows. The other 544 are combinations of them | `linalg_kit.row_basis` | `05-redundancy.png` |
| 6 | Orthogonalization | Two different spaces. **Col(A) ⊂ R⁵⁵⁸:** thin QR gives a 558 × 15 `Q`; the first 14 columns span Col(A) and the 15th is a completion outside it. **Row(A) ⊂ R¹⁵:** Gram–Schmidt (classical and re-orthogonalised) on the 14 pivot rows gives a 14 × 15 orthonormal basis, with off-orthogonality traced at each step | `linalg_kit.col_space_basis`, `linalg_kit.gram_schmidt` | `06-qr.png` |
| 7 | Projection | `b = A x̂ + r`. Checks that `r · q_j = 0` for all 14 in-space directions (the normal equations) and that Pythagoras holds | `demo._stage_7` (uses stage 6's column basis) | `07-projection.png` |
| 8 | Prediction / least squares | Three least-squares routes (`lstsq`, `normal_equations`, `constrained` = `solve(AᵀA + 11ᵀ, Aᵀb)`) agree to 4.8e-14. Prints standard errors, both R² denominators, the intercept variant, winner accuracy against the majority class, the held-out split (last 3 seasons) with its degeneracy, noise against signal on one scale, and a ridge sweep | `models.massey`, `models.ridge`, `models.held_out_fit`, `diagnostics.*` | `08-least-squares.png` |
| 9 | Pattern discovery | Live power iteration on `M = W + Wᵀ + C` starting from the normalised ones vector, checked against `models.colley`. Prints λ₁, λ₂ (from `eigvalsh`), the smallest eigenvalue (M is indefinite), and checks out loud that every share is strictly positive | `linalg_kit.power_iteration`, `models.colley` | `09-eigen.png` |
| 10 | System simplification | Forms `AᵀA` (15 × 15, symmetric by construction) and shows that its eigenvalues are the squared singular values of `A`. The one zero eigenvalue is the rank-14 deficiency again | `models.svd_of_A` | `10-diagonalisation.png` |
| 11 | Final application output | Joins the rankings to the official table **by team name**. Covers three claims (the margin model fails; why, measured on one scale; win/loss carries what the margin throws away), the refuted frequency-balancing hypothesis, and the headline summary table | `diagnostics.spearman`, `diagnostics.noise_vs_signal`, `models.frequency_balanced`, `diagnostics.summary_table` | `11-ranking.png`, `12-findings.png`, `13-divergence.png` |

## How the matrices are built (`data.py`)

- **`A`, `b`:** one row per run-margin match that has a winner, in CSV
  (chronological) order. The code does
  `sign = +1 if winner == team1 else -1`, then `A[i, team1] = sign`,
  `A[i, team2] = -sign` and `b[i] = sign * margin_runs`. The winner's column
  gets +1 and the loser's −1. `b` is positive when team1 won and negative when
  team2 won. The two conventions conflict; see
  [10-known-issues.md](10-known-issues.md).
- **`W`, `C`, `M`:** these use all 1,218 decided matches. `W[i, j]` counts how
  many times `i` beat `j`. `C[i, j]` counts the games between them (symmetric,
  zero diagonal). `M = W + Wᵀ + C`.
- **`games`:** the games each team played within the 558 run-margin matches.
  They sum to 1,116.
- **`official`:** the all-time table **computed from the snapshot** at 2 points
  per win. The 25 no-winner matches are excluded, so Super Over ties do not get
  the 1 point each they really earn. It is not the published IPL table.
  `AGENTS.md`'s manual checklist flags that all-time vs per-season is a
  question you will be asked in the viva.
- **Team order:** alphabetical everywhere. Every matrix indexes teams by
  position.

## The two models

| Model  | Dataset                | Method |
| ------ | ---------------------- | ------ |
| Massey | 558 run-margin matches | least squares, `A x ≈ b`, centred so that `Σx = 0` |
| Colley-style | 1,218 decided matches | Perron eigenvector of `M`, normalised to shares that sum to 1 |

"Colley-style" is a deliberate attribution. Colley's 2002 paper solves a linear
system; this project computes the eigenvector form of the same idea.

## Numbers the demo currently prints

These are as measured today. Each depends on the sign convention above.

- Centred R² **−0.2103**, uncentred **+0.0214**. Adding an intercept gives
  **+0.0181**.
- Winner accuracy **55.02%** against a majority-class baseline of **77.96%**.
- `||r||/sqrt(m) = 40.79` against `std(A x) = 5.98`, a ratio of **6.82×**.
- Held-out accuracy **43.2%**. The split is degenerate from 2018 onward.
- Spearman: Massey vs Colley **0.000**, Colley vs official **+0.939**, Massey
  vs official **+0.093**.
- Frequency balancing makes `max|x|` worse: **17.43 → 25.64**.
