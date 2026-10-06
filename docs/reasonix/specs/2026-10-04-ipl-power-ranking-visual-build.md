# Spec — IPL power ranking: the visual end-to-end build

- **Slug:** `2026-10-04-ipl-power-ranking-visual-build`
- **Continues:** `2026-10-02-ipl-power-ranking-f1` (spec, plan, build-audit, handoff). Read all four first.
- **Course:** UE25MA242A — Mathematical Foundation for AI & Data Science, PES University, CSE. 10 marks: 5 demo + 5 viva.
- **Declared risk:** `medium`. **Adapter:** `generic [fallback]` — unguarded, no `docsRoot`, so documentation is not gate-enforced. Written anyway.
- **Stage reached when written:** stage 2 ARCHITECT. Numbers below are **measured 2026-10-04 by the stage-0/2 probe**, not inherited.

## 0. The blocker — still open, and what this run does about it

> Is the student free to substitute the dataset and re-frame the real problem, as long as the mandated LA workflow and the named Strang problem are honoured — or must the book's exact task list be submitted?

**Status as of 2026-10-04: NOT ANSWERED. No instructor contact is recorded anywhere in this repository.**

What this run records, in the form `AGENTS.md` §2 demands:

| Field | Value |
|---|---|
| Who gave an answer | **Nobody.** No instructor answer exists. |
| When | — |
| In what form | — |
| Who authorised building anyway | The repository owner, in session, 2026-10-04: *"read all files and start building the project. must be the full thing end to end and working"* |
| Scope of that authorisation | Build the full artefact so the instructor question can be asked **against a working demo**, and hand the owner a manual checklist. **It is not an instructor answer and does not close the gate.** |

**This run therefore treats the blocker as OPEN and ships it as item 1 of the manual checklist.** Code exists so the question can be put to the instructor with evidence in hand. If the answer comes back *"must submit the book's task list"*, the IPL reframe is illegal, F1's uniqueness argument is gone, and the pick reopens — the code here would be discarded, not adapted.

## 1. Goal, restated after measurement

Build the whole thing end to end and working, where **every step of the run is visual**: the terminal shows what is being computed, which mathematical principle it uses, and the numbers as they land — and every stage produces a figure.

This is a **scope change** from the inherited spec, which said (§8) "Any web or GUI demo" is out of scope and (§9.4) "Demo output is terminal plots and printed tables." The owner's 2026-10-04 instruction overrides that. Recorded here so the change is visible rather than silent.

**Stack is unchanged and remains fixed** (`AGENTS.md` §8): Python 3 + NumPy + Pandas + Matplotlib + pytest. No web framework, no notebook, no new dependency. "Visual" is achieved with (a) a purpose-built ANSI console renderer in pure Python, (b) Matplotlib PNGs, and (c) one self-contained static HTML page assembled by string formatting from those PNGs. A static HTML file is not a front end and adds no dependency.

## 2. Measured dataset facts — re-verified 2026-10-04

Re-measured directly against `ipl_json/`, because `AGENTS.md` §4 and the INDEX lesson *verify the replacement, not just the original* both apply: an earlier run's inherited figures were wrong twice already.

| Fact | Value | Status |
|---|---|---|
| Match files | 1,243 | confirmed |
| Distinct raw team strings | 19 | confirmed |
| Canonical franchises, `n` | **15** | confirmed |
| Matches with a winner | 1,218 | confirmed |
| No winner | **25** = 16 Super Over ties + 9 `no result` | confirmed |
| Run margin present | **558** | confirmed |
| Wicket-only, no run figure | **660** | confirmed |
| `info.outcome.method == "D/L"` | 23 | confirmed |
| Seasons (type-normalised) | 19 | confirmed |
| `rank(A)` | **14** | confirmed, measured |
| `nullity(A)` | **1** | confirmed, measured |
| `cond(A)` on its rank | 5.62 | confirmed |

**Season typing: re-measured, and this run's first measurement was WRONG.** I measured `info["season"]` as always-`str` and the naive count as 19, and wrote that here. The implementation node then measured it against the raw files and refuted me: **`int` in 511 files, `str` in 732.** Five labels (2012, 2013, 2015, 2016, 2017) appear under both types and `2012 != "2012"`, so the naive `len(set(...))` returns **24** and the normalised count **19**. `AGENTS.md` §3 was right and this spec was wrong; it is corrected here.

**And the mechanism is narrower than the warning implies.** The over-count is a *pure-Python-set artefact only*. Pandas infers a common `str` dtype on read, so the coercion is invisible at the CSV boundary and the committed CSV hash is unchanged with or without it. The coercion is still required and still correct — a test pins it against the raw JSON, and it is the only test that fails when it is removed — but "you will get 24 and your test will fail against correct data" is too strong. Corrected, not withdrawn: the warning stands, the stated consequence is narrower.

## 3. The two corrections this run makes to the inherited analysis

### 3a. `R² = 0.0214` is the wrong denominator — and the honest number is negative for a reason the project first got wrong too

The build-audit, the handoff and spec D1 all headline **`R² = 0.0214`**. Measured 2026-10-04:

```text
‖r‖²       = 928,185.2
‖b‖²       = 948,444.0      →  1 − ‖r‖²/‖b‖²       = +0.0214   ← the inherited figure
‖b − b̄‖²   = 766,931.3      →  1 − ‖r‖²/‖b−b̄‖²     = −0.2103   ← standard coefficient of determination
```

`0.0214` is `1 − SS_res/SS_tot` with an **uncentred** `SS_tot`. The standard coefficient of determination centres the total sum of squares, and it is **negative**.

**CORRECTED 2026-10-05 by adversarial review, verified independently.** "Negative R², therefore the model is worse than the mean, therefore noise is to blame" is **the wrong causal story**, and this spec asserted it until a reviewer showed otherwise:

```text
mean(b)             = +18.0358 runs      the dataset has a large positive mean margin
mean(A x̂)           = +0.7344 runs       the fit is ~17.3 runs LOW on every single match
A has no intercept column — and stage 4 PROVES A @ 1 = 0, so A x cannot represent a constant
add one constant column: intercept = 18.1369, SS_res 928,185 → 753,088
                        R² centred  −0.2103 → +0.0181
```

The negative centred R² is **a specification artifact of the no-intercept design matrix**, which is the *same gauge freedom the project itself proves in stage 4* — the rank deficiency that forbids an absolute level. The project presented a structural consequence of its own stage-4 finding as a data finding about noise.

**This makes the project better, not worse.** The corrected story is one continuous argument across stages 4 and 8: *the null space forbids an absolute level, so the model cannot fit a constant; it therefore looks worse than a constant; add the intercept it was never allowed and it is still only `R² = +0.018`.* Both R² values are reported, each labelled with its denominator, and the intercept variant is reported beside them.

### 3c. The ridge claim was wrong — corrected 2026-10-05

This spec previously asserted that ridge "cannot improve R² here, and this is a theorem". **That statement was wrong and is withdrawn.** Measured:

```text
λ        0     1     10    50    200   1000
R²c   −0.2103 −0.2104 −0.2122 −0.2163 −0.2237 −0.2324
```

Ridge **does** change R², monotonically downward. The correct statement is narrower: the *unregularised* solution `x̂` is the minimiser of `‖Ax − b‖`, so **no other unregularised least-squares fit can beat it** — but ridge is a *constrained* fit (shrinking toward zero), which is a different objective, and on this problem it is strictly worse by the unweighted residual. An earlier probe of mine appeared to show invariance because it passed a malformed right-hand side; the reviewer's table is correct and the code already measures it.

Recorded because the error is instructive: an "obvious theorem" asserted without measurement was wrong in exactly the way `AGENTS.md` §4 warns about.

### 3d. The predicted fix does not work, and this is the finding

Build-audit Part 13 predicted that **frequency-balanced least squares** (weight match `i` by `1/(games(t1) + games(t2))`) would stop Kochi Tuskers and Gujarat Lions dominating. **Measured: it makes the extremity worse.**

```text
                        games    OLS x    balanced x
Kochi Tuskers Kerala        5   +17.43     +25.64     ← worse
Gujarat Lions               5   −13.70     −13.24     ← unchanged
max|x| over the 15 teams            17.43      25.64
```

The reason is measurable and is the point: balancing **up-weights** the handful of matches Kochi played, so its extreme coefficient is amplified rather than tamed. The build-audit prediction is **withdrawn as refuted by measurement.**

**Ridge shrinkage likewise cannot help on this objective**, and this is a theorem rather than an observation: `x̂` is *the* minimiser of `‖Ax − b‖`, so no re-fit by least squares can reduce that residual sum of squares. Measured `R²` is unchanged to 4 decimals for `λ ∈ [1, 1000]`. Reporting "shrinkage improved R²" would have been arithmetically impossible.

**What frequency balancing *does* change** is reported instead: it moves the *direction* of the coefficient vector while leaving the fit just as bad.

## 4. The finding, as measured

Every number below was computed from the snapshot on 2026-10-04.

```text
GAUGE      mean(b) = +18.0358 runs, but mean(A x̂) = +0.7344: the fit is ~17.3 runs low
           on every match, because A has no intercept and A @ 1 = 0 forbids one
           adding the intercept it was never allowed: R² centred −0.2103 → +0.0181

SNR        residual spread  ‖r‖/√m = 40.79 runs of unexplained margin
           fitted spread    std(A x̂) = 5.98 runs of team signal
           → noise exceeds signal by about 6.8×

in-sample  winner accuracy of the fitted ranking            55.0%
           **majority-class baseline (always team1)         78.0%**  ← the model is worse
held-out   train = first 16 seasons, test = last 3          43.2%, RMSE 46.71
           "predict the mean" RMSE                           35.35
           **but the split is degenerate:** team1 won 100% of run-margin matches
           in EVERY season from 2018 onwards — nine consecutive seasons, of which
           2024–26 are the test set — against 0.44–0.67 across 2007/08–2017.
           The archive's team-ordering convention changed, so the test target
           never varies AND six of the sixteen training seasons are degenerate.

significance  per-team standard errors, σ² = ‖r‖²/(m − rank) = ‖r‖²/544
              se ranges 4.68 … 17.63 runs
              max |x/se| over all 15 teams = 1.20 (Rajasthan Royals)
              → NOT ONE coefficient is distinguishable from zero at 2σ

divergence   Spearman(Massey, Colley)        =  0.000   (Pearson −0.122)
             Spearman(Massey, official table) = +0.093
             Spearman(Colley, official table) = +0.939
```

Four claims follow, and they are the deliverable:

1. **The obvious approach does not work.** Difference-in-strength = run margin yields `R² = +0.018` once it is even allowed to fit a constant, **55.0%** winner accuracy against a **78.0%** majority-class baseline, and not one coefficient significant at 2σ.

**A correction to a correction, recorded because it is the third instance of the same failure in this repository.** A reviewer measured the majority-class baseline as 77.96% (435/558). This spec "corrected" that to 62.19% on the strength of a probe that compared `canonical_team1` against the **raw** `winner` string — which silently drops every match won by a renamed franchise. Measured four ways: `raw team1 == raw winner` 0.7796, `canon == canon` 0.7796, `canon vs raw` 0.6219, `raw vs canon` 0.6219. **The raw 77.96% is right and the "correction" was wrong.** The lesson is the one already written in `INDEX.md` — *verify the replacement, not just the original* — and it was violated by the very document that quotes it. The same bad comparison also produced a wrong per-season table (0.68–0.88 for 2018–23); the true shares are **exactly 1.000** from 2018 onward.
2. **The negative R² is structural, not empirical.** The design matrix has no intercept — and cannot, because `A @ 1 = 0`. The model is 17.3 runs low on every match by construction. **The rank deficiency that stage 4 proves is the reason the stage-8 number looks the way it does.** Those two stages are one argument, not two.
3. **Even after that correction, the signal is absent.** Residual spread 40.79 runs against fitted spread 5.98 runs — noise exceeds signal by about 6.8×. The "about five times" and "SNR ≈ 0.19" figures in the inherited write-up compare a *coefficient* spread to a *data* spread and are not well-defined quantities; the corrected ratio is stated above.
4. **Win/loss carries the information the margin throws away.** Colley's eigenvector on the same graph reproduces the official points table at Spearman **+0.939**; the margin fit does not, at **+0.093**.

**The held-out number is reported with its caveat attached, not hidden.** The 43.2% is real but the split is not a clean out-of-sample test, because the first-listed team won every run-margin match in the three test seasons. A margin model evaluated on a target that is constant is being scored on a coin that has already landed.

### Why this is not circular (`AGENTS.md` §4)

Massey (1997) and Colley (2002) are both published *methods*, but no published source reports the coefficient vector of the IPL least-squares margin fit, its standard errors, its held-out accuracy, or the Spearman correlation between the two fits **on IPL data**. Nothing here is recovered from print; the IPL numbers are new measurements. The published quantities are the *methods*, not the *answers*.

## 5. Non-goals, unchanged from `AGENTS.md` §10

- **Held:** the residual-SVD stretch variant. Named, not attempted.
- **Held:** recency weighting (spec D4). It is the answer to "what next", printed in the demo as such.
- **Not attempted:** the wicket→run conversion. Refused on integrity grounds; the 558/660 split is reported instead.
- **Not merged:** Gujarat Lions→Titans, Deccan→Sunrisers. Either merge changes `n` and invalidates every dimension.

## 6. Acceptance criteria

- [ ] `pytest -q` green from a clean shell, offline.
- [ ] Every §2 and §4 number pinned by an assertion in a test — computed, never asserted in prose.
- [ ] `data/matches.csv` + `data/provenance.json` committed; demo reads **only** the CSV and never the network.
- [ ] Provenance honest about *what was hashed*: the downloaded archive was not retained on this machine, so the hash covers the extracted file set, and the record says so.
- [ ] Licence stated as AGENTS.md §7 requires: precise attribution, **no licence term asserted that was not read from the primary source.**
- [ ] All 11 mandated stages, in the guidelines' order, each producing a named figure and a terminal panel naming its principle.
- [ ] Each of the three findings in §4 visible in the terminal output **and** in `report/report.html`.
- [ ] Two consecutive demo runs produce byte-identical figure files and identical terminal output.
- [ ] Every exclusion counted and stated: 25 of 1,243 no-winner, 660 of 1,243 wicket-only.
- [ ] `report/report.html` self-contained: no network fetch, no external CSS/JS.
- [ ] The manual checklist delivered, with the instructor question as item 1.

## 7. Assumptions recorded

1. **The owner authorised building with the blocker open** (§0). Conservative reading, stated, and the blocker ships as manual item 1.
2. **"Visual" means terminal + static HTML + PNG figures**, no new dependency, no server. Chosen because `AGENTS.md` §8 forbids adding a dependency without justifying it against the fixed stack, and this needs no justification: it is the fixed stack.
3. **All-time official table** (2 points per win, all 19 seasons) is the comparison, and the demo says so out loud. Per-season is noted, not used, to avoid ambiguity.
4. **The 15 canonical franchises keep `Deccan Chargers` separate from `Sunrisers Hyderabad`.** Sensitivity is printed, not applied.