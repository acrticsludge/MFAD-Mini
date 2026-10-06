# Dispatch — S9/S10: figures, the 11-stage visual demo, and the HTML report

This is the deliverable the owner actually sees. Everything exists to serve it.

**Read first:** `AGENTS.md` (§5 the 11 mandated stages in order, §10 the maths must be legible), `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` §1 and §4, `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` §3 and §4.

**Everything below is finished, tested (187 passing) and correct. Read the real APIs — do not modify:**
`src/iplranking/data.py`, `models.py`, `diagnostics.py`, `linalg_kit.py`, `canon.py`, `console.py`, and all five test files.

Key APIs you will use:
- `data.build_systems() -> Systems` with fields `matches, A, b, W, C, M, teams, games, official`; also `load_matches()`, `teams()`, `design_matrix()`, `colley_matrices()`, `games_played()`, `official_table()`.
- `models.massey(A, b) -> MasseyFit` (`.x`, `.resid`, `.routes`, `.max_route_diff`, `.cond_constrained`, `.singular_values`, `.rank`); `models.colley(W, C) -> ColleyFit` (`.r`, `.lam1`, `.lam2`, `.iterations`, `.history`, `.min_entry`, `.all_positive`); `models.frequency_balanced(A, b, games) -> BalancedFit` (`.x`, weights); `models.ridge(A, b, lam)`; `models.held_out_fit(matches, teams, n_test_seasons=3) -> HeldOutResult`; `models.svd_of_A(A) -> SvdResult`.
- `diagnostics.r_squared(b, pred, *, centred: bool)` (**keyword-only, no default — read the docstring, it records the R² denominator error**); `standard_errors(A, resid, rank, *, x)`; `spearman(u, v)`; `winner_accuracy(pred, b)`; `official_comparison(x, se, colley_r, official_df, names)`; `summary_table(...)`. **Use `diagnostics._official_points` / `official_comparison` for anything joined to the official table — it re-indexes by team name, and comparing positionally against the points-sorted table silently measures nothing. That trap has already produced one wrong measurement in this project.**
- `linalg_kit.rref`, `null_space`, `row_basis`, `gram_schmidt`, `power_iteration`.
- `console` has exactly these public names — use them, do not invent new ones: `init`, `is_color`, `set_width`, `style`, `dim`, `bold`, `cyan`, `green`, `yellow`, `red`, `magenta`, `blue`, `white`, `ok`, `warn`, `bad`, `info`, `width`, `rule`, `box_top`, `box_bottom`, `box_sep`, `kv`, `table`, `mat`, `vec`, `vec_bars`, `Progress`, `sparkline`, `converge`, `stage`, `formula`, `step`, `note`, `measured`, `verdict`, `excluded`, `figure`, `timeline`.

**Blast radius — you may create/modify ONLY these four files:**
- `ipl-power-ranking/src/iplranking/figures.py`
- `ipl-power-ranking/src/iplranking/demo.py`
- `ipl-power-ranking/src/iplranking/report.py`
- `ipl-power-ranking/src/iplranking/__main__.py`

You may also **create** `ipl-power-ranking/tests/test_demo.py`. Nothing else. Do NOT run `git add`/`commit`/`push`. Do NOT edit anything under `docs/`, `data/`, `figures/`, `report/` (you *write into* `figures/` and `report/` as outputs — that is expected).

**Environment:** system Python 3.14.7, numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.2, pytest 9.1.1. No SciPy. No new dependency. No venv. Use the **Agg** matplotlib backend and headless operation.

Run from `C:\Anubhav\MFAD-Mini\ipl-power-ranking`. Tests: `python -m pytest -q`.

## The owner's requirement, verbatim

> the end result must be visual, every step when the project is run, whether it is a terminal command or whatever must be visual. each step must show what its calculating etc where what math principle is used

So: **`python -m iplranking` (and `python -m iplranking.demo`) must print a narrated walkthrough of all 11 mandated stages, and each stage must show the principle, the formula, what is being computed as it happens, and the numbers as they land — plus a saved figure per stage.**

## 1. `figures.py`

`figure_dir` and `report_dir` resolve from `__file__` up to the repo root — **no absolute paths, no env vars**. Matplotlib `Agg`, fixed DPI, fixed figure size. One function per figure, each documented with the mandated stage it serves and the linear-algebra principle it visualises. **Every figure must be deterministic** — fixed ordering (alphabetical by team), no randomness, no timestamps in the image. Use a consistent house style: one restrained palette, readable at projector size, labels on every axis, no chart junk. Team names on the y-axis in full — do not abbreviate IPL franchise names, an examiner must be able to read them.

Produce these, named exactly:
1. `01-data.png` — the 1,243-match funnel: total → with winner 1,218 → run-margin 558 → wicket-only 660 → no winner 25. Shows the constraint honestly rather than hiding it.
2. `02-design-matrix.png` — `A` (558×15) as a ±1 heatmap with 15 labelled team columns. Make the sparsity and the row-sums-to-zero structure visible.
3. `03-rref.png` — RREF of `A`: the pivot rows and the **singular (zero) row that exposes the null direction**.
4. `04-structure.png` — the 15 singular values on a log scale, with the null direction annotated, showing one value at numerical zero and `rank = 14`.
5. `05-redundancy.png` — 558 match rows, 14 highlighted as the independent basis, the other 544 greyed as redundant. The visual punchline of stage 5.
6. `06-qr.png` — the `Col(A)` vs `Row(A)` distinction, made visible. These are **different spaces in different ambient dimensions**; label the dimensions (R^558 vs R^15) and make clear which 15 directions of `Q` span `Col(A)` and which are the numerical null direction. Do not draw a picture that implies `Q` is a basis of `Col(A)`.
7. `07-projection.png` — `b`, its projection onto `Col(A)`, and the residual `r`, in the first principal direction; plus the residual norm.
8. `08-least-squares.png` — fitted vs actual signed margin with the y=x line; annotate `R² = −0.2103` and 55.0% winner accuracy.
9. `09-eigen.png` — Colley power-iteration convergence (from `ColleyFit.history`) and the top eigenvalues of `M = W + Wᵀ + C`, showing `λ₁ = 469.18` dominating `λ₂ = 14.81`.
10. `10-diagonalisation.png` — `AᵀA = VΣ²Vᵀ`: the singular-value spectrum and the fact that the eigenvalues of `AᵀA` are the squared singular values.
11. `11-ranking.png` — the two rankings side by side with per-team `x ± se` bars.
12. `12-findings.png` — the significance plot: every team with its `t = x/se` and a ±2σ band, showing **no coefficient crosses it**. Also `corr(games, |x|) = −0.663`.
13. `13-divergence.png` — Massey vs Colley rank, and each vs the official table, so the three-way divergence is one picture.

Each figure function returns the path it wrote, so `demo.py` can print `console.figure(...)`.

## 2. `demo.py` — the narrated walkthrough

One function per mandated stage, called in the guidelines' order (**Simplification is stage 3, Structure is stage 4** — this order was transposed in earlier docs and caught only by review; get it right). Each stage function:

- opens `with console.stage(N, "<mandated name>", "<the principle in one line>") as s:`
- `console.formula(...)` with the actual maths of that stage
- `console.step(...)` lines for what is being computed, and a `console.Progress(...)` bar for the step that iterates, so the run visibly progresses rather than freezing
- `console.measured(name, value, unit=None, meaning=...)` for **every number** — never print a bare float
- calls the `figures.py` function and prints `console.figure(name, caption)`
- ends with `console.verdict("<plain-English conclusion>")`

Concretely, and these are the substance — get the narration right, not just the code:

- **Stage 1** show the funnel and call `console.excluded(25, 1243, "16 Super Over ties + 9 no result")` **loudly**. `AGENTS.md` §4 requires exclusions be stated, not footnoted. Also state that 660 of 1,243 give wickets, not runs, and that **no run-equivalent conversion was invented** and why.
- **Stage 2** show `A` as a small labelled matrix with `console.mat`, state its shape (558, 15), and show that every row sums to zero — and what that means.
- **Stage 3** run RREF with a live progress bar over the elimination steps, then print the pivot rows and **the singular row**.
- **Stage 4** report `rank = 14`, `nullity = 1`, and demonstrate `A @ ones = 0` numerically. This is the project's central insight: add the same number to every team and no predicted margin changes, so only *differences* are identifiable.
- **Stage 5** show 14 of 558 rows forming the basis and 544 redundant.
- **Stage 6** do **both** orthogonalisations and say explicitly that they are different spaces — `Col(A) ⊆ R^558` and `Row(A) ⊆ R^15`. This is a documented correction of an earlier claim in this project; state it.
- **Stage 7** show `r = b − Ax̂`, `‖r‖ = 963.42`, and that `r ⟂ Col(A)` (the normal-equation condition — verify it numerically, `resid @ A ≈ 0`).
- **Stage 8** show all three least-squares routes and their max difference (4.8e-14), then `R² = −0.2103` **centred** and `+0.0214` uncentred, each labelled with its denominator, and **say plainly that the inherited write-up quoted only the uncentred one and thereby hid that the model is worse than predicting the mean.** Then 55.0% in-sample, and the held-out result 43.2% with RMSE 46.71 against the mean-baseline 35.35.
- **Stage 9** run power iteration with `console.converge(...)` or a progress bar and a sparkline of `history`; assert positivity out loud; report `λ₁ = 469.18`, `λ₂ = 14.81`, iterations to tolerance.
- **Stage 10** show `AᵀA` symmetric, eigenvalues `≥ −1e-10` (i.e. non-negative to float error), and that they equal the squared singular values.
- **Stage 11** the headline: the three-way comparison table, and **the finding**, stated as: the obvious approach does not work; per-match noise `σ ≈ 37.07` runs against team-strength spread `σ ≈ 7.03` runs (SNR ≈ 0.19); least squares weights every match equally so short-history franchises get extreme coefficients (`corr(games, |x|) = −0.663`); **not one coefficient is distinguishable from zero at 2σ** (`max|t| = 1.20`); frequency balancing was tried and made it **worse** (max|x| 17.43 → 25.64) because it up-weights the few matches a short-lived franchise played — report the refuted hypothesis, do not hide it; and win/loss reproduces the official table at Spearman **+0.939** while margin manages **+0.093**.

Also print a `console.timeline(...)` at the end: stage → figure → key number.

Entry point `main(argv=None) -> int` supporting `--offline` (accepted and asserted: the demo must run with no network — it reads only `data/matches.csv`), `--figures-only`, and `--width N` (forwarded to `console.set_width`). **Exit code 0 on success, non-zero on failure.** Add `__main__.py` so `python -m iplranking` works.

## 3. `report.py` — self-contained HTML

`build_report() -> Path` writing `report/report.html`. **Self-contained: every PNG base64-inlined, no external CSS, no JS, no network, no CDN.** Build the HTML by string formatting only — **no template engine, no new dependency** (`AGENTS.md` §8). Escape all interpolated text. One `<section>` per mandated stage in order, each with: the mandated name, the principle, the formula in `<pre>`, the measured numbers, the figure, and the verdict. Plus a findings section carrying the three claims, and an honest "what was excluded" block stating 25 of 1,243 and 660 of 1,243.

Include a short provenance block reading `data/provenance.json` — source URL, what the SHA-256 actually covers, row count, and the licence position **as `AGENTS.md` §7 requires it: precise attribution, no licence term asserted that was not read from the primary source.**

Make it print-friendly (`@media print`) and readable on a projector: large type, high contrast, dark-on-light.

## 4. Tests — `tests/test_demo.py`

Do not weaken the existing 187 tests to accommodate yourself.
- `main()` returns 0.
- All **13** figures are written and each is a non-empty valid PNG (check the magic bytes).
- `report.html` is written, is valid-ish (balanced tags, no `<script src=`, no `http://` or `https://` resource reference), and contains every stage heading and the phrase-level evidence for the three findings.
- **Determinism:** run the demo twice into two temporary output directories and assert every produced file is **byte-identical**. This is a hard acceptance criterion.
- The demo's terminal output contains the mandated stage numbers 1..11 **in ascending order** — that is what protects against the transposition error that lived in this project's docs for two runs. Implement it by asserting the order of first appearance of each stage banner in captured stdout.
- The output states the 25-of-1,243 exclusion.
- The output contains **both** R² values, so a future edit cannot silently drop one.

## 5. Verify before reporting — paste verbatim
```
cd C:\Anubhav\MFAD-Mini\ipl-power-ranking
python -m pytest -q
python -m iplranking --offline
python -m iplranking --offline > run1.txt 2>&1
python -m iplranking --offline > run2.txt 2>&1
(Get-FileHash run1.txt).Hash; (Get-FileHash run2.txt).Hash
```
The two hashes must match. Then delete `run1.txt`/`run2.txt` (they are scratch) — but **report the hashes first**.

## 6. Report back
1. Verbatim pytest final line; count of tests.
2. Verbatim output of `python -m iplranking --offline` (full, it is the deliverable).
3. The two determinism hashes, and whether every figure PNG was byte-identical across the two runs.
4. Any measured number that disagreed with what the spec states, with both values.
5. Confirmation you touched only the four allowed files plus the created `test_demo.py`, and that you wrote only into `figures/` and `report/` outside those.