# Dispatch — S9b/S10 (remainder): `demo.py`, `report.py`, `__main__.py`, `test_demo.py`

A previous node was interrupted after landing **`figures.py` (complete, 54 KB) and generating all 13 PNGs**. Those are done — 13 files exist in `figures/`, from `01-data.png` to `13-divergence.png`, all non-trivial sizes. **Do not rewrite `figures.py` or regenerate figures with different names.** Read it first to learn the exact `f01_data_funnel(...) … f13_divergence(...)` signatures — they are multi-line, so read them, do not guess.

**Read first:** `AGENTS.md` (§5 the 11 mandated stages **in order**; §7 provenance and licence; §10 maths legible), `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` §1 and §4, `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` §3 and §4.

**Finished, tested, correct — read the real APIs, do NOT modify any of them:**
`data.py`, `models.py`, `diagnostics.py`, `linalg_kit.py`, `canon.py`, `console.py`, `figures.py`, and all five existing test files. **187 tests currently pass and must stay green.**

APIs available to you:
- `data.build_systems() -> Systems` (`.matches, .A, .b, .W, .C, .M, .teams, .games, .official`), plus `load_matches`, `teams`, `design_matrix`, `colley_matrices`, `games_played`, `official_table`.
- `models.massey(A,b)` → `.x .resid .routes .max_route_diff .cond_constrained .singular_values .rank`; `models.colley(W,C)` → `.r .lam1 .lam2 .iterations .history .min_entry .all_positive`; `models.frequency_balanced(A,b,games)`; `models.ridge(A,b,lam)`; `models.held_out_fit(matches,teams,n_test_seasons=3)` → `.n_train .n_test .accuracy .rmse .baseline_rmse`; `models.svd_of_A(A)`.
- `diagnostics.r_squared(b, pred, *, centred)` — **keyword-only, no default**; `standard_errors(A, resid, rank, *, x)` → `(se, sigma2, t)`; `spearman`; `winner_accuracy`; `official_comparison(x, se, colley_r, official_df, names)`; `summary_table(...)`; `_official_points(official_df, names)`.
- `linalg_kit.rref, null_space, row_basis, gram_schmidt, power_iteration`.
- `figures.f01_data_funnel … f13_divergence`, plus `figures.figure_dir()` and `figures.report_dir()`.
- `console` public names — **use these, invent none**: `init, is_color, set_width, style, dim, bold, cyan, green, yellow, red, magenta, blue, white, ok, warn, bad, info, width, rule, box_top, box_bottom, box_sep, kv, table, mat, vec, vec_bars, Progress, sparkline, converge, stage, formula, step, note, measured, verdict, excluded, figure, timeline`.

**Blast radius — create/modify ONLY:** `ipl-power-ranking/src/iplranking/demo.py`, `ipl-power-ranking/src/iplranking/report.py`, `ipl-power-ranking/src/iplranking/__main__.py`, `ipl-power-ranking/tests/test_demo.py`. Four files. You write *into* `figures/` and `report/` as outputs. Nothing else. No `git add`/`commit`/`push`. Nothing under `docs/`.

**Environment:** Python 3.14.7, numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.2, pytest 9.1.1. No SciPy, no new dependency, no venv, no pip install.

## The owner's requirement

> every step when the project is run must be visual. each step must show what its calculating and what math principle is used

**`python -m iplranking` must print a narrated walkthrough of all 11 mandated stages.** Each stage: the principle in one line, the formula, what is being computed *as it happens* (a progress bar or live sparkline on the iterating step), every number via `console.measured(...)`, the saved figure via `console.figure(...)`, and a plain-English `console.verdict(...)`.

**Stage order, from `AGENTS.md` §5 — get this exactly right.** Matrix Simplification is **stage 3**, Structure of the Space is **stage 4**. This pair was transposed in this project's documents for two full runs and only adversarial review caught it.

## The substance — the narration is the deliverable

- **Stage 1** funnel; `console.excluded(25, 1243, "16 Super Over ties + 9 no result")` **loudly**; state 660 of 1,243 give wickets not runs and that **no run-equivalent conversion was invented**, with the reason.
- **Stage 2** `A` via `console.mat`, shape 558×15, every row sums to zero, and what that implies.
- **Stage 3** RREF with a live `Progress` bar over the elimination steps, then the pivot rows and **the singular row**.
- **Stage 4** `rank=14`, `nullity=1`, and demonstrate `A @ ones = 0` numerically — the central insight: only *differences* are identifiable.
- **Stage 5** 14 of 558 rows form the basis, 544 redundant.
- **Stage 6** **both** orthogonalisations, explicitly as **different spaces** — `Col(A) ⊆ R^558`, `Row(A) ⊆ R^15`. Say that this corrects an earlier claim in this project.
- **Stage 7** `r = b − Ax̂`, `‖r‖ = 963.42`, and `resid @ A ≈ 0` verified numerically.
- **Stage 8** all three least-squares routes, max diff `4.8e-14`; then **both** `R² = −0.2103` (centred) **and** `+0.0214` (uncentred), each labelled with its denominator, and say plainly that the inherited write-up quoted only the uncentred one and so hid that the model is **worse than predicting the mean**. Then in-sample `55.0%`; then held-out `43.2%`, RMSE `46.71` vs mean-baseline `35.35`.
- **Stage 9** power iteration with `console.converge(...)` or a sparkline of `ColleyFit.history`; **assert positivity out loud**; `λ₁ = 469.18`, `λ₂ = 14.81`, iterations to tolerance.
- **Stage 10** `AᵀA` symmetric, eigenvalues `≥ −1e-10`, and equal to the squared singular values.
- **Stage 11** the finding, stated plainly: the obvious approach does not work; noise `σ ≈ 37.07` runs vs strength spread `σ ≈ 7.03` runs (SNR ≈ 0.19); least squares weights every match equally so short-history franchises get extreme coefficients (`corr(games, |x|) = −0.663`); **not one coefficient distinguishable from zero at 2σ** (`max|t| = 1.20`); **frequency balancing was tried and made it worse** (max|x| 17.43 → 25.64) — report the refuted hypothesis, do not hide it; win/loss reproduces the official table at Spearman **+0.939** while margin manages **+0.093**.

Finish with `console.timeline(...)`: stage → figure → key number.

`main(argv=None) -> int` supporting `--offline` (assert no network), `--figures-only`, `--width N` → `console.set_width`. **Return 0 on success, non-zero on failure.** Add `__main__.py` so `python -m iplranking` works.

## `report.py`

`build_report() -> Path` → `report/report.html`, using `figures.report_dir()`. **Fully self-contained: every PNG base64-inlined, no external CSS, no JS, no CDN, no template engine** (`AGENTS.md` §8). Escape all interpolated text. One `<section>` per mandated stage in order: name, principle, formula in `<pre>`, measured numbers, the figure, the verdict. Plus a findings section with the three claims and an honest "what was excluded" block (25 of 1,243; 660 of 1,243). Plus a provenance block from `data/provenance.json` — URL, **what the SHA-256 actually covers**, row count, and the licence position exactly as `AGENTS.md` §7 requires: **precise attribution, no licence term asserted that was not read from the primary source.** Print-friendly (`@media print`), projector-readable.

## `tests/test_demo.py`

Never weaken an existing test to accommodate yourself.
- `main()` returns 0.
- All **13** figures exist and are valid PNGs (magic bytes).
- `report.html` written; no `<script src=`, no `http://`/`https://` resource reference; contains every stage heading; contains both R² values.
- **Determinism:** run the demo twice into two temp output dirs, assert every produced file is **byte-identical**.
- **Stage order:** captured stdout contains stage banners 1..11 in **ascending** order of first appearance. This is the regression test for the transposition that lived in this project's docs for two runs.
- Terminal output contains the 25-of-1,243 exclusion **and both R² values**.

## Verify before reporting — paste verbatim
```
cd C:\Anubhav\MFAD-Mini\ipl-power-ranking
python -m pytest -q
python -m iplranking --offline
python -m iplranking --offline > run1.txt 2>&1
python -m iplranking --offline > run2.txt 2>&1
(Get-FileHash run1.txt).Hash; (Get-FileHash run2.txt).Hash
```
Hashes must match. Delete `run1.txt`/`run2.txt` afterwards but **report the hashes**.

## Report back
1. Verbatim pytest final line and test count.
2. **Full verbatim terminal output of `python -m iplranking --offline`** — it is the deliverable, do not truncate or summarise it.
3. The two hashes and whether every figure was byte-identical across runs.
4. Any measured number that disagreed with this prompt, with both values.
5. Confirmation you touched only the four allowed files.