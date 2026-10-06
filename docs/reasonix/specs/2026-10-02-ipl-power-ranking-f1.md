# Spec — F1: IPL power ranking by least squares (Strang #5)

- **Slug:** 2026-10-02-ipl-power-ranking-f1
- **Continues:** `2026-10-02-cie-spark-mini-project-idea-selection` and `2026-10-02-pesu-college-oriented-idea-shortlist`. Read both specs and the F1 shortlist section before starting.
- **Course:** UE25MA242A — Mathematical Foundation for AI & Data Science, PES University, CSE.
- **Declared risk:** low (documentation only). Plugin floor raised to `medium` on file observation.
- **Adapter:** generic [fallback] — unguarded, no `docsRoot`, so documentation is not gate-enforced. Written anyway; the next session needs it.
- **Decision:** the student has **picked F1**. The shortlist question is closed.

## 0. The blocker — resolve before writing any code

Carried open through **two** prior runs and still not answered:

> Is the student free to substitute the dataset and re-frame the real problem, as long as the mandated LA workflow and the named Strang problem are honoured — or must the book's exact task list be submitted?

Strang #5 in the projects book is *"Linear equations + **college football** team ranking."* F1 keeps Strang's mathematics and replaces the dataset with the IPL.

- **If substitution is permitted** — F1 stands as designed below. Its entire uniqueness argument survives: a classmate doing #5 on American college football is not a realistic threat.
- **If the book's task list is mandatory** — **the IPL framing is illegal and F1 loses the reason it won.** It collapses back to college football, and the one thing that made F1 better than F2/F3 (a dataset nobody else would touch) disappears. The pick must be reopened.

**This is a five-minute question to the course instructor and it gates everything after it.** The prior runs assumed the permissive reading and wrote every candidate to satisfy the strict one, but an assumption is not an answer. Step 1 of the plan is this question, not `pip install`.

**The gate is the recording, not the medium.** Record the answer here before any project code is written — who gave it, when, and in what form. A written answer (email or message) is preferred. If the answer is given verbally, record it in this section immediately and confirm it in writing before writing code. An inferred or unrecorded answer does not count, and the verbal answer alone is never sufficient.

## 1. Goal

Build a ranking of IPL teams that uses **score margin and the fixture graph**, then show it disagrees with the official points table — and show exactly where and why.

The official table ranks on wins and points only. That discards margin of victory and the directed structure of who beat whom. Two teams with identical W–L records can be different strengths.

## 2. Measured dataset facts

Gathered 2026-10-02 from `https://cricsheet.org/downloads/ipl_json.zip` (5,180,977 bytes). The gather node extracted to OS temp only; the same snapshot independently exists in this repo at `ipl_json/` (1,243 files + the archive's `README.txt`), which states "This archive contains 1243 Indian Premier League matches." **No provenance record exists yet** — see §7.

| Fact | Value | Note |
|---|---|---|
| Matches | **1,243** | Prior run's figure **confirmed correct** |
| Distinct team-name strings | **19** | |
| Distinct franchises after canonicalisation | **15** (14 if Deccan→SRH) | This is **n** |
| Matches with a winner | 1,218 | |
| No winner — tied | 16 | All 16 decided by Super Over |
| No winner — no result | 9 | Schema has no `abandoned` value |
| **Run margin present** | **558** | **Only these can supply a run-differential `b`** |
| Wicket margin present | 660 | No run figure in the schema at all |
| Margin sign | **unsigned** | `winner` is a separate field; signed margin must be constructed |
| `outcome.method == "D/L"` | 23 | Rain-affected, still have a winner and a margin |
| Win/loss graph connectivity | **1 component** for the full graph and every **modelling** subset | Measured by BFS; see F1-c for what "modelling" excludes |

Per-season squad sizes: 8 teams in most seasons, 10 in 2022–2026, 9–10 in 2011–2013.

**Schema gotcha on `season`:** `info["season"]` is **inconsistently typed** — sometimes an `int` (`2012`), sometimes a `str` (`"2007/08"`, `"2012"`). A naive `len(set(info["season"]))` returns **24**, not 19. Normalise before counting, or the invariant test for the season count fails against correct data. The same applies to the winner: it lives at `info.outcome.winner`, and `info["winner"]` raises `KeyError` in every file rather than returning `None`.

### The three facts that shape the build

**F1-a. `b` exists for 45% of the rows.** Cricket has two incommensurable notions of margin: runs and wickets. A chase won by 7 wickets and a defence won by 1 run are both "comfortable," but their numbers are on different scales, and the wicket-margin rows carry **no run figure whatsoever**. A single 1,243-row run-margin design matrix is not buildable. This is the central design constraint.

**F1-b. `n = 15`, not 10.** The prior shortlist's "10 unknowns" is one recent season's squad size, not the franchise count.

**F1-c. The graph is connected.** One component for the full graph and for every **modelling** subset — all-winner (1,218), run-margin (558), wicket-only (660), and per-season. Those are the subsets that feed a design matrix, so `nullity(A) = 1` and `rank(A) = n − 1 = 14`. The singular direction is exactly the constant vector — "add the same number to every team" leaves every margin prediction unchanged. Rank deficiency is *the insight*, not a failure, and it is provable rather than asserted.

**What this is not.** It is not "1 component in every subset". A random 30-match subset disconnected in **18 of 200** trials and the first 5 matches in the archive give **3 components**. The earlier "and under every name mapping" clause is withdrawn too: the measurement covers the canonicalisation map in §D2, not alternative mappings. Only the modelling subsets matter for the rank claim, so the inference stands — but a quantifier that outruns the measurement is a false claim under `AGENTS.md` §4.

## 3. Corrections to the prior shortlist

Two claims in `2026-10-02-cie-spark-mini-project-idea-selection-shortlist.md` are wrong. Both are recorded because the INDEX lesson is *verify the replacement, not just the original*.

**Wrong 1 — "10 unknowns."** Measured: 19 raw / 15 canonical franchises. The shortlist's 30-second demo script ("1,243 matches, 10 unknowns") would have been corrected by the examiner mid-sentence.

**Wrong 2 — "QR of A … you get an orthonormal basis of the row space … and the least-squares solution from the same operation."** Half right, and the wrong half is the part the guidelines name explicitly. `A` is `m × n` with `m = 558 > n = 15`. Thin QR gives `A = QR` with `Q` of shape `m × n`; `Q`'s columns are an orthonormal basis of a space **containing** `Col(A)` — but because `A` has rank `n − 1`, not `n`, that space is 15-dimensional while `Col(A)` is only 14-dimensional. `Q`'s columns are **not** a basis of `Row(A)`. `Row(A) ⊆ R^15` is a different space and needs its own orthogonalization (Gram–Schmidt on the rows of `A`, or QR of `Aᵀ`).

Both spaces are worth showing — they are cheap at `n = 15`, and together they cover the guidelines' "basis and orthogonal basis formation" properly instead of conflating two subspaces.

**To be verified in code, not asserted here:** how `numpy.linalg.qr` actually behaves on this rank-deficient `A` (rank-revealing vs not), so the plan does not depend on a guess about which leading columns of `Q` span `Col(A)`.

## 4. Modelling decisions

### D1 — Two models on two datasets, compared. Rejected: one model on one dataset.

This is the load-bearing decision, forced by F1-a.

| | Model 1 — **Massey** (least squares) | Model 2 — **Colley** (eigenvector) |
|---|---|---|
| Rows | the **558** run-margin matches | all **1,218** matches with a winner |
| System | `A x ≈ b`, `b` = signed run margin | `(W + λC) r = r` |
| Strengths | margin-aware; Strang #5's actual method | uses every match; robust to the margin problem |
| Weakness | discards 55% of matches | throws margin away |

- **Rejected — wins-only least squares on all 1,218 rows.** Works, but margin contributes nothing, so stage 8 is least squares over a binary `±1` right-hand side. That is a worse demo and wastes the dataset's richest feature.
- **Rejected — convert wicket margins to run equivalents.** Requires an invented conversion factor. That is a fabricated number in the middle of a linear-algebra project, and an examiner will ask where it came from. Rejected on integrity, not convenience.
- **Rejected — drop wicket-margin matches silently.** Loses more than half the data and hides the reason.

The comparison is not a workaround — **it is the finding.** Massey and Colley are both published (Massey 1997; Colley 2002), they encode different assumptions, and they do not agree. Showing *which* notion of dominance moves which team, and by how much, is a real result with literature behind it.

**Measured 2026-10-02 by a feasibility probe** (`reports/2026-10-02-ipl-power-ranking-f1-build-audit.md`) — this is stronger and stranger than the framing above assumed:

```text
Model 1  Massey least squares, 558 rows × 15 unknowns
         R² = 0.0214,  predicts the correct winner 55.0% of the time (coin flip = 50%)
Model 2  Colley eigenvector, 1218 rows — Perron-Frobenius positivity confirmed
Spearman( Model 1 , Model 2 ) = 0.000
```

**Zero rank correlation.** The margin model is topped by Kochi Tuskers Kerala — a franchise that existed for **one season** — and bottomed by Gujarat Lions, which existed for two. It is not ranking team strength; least squares weights every match equally, so short-history franchises get extreme coefficients, and per-match T20 margin noise (σ ≈ 37 runs) swamps the entire spread of team strengths (≈ 5–8 runs).

So the project is better stated as: *the obvious approach does not work, here is the measurement, here is the diagnosis, here is what fixes it.* Fix candidates, in order of cost: frequency-balanced least squares (weight each match by `1/(games(t1)+games(t2))`), then ridge shrinkage. **Fit the unbalanced model, show it fail, show the fix, show what it buys** — fitting three and reporting the best is cherry-picking. These two variants are **not yet measured.**

**The shortlist overclaimed here.** It said the eigen route should "reproduce" the least-squares solution. It will not. `AᵀA x = Aᵀb` has a right-hand side; the eigenvector problem does not. They answer different questions on different data. The honest claim is *correlated, divergent in identifiable ways* — not *reproduces*.

### D2 — Canonicalise team names to 15 franchises. Rejected: leave 19 raw strings.

Leaving the raw strings silently invents a phantom franchise: **`Rising Pune Supergiant` (2017) and `Rising Pune Supergiants` (2016) are two distinct strings for one team** — the franchise dropped the "s" mid-run. Failing to merge them adds a spurious unknown with almost no data, which is exactly the kind of thing that produces a garbage-looking answer.

Measured rename map (four merges, each backed by non-overlapping season ranges):

```
Royal Challengers Bangalore  +  Royal Challengers Bengaluru   -> RCB
Delhi Daredevils             +  Delhi Capitals                 -> DC
Kings XI Punjab              +  Punjab Kings                   -> PBKS
Rising Pune Supergiants(2016)+ Rising Pune Supergiant (2017)   -> RPS
```

**Deliberately not merged:** `Deccan Chargers` → `Sunrisers Hyderabad`. The 2013 franchise sale makes this defensible, but it is a judgement call, so it gets a flag and a sensitivity check rather than a silent merge.

**Correction to a common assumption:** "Deccan Chargers / Rajasthan Royals became Mumbai Indians in 2011" is **false**. Mumbai Indians appears in all 19 seasons; Deccan ends 2012 and Sunrisers begins 2013. Do not carry this into the code.

### D3 — Drop the 25 no-winner matches. Rejected: force them into the system.

A tie has no signed margin and no `winner`; a Super Over decided match has an `eliminator` but the format doc confirms **no `winner` field**, so even that subset cannot populate `A` and `b` as designed. 558 rows is already thin — forcing 25 meaningless rows in would corrupt the least-squares fit. Drop them and **state the exclusion count in the demo**, because silently dropping 25 of 1,243 is the kind of omission that reads as cherry-picking.

### D4 — Recency weighting: held in reserve.

Time-varying team strength is real, and exponentially down-weighting old seasons is a two-line change to `b`. But it also destroys the clean interpretation of `AᵀA` as "who beat whom by how much" and complicates the residual story. **Not in the first pass.** Note it as the answer to "what would you do with more time."

### D5 — Quote per-team standard errors. Cheap, and it pre-empts the obvious attack.

"Scores are team strengths" is obviously false; some teams are estimated precisely, some from 60 matches, some from 10. The covariance of the least-squares estimator is `σ²(AᵀA)⁻¹` — an `n × n` inverse on a 15-unknown system. Reporting `x ± se` converts an unjustified ranking into an honest one and identifies exactly which teams the official table gets *least* confidently wrong.

## 5. The 11 mandated stages, mapped

Order taken from page 2 of `UE25MA242A_MFAD -Mini-Project Guidelines.pdf`, re-verified 2026-10-02. **Matrix Simplification is stage 3 and Structure of the Space is stage 4** — the inherited first-run doc had them transposed.

| # | Stage | What is actually done | Status |
|---|---|---|---|
| 1 | Real-world data | Snapshot acquisition at `ipl_json/`, parse to a tidy CSV, the four-pair canonicalisation map, and the provenance record (`data/provenance.json`: URL, UTC fetch date, HTTP status, SHA-256, row count). Plan Phase B, steps 3–5. | CORE |
| 2 | Matrix representation | `A ∈ R^{558×15}`, `+1` winner / `−1` loser; `b` = signed run margin. Also `W` for Model 2. | CORE |
| 3 | Matrix simplification | RREF of `A` exposes the singular direction explicitly. | CORE |
| 4 | Structure of the space | `rank(A) = 14`, `nullity = 1`, provable from graph connectivity. Null space = the constant vector. | CORE |
| 5 | Remove redundancy | Maximal independent subset of match rows — a basis of `Row(A)`; the rest are dependent. | CORE |
| 6 | Orthogonalization | **Two** spaces. QR of `A` → `Q`'s 15 orthonormal columns span a 15-dimensional space **containing** `Col(A)`; its 15th direction is the numerical null direction, so `Q` is **not** a basis of the 14-dimensional `Col(A)`. Gram–Schmidt on rows (or QR of `Aᵀ`) → orthonormal basis of `Row(A) ⊆ R¹⁵`. Fixes the shortlist's conflation. | CORE |
| 7 | Projection | The fit **is** the projection of `b` onto `Col(A)`. `r = b − Ax̂`. | CORE |
| 8 | Prediction / approximation | `numpy.linalg.lstsq`, the (singular) normal equations `AᵀA x = Aᵀb`, and the constrained form `AᵀA x + 11ᵀx = Aᵀb` that pins the null direction. **Measured 2026-10-02: all three agree to 4.8e-14, and `cond(AᵀA + 11ᵀ) = 31.55` — the normal equations are numerically benign, not ill-conditioned.** An earlier draft predicted ill-conditioning; it was wrong. | CORE |
| 9 | Pattern discovery | Colley/Markov: dominant eigenvector by Perron–Frobenius. Different data, different assumption — compare with Model 1. | CORE |
| 10 | System simplification | `AᵀA` is **symmetric positive semi-definite by construction**, so the spectral theorem applies: real non-negative eigenvalues, orthogonal diagonalisation. `AᵀA = VΣ²Vᵀ` links it to the SVD of `A` for free. | CORE |
| 11 | Final application output | Two rankings vs the official points table; divergence plot; residual norm; per-team confidence intervals. | CORE |

All eleven load-bearing stages, up from seven. The genuine gain is stages 6, 9 and 10 — the shortlist's three weakest — and each is now doing real work rather than being bolted on.

**Stage 10 is the strongest of the three** and the shortlist missed it: `AᵀA` is *literally* symmetric, so diagonalisation is a one-line consequence of stage 8, not a separate contrivance.

## 6. Acceptance criteria

- [ ] Blocker (§0) answered **and recorded** per §0 — who, when, in what form — with the written confirmation obtained before any project code was written.
- [ ] Snapshot committed with provenance: source URL, UTC fetch date, HTTP status, SHA-256, row count.
- [ ] Team-name canonicalisation covered by a test that asserts `n = 15` and catches the Supergiant/Supergiants split.
- [ ] `rank(A)`, `nullity(A)` asserted numerically in a test, not assumed from the connectivity argument.
- [ ] Both least-squares routes agree to stated tolerance, or the disagreement is reported as a finding.
- [ ] Normalisation of `x` explicit — only differences are identifiable, so centre or scale to zero-sum.
- [ ] Every exclusion (25 no-winner matches) counted and stated in the demo.
- [ ] Demo runs offline from the committed snapshot.
- [ ] Colley eigenvector is positive-dominant (Perron–Frobenius) — asserted, not assumed.
- [ ] Licence position stated accurately: **ODC-BY for match data is unverified from the primary source** (see §7).

## 7. Licence — weaker than inherited

The gather node swept every page in cricsheet.org's `sitemap.xml` and found **no licence statement for the match data**; there is no `/licence/` page (404). The only explicit ODC-BY statement on the site covers the *Register* dataset. Four third-party sites assert ODC-BY 1.0 for match data, which is corroboration but not the primary source.

The prior run recorded "ODC-BY" as fact. **Soften it.** Attribute Cricsheet precisely, cite the file and retrieval date, and do not assert a licence term that was not read from the source. This is cheap to get right and expensive to get caught on.

## 8. Out of scope

- Any web or GUI demo. The guidelines ask for derivations and analysis, not manual calculation, and a 10-mark project does not need a front end. There is no `src/`, no `package.json`, no `frontend/`, no `backend/`. (`AGENTS.md` and `CLAUDE.md` used to describe an unrelated web-stack project that does not exist here; both were rewritten on 2026-10-02. See `INDEX.md` for the standing note.)
- The residual-SVD stretch variant from the shortlist §8. Held. Note it and do not attempt it.
- The `no result` vs `abandoned` distinction — the schema cannot express it.
- Deployment, hosting, and CI. There is nothing to deploy: a 10-mark coursework project that runs offline from a committed snapshot.
- Committing `ipl_json/` by default. It is 1,243 re-fetchable files; the demo needs only the parsed CSV. That is a decision, not a default — see plan step 2.

## 9. Assumptions recorded

1. **Substitution is permitted** (§0). Conservative reading, unresolved, and it gates everything.
2. **Objective is marks via the viva**, not a portfolio piece — this is a 10-mark course project, so the 11-stage coverage and the ability to defend it matter more than visual polish.
3. **Python 3 + NumPy + Matplotlib + Pandas only.** No web framework, no database, no notebook service. The Strang projects book is Python; adding anything else is cost without benefit.
4. **Demo output is terminal plots and printed tables.** Accepted: the bar chart is not flashy, and the wow is in the disagreement finding.