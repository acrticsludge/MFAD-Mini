# IPL Power Ranking

A 10-mark mini-project for **UE25MA242A — Mathematical Foundations for AI &
Data Science**, PES University. It is Gilbert Strang's linear-algebra problem
**#5** (_linear equations + college football team ranking_) with Strang's
mathematics kept intact and the dataset replaced: **19 seasons of the Indian
Premier League**, 1,243 committed matches.

The course mandates eleven stages, and the demo walks all eleven in the
guidelines' own order — Matrix Simplification (3) before Structure of the Space
(4) — with a formula, its own work in progress, a figure and a verdict for each.

## 1. Prerequisites

- Python **3.11+** (measured on Python 3.14.7)
- Four packages: `numpy`, `pandas`, `matplotlib`, `pytest`
- No SciPy, no install step, no network, no environment variables

```bash
pip install numpy pandas matplotlib pytest
```

`pyproject.toml` deliberately declares no build backend, and the demo never
opens a socket — nothing is installed, everything runs from a clean clone.

## 2. Run the demo

From the repository root:

```bash
python ipl-power-ranking/scripts/run_demo.py --offline
```

Or from the project directory:

```bash
cd ipl-power-ranking
python scripts/run_demo.py --offline
```

The launcher works from **any** directory — it resolves `src/` from its own
file location, puts it on `sys.path`, and hands over to the CLI. Its output is
byte-identical to the module form's (`python -m iplranking`), and its exit code
is the demo's own.

### Useful flags

```bash
python ipl-power-ranking/scripts/run_demo.py                 # full default run
python ipl-power-ranking/scripts/run_demo.py --width 88
python ipl-power-ranking/scripts/run_demo.py --no-report     # terminal walkthrough only
python ipl-power-ranking/scripts/run_demo.py --help
```

All arguments are forwarded to the CLI unchanged. Exit codes: `0` success,
`1` offline violation, `2` a stage/figure/report failure, `3` a bad command line.

`--offline` is an **assertion, not a permission**: the flag replaces
`builtins.__import__` and `socket.socket` for the whole run (installed before
`run_demo`, restored in a `finally` afterwards), so a fetch anywhere inside the
walkthrough stops the run with exit code 1. `tests/test_demo.py` wraps
`run_demo` reaching for `urllib.request` and asserts that exit code.

### Why the launcher and not `python -m iplranking`

The package lives at `ipl-power-ranking/src/iplranking` and nothing is
installed, so `python -m iplranking` fails with `No module named iplranking`.
pytest finds the package through `pythonpath = ["src"]`; `python -m` does not
read `pyproject.toml`. Use `scripts/run_demo.py` instead.

## 3. Run the tests

```bash
cd ipl-power-ranking
python -m pytest -q
```

235 tests. Five files pin the mathematics (counts, shapes, rank, both R²
denominators, the intercept correction, the Spearman values) and one pins the
deliverable. The launcher tests run it as a subprocess with an environment
containing no `PYTHONPATH`, from two different working directories, and assert
the eleven stage banners come out in ascending order — plus a negative control
proving that environment cannot import the package by itself, so the launcher
is what is doing the work.

## 4. Rebuild the data snapshot (optional, provenance check)

The demo reads only the committed `data/matches.csv`. To verify its provenance,
re-derive it from the committed raw archive:

```bash
python ipl-power-ranking/scripts/build_snapshot.py
```

and check the reported manifest hash against `data/provenance.json`. This works
offline from the committed `ipl_json/` extraction — no download.

## 5. Outputs

Written beside the repository root, resolved from the package's own location
rather than from the working directory:

- `figures/01-data.png` … `figures/13-divergence.png` — 13 PNGs, one per stage
  (stage 11 has three).
- `report/report.html` — a **self-contained** report, ~2.4 MB, with all 13
  figures inlined as base64. No CDN, no external stylesheet, no font fetch, no
  script. Opens from a USB stick with the network off.

Every run is deterministic: no timestamp, no duration, no hostname, no random
draw, no environment-derived path. Two runs produce byte-identical output and
byte-identical artefacts, and the test suite asserts it.

## 6. The finding

Only **558** of the 1,243 matches carry a run margin; the other 660 decided
matches carry a _wicket_ margin, which is a different quantity on a different
scale. Converting one to the other would need a runs-per-wicket constant that
no source supplies, so **two models are run on two honest datasets** and their
divergence _is_ the result:

| Model  | Dataset                   | Method                                     |
| ------ | ------------------------- | ------------------------------------------ |
| Massey | 558 run-margin matches    | least squares, `A x ≈ b`                   |
| Colley | all 1,218 decided matches | dominant eigenvector of a symmetric matrix |

Measured, not assumed, at run time:

- The margin model **does not work, and the headline negative R² is not the
  reason people first assume.** Centred **R² = −0.2103**, but that number is
  _structural_: every row of `A` sums to zero, so `A x` has mean zero while
  `mean(b) = +18.04` runs. The fit sits **17.30 runs low on every match** by
  construction, because the design matrix has no intercept and `A @ 1 = 0`
  forbids one. Adding the constant column lifts centred R² to **+0.0181** — a
  real improvement, and still no signal. **Stage 4's gauge freedom and stage 8's
  statistic are one argument.**
- Winner accuracy is **55.02%** against a **majority-class baseline of 77.96%**
  (the first-listed team won 435 of the 558 run-margin matches), so the model has
  **negative skill**. A coin flip at 50% is not the relevant comparison.
- The reason is measured on **one scale**: `||r|| / sqrt(m) = 40.79` runs of
  unexplained margin against `std(A x) = 5.98` runs of fitted signal — a ratio of
  **6.82×**. (An earlier draft compared `std(b)` against `std(x)`, a data spread
  against a coefficient spread, and called the ratio a signal-to-noise figure;
  both quantities are real, that ratio was not defined.)
- The held-out figure is **43.2%**, reported **with its defect attached**: the
  first-listed team won 100% of run-margin matches in _every_ season from 2018
  onward, so the test target never varies and six of the sixteen training seasons
  are degenerate too. It is not a clean out-of-sample estimate.
- The two orderings are **uncorrelated** (Spearman **exactly 0**): same 15
  franchises, completely unrelated rankings.
- Win/loss — the signal the official points table actually uses — reproduces the
  official table at Spearman **+0.939**, where the margin model manages **+0.093**.
- An inherited hypothesis was **refuted and reported**, not dropped:
  frequency-balancing the matches was predicted to tame the short-history
  franchises; measured, it made the extremity worse (`max|x|` 17.43 → 25.64).

25 of 1,243 matches have no winner (16 Super Over ties, 9 abandonments) and are
excluded from both models. The count is printed in the demo, not footnoted.

**None of this is published.** It is a coursework result computed from a
committed snapshot, and it has not been reviewed by anyone.

## 7. Project structure

```
.
├── AGENTS.md                    binding project rules (read before coding)
├── CLAUDE.md                    the process
├── docs/reasonix/               specs, plans, run reports, INDEX.md
├── data/                        matches.csv + provenance.json
├── ipl_json/                    committed raw extraction of the Cricsheet archive
├── figures/                     generated PNGs (regenerated each run)
├── report/                      generated report.html (regenerated each run)
└── ipl-power-ranking/
    ├── pyproject.toml           fixed stack, pytest config, no build backend
    ├── scripts/
    │   ├── run_demo.py          the launcher (no install needed)
    │   └── build_snapshot.py    re-derive data/matches.csv offline
    ├── src/iplranking/          the package
    └── tests/                   235 tests
```

## 8. Data, provenance and licence

The snapshot is `data/matches.csv`, built once by
`ipl-power-ranking/scripts/build_snapshot.py` from **`ipl_json.zip` downloaded
from `https://cricsheet.org/downloads/ipl_json.zip`** (Cricsheet JSON format
version 1.2.0), retrieval date recorded in `data/provenance.json` together with
the SHA-256 of a deterministic manifest of the extracted file set. The demo
reads only that CSV, never the network and never the raw archive. The raw
extraction is committed at `ipl_json/`, so the CSV can be re-derived from a
clean clone.

**No licence term is asserted.** No licence statement for Cricsheet _match data_
was found on cricsheet.org — the site's licence path returns 404, and the only
explicit ODC-BY statement there covers the separate Register dataset. Four
third-party sites assert ODC-BY 1.0 for match data, which is corroboration but
not proof, because none of them is the primary source. Attribution is therefore
by file name, source URL and retrieval date only. This is stated rather than
smoothed over because the alternative is asserting a licence nobody read.

## 9. The open blocker

**This reframing may not be permitted, and nobody has answered.**

The course assigns 14 fixed problems from Strang's projects book. Uniqueness
cannot come from the mathematics, because every student draws from the same 14 —
so this project's advantage is the dataset. That advantage is only legitimate if
substituting the dataset is allowed.

Nobody has confirmed that. The question has been open across four runs of this
project. It is load-bearing, not theoretical: if the answer is "the book's task
list is mandatory", then Strang #5 is _college football_, this reframe is
illegitimate, and the pick reopens.

The code exists so the question can be **asked with evidence in hand** — a
worked demo, a measured result and 235 passing tests make the argument in about
three minutes, which is worth more than a paragraph of speculation. It is not a
claim that the answer is yes.

## 10. What you must do by hand

The code will not do these for you, and item 1 gates the rest. The generated
`report/report.html` ends with the same list, and the demo prints it as item 1 of
its own hand-off.

1. **Ask the instructor the blocker question above and record the answer** — who,
   when, in what form. A written reply is preferred; a verbal answer must be
   confirmed in writing. `AGENTS.md` §2 makes the _recording_ the gate, not the
   medium.
2. State the licence position as read, not as assumed — see the provenance
   section above. No term is asserted that was not read from the primary source.
3. Confirm the snapshot provenance by rebuilding it with
   `python ipl-power-ranking/scripts/build_snapshot.py` and checking the reported
   manifest hash against `data/provenance.json`.
4. Rehearse the two viva answers this build was corrected to give honestly: why a
   margin model cannot fit the dataset's mean margin (stage 4's `A @ 1 = 0`), and
   what the majority-class baseline of 77.96% does to a 55.02% accuracy claim.
5. Decide whether the demo presents the **all-time** official table or a
   per-season one, and say which out loud — the ambiguity is a known viva risk.
6. Record the released answer, or the reopen decision, in `docs/reasonix/` and add
   the run row to `docs/reasonix/INDEX.md`.

## 11. Further reading

`docs/reasonix/` holds the specification, the plans and the run reports, and
`docs/reasonix/INDEX.md` is the entry point — it carries the open blocker and the
measured facts that cost this project real work twice. **`docs/runbook/`**
documents how each step runs end to end — setup, snapshot build, demo, stages,
tests, outputs, offline guard, module map. `AGENTS.md` at the
repository root states the rules this code is bound by; `CLAUDE.md` describes the
process.
