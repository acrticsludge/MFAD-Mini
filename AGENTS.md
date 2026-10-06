# MFAD Mini-Project — IPL Power Ranking — Binding Project Rules

These rules bind every agent and every human working in this repository. `CLAUDE.md` describes the *process*. This file describes what is *true* and what is *forbidden*. The two must agree on the stack, the blocker, honesty, and the docs location; if they ever stop agreeing, that is a bug to fix.

**Current status: nothing is implemented.** There is no `src/`, no package manifest, no test runner, and no Python module in this repository. Do not write or speak as though any stage of the build exists.

---

## 1. The assignment is the constraint

- Course: **UE25MA242A — Mathematical Foundation for AI & Data Science**, PES University, CSE. Deliverable: a **10-mark** mini-project.
- Marking scheme: **5 marks demo + 5 marks viva**.
- The guidelines explicitly require **no derivations, no proofs, no manual calculation**. Show the machinery, not the algebra.
- The course assigns **14 fixed problems**. Uniqueness cannot come from the mathematics, because every student draws from the same 14.
- Chosen: Gilbert Strang **problem #5**, *"Linear equations + college football team ranking"*, from the Strang linear-algebra projects book.
- **The framing (F1):** keep Strang's mathematics, replace the college-football dataset with the **IPL**. Build a least-squares power ranking of IPL teams from score margin and the fixture graph, show that it disagrees with the official IPL points table, and show exactly where and why.
- **Why IPL:** the obvious alternative pick for #5 is American college football, so IPL is not a realistic collision. The advantage comes from the dataset, never from the mathematics.

**ALWAYS:** filter every design choice through "will this survive five minutes of a viva?" **NEVER:** build something that needs a derivation on the whiteboard.

---

## 2. The blocker — HARD GATE

This is unresolved and it gates the entire project:

> Is the student free to substitute the dataset and re-frame the real problem, as long as the mandated LA workflow and the named Strang problem are honoured — or must the book's exact task list be submitted?

- **NEVER write project code before this is answered and recorded.** The gate is the **recording**, not the medium. Record the answer in `docs/reasonix/` — who gave it, when, and in what form. A written answer (email or message) is preferred. If the answer is given verbally, record it immediately in the spec and confirm it in writing before writing code. An inferred or unrecorded answer does not count.
- If the answer is **"the book's task list is mandatory"**, then Strang #5 is *college football*, the IPL reframe is illegal, and F1's entire advantage disappears. **The pick reopens.** Do not start work on the next-best candidate either until that reopen is done deliberately.
- If the answer is **"the framing is free"**, record it, then proceed to stage 4 IMPLEMENT.

This question has been open across three prior runs. It is load-bearing, not theoretical.

---

## 3. CRITICAL: measured numbers only

Measured **2026-10-02** from `https://cricsheet.org/downloads/ipl_json.zip` (Cricsheet JSON v1.2.0). These are measured, not recalled.

| Fact | Value |
|---|---|
| Matches | **1,243** |
| Distinct team-name strings | **19** |
| Distinct canonical franchises — the number of unknowns, `n` | **15** |
| Matches with a winner | 1,218 |
| No `winner` field, `outcome.result == "tie"` | 16 |
| `outcome.result == "no result"` | 9 |
| **Run margin available** | **558** |
| Wicket margin only, no run figure at all | 660 |
| Margin sign in the data | **unsigned** |
| `info.outcome.method == "D/L"` | 23 |
| Win/loss graph connected components | **1** for the full graph and every **modelling** subset |
| Seasons present | 19, from 2007/08 to 2026 |

**These override any conflicting figure in any other document in this repository.** The inherited planning docs carried two wrong numbers; a future agent must not reintroduce them.

- `n = 15`, **not 10**. "10" was one recent season's squad size. The design matrix is 15 by 15, not 10 by 10.
- **Run margin exists for only 558 of 1,243 matches.** The other 660 carry a *wicket* margin, a different scale with no run figure. **A single 1,243-row run-margin design matrix cannot be built.** This is the central design constraint, and it is why the design runs two models on two datasets: Massey least squares on the 558 run-margin matches, Colley eigenvector on all 1,218 matches with a winner. Their divergence *is* the finding.
- Margin is unsigned. A signed margin must be constructed from `winner` plus `by.runs`.
- `info["season"]` is **inconsistently typed** — sometimes an `int` (`2012`), sometimes a `str` (`"2007/08"`, `"2012"`). A naive `len(set(info["season"]))` returns **24**, not 19. Normalise before counting, or the invariant test for "19 seasons" will fail against correct data.
- Graph connectivity is 1 component **for the matrices actually used** — the full graph and every modelling subset — so `nullity(A) = 1` and `rank(A) = n − 1 = 14`. **The singular direction is the constant vector**: adding the same number to every team changes no predicted margin. That is the insight, not a failure.
- **"1 component" is not a claim about arbitrary subsets, and must not be restated as one.** Measured: 1 component for the full graph (1,243) and for every **modelling** subset that pools seasons — all-winner (1,218), run-margin (558), wicket-only (660). It is **false** for small arbitrary subsets: a random 200-match subset was connected in 200 of 200 trials, but a random 30-match subset disconnected in **18 of 200**, and the first 5 matches in the archive give **3 components**.
- **Correction 2026-10-05: "and per-season" was itself over-broad, the same defect one level down.** Measured over all 15 canonical franchises, a single season's graph has **6–8 components**, because franchises that did not play that season are isolated vertices. Restricted to the teams **active** in that season it is 1 component, in all 19 seasons. So the inference holds only in the "among active teams" reading. Since the design matrix is built over the **pooled** subset and never over a single season, the rank argument above is unaffected — but the unqualified phrase was a false claim under §4 and is withdrawn, exactly as §4 requires: qualify the quantifier, keep the inference.

---

## 4. CRITICAL: honesty and academic integrity

Three prior runs in this repository lost real work to unmeasured numerical claims. These are hard rules, not advice.

- **NEVER assert a numerical property of a dataset you have not measured.** "The five ranking indicators are collinear" was assumed, never measured. They are not. That one unmeasured assumption was propping up a self-assessed score of "9–10 CORE stages". **Every count, rank, nullity and condition number in this project must be computed by a test**, not written down in advance and trusted.
- **ALWAYS verify the replacement, not just the original.** A false claim was once "corrected" into a *different* false claim. A correction you have not re-verified is a second bug, not a fix.
- **NEVER build a forensic question whose answer is already published.** If the authority publishes the coefficients you would "discover" by least squares, the fit is circular and there is no finding.
- **NEVER present an identity that holds for every object in the class.** A stage that cannot fail cannot find anything.
- **Treat adversarial review findings as evidence, not verdict.** One reviewer's "fabrication" turned out to be a stale but real published figure. Verify before correcting.
- **NEVER manufacture a conversion factor to fill a gap.** Turning wicket margins into "run equivalents" requires an invented constant and was rejected on integrity grounds. Two honest models on two datasets beat one dishonest model.
- **ALWAYS say what you did not exclude, out loud.** 25 of 1,243 matches have no winner. Silently dropping them reads as cherry-picking; stating the count is a strength. Put the count in the demo, not in a footnote.
- **NEVER make a test pass by changing the test.** Skipping, deleting, or loosening an assertion is a hard stop, not a retry strategy.

---

## 5. The mandated 11 stages

Fixed by the course guidelines, in this order:

1. REAL-WORLD DATA
2. Matrix Representation (System of Linear Equations / Linear Transformations)
3. Matrix Simplification (Gaussian elimination / RREF / LU)
4. Structure of the Space (Vector Spaces → Subspaces → Basis → Rank & Nullity)
5. Remove Redundancy (Linear Independence → Basis Selection)
6. Orthogonalization (Orthogonal Vectors → Gram–Schmidt → Orthogonal Bases)
7. Projection (Orthogonal Projections → Projection onto Subspaces)
8. Prediction / Approximation (Least Squares)
9. Pattern Discovery (Eigenvalues & Eigenvectors)
10. System Simplification (Diagonalization of Matrix / Symmetric Matrix)
11. FINAL APPLICATION OUTPUT (Predictions / Compression / Trends / Noise Reduction / Modeling)

**Simplification (3) comes before Structure (4).** Stages 3 and 4 were transposed in an inherited first-run document, and `AGENTS.md`, the spec and the plan all carried that error for two runs. The order above was re-verified on 2026-10-02 against page 2 of `UE25MA242A_MFAD -Mini-Project Guidelines.pdf`. **If a document claims a list is quoted from a source, open the source and diff it** — "verbatim from the diagram" was claimed and never checked.

The examiner explicitly expects to see **explained**: matrix representation; RREF; basis and orthogonal basis formation; projection-based prediction; least squares estimation; eigenvalue/eigenvector analysis; final output.

- The design covers **all 11 of the mandated stages honestly**, up from 7 in earlier planning. If you find a stage is genuinely thin, **name it out loud rather than hiding it** — but do not manufacture a gap to appear rigorous, and never pad a stage with fake analysis to fill a slot.
- **NEVER make a stage FAKE to fill the workflow.** If a stage cannot be done honestly, say so out loud rather than bolting something on. An earlier candidate problem in this course had five of eleven stages fake and was explicitly rejected for that reason.

---

## 6. Two binding mathematics corrections

A prior document got both of these wrong. They are now settled.

1. **Thin QR of `A` orthogonalises the columns — `Col(A)`, not `Row(A)`.** For `A` at `558 × 15` with `rank(A) = 14`, thin QR yields a `Q` of shape `m × n` whose columns span a 15-dimensional space that *contains* the 14-dimensional `Col(A)`. `Row(A) ⊆ R¹⁵` is a different space and needs its own orthogonalization — Gram–Schmidt on the rows, or QR of `Aᵀ`. The guidelines name both, so both are legitimate; do not conflate them.
2. **The eigen route does not "reproduce" the least-squares solution.** `AᵀA x = Aᵀb` has a right-hand side; the eigenvector problem does not. They run on different datasets. Massey (1997, least squares on margins) and Colley (2002) are both published, they **diverge**, and that divergence is this project's result.
   - **Precision correction 2026-10-05: "Colley (2002, eigenvector on win rates)" is loose attribution, and code and report must not present the method as Colley's own.** Colley's 2002 paper solves a **linear system** — `(W + λC) r = r`, i.e. a win-rate rating with a shrinkage parameter. What this project computes is a **Colley-style Perron eigenvector**: the dominant eigenvector of the symmetric, entrywise non-negative matrix `W + Wᵀ + C`, which is the Massey–Colley family's *ranking* content but a different problem from the published one. The distinction costs one line in the demo and is the kind of thing a sharp examiner asks about, so it is stated on purpose rather than glossed.

---

## 7. Data rules

- **ALWAYS commit the snapshot with its provenance**: source URL, UTC fetch date, HTTP status, SHA-256 of the downloaded archive, and row count. The raw archive contents are on disk at `ipl_json/` but **no provenance record exists in this repository yet** — writing one is an outstanding obligation, not a done item.
- **ALWAYS make the demo read ONLY the committed snapshot.** Never the network. A demo that fails because a website is down costs 5 marks.
- **NEVER hard-code a count.** Derive it in code from the snapshot, and pin it with an invariant test.
- **JSON gotcha:** the winner is at `info.outcome.winner`, not `info.winner`, and the margin is at `info.outcome.by.runs` / `.by.wickets`. A naive `info["winner"]` raises **`KeyError: 'winner'`** in all 1,243 files — verified 2026-10-02. Only `info.get("winner")` returns `None`. The failure mode is a hard error on the first file, not a silently empty dataset.

### Canonicalisation map

`n = 15` is obtained by merging exactly **four** rename pairs:

| Raw string(s) | Canonical |
|---|---|
| `Delhi Daredevils` / `Delhi Capitals` | Delhi Capitals |
| `Kings XI Punjab` / `Punjab Kings` | Punjab Kings |
| `Royal Challengers Bangalore` / `Royal Challengers Bengaluru` | Royal Challengers Bengaluru |
| `Rising Pune Supergiants` (2016) / `Rising Pune Supergiant` (2017) | Rising Pune Supergiant |

- The Rising Pune pair is a **spelling drift mid-run**: one franchise, two strings. Leaving them unmerged silently invents a **16th unknown with almost no data**.
- **Deliberately do NOT merge** `Gujarat Lions` into `Gujarat Titans`, and do **NOT** merge `Deccan Chargers` into `Sunrisers Hyderabad`. They are separate unknowns in this design. One extra merge would take `n` from 15 to 14; both would take it to 13. The relation `rank(A) = n − 1` still holds either way — the merge changes `n` and every dimension, so it invalidates every already-computed figure.

### Banned claim

- **NEVER** claim that "Deccan Chargers / Rajasthan Royals became Mumbai Indians in 2011". **That is false.** Mumbai Indians appears in all 19 seasons. Deccan ends in 2012, Sunrisers begins in 2013. Do not put it in the map, and do not repeat it in the demo.

### Licence and attribution

- No licence statement for the **match data** exists anywhere on cricsheet.org. There is no licence page on the site; it returns 404. The only explicit ODC-BY statement on the site covers the *Register* dataset.
- Four third-party sites assert ODC-BY 1.0 for match data. That is corroboration, **not proof**, because none of them is the primary source.
- **ALWAYS** attribute precisely: archive file name, source URL, UTC retrieval date. **NEVER** assert a licence term that was not read from the primary source. If asked in the viva, say exactly that.

---

## 8. The stack is fixed

- **Python 3 + NumPy + Pandas + Matplotlib + pytest.**
- **No web framework. No database. No front end. No notebook server.** The Strang projects book is itself Python; the tools match the book.
- **Carve-out recorded 2026-10-05: the generated static `report/report.html` is permitted, and is not a "front end".** The owner required that the run be visual at every step. The report is assembled by string formatting from the same measurements the terminal printed, with every figure base64-inlined; it adds **no dependency** (stdlib string formatting, Matplotlib PNGs by the fixed stack), runs no server, fetches nothing, and is not part of the demo's computation path — delete it and the demo still works. A framework, a template engine, a bundler or a served app would still be a defect.
- **NEVER add a dependency without stating, in the report, why the fixed stack cannot do the job.** A web app in a 10-mark NumPy coursework project is a defect, not a feature.
- Everything must run from a clean clone with no network access.

---

## 9. Where the docs live

- `docs/reasonix/specs/` — specifications
- `docs/reasonix/plans/` — plans
- `docs/reasonix/reports/` — reports and handoffs
- `docs/reasonix/INDEX.md` — the run index

**ALWAYS read `docs/reasonix/INDEX.md` before planning anything.** It carries the open blocker and the lessons that cost real work. **ALWAYS append a row after each run**, and never rewrite history: a superseded run stays in the table marked superseded, because the fact that it happened is part of the history.

---

## 10. Scope discipline

- **NEVER** attempt the held residual-SVD stretch variant (shortlist §8). It is held on purpose, per the shortlist's own advice.
- **NEVER** add recency weighting in the first pass (spec §D4). It is the answer to "what next", not part of this deliverable.
- **NEVER** widen scope to "improve" the design, the visual output, or the problem statement. Ten marks, five of them a demo.
- If an idea is genuinely better than what is specified, raise it. Do not silently build it.