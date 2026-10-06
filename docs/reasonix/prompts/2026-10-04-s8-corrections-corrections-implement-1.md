# Dispatch — correction pass: adversarial review + harden findings

An adversarial reviewer and a hardening pass both returned findings. **Every number in this dispatch was independently re-measured by the orchestrator** before being accepted, so treat them as confirmed, not as opinions. One reviewer number was **wrong** and has been corrected here — see F2.

**Read first:** `AGENTS.md`, `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` §3a, §3c, §3d and §4 (**just rewritten — these are now binding**).

**Existing state:** 224 tests green. The demo runs all 11 stages, writes 13 PNGs and a 2.35 MB self-contained report, byte-identical across runs.

## Blast radius — you may modify ONLY these

`ipl-power-ranking/src/iplranking/{diagnostics,models,demo,report,parse,data,__main__}.py`, `ipl-power-ranking/tests/*.py`, `.gitignore`, `README.md`.

Do **not** modify `canon.py`, `console.py`, `figures.py`, `linalg_kit.py`, `scripts/*`, or anything under `docs/`. No `git add`/`commit`/`push` — the orchestrator commits. Environment: Python 3.14.7, numpy/pandas/matplotlib/pytest. No SciPy, no venv, no pip install, no network.

## THE RULE

**NEVER make a test pass by editing, skipping, deleting or weakening an assertion.** All 224 existing tests must stay green and unweakened. If a correction below breaks an existing test, **the test is probably encoding the old, wrong claim — fix the test's expectation and say so in your report**, do not delete the assertion. If a correction turns out to be wrong, stop and report.

---

## F1 — HIGH. The negative R² is a missing-intercept artifact, not a noise finding

`demo.py` claims the model is "worse than predicting the mean" and attributes it to noise. Measured:

```text
mean(b)              = +18.0358 runs
mean(A x_hat)        = +0.7344 runs    the fit is ~17.3 runs LOW on every match
A @ 1 = 0            → A x cannot represent a constant; stage 4 proves this
add one constant column:  intercept = 18.1369,  SS_res 928,185 → 753,088
                        R2 centred  −0.2103 → +0.0181
```

The design matrix has no intercept, and **cannot** have one — that is the gauge freedom stage 4 exposes. The negative R² is a structural consequence of the project's own stage-4 finding, presented as a data finding.

**Fix:**
- `diagnostics`: add `intercept_model(A, b) -> InterceptFit` — append a constant column, solve by `lstsq`, return `intercept`, `x`, `r_squared_centred` (**+0.0181**), `ss_res` (**753,087.7**), `fitted_spread` (`std(A x̂)`, **5.9805**), `mean_b` (**18.0358**), `mean_fitted` (**0.7344**), `bias` (**17.3014**).
- `demo` stage 8: report the intercept model **beside** the no-intercept one. Narration must say plainly that the negative centred R² is caused by the missing intercept, that stage 4 is the proof, and that after the correction the model reaches only `R² = +0.018`.
- `report.py`: same content in the stage-8 section and the findings section.

## F2 — HIGH. Winner accuracy is benchmarked against a coin flip that is not the relevant baseline

The reviewer claimed the majority class is 77.96%. **That is wrong. Measured: 347 of 558 = 62.19%.** The direction of the finding stands — the model's **55.02%** is **worse than always predicting the first-listed team**.

- `diagnostics`: add `majority_class_accuracy(pred, b, team1_won) -> float` and `team1_win_share(matches) -> float` (**0.6219**).
- `demo`: replace "a coin flip is 50%" as the headline comparator with the **majority-class baseline 62.2%**, and keep the coin flip as the weaker secondary reference. State that the model has **negative skill** against the majority class.
- Every place that says "worse than a coin flip" must be corrected. Grep for it.

## F3 — MEDIUM. The held-out split is degenerate and the project does not say so

Measured share of run-margin matches won by the first-listed team:

```text
2007/08 0.292 ... 2017 0.346     2018 0.679  2019 0.727  2020/21 0.815
2021 0.773  2022 0.865  2023 0.875     2024 1.000  2025 1.000  2026 1.000
```

The last three seasons are **100% team1**. The 43.2% held-out figure is being scored against a target that never varies, so it is not a clean out-of-sample estimate.

- `diagnostics`: add `team1_share_by_season(matches) -> pd.Series` (the table above).
- `demo`: report the held-out number **with this caveat attached**, print the per-season share, and state that the ordering convention drifts monotonically from ~0.3 to 1.0 across the archive. Do not quietly drop the 43.2% — report it *and* qualify it. Add it to the "what was not excluded" line.

## F4 — MEDIUM. The signal-to-noise ratio compares two unrelated quantities

`σ(b) = 37.07` is the total spread of the right-hand side — it contains the +18 mean and the team signal. `σ(x) = 7.03` is the spread of the *coefficients*. Their ratio "≈ 0.19", and the phrase "noise about five times the signal", are not well-defined.

Correct measured quantities:

```text
residual spread   ||r|| / sqrt(m) = 40.79 runs of unexplained margin
fitted spread     std(A x_hat)   =  5.98 runs of team signal
ratio             noise / signal ≈ 6.8x
```

- Replace the SNR narration and the "five times" claim everywhere, in `demo.py`, `report.py`, `README.md`. Grep for `37.07`, `7.03`, `five times`, `SNR`, `0.19`.
- Keep `σ(b) = 37.07` reported as *the spread of the signed margins*, which is true and useful — just not as "the noise".

## F5 — LOW. Ridge: the code is right, the narration is wrong

Code already measures R² falling with λ. Grep `demo.py`/`report.py`/`README.md` for any claim that ridge leaves R² unchanged or "cannot" change it, and remove it. The correct statement is narrow: **the unregularised solution minimises `‖Ax − b‖`, so no other unregularised least-squares fit can beat it; ridge is a constrained fit and on this problem it is strictly worse by the unweighted residual.** Measured table to print: `λ = 0, 1, 10, 50, 200, 1000 → R² = −0.2103, −0.2104, −0.2122, −0.2163, −0.2237, −0.2324`.

## F6 — LOW. No manual checklist exists, and the blocker is absent from the report

- `report.py`: add a **"What you must do by hand"** section listing the manual items, with the **instructor question as item 1**, quoting it verbatim: *"Strang problem 5 is 'Linear equations + college football team ranking.' May I keep Strang's mathematics and rank IPL teams instead, using the mandated 11-stage LA workflow and the 1,243-match Cricsheet dataset? Or must I submit the book's task list on college football data?"* State that it is **unanswered**, that no instructor contact is recorded anywhere in the repository, and that the code exists so the question can be asked with evidence in hand.
- Add an explicit **blocker banner** near the top of the report.
- `README.md`: same checklist.

## F7 — LOW. The eigen method is Colley-*style*, not Colley's published system

`AGENTS.md` §6 itself writes "Colley (2002, eigenvector on win rates)", so the shorthand came from the project's own binding file. Still: `demo.py`, `report.py` and `README.md` must label the model as a **Colley-style Perron eigenvector / rating-mass eigenvector**, not as "Colley's method", and must say that Colley's 2002 paper solves a different (linear) system, so the attribution is loose. Fix `AGENTS.md` §6 too — **no, you may not edit `AGENTS.md`; the orchestrator does. Flag it in your report.**

## H1 — `should-fix`. `--offline` enforcement is cosmetic and the code overclaims

`demo.py:245-252` installs the import/socket block and **removes it inside the same function**, before `run_demo` is called from `__main__.py:160`. Measured: `import urllib.request` and `socket.socket()` both **succeed** after `assert_offline()` returns. So the flag cannot "fail loudly", and `_OFFLINE_EXIT = 1` is dead code. Three docstrings and `README.md` promise otherwise.

**Fix (option (a), the strong one):** hold the block for the whole run — install it in `__main__.main` **before** `run_demo`, restore in a `finally` **after**. Return `1` on a blocked import. Add a test that monkeypatches `run_demo` to attempt `import urllib.request` **during** the run and asserts exit code 1. Then the promise is true.

## H2 — `should-fix`. `.gitignore` claims the snapshot is committed; it is not

`.gitignore:31-32` says "data/matches.csv and data/provenance.json are committed". Measured: `git ls-files -- data` is empty and the repo has **zero commits**. The orchestrator commits at stage 9 — **you just fix the comment so it is not an overclaim until then**, e.g. state they are inputs that must be committed, and note the demo fails without them.

## H3 — `note`. Missing/corrupt snapshot shows a raw traceback

`__main__.py:161-163` catches `Exception` and calls `traceback.print_exc()`. Catch `FileNotFoundError` and the `ValueError` from `load_matches` and print **one line** naming the file and the remedy (`scripts/build_snapshot.py`), returning 2. Keep the traceback only for genuinely unexpected errors.

## H4 — `note`. Parser robustness at build time

`parse.py`: `_normalise_season(None)` returns the string `'None'`, silently inventing a season. `_nullable_int('abc')` raises a bare `ValueError` with no file or field name. Missing `teams`/`dates` raise a bare `KeyError`. Raise a named error carrying `path.name` and the offending field for a missing or ill-typed `season`, `teams`, `dates`, or non-numeric margin. **The 19-season invariant test must still pass.**

## H5 — `note`. An absolute machine path can reach the committed report

`report.py:204` writes `fig.figure_dir()` (absolute) into the missing-figure placeholder that lands in `report.html`. Use a repo-relative label like `figures/<name>`. Apply the same relative treatment to the report path printed at `demo.py:326` and `report.py:629-630`.

## H6 — `note`. `load_matches` never checks the row count

`data.py:_cached_matches` validates columns but not length. A truncated CSV is accepted silently. Add a row-count check (**1,243**) with an error naming the expected and actual counts and pointing at `scripts/build_snapshot.py`.

---

## Tests to add (in the existing files; do not delete anything)

- F1: `r_squared_centred` of the intercept model is **+0.0181**; `intercept == 18.1369`; `ss_res == 753,087.7`; `mean_b == 18.0358`; `bias == 17.3014`.
- F2: `majority_class_accuracy == 0.5502` is **less than** `team1_win_share == 0.6219` — assert the *direction* (negative skill), with a comment saying this is a result.
- F3: `team1_share_by_season` for 2024/2025/2026 is exactly `1.0`, and for 2007/08 is `0.292`.
- F4: `residual_spread == 40.79`, `fitted_spread == 5.98`, ratio ≈ `6.8`.
- F5: ridge R² at λ=1000 is ≈ **−0.2324**, i.e. **not** invariant — assert the fall.
- F6: `report.html` contains the instructor question verbatim and the phrase identifying item 1.
- F1 in the report: `report.html` contains **both** `−0.2103` and `+0.0181`.
- H1: a test that a network import attempted **during** the run yields exit code 1.
- H6: a wrong-length CSV raises, naming expected and actual.
- A guard test that the demo output no longer contains the retracted strings: `five times`, `SNR`, `worse than a coin flip`, and any "ridge leaves R² unchanged" phrasing. This is the regression test for F4/F5 and it must actually fail on the current text — check that before you pass it.

## Verify before reporting — paste verbatim

```
cd C:\Anubhav\MFAD-Mini\ipl-power-ranking
python -m pytest -q
python scripts\run_demo.py --offline
```

## Report back
1. Verbatim pytest final line and total count.
2. Verbatim output of the corrected stage 8 and stage 11 sections of the demo.
3. Which of the 224 pre-existing assertions you changed, if any, and **why each was encoding a retracted claim**.
4. The `AGENTS.md` §6 Colley-attribution wording you recommend (do not apply it).
5. Anything you believe in this dispatch is **wrong**, with both values. The reviewer was wrong once already.
6. Confirmation you touched only the allowed files.