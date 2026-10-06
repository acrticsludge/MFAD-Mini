# Plan — F1: IPL power ranking by least squares (Strang #5)

- **Slug:** 2026-10-02-ipl-power-ranking-f1
- **Stage run:** stage 3 PLAN output. Stages 0–2 complete; stage 4 (implement) not started.
- **Spec:** `docs/reasonix/specs/2026-10-02-ipl-power-ranking-f1.md`
- **Read first:** the spec, then the two corrections in its §3. The inherited shortlist is wrong in two places and will mislead you.

## 0. Ground rules for this plan

- **Sequential, not parallel.** Each step's verification depends on the previous step's output. Do not start step N+1 until step N's check passes.
- **Verify numerically, never assert.** The INDEX lesson from two prior runs: an unmeasured numerical claim cost a full project. `rank`, `nullity`, `n`, and every count in this plan must be **computed in a test**, never written down in advance and trusted.
- **This repo has no code gate.** There is no `package.json`, `pyproject.toml`, test runner, or `src/`. One gets created in step 2. Until then stage 5 VERIFY is genuinely not applicable — do not record a pass.
- **Git exists but has never been committed to.** Branch `main`, **zero commits**, ~1,258 entries staged, and no `.gitignore`. Step 2 must write a `.gitignore` and establish a baseline commit *before* any real work lands, or nothing is recoverable.
- **The raw snapshot is already on disk** at `ipl_json/` — 1,243 Cricsheet JSON files plus the archive's `README.txt`. Step 3 therefore does not need to download it; it needs to parse it and record provenance. Confirm the file count before parsing.

---

## Phase A — Unblock and scaffold

### Step 1 — Ask the instructor the one question that gates everything

**Blocks everything after it.** Spec §0.

> Strang problem 5 in the projects book is *"Linear equations + college football team ranking."* May I keep Strang's mathematics and rank **IPL** teams instead, using the mandated 11-stage LA workflow and the 1,243-match Cricsheet dataset? Or must I submit the book's task list on college football data?

Get a yes or a no. **The gate is the recording, not the medium.** Record the answer before any project code is written — who gave it, when, and in what form. A written answer (email or message) is preferred; if it is given verbally, record it verbatim in spec §0 immediately and confirm it in writing before writing code. **An inferred or unrecorded answer does not count, and a verbal answer alone is never sufficient.** If the answer is "must submit the book", stop: F1's uniqueness argument is gone and the pick reopens.

- **File touched:** none, apart from recording the answer itself (spec §0 and `INDEX.md`). This step is a question.
- **Verify:** the answer is recorded verbatim in spec §0 with who gave it, when, and in what form — and the written confirmation is in hand before any project code is written.

### Step 2 — Scaffold the project and create a real code gate

The repository already exists on branch `main` with **zero commits**, ~1,258 entries staged, and **no `.gitignore`**. Establish a baseline before writing code.

```
# 1. Ignore the things that must never be committed
#    .venv/, __pycache__/, *.pyc, .pytest_cache/, scratch/
#    Write .gitignore FIRST — without it, `git add -A` stages your virtualenv.

# 2. Decide what to do with ipl_json/ BEFORE staging it.
#    1,243 raw JSON files. Committing them is a deliberate choice, not a default.
#    The demo only ever needs the parsed CSV, so the usual answer is:
#      ipl_json/            # ignored — re-fetchable from cricsheet.org
#      data/matches.csv     # committed — this is what the demo reads
#    See "Verify" below: confirm the row count survives the parse.

# 3. Commit the baseline
git add .gitignore docs AGENTS.md CLAUDE.md
git commit -m "docs: MFAD project rules, F1 spec and plan; IPL snapshot ignored"

# 4. Then, only after the baseline exists:
python -m venv .venv && .venv\Scripts\activate
pip install numpy pandas matplotlib pytest
```

`ipl-power-ranking/pyproject.toml` and `ipl-power-ranking/tests/`. The moment `pytest` exists, stage 5 has a gate to run.

- **Files touched:** `.gitignore`, `pyproject.toml`, `README.md`
- **Verify:**
  - `git log --oneline` shows a baseline commit.
  - `git status --porcelain` no longer lists `.venv/` after it is created.
  - `pytest --version` and `python -c "import numpy, pandas, matplotlib"` both succeed.

---

## Phase B — Data *(mandated stage 1: Real-world data)*

### Step 3 — Parse the snapshot and record its provenance

The raw archive is **already on disk** at `ipl_json/` (1,243 match files + `README.txt`, Cricsheet v1.2.0). Do not re-download. Parse it to a tidy CSV and commit **only the CSV**, with provenance in a machine-readable sidecar.

```
data/
  provenance.json     # url, utc_fetch_date, http_status, sha256, row_count
  matches.csv         # the committed snapshot — the demo reads ONLY this
```

Provenance fields are the hardening constraints carried from the prior run: **source URL, UTC fetch date, HTTP status, SHA-256, row count.** The committed CSV is what makes the demo work with the venue's wifi switched off, which is the single most common demo-day failure.

- **Files touched:** `ipl-power-ranking/scripts/fetch_snapshot.py`, `data/provenance.json`, `data/matches.csv`
- **Verify:** `python -c "import json;d=json.load(open('data/provenance.json'));print(d['sha256'],d['row_count'])"` — and confirm the row count equals what the parse step reports in step 4, which is how you catch a silent truncation.

### Step 4 — Parse to tidy CSV, handling every edge case the gather found

This is the 60–90 minute step the shortlist warned about, and it is where the real correctness risk lives.

Required handling, each one measured by a gather node:

| Case | Count | Required action |
|---|---|---|
| Winner + run margin | 558 | Keep. Supplies `b`. |
| Winner + wicket margin | 660 | Keep the match; mark `margin_runs` null. Feeds Model 2 only. |
| `outcome.eliminator` present | 16 | Tied, **no `winner` field**. Exclude, count it. |
| `outcome.result == "no result"` | 9 | Exclude, count it. |
| `outcome.method == "D/L"` | 23 | Keep — has a winner and a margin. |
| `margin_runs` sign | — | **Unsigned.** Construct signed margin from `winner` + `by.runs`. |

Columns: `match_id, date, season, team1, team2, winner, margin_runs, margin_wickets, method, is_super_over, canonical_team1, canonical_team2`.

**Apply the canonicalisation map in spec §D2 — four merges.** Do not merge Deccan→Sunrisers silently; flag it for a sensitivity check.

- **Files touched:** `ipl-power-ranking/src/parse.py`, `data/matches.csv`
- **Verify:** the test in step 5 is the real check. Assert the counts land on **558 / 660 / 16 / 9**.

---

## Phase C — The linear algebra, one mandated stage at a time

Build this as a sequence of scripts that each print one number you can check. A mini-project demo is a walk up these numbers, so each step should be independently demonstrable.

### Step 5 — Test the invariants first, before building anything on top

Write the tests that encode the spec's measured facts. If these fail, the data is wrong and everything downstream is garbage.

- `n == 15` canonical franchises
- run-margin rows == **558**; wicket-margin rows == **660**
- no-winner rows == **25** (16 eliminator + 9 no result)
- **`Rising Pune Supergiant` and `Rising Pune Supergiants` merged** — this is the trap
- `rank(A) == 14`, `nullity(A) == 1`, `len(null_space(A)[0]) == 15`

The rank/nullity test is the important one. The connectivity argument in spec §F1-c *predicts* it; the test **measures** it. Do not skip the test because the argument is convincing.

- **Files touched:** `ipl-power-ranking/tests/test_data_invariants.py`, `ipl-power-ranking/tests/test_canonicalisation.py`, `ipl-power-ranking/tests/test_structure.py`
- **Verify:** `pytest -v` — all pass, and the printed counts match the table in step 4.

### Step 6 — Build `A` and `b`

`A ∈ R^{558×15}`, `A[i,j] = +1` if team `j` won match `i`, `−1` if lost. `b[i]` = signed run margin. Sign convention: margin is positive when the **stronger side** wins.

Also build `W` for Model 2: `W[i,j]` = games team `i` beat team `j`, from all **1,218** winner rows.

- **Files touched:** `ipl-power-ranking/src/iplranking/design_matrix.py`, `ipl-power-ranking/tests/test_design_matrix.py`
- **Verify:** the shape of `A` is exactly `558 × 15`, asserted at the boundary where it is built — not trusted.

### Step 7 — Stages 3, 4, 5: RREF, structure, redundancy

One script. Compute `rank`, `nullity`, the null-space basis, RREF, and a maximal independent subset of match rows.

The demo line: *"1,243 matches, 15 teams — so the matrix has a null space, and it is exactly one-dimensional. Here is the direction: add the same number to every team and not one predicted margin changes. That is not a bug, it is the reason I can only ever rank teams by their **differences**."*

### Step 8 — Stages 6, 7: orthogonalization and projection

Two orthogonalizations, because `Col(A)` and `Row(A)` are different spaces — this is the shortlist's error corrected:

- QR of `A` → `Q`'s 15 orthonormal columns span a 15-dimensional space that **contains** `Col(A)` (fitted margin space); its 15th direction is the numerical null direction, so `Q` is **not** a basis of the 14-dimensional `Col(A)`
- Gram–Schmidt on the rows, or QR of `Aᵀ` → orthonormal basis of `Row(A) ⊆ R¹⁵` (team space)

Then `r = b − A x̂` is the projection residual. Report `‖r‖`.

**Measure, don't assume:** check how `numpy.linalg.qr` actually behaves on this rank-deficient `A`, and determine which leading columns of `Q` span the 14-dimensional `Col(A)`. Spec §3 explicitly defers this to code rather than asserting it.

### Step 9 — Stage 8: least squares, both routes, plus confidence intervals

- Route 1: normal equations `AᵀA x = Aᵀb`, solved by hand via the pivoted factorisation from stage 3.
- Route 2: `numpy.linalg.lstsq(A, b)`.

**Correction, measured 2026-10-02:** this step previously predicted that `AᵀA` would be badly conditioned and that any disagreement between routes would be a finding. **It is not the case.** Measured: `cond(A)` on its rank is 5.62, `cond(AᵀA + 11ᵀ) = 31.55`, and the constrained solve agrees with `lstsq` to 4.8e-14. Show the three routes agreeing, and make the **constrained** form the demonstrated one — it is the only one that is nonsingular, and it makes the null space explicit rather than hiding it.

Then **normalise `x`**: only differences are identifiable, so centre to zero-sum. And compute the estimator covariance `σ²(AᵀA)⁻¹` for per-team standard errors (spec §D5).

### Step 10 — Stage 9: Colley eigenvector (Model 2)

`(W + λC) r = r`, `C` the matrix of games played, `λ` the shrinkage constant. Perron–Frobenius gives a positive dominant eigenvector for a non-negative irreducible matrix — so **assert positivity**, don't assume it.

Normalise `r` to unit length, then compare against Model 1. Expect correlation, not equality — the shortlist's claim that the eigen route "reproduces" the least-squares fit is withdrawn in spec §D1.

**The headline output of the whole project:** the divergence between the two rankings, and which teams move.

### Step 11 — Stage 10: diagonalization

`AᵀA` is symmetric positive semi-definite by construction, so the spectral theorem applies directly — real non-negative eigenvalues, orthogonal diagonalisation, no contrivance needed.

Then the free bonus: `AᵀA = VΣ²Vᵀ` means the eigendecomposition of `AᵀA` **is** the SVD of `A`. One line, and it links stage 10 to Strang #14 without attempting the held stretch variant.

### Step 12 — Stage 11: output against the official table

- Model 1 ranking and Model 2 ranking, side by side
- Official points table (wins + points), for the same season or all-time — **state which, do not leave it ambiguous**
- Divergence plot
- Residual norm, and per-team `x ± se`

**The finding to state plainly.** An earlier draft of this plan said "which teams the official table gets most wrong." **Measured 2026-10-02, that is the wrong framing.** The margin model has `R² = 0.0214` and picks the winner only **55%** of the time, and `Spearman(margin-ls, Colley) = 0.000` — the two models are in completely unrelated orders. The honest finding is:

> The obvious approach — difference in team strength equals run margin — does not work. Here is the measurement (`R² = 0.02`, 55% winner accuracy), here is why (per-match noise σ ≈ 37 runs swamps team strengths spread ≈ 5–8 runs, and least squares weights every match equally so one-season franchises get extreme coefficients), and here is what fixes it (frequency balancing, then shrinkage).

**Predict what frequency balancing will do before you run it** (`reports/2026-10-02-ipl-power-ranking-f1-build-audit.md`, Part 13). Kochi Tuskers and Gujarat Lions should stop dominating. A prediction you were right about is a viva line; a number you only got by running code is not.

---

## Phase D — Demo

### Step 13 — Make the demo bulletproof

- **Offline.** Reads `data/matches.csv` only. No network calls anywhere in the demo path. Test it by disconnecting.
- **Reproducible.** One command, ~10 seconds, deterministic.
- **Honest about exclusions.** "I excluded 25 of 1,243 matches with no winner — 16 ties decided by a Super Over and 9 with no result" — said out loud, before the examiner asks.

### Step 14 — Write the viva script

Half the marks are viva, and the questions are predictable. Prepare answers for:

1. Why least squares and not exact solving? *(558 rows, 15 unknowns — over-determined. The 1,218-row system is Model 2's, not this one.)*
2. Your matrix is singular. Is that a problem? *(Nullity 1 = the constant vector. Only differences are identifiable. This is the insight, not a failure.)*
3. Why only 558 matches? *(Run margin is the only signed numeric margin. The other 660 give wickets, which is a different scale. I refused to invent a conversion.)*
4. Why does the eigen method not match your least-squares answer? *(Different assumption and different data — Massey uses margin on 558 matches, Colley uses wins on 1,218. The divergence is the finding.)*
5. How do you know your ranking is better than the official one? *(On what objective? See below — have an honest answer, and if the answer is "it isn't provably better, it is differently informative", say that.)*
6. Which team's estimate do you trust least? *(The standard errors tell you.)*

Question 5 is the one that catches people out. Have a real answer before the demo, not during it.

---

## Verification summary

| Gate | Command | Blocking? |
|---|---|---|
| Data invariants | `pytest tests/test_data_invariants.py` | Yes — everything downstream is garbage if it fails |
| Canonicalisation | `pytest tests/test_canonicalisation.py` | Yes — `n` depends on it |
| Design matrix | `pytest tests/test_design_matrix.py` | Yes — the shape and the sign convention are load-bearing |
| Structure | `pytest tests/test_structure.py` | Yes |
| Full suite | `pytest -v` | Yes |
| Offline demo | run with network disabled | Yes |
| Reproducibility | run twice, identical output | Yes |

## Not in this plan, deliberately

- The residual-SVD stretch variant (shortlist §8) — held, per the shortlist's own advice.
- Recency weighting (spec §D4) — the answer to "what next", not part of the first pass.
- Any web demo, any database, any git hosting — this repo has none and needs none.