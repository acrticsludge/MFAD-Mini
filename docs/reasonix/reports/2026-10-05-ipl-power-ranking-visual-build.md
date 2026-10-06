# Report — visual end-to-end build of the IPL power ranking

- **Slug:** `2026-10-04-ipl-power-ranking-visual-build`
- **Spec:** `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md`
- **Plan:** `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md`
- **Status:** **built, verified, corrected by adversarial review. Code gate green at 235 tests.**
- **Blocker:** still open, and shipped as manual checklist item 1.

## 1. What was delivered

Everything runs from a clean clone, offline, with nothing installed:

```text
python ipl-power-ranking/scripts/run_demo.py --offline
```

That single command walks **all 11 mandated stages in the guidelines' order**,
printing for each: the mandated name, the mathematical principle, the formula,
the work in progress (progress bars, live convergence sparklines), every measured
number labelled, the saved figure, and a plain-English verdict. It writes
**13 PNGs** into `figures/` and a **self-contained 2.4 MB `report/report.html`**
(13 figures base64-inlined, no external CSS/JS/CDN, no template engine).

| Component | Path |
|---|---|
| Data layer, canonicalisation, design matrices | `ipl-power-ranking/src/iplranking/{canon,parse,data}.py` |
| Hand-written RREF, Gram–Schmidt, power iteration | `ipl-power-ranking/src/iplranking/linalg_kit.py` |
| Three least-squares routes, Colley, balancing, ridge, SVD | `ipl-power-ranking/src/iplranking/models.py` |
| R² (two denominators), standard errors, Spearman, baselines | `ipl-power-ranking/src/iplranking/diagnostics.py` |
| ANSI console renderer | `ipl-power-ranking/src/iplranking/console.py` |
| 13 figures | `ipl-power-ranking/src/iplranking/figures.py` |
| 11-stage narrated walkthrough | `ipl-power-ranking/src/iplranking/demo.py` |
| Self-contained HTML report | `ipl-power-ranking/src/iplranking/report.py` |
| Zero-install launcher | `ipl-power-ranking/scripts/run_demo.py` |
| Snapshot builder (not on the demo path) | `ipl-power-ranking/scripts/build_snapshot.py` |
| Tests | `ipl-power-ranking/tests/` — **235 passing** |

## 2. Measured dataset facts — re-verified, not inherited

| Fact | Value |
|---|---|
| Matches | 1,243 |
| Raw team strings → canonical franchises | 19 → **15** |
| With a winner | 1,218 |
| No winner | **25** = 16 Super Over ties + 9 no result |
| Run margin present | **558** |
| Wicket-only, no run figure | **660** |
| D/L | 23 |
| Seasons | 19 |
| `rank(A)` / `nullity(A)` / `cond` on rank | 14 / 1 / 5.6167 |
| Null direction | **exactly the constant vector** — `A @ 1 = 0` on all 558 rows |

**One inherited figure was wrong and is corrected here:** `info["season"]` is
`int` in 511 files and `str` in 732, with five labels appearing under both types,
so the naive `len(set(...))` returns **24**, not 19. This run's own spec first
asserted the opposite; the implementation node measured it and was right.

## 3. The finding, after correction

The adversarial review found four real interpretation defects. Every one was
independently re-measured before being accepted, and one reviewer number was at
first wrongly "corrected" — see §4.

1. **The margin model does not work.** Centred `R² = +0.0181` once it is *allowed*
   to fit a constant. Not one of the 15 coefficients is distinguishable from zero
   at 2σ (`max|t| = 1.20`).
2. **The negative centred `R²` of −0.2103 is structural, not statistical.** `A`
   has no intercept — and cannot, because `A @ 1 = 0`. `mean(b) = +18.0358` while
   `mean(A x̂) = +0.7344`, so the fit is **17.3015 runs low on every match** by
   construction. Adding the forbidden constant column: `SS_res` 928,185 → 753,088,
   centred `R²` → **+0.0181**. **Stage 4's gauge freedom is the cause of stage 8's
   negative number — they are one argument, not two.**
3. **Accuracy 55.02% has negative skill** against the majority-class baseline of
   **77.96%** (435 of 558). A coin flip at 50% was the wrong comparator.
4. **Win/loss carries what the margin throws away.** The Colley-*style* Perron
   eigenvector reproduces the official table at Spearman **+0.939**; the margin
   fit manages **+0.093**; and the two are uncorrelated (`0.000`).
5. **The refuted hypothesis is reported, not hidden.** Frequency balancing makes
   short-history extremity *worse* (`max|x|` 17.43 → 25.64).
6. **Ridge does not leave `R²` unchanged** — it falls monotonically to **−0.2324**.
   The earlier "theorem" was wrong: only the *unregularised* solution minimises
   `‖Ax − b‖`; ridge is a different objective.

## 4. The correction to the correction — the run's most instructive failure

A reviewer measured the majority-class baseline at 77.96%. This run "corrected"
it to 62.19% using a probe that compared `canonical_team1` against the **raw**
`winner` string — silently scoring all 88 renamed-franchise wins as losses.
Measured four ways:

```text
raw team1 == raw winner      0.7796     ← correct
canon team1 == canon(winner) 0.7796     ← correct
canon team1 == raw winner    0.6219     ← the artifact
raw team1 == canon(winner)   0.6219     ← the artifact
```

**The reviewer was right; the correction was wrong.** The same bad comparison
produced a wrong per-season table (0.68–0.88 for 2018–23); the true shares are
**exactly 1.000 in every season from 2018 onward** — nine consecutive seasons,
including all three held-out test seasons. So the held-out 43.2% is reported
**with its degeneracy attached**, and six of the sixteen training seasons are
degenerate too.

This is the documented lesson *verify the replacement, not just the original*,
violated by the very document that quotes it. `INDEX.md` now records it.

## 5. Hardening findings, and what changed

| Finding | Severity | Resolution |
|---|---|---|
| `--offline` restored its own guard *before* the run, so its "fails loudly" promise was false and the exit-1 path was dead code | should-fix | Guard now installed in `main`, **held for the whole run**, restored in `finally`; a test reaches for `urllib.request` *during* the run and asserts exit 1 |
| `.gitignore` claimed the snapshot was committed; nothing was committed | should-fix | Comment corrected; the baseline commit is this run's SHIP step |
| Missing/corrupt snapshot produced a raw traceback | note | `FileNotFoundError`/`ValueError` now print one line naming the file and the remedy, exit 2 |
| A truncated CSV was accepted silently | note | `load_matches` checks the row count (**1,243**) and names expected vs actual |
| Absolute machine path could reach the committed HTML | note | Figure placeholder and report path are repo-relative |
| `None` season silently became the string `'None'` | note | Already fixed in `parse.py`: `SnapshotFieldError` names the file and the field |

Clean on inspection: no network imports anywhere on the demo path; the provenance
SHA-256 recomputes exactly and honestly states it covers an **extracted-file
manifest**, not the unretained archive; `http_status` is recorded as *not
recorded*; no licence term asserted; the HTML is fully self-contained; two runs
produce byte-identical terminal output, figures and page.

## 6. Verification actually performed

| Gate | Result |
|---|---|
| `python -m pytest -q` | **235 passed** |
| Demo from a clean shell, empty `PYTHONPATH` | exit **0**, 538+ lines of narration |
| Two consecutive runs | terminal output, 13 PNGs and `report.html` **byte-identical** |
| Offline violation during the run | exit **1**, message names the module |
| Stage order in captured stdout | 1→11 ascending, **3 before 4** (the transposition that lived in the docs for two runs) |
| Retracted phrases absent from output | `five times`, `SNR 0.19`, `worse than a coin flip` all asserted **not** present |
| Both `R²` values present | asserted in terminal output and in the report |

## 7. What is NOT done, stated plainly

- **The blocker is unanswered.** No instructor contact is recorded anywhere in
  this repository. It is manual checklist item 1 and appears as a red banner at
  the top of `report/report.html`.
- **The held-out evaluation is not clean**, for the reason in §4. The number is
  reported with the defect rather than dropped.
- **The licence position is unverified from the primary source.** Four third-party
  sites assert ODC-BY 1.0 for the match data; cricsheet.org has no licence page
  for it. Corroboration is not proof, and nothing stronger is claimed.
- **Recency weighting and the residual-SVD stretch variant remain out of scope**
  by explicit decision (`AGENTS.md` §10).
- **The report is a static artefact, not part of the computation path** — delete
  it and the demo still runs. The carve-out is recorded in `AGENTS.md` §8.
