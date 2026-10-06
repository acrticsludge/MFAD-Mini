# Dispatch — stage 7 REVIEW (free-tier, adversarial, fresh context)

You are an adversarial reviewer with **no prior context on this work**. Your job is to try to prove it wrong. You did not write it and you have no stake in it.

**Return exactly one verdict: `ship`, `blocked`, or `changes-requested`.** `ship` only if you found nothing that would cost marks or mislead an examiner. A truthful `blocked` is a good outcome; a confident wrong `ship` is the worst result you can produce. **Do not lower the bar to be agreeable.**

## The project

`C:\Anubhav\MFAD-Mini` — a 10-mark university mini-project (UE25MA242A, PES University). Gilbert Strang problem #5, "linear equations + college football team ranking", reframed onto the Indian Premier League using 1,243 real matches from Cricsheet.

**Read, in this order:**
1. `AGENTS.md` — the binding project rules. Especially §2 (the blocker), §3 (measured dataset facts), §4 (honesty and academic integrity), §5 (the 11 mandated stages), §6 (two binding mathematics corrections), §7 (data rules), §8 (fixed stack), §10 (scope discipline).
2. `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` — this run's spec, including §3 (two corrections to the inherited analysis) and §4 (the finding).
3. `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` — the plan.
4. The code: `ipl-power-ranking/src/iplranking/*.py`, `ipl-power-ranking/tests/*.py`, `ipl-power-ranking/scripts/*.py`.
5. `README.md`, `data/provenance.json`.

Run it yourself: `python ipl-power-ranking\scripts\run_demo.py --offline` from the repo root, and `python -m pytest -q` from `ipl-power-ranking/`. Do not take any number in any document on trust.

## The project's central claims — attack these first

1. `n = 15` canonical franchises from 19 raw team strings, via exactly four rename pairs.
2. 1,243 matches; 1,218 with a winner; 558 with a run margin; 660 wicket-only; 25 with no winner (16 Super Over ties + 9 no result); 19 seasons.
3. `rank(A) = 14`, `nullity(A) = 1`, and the null direction is **exactly** the constant vector.
4. `R² = −0.2103` (centred) and `+0.0214` (uncentred). The spec claims the inherited write-up quoted only the uncentred one and thereby hid that the model is worse than predicting the mean.
5. `σ(b) = 37.07` runs of noise against `σ(x) = 7.03` runs of team-strength spread; SNR ≈ 0.19.
6. In-sample winner accuracy 55.0%; held-out (train first 16 seasons, test last 3) 43.2%, RMSE 46.71 against a mean-baseline 35.35.
7. Three least-squares routes agree to ~4.8e-14.
8. Colley: all 15 entries strictly positive, `λ₁ = 469.18`, `λ₂ = 14.81`.
9. `Spearman(Massey, Colley) = 0.000`; `Spearman(Massey, official) = +0.093`; `Spearman(Colley, official) = +0.939`.
10. **No coefficient is distinguishable from zero at 2σ** — `max|t| = 1.20`.
11. Frequency balancing makes the short-history extremity **worse** (`max|x|` 17.43 → 25.64), refuting the inherited plan's prediction that it would help.
12. Ridge cannot improve R² on this objective, as a theorem rather than an observation.

## Specifically try to break

**Honesty — the highest-value target.** `AGENTS.md` §4 forbids asserting any numerical property that was not measured. For **every** number above: is it computed by code, or asserted in prose? Recompute at least six of them yourself, independently, from `data/matches.csv` or `ipl_json/`. Report any that do not reproduce, with both values.

**Is the finding circular?** `AGENTS.md` §4 forbids building a forensic question whose answer is already published. Massey (1997) and Colley (2002) are published methods. Is the *specific* result here already in print, and would an examiner call the exercise circular?

**Is the diagnosis actually right?** The claim is that per-match noise swamps team-strength signal. That is a plausible story. Test it: if the claim is true, the fitted coefficients should be near-zero and insignificant — check. Is there an alternative explanation the project has not excluded? Consider: schedule imbalance, era effects, home/away, the wicket-margin matches being systematically different, or the possibility that `b` is systematically biased (e.g. the mean margin is +18 runs, which the demo reports — what does a non-zero mean margin do to a model that forces every row to sum to zero?).

**The `AᵀA` / projection claims.** Is the constrained form `AᵀA x + 11ᵀx = Aᵀb` the correct constrained least-squares problem, and is the constraint `Σx = 0` the right one? Is the claim "least squares is the orthogonal projection of `b` onto `Col(A)`" used correctly?

**The `Col(A)` vs `Row(A)` distinction.** `AGENTS.md` §6 records that an earlier document wrongly claimed QR of `A` gives a basis of `Row(A)`. Does the current code and demo state this correctly, or has the error resurfaced in new words? Check `figures.f06_two_spaces` and the stage-6 narration.

**Stage coverage.** `AGENTS.md` §5 fixes 11 mandated stages in order, with **Simplification (3) before Structure (4)**. That pair was transposed in this project's documents for two full runs. Verify the code walks them in the correct order, and that each is doing **real** work rather than being padded to fill a slot (`AGENTS.md` §5: never make a stage FAKE).

**Scope discipline.** `AGENTS.md` §10 holds two items out of scope: the residual-SVD stretch variant and recency weighting. Has either been quietly attempted? Also: was a runs-per-wicket conversion factor invented anywhere (`AGENTS.md` §4 forbids manufacturing one)?

**The blocker.** `AGENTS.md` §2 forbids writing project code before the instructor's answer is recorded. Code exists. Does the repository state this honestly, and is it recorded rather than papered over?

**Reproducibility.** Run the demo twice, compare byte-for-byte. Run pytest. Try to find any nondeterminism.

**Would this survive five minutes of a viva?** Name the three questions you think a sharp examiner would ask where the project's current answer is weakest.

## Rules

- **You may not modify any file.** Read-only review.
- Scratch space, if you need it: `C:\Users\anubh\AppData\Local\Temp\opencode\`.
- **Verify before you correct.** `AGENTS.md` and the index both record that a previous reviewer flagged a stale-but-real figure as fabricated. Be precise about what you actually ran.
- Quote reviewers' evidence, not impressions. For every finding give `file:line` or the exact command and its output.
- Do not report style preferences as blockers.

## Report format

1. **Verdict** — one line: `ship` / `changes-requested` / `blocked`.
2. **Findings**, most severe first. Each: severity, `file:line`, the claim verbatim, why it matters for marks or honesty, the minimal fix. Distinguish **measured** from **inferred**.
3. **What you independently recomputed**, with the commands and the numbers you got, including any that disagreed.
4. **What you could not verify**, and why.
5. **The three weakest viva answers**, and what would strengthen them.