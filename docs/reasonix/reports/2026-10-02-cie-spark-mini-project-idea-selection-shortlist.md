# Shortlist — CIE SPARK mini-project idea selection

- **Slug:** 2026-10-02-cie-spark-mini-project-idea-selection
- **Stage:** 1 DEFINE / 2 ARCHITECT output. No decision taken yet — this is the input to that decision.
- **Evidence base:** three independent read-only research passes. Every dataset URL below was fetched live and verified by a gather node; licence and size are as reported at fetch time, not guessed.

## 1. How the field was cut down to four

Fourteen problems were read from the source PDF. Eight were eliminated before scoring.

**Eliminated on triviality** — cannot honestly fill an 11-stage workflow:

- **#1** Basic matrix ops — it is a `numpy` tutorial.
- **#4** Solving linear systems — no eigen, no least squares, no Gram–Schmidt. The workflow looks padded.

**Eliminated on saturation** — excellent pipeline, but your classmates will do these:

- **#11** PCA face recognition — _the_ most-attempted project in this book.
- **#12** PageRank — second most-attempted; a one-trick pipeline.
- **#14** SVD image compression — the "keep k singular values" set piece.
- **#2, #3, #6** the image-filter cluster — four of fourteen problems are image manipulation, which is why so many students will land there.

**Held but not shortlisted:** **#7** (MovieLens norms/angles — excellent dataset, but norms-and-angles alone under-fills the workflow; viable only if you extend it to SVD), **#9** (orthogonal matrices / 3D graphics — rarest pick and a great demo, but least squares, elimination and diagonalization are all absent and the viva will expose it), **#10** (chaos game — the most beautiful artefact available, ~20 lines, but **five of eleven stages are FAKE**; do not pick this).

## 2. The structural problem, stated honestly

**No single Strang problem exercises all eleven mandated stages honestly.** This is the finding that should drive the pick, and it is why "just pick a nice problem" fails.

| Candidate           | Strang # | CORE stages | Genuinely missing                                    |
| ------------------- | -------- | ----------- | ---------------------------------------------------- |
| Sports team ranking | 5        | **7**       | Gram–Schmidt, eigen, diagonalization                 |
| Climate fit         | 8        | **7**       | eigen, diagonalization                               |
| Movie / choice rec  | 7        | 6           | Gaussian elimination; basis selection light          |
| Social networks     | 13       | 4           | elimination, Gram–Schmidt, projection, least squares |
| 3D graphics         | 9        | 4           | elimination, least squares, diagonalization          |
| Chaos game          | 10       | 4           | Gram–Schmidt, projection, least squares, elimination |

But the guideline demands you explain **"basis and orthogonal basis formation"** _and_ **"eigenvalue/eigenvector analysis"** in the same demo. So a candidate that cannot honestly produce both is a liability in the viva, however good its application looks.

**Therefore: uniqueness cannot come from the mathematics — the assignment fixes it. It comes from the dataset and the framing.** A classmate doing the same Strang problem on American college football is not competing with you. A classmate doing it on the IPL is not a realistic threat.

## 3. The four finalists

| #      | Problem   | Framing                                                                                   | Dataset (verified)                                                                          | Licence                          | Integrity | Build | Wow   | Viva  | Novelty |
| ------ | --------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------- | --------- | ----- | ----- | ----- | ------- |
| **F1** | **#5**    | Least-squares power ranking of IPL teams, cross-checked against the official points table | Cricsheet IPL — `https://cricsheet.org/downloads/ipl_json.zip`, 1,243 matches, ball-by-ball | **ODC-BY**                       | 5         | 5     | 3     | **5** | **5**   |
| **F2** | **#8**    | Monsoon / crop-yield trend + forecast across 712 Indian districts                         | India Data Portal APY crop statistics, 49.1 MiB, 1997–2021, 712 districts                   | **ODC-BY**                       | 5         | 4     | 4     | **5** | 4       |
| **F3** | **14/11** | Low-rank (SVD/PCA) model of Indian air quality — **explicitly non-image**                 | CPCB via Kaggle `rohanrao/air-quality-data-in-india`, `city_day.csv` 2.57 MB, 26 cities     | **CC0**                          | 4→5       | 4     | 4     | 4     | **5**   |
| **F4** | **#13**   | Eigenvector centrality of the Indian railway network — find chokepoint stations           | `IR_Stations.parquet` 1.2 MB, ~8,801 stations                                               | CC0 packaging (verify per layer) | 2→3       | 3     | **5** | 2     | **5**   |

Scores are the pipeline pass's 1–5 ratings, with novelty adjusted for Indian data.

## 4. F1 — RECOMMENDED: the IPL power ranking

### The real problem

The IPL's official points table ranks teams purely on **wins and points**, which throws away two things: the _margin_ of victory, and _who actually beat whom_. Two teams can have identical W–L records and be genuinely different strengths. **Build a ranking that uses the margin and the fixture graph, then show it disagrees with the official table — and show exactly where and why.**

This is a real, published method, not a contrived exercise: Massey (1997) and Colley (2002) power rankings, and Vogel (2013) framing it as an eigenvector problem. Your output is a defensible ranking plus a residual norm quantifying how badly the official table fits the data.

### Dataset

`https://cricsheet.org/downloads/ipl_json.zip` — 1,243 matches, nested JSON (innings → deliveries → balls), ODC-BY licence, ~1 MB, static, no key. Cite Cricsheet.

### How all eleven stages are covered honestly

| Stage                                 | What you actually do                                                                                                                                                                                                                                                             |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Matrix representation                 | One row per match; `+1` winner, `−1` loser. RHS = score margin.                                                                                                                                                                                                                  |
| Vector space / basis / rank / nullity | The strengths live in R^n; the null space is exactly _"add a constant to every team"_ — **rank deficiency is the insight, not a bug.**                                                                                                                                           |
| Gaussian elimination / RREF / LU      | RREF on the system matrix exposes the singular direction explicitly.                                                                                                                                                                                                             |
| Linear independence / basis selection | Are the games independent equations? Disconnected groups → disconnected components.                                                                                                                                                                                              |
| **Orthogonalization**                 | **Solved honestly via QR of A — which _is_ Gram–Schmidt on the columns of A.** You get an orthonormal basis of the row space _and_ the least-squares solution from the same operation.                                                                                           |
| **Projection**                        | The least-squares solution **is** the projection of the margin vector onto the column space of A. Say this explicitly.                                                                                                                                                           |
| Least squares                         | The core of Strang #5: over-determined, so solve `AᵀA x = Aᵀb`.                                                                                                                                                                                                                  |
| **Eigenvalues / eigenvectors**        | **The Colley/Markov formulation makes the ranking the dominant eigenvector of a stochastic matrix** (Perron–Frobenius). Solve by least squares first, then show the eigen route reproduces it. This is a genuine cross-check with a published precedent — not a bolted-on stage. |
| Diagonalization / symmetric matrix    | Note the transition matrix is _similar to_ a symmetric matrix, so it is diagonalisable with real eigenvalues.                                                                                                                                                                    |
| Final output                          | Ranked list + bar chart vs official standings + divergence plot.                                                                                                                                                                                                                 |

### The 30-second demo

> "IPL teams are ranked officially by just wins and points. I threw away that assumption and treated every match as an equation — the difference in team strength equals the score margin. 1,243 matches, 10 unknowns, so I solved it in the least-squares sense. Here is my ranking next to the official table, and here are the teams the official table gets most wrong."

### Risks, honestly

- Nested JSON needs a small parser — budget 60–90 minutes. The flatter CSV format is documented at `https://cricsheet.org/format/csv_ashwin/`.
- **Rank deficiency will happen.** If teams never play each other, `AᵀA` is singular. Use `np.linalg.lstsq` and explain it — this becomes a feature, not a failure.
- **Demo must not need the network.** Bundle a committed CSV of parsed results. This is the single most common demo-day failure.
- The bar chart is not flashy. The wow is in the method and the disagreement finding. Accept this: it is a 10-mark mini-project where the viva is half the marks.

## 5. F2 — runner-up: district-level crop trend and forecast

Same 7-CORE pipeline as F1, with a better-looking artefact: a 3-panel data → fit → residuals figure, plus a forecast. Slightly more work than F1 because the source data is messy (district-name variants, near-empty 2020–21 rows) and because Vandermonde matrices go numerically unstable above degree ~6 — cap the degree and centre/scale your x-values, or the extrapolation will produce absurd temperatures and the examiner will notice.

**Choose F2 over F1 if** you would rather have the stronger visual and do not mind data cleaning.

## 6. F3 — the best "not a cliché" escape hatch

The SVD-on-an-image projects are the most crowded in the book. Doing SVD on a **pollutant matrix** instead is the cheapest way to look like an individual while still using the algorithm the examiner expects.

`X` = stations × days × 12 pollutants. Missing values make `X` genuinely rank-deficient, so **rank is the compression dimension and imputation is a linear-algebra decision, not a chore.** Modes 1 and 2 are interpretable — seasonal winter spike, and a traffic (NO/NO₂) vs crop-burning (PM) split. Rank-2 reconstruction gives a good visual.

Costs: Kaggle needs a free account, and the NaN rate is severe (Xylene is 22.9k non-null out of 108k), so imputation is real work. CC0 licence is a genuine plus.

**Choose F3 if** your real fear is looking like everyone else, more than you fear data cleaning.

## 7. F4 — the high-uniqueness, high-risk option

The most striking demo available: an 8,801-station national network, node size by eigenvector centrality, then delete the top station and watch the graph fragment. Almost zero classmates will touch it.

But it is the weakest in the viva, and the reason is concrete: the Kaggle station table **has no edges**, so you must derive the graph yourself, and _then_ you still have to explain to the examiner why Gram–Schmidt, projection and least squares are absent. Licence on `datameet/railways` is unverified (no LICENSE file); the `india-geodata` packaging is CC0 but per-layer sources vary.

**Choose F4 only if** you are confident you can defend four CORE stages without faking the rest.

## 8. Stretch variant, if the brief turns out generous

F1 plus the eigen cross-check already reads as a two-part project. A third part — taking the **residual matrix** of your ranking and applying a low-rank decomposition to expose _systematic_ bias in margin-only rankings — is genuinely interesting and is the single best fusion of two Strang problems (#5 + #14). **Do not attempt this for a 10-mark mini-project** unless the timeline is generous. Note it; hold it.

## 9. What is still open

- Whether the booker's task list is mandatory or the dataset may be substituted. **This can invalidate the entire shortlist** — see the blocker in the spec.
- Hours available.
- Whether the goal is marks, portfolio, or both.
- Whether a terminal/plot output is acceptable or a web/GUI demo is expected.
- Whether you have Kaggle / data.gov.in accounts and whether demo-day internet is reliable.

**Stage 2 ARCHITECT and stage 3 PLAN are blocked on these.**
