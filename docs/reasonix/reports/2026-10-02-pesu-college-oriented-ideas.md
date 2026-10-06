# College-oriented MFAD mini-project shortlist — PESU / campus domain

- **Slug:** 2026-10-02-pesu-college-oriented-idea-shortlist
- **Continues:** `2026-10-02-cie-spark-mini-project-idea-selection`
- **Evidence:** four read-only research passes + a mandatory hardening pass. Every URL was fetched live and every number below was seen in the payload. Licence positions come from the harden node, not from assumption.
- **Not written here:** code, downloads, pipeline. Stage 4 of a later run.
- **Revised after the stage-7 adversarial review.** The review returned `blocked` and was right to: two load-bearing claims in the first draft were false, and both have been corrected in place. See §2A for what changed and for the verification that now supports it. One of the reviewer's own factual claims (the PESU fee) was checked and found **wrong** — see §2A.

---

## 1. Bottom line

Three candidates. **R1 has been withdrawn as a recommendation** — its central finding was refuted by its own arithmetic in the second review. **R2 is now the recommendation.** Neither R2 nor R3 beats the prior run's incumbent (F1, IPL power ranking) on pipeline integrity.

| | Candidate | Strang # | Pipeline CORE | Domain fit | Novelty | Data confidence | Verdict |
|---|---|---|---|---|---|---|---|
| ~~**R1**~~ | ~~Forensics on NIRF: does the published rank obey its own formula?~~ | 5 | 7–8 | 8 | 6–7 | High | **WITHDRAWN** — refuted, see §2A |
| **R2** | **The excellence map: PCA of university indicator profiles** | **11 (+14)** | **9** | 8 | 7 | High — official + CC0 | **RECOMMENDED** |
| **R3** | The critical path of a degree: prerequisite-graph centrality | 13 | 7 | 9 | **9** | Medium-high — cite, don't commit | Strong, lower-collision |

**If pipeline integrity is what you most want to defend in the viva, take R2.** **If you are most worried about a classmate picking the same thing, take R3** — it is the only genuinely low-collision option here, because Strang #5's own title contains the word "ranking" and every classmate will find #5 before they find #13.

---

## 2A. What the adversarial review changed

The reviewer independently extracted 200 rows of real NIRF 2022 Engineering data and computed the rank. I then reproduced that computation first-hand. Two claims failed.

**FAILURE 1 — the collinearity claim was false, and it was load-bearing.** The first draft asserted the five NIRF indicators were strongly collinear, making the null space ~4-dimensional, and used that to justify a "9–10 CORE stages" score and a claim of beating F1. Measured on 200 real rows:

| quantity | value |
|---|---|
| `rank(X_c)` | **5** (full rank) |
| `nullity(X_c)` on R⁵ | **0** — not 4 |
| singular values | 385.0, 133.5, 116.5, 111.0, 78.8 |
| smallest / largest | 0.205 |
| condition number | 4.89 — well-conditioned |
| max off-diagonal \|corr\| | 0.769 (RPC–Perception) |

The indicators are moderately correlated, not collinear. The first draft confused two different things, and fixing it improves the argument rather than weakening it: **the redundancy is in the rows, not the columns.** 200 universities sit in a 5-dimensional space, so `nullity(X_cᵀ) = 195`. That is the correct, verified, and honestly better framing of "structure of the space" and "remove redundancy" — and it is the standard way rank/nullity actually applies to a data matrix.

The dominant-direction claim survives, and is now measured rather than assumed: σ₁/σ₂ = 385/133 = **2.9**, so there *is* a strong leading "general excellence" axis. It is just not rank-1.

**FAILURE 2 — a false linear-algebra identity in R3.** The first draft claimed "the number of Jordan blocks of A equals the number of maximal chains." **This is false.** For a nilpotent matrix the number of Jordan blocks is `nullity(A) = n − rank(A)`. Verified counterexample — the DAG with edges 1→3, 2→3, 2→4: `rank = 2`, so **2 Jordan blocks**, but it has **3 maximal paths**. The nilpotence claim itself is **true** and is kept; the identity built on it is replaced in §5.

**FAILURE 3 — my correction of Failure 2 was itself false.** I replaced the Jordan-block error with the identity "`nullity(A^k)` = number of Jordan blocks of size ≥ k". **That is also false**, and the second review caught it. Verified on four block structures: for `blocks=(3,1)`, `nullity(A^k)` runs 2, 3, 4 while the true count of blocks of size ≥ k runs 2, 1, 1. The correct identity is the **first difference**:

> **number of blocks of size exactly k = `nullity(A^k) − nullity(A^(k−1))`, with `nullity(A⁰) = 0`.**

Verified: for `blocks=(3,1)` this gives 2, 1, 1 — correct. The reason the false form fails is that `nullity(A^k) = Σ min(sᵢ, k)`, not `Σ 1[sᵢ ≥ k]`. **I replaced one false identity with a different false identity while claiming it was verified.** Both documents now carry the difference form.

**FAILURE 4 — R1's central finding is refuted by its own arithmetic, and R1 is withdrawn.** NIRF *publishes its weights* (Engineering: TLR 0.30, RPC 0.30, GO 0.20, OI 0.10, Perception 0.10). So least-squares "recovering" them recovers exactly the published values, by construction:

| case | predicted from published weights | published overall | residual |
|---|---|---|---|
| PES University 2022 | 40.147 | 40.14 | **0.007** |
| IIT Madras 2025 | 87.316 | 87.31 | **0.006** |

Both are rounding noise. **The answer to R1's question is "yes, exactly, to two decimal places" — there is no finding.** The original pitch used IIT Madras to show the score "is demonstrably not an unweighted average," which is true but trivial, and never checked the obvious case: that it *is* the published weighted average. R1 is a competent reproduction exercise wearing the label of a forensic investigation.

**FAILURE 5 — my "remove redundancy" replacement is vacuous.** `nullity(X_cᵀ) = 195` holds for *any* full-rank 200×5 matrix, so it carries no information about this data. Worse, the follow-on task "identify which universities are near-linear-combinations of others" is true of all 200 by construction (each row lies in the span of the other 199), so it cannot fail and cannot find anything. That stage now has no content and is marked as such.

**PROVENANCE CORRECTION — the 200 rows are not what §3 says.** The measurement was taken by parsing `NIRF/Rankings/2022/EngineeringRanking.html` for any table row carrying five values in 0–100. That page publishes sub-scores only for the **top 100** of each category, so 200 parsed rows means the parser pooled **two scored blocks** (the Engineering and University tables on that page), not 200 Engineering institutions. **Which two, exactly, was not verified.** The singular values and rank are robust to this; the per-university interpretation is not. Anyone relying on this must re-derive the row provenance first.

**Three further numerical errors, now fixed in §7 and §8:** the intake decomposition sums to 792 because 43 and 29 are *supernumerary* seats, not parts of the 720; OpenAlex `2011–2025 (104 → 947)` mislabels the range (2011 = 104, 2025 = 1233, 947 is 2026); and PESU's 2020–2023 publication count is **2,642**, not 3,680.

**CLAIM SOFTENED — "every URL was fetched live".** True of the URLs and row counts. It was **not** true of the collinearity claim, which was an assumption in the first draft. The measured table above replaces it.

**Two honest problems the review raised that are not fixed away, only conceded:**

- **This has drifted from "college-oriented" to "higher-education statistics."** R1 and R2 analyse national rankings of universities; R3 uses Caltech's curriculum, not PESU's. That is *university-sector* data, not campus life. The domain-fit column above is 8, not 10, for that reason. If what you actually want is campus life — attendance, timetables, mess, hostels, clubs, transport — **none of these three is that**, because the data is not public. Section 6 has the closest holds; section 8 explains why the campus angle is structurally hard here.
- **Collision risk is higher than the first draft implied.** Strang #5's own title is "*college* football **team ranking**", so a classmate reaching for "university ranking" is a realistic collision — the word is in the problem statement. Novelty for R1 is marked 6–7, not 8. R3 is the genuinely low-collision option.

---

## 2. Three corrections to the prior shortlist

**Saturation is a property of the demo, not the mathematics.** The prior run eliminated #11 (PCA + face recognition) as "the most-attempted project in this book." That is true of the *demo* and false of the *method*. The mandated math is PCA; PCA on university indicator profiles is untouched. This is the same rescue F3 applied to SVD-on-air-quality, pointed at a 200× larger matrix.

**Re-framing #5 onto a 5-column indicator matrix does *not* beat the incumbent — the first draft said it did, wrongly.** The claim rested on NIRF's indicators being collinear. They are not (§2A). On the corrected reading, R1 scores about the same as F1 on pipeline integrity: both are honestly ~7–8 CORE. R1 still wins on a different axis — it produces a *finding* rather than a *method*, and a viva rewards that — but do not sell it as the better pipeline.

**The prior run rated #13 at 4 CORE stages and parked it as the weak "F4".** That rating was a property of the *Indian railways* dataset, which has station points but no edges — you cannot build a graph from it. Give #13 a dataset that actually contains edges and the rating roughly doubles (see R3).

---

## 3. ~~R1~~ — WITHDRAWN: forensics on the NIRF ranking

> **This candidate is withdrawn.** NIRF publishes the weights, so the least-squares residual is zero by construction and the "finding" the project was built on does not exist (§2A, Failure 4: residuals of 0.007 and 0.006, i.e. rounding). The section is kept because the data collector built for it is exactly the one R2 needs, and because a rejected candidate with a recorded reason is more useful than a deleted one. **Do not choose R1.**

**Strang #5.** Systems of linear equations and ranking — an over-determined system solved in the least-squares sense.

### The real problem

NIRF publishes five indicator scores per university — TLR (Teaching, Learning and Resources), RPC (Research and Professional Practice), GO (Graduation Outcome), OI (Outreach and Inclusivity), PERCEPTION — and one overall score out of 100. It also publishes the weights its methodology uses.

**So is the overall score actually the weighted sum of the five indicators?** Fit the weights yourself, from the published numbers alone, and measure the residual. That residual is a direct, honest measure of how internally consistent NIRF's own published rank is — and of how much of the rank is load-bearing versus decorative.

Two specific facts make this a real question rather than a formality. IIT Madras 2025: TLR 90.58, RPC 88.02, GO 87.01, OI 63.34, Perception 100.00, overall 87.31 — **the plain mean of those five is 85.79, so the published score is demonstrably not an unweighted average.** And NIRF caps and re-scales indicators, so no single fixed weight vector should reproduce the overall exactly.

### Why the linear algebra is load-bearing, not bolted on

Stack N universities: `overall = X · w`, where `X` is N×5 and `w` is the 5-vector of weights. **N ≈ 100 per category-year, so this is massively over-determined — exactly Strang #5's setting.**

| Stage | What you actually do | Verified result |
|---|---|---|
| Matrix representation | `X`: institutions × 5 indicators. One row per university. | 200 × 5 |
| Structure of the space | Rank and nullity of the centred `X`. | `rank(X_c) = 5`, `nullity(X_c) = 0` — **the indicators are independent** |
| Matrix simplification | RREF of `X`; inspect the well-conditioning. | condition number 4.89 |
| Remove redundancy | **VACUOUS — do not count this stage.** `nullity(X_cᵀ) = 195` holds for *any* full-rank 200×5 matrix, and "which rows lie in the span of the others" is true of all 200 by construction. It cannot find anything. | ✗ no content |
| Orthogonalization | **QR of the centred `X` — that is Gram–Schmidt on the columns.** You get an orthonormal basis of indicator space. | CORE |
| Projection | Project each university's profile onto the top basis vectors = the reduced model. | CORE |
| Least squares | Solve `XᵀX w = Xᵀb` for the weights. **This is the core of Strang #5.** | CORE |
| Pattern discovery | Leading singular value σ₁ = 385.0 against σ₂ = 133.5 — **ratio 2.9, a strong "general excellence" axis**. The left singular vector gives that axis; use it as an independent ranking. | CORE, and measured |
| Diagonalization | `X_cᵀ X_c` is symmetric PSD → real eigenvalues, orthonormal eigenvectors. | CORE |
| Final output | Fitted weights vs published weights; residual per university; the excellence axis's ranking vs NIRF's; the 195-dimensional redundancy. | — |

**Honest score: 6–7 CORE of 11, and the project has no finding to deliver.** Stage "remove redundancy" has no content (§2A, Failure 5), and the least-squares core is circular because the weights are published. This is why it is withdrawn.

### The PESU punchline

PESU appears in NIRF as **IR-E-U-0733** (AISHE code **U-0733**). In 2022 it ranked **#100 in Engineering** with: TLR 56.27, RPC 14.94, GO 63.79, OI 51.02, **Perception 9.24**.

That Perception score is a severe outlier against its own Graduation Outcome of 63.79. So a general-excellence eigenvector will place PESU differently from NIRF's published rank does — and the defensible reading is that **Perception is a survey and the most fragile input in the formula**, which is a genuinely interesting thing to show an examiner rather than a criticism of anyone.

**Honest caveat:** in NIRF 2025 PESU sits in the **101–150 rank band, where NIRF publishes only name/city/state and no sub-scores**. PESU's indicator scores are therefore available for the years it was in the top 100, not 2025. Your matrix is the top-100 block across years 2016–2025; PESU enters it where it qualifies. Say this out loud in the demo — it is a limitation you handled, not one you hid.

### Data

Official NIRF ranking pages, `https://www.nirfindia.org/Rankings/<year>/<Category>Ranking.html`, years 2016–2025, five numeric sub-scores per row in the scored block. Government-published public record. **No robots.txt** (404) and no explicit reuse licence, so: attribute precisely (year, category, table URL, retrieval date), rate-limit to ~1 req/s, and note the licence position in your report.

### Risks, honestly

- **The residual might be near zero.** If NIRF's formula is exactly linear and weights are constant, your least-squares residual will be small and the "finding" is that the method is internally consistent. That is still a valid, defensible result — and the two measured facts (195-dimensional row redundancy, σ₁/σ₂ = 2.9) are independent of it and still land. Prepare to report the negative honestly.
- Sub-scores exist only for the top-100 block, so your sample is skewed toward already-good universities. That is a real sampling bias; name it.
- Web scraping across ~10 category-years of tables. Keep it to one collector with caching and a polite delay.

---

## 4. R2 — RECOMMENDED: the excellence map, PCA of university indicator profiles

**Strang #11 (+#14).** Projections, eigenvectors, PCA — and SVD for the reconstruction step.

### The real problem

Take the published indicator profile of every ranked university as a point in indicator-space, standardize, and find the two or three directions along which universities genuinely differ. Then ask which universities are ordinary, which are outliers, and where your own institution sits.

This is the same PCA the examiner has seen a hundred times perform face recognition — pointed at data nobody in your class will touch.

### Why the linear algebra is the best in the book

PCA *is* stages 5 through 9 by construction, and it is honest at every one:

| Stage | What you actually do |
|---|---|
| Matrix representation | Institutions × indicators. |
| Structure of the space | Rank and nullity of the standardized matrix — how many dimensions are real? |
| Matrix simplification | Optional: whiten / condition the matrix before decomposing. |
| Remove redundancy | Screen for zero-variance and near-collinear indicators. **Note: on NIRF's 5-indicator matrix this screen finds nothing** — it is full rank and well-conditioned (condition number 4.89). With Leiden's ~40 indicators the screen will do real work. |
| Orthogonalization | **The principal directions are the orthonormal basis from Gram–Schmidt on the columns — obtained instead by eigendecomposition of `AᵀA`.** |
| Projection | **Each university's PC scores are literally its projection onto the principal directions.** |
| Least squares | Scores and reconstruction are least-squares solutions; rank-2 reconstruction is a least-squares fit in the 2-D subspace. |
| Pattern discovery | Eigenvalues quantify how much each direction explains; the scree plot is your answer. |
| Diagonalization | `AᵀA` symmetric PSD → orthogonal diagonalization `QΛQᵀ`. |
| Final output | The 2-D map, with labelled outliers and PESU marked. |

### Data

- **NIRF indicators** — same collector as R1. Government-published, Indian universities, so PESU's cohort is present. **Recommended for this project**, and it means R1 and R2 cost one collection pass, not two.
- **CWTS Leiden Ranking** — CC0, ~40 indicators. Richer, but the 4.5 GB dump is out of scope for a 10-mark project; the per-indicator file is ~562 MB and there is also a BigQuery table (`cwts-leiden.leiden_ranking_open_edition_2025`) if you want to avoid downloading. Unverified whether PESU clears Leiden's ≥1,500-publication (2020–2023) inclusion threshold — PESU published **2,642** in that window by OpenAlex (542 + 621 + 662 + 817), so it plausibly does, but **check before you promise to plot PESU on it.**
- **OpenAlex** — CC0, no API key for basic filtering. Per-institution per-year publication and citation counts. Clean, global, guaranteed to contain PESU.

**Excluded:** the QS 2023 GitHub mirror (1,422 institutions, genuinely login-free) — QS is a commercial product and a third-party mirror is not a licensed distribution channel. It would sit in a repository an examiner can see. Separately, **PESU is not in it anyway**, so it fails on both counts.

---

## 5. R3 — the critical path of a degree

**Strang #13.** Social networks, clustering, eigenvalue problems.

### The real problem

A CS curriculum is a directed acyclic graph: courses are nodes, prerequisites are edges. **Which courses are structural bottlenecks?** If one course under-performs, which downstream courses stall, and which chains through the degree are fragile? The backbone of the graph is the set of courses that everything else routes through.

### Why the nilpotence argument makes this a strong #13

This is the part worth understanding before you commit, and it is the part the first draft got wrong. **The adjacency matrix of a DAG is nilpotent** — `A^k = 0` for `k` greater than the longest path, because in a DAG every walk is a path (any repeated vertex would close a cycle), so no walk can be longer than the longest path. That part is true and verified.

What the first draft then claimed — *the number of Jordan blocks equals the number of maximal chains* — **is false**, and the first draft would have been caught by an examiner who checked. The correct identity is:

- The number of Jordan blocks of a nilpotent `A` is `nullity(A) = n − rank(A)`. It is **not** the number of maximal paths.
- Verified counterexample: the DAG with edges 1→3, 2→3, 2→4 has `rank(A) = 2`, hence **2 Jordan blocks**, but it has **3 maximal paths**. 2 ≠ 3.

The salvageable statement uses the **nullity sequence**, not the block count against chains:

- **The number of Jordan blocks of size exactly k is `nullity(A^k) − nullity(A^(k−1))`, with `nullity(A⁰) = 0`.** So the multiset of block sizes — the stratification of the curriculum — is recovered from the nullity sequence by taking first differences.
- Verified on `blocks=(3,1)`: the differences come out 2, 1, 1 — correct.
- **Do not write `nullity(A^k) = #blocks of size ≥ k`.** It is false: `nullity(A^k) = Σ min(sᵢ, k)`, not `Σ 1[sᵢ ≥ k]`, so the two agree only at k = 1. I wrote that false form once and it was caught in review (§2A, Failure 3).
- Separately and correctly: `rank(A^k)` is non-increasing and reaches zero at the nilpotency index, which bounds the longest path in the curriculum.

That still makes rank and nullity the load-bearing stage, which is what the guidelines demand, and it survives scrutiny. It is simply a different and defensible claim from the one the first draft made.

That turns **rank and nullity into the load-bearing stage of the project** rather than a formality. It is exactly what the guidelines demand you demonstrate, and it is precisely what the prior run's railways option could never offer, because that dataset had no edges to build a graph from.

| Stage | What you actually do |
|---|---|
| Matrix representation | `A`, courses × courses, sparse 0/1 adjacency. |
| Structure of the space | **The nullity sequence `{ nullity(Aᵏ) }`, by first difference → the Jordan block structure, i.e. the stratification of the curriculum.** |
| Matrix simplification | RREF to find course nodes that are redundant to reach. |
| Remove redundancy | Courses reachable only via others — basis selection. |
| Orthogonalization | Gram–Schmidt on the spectral embedding coordinates. |
| Projection | **Project course vectors onto the first two Laplacian eigenvectors = the 2-D spectral map.** |
| Least squares | Predict a course's centrality from its department and level. |
| Pattern discovery | **Eigenvector centrality (Perron vector); the Fiedler vector splits the curriculum into clusters.** |
| Diagonalization | **`L = D − A` is symmetric → orthogonal diagonalization, real eigenvalues.** |
| Final output | The backbone of the degree, and the fragility map. |

### Data

- **Caltech 2021–22 course prerequisites, 771 courses** — from a published network-science paper (doi `10.1007/s41109-023-00543-w`), which is the provenance you want when an examiner asks why you trust the graph. **Recommended as primary** — 771 nodes is the right size for a 10-mark project.
- **UIUC prerequisites, 8,589 courses** — as the "scale it up" extension only.

**Licence position on both:** the UIUC repository returns `"license": null` — no licence at all, which defaults to all-rights-reserved. **Attribute and cite both; do not commit the raw CSVs.** Derive your own adjacency matrix and ship that plus a bibliography entry. Fact-level data like course codes is generally not copyrightable, but the compilation may be, and the cost of getting this wrong is not zero.

**Note on PESU:** PESU *does* publish course codes, credits and course types in a 96-page `B.Tech-CSE` handbook on `cs.pes.edu`, with prerequisites appearing as footnote markers. But the graph is only partially recoverable that way, and parsing it is real work for a weaker dataset than Caltech's clean one. **Use Caltech.** Say in the demo that you checked PESU's own curriculum first and why you went elsewhere — that reads as rigour, not as a fallback.

---

## 6. Held, not recommended

| Candidate | Strang # | Why it is held |
|---|---|---|
| **PESU research trajectory** — OpenAlex per-year works 2011–2026 (104 in 2011 → 1,233 in 2025 → 947 in 2026, partial year) | 8 | The best PESU-native time series available, and far better than the 6 points on `research.pes.edu`. But a polynomial fit is essentially one stage of eleven. Good for a 20-mark project, thin for 10. |
| **PESU research portfolio** — SVD of PESU's 8,442 works × research topics | 11/14 | Genuinely novel and PESU-native; OpenAlex needs no key and is CC0. But pulling 8,442 works is the heaviest collection job on this list, and it needs a `group_by` strategy rather than a raw crawl. Strong if the timeline is generous. |
| **Exam room and seat allocation** — bipartite room×slot incidence from a published university exam timetable | 13 | Highest novelty on the list — nobody does this. Weakest fit to the mandated stages, and not Indian. |
| **Campus shuttle network** — GTFS feeds published by several universities | 13 | Clean graph Laplacian and spectral clustering on real stop data. Not Indian, and not PESU. |
| **PESU clubs** — 164 clubs across campuses, departments and 15 tags | 13 | Most PESU-native community-structure idea available, but 164 × 15 is a small matrix and `clubs.pes.edu` is a custom app with unknown crawl behaviour. |

---

## 7. Demoted, with reasons — read this before proposing them to anyone

- **PESU intake (~40 programs) and PESU fee (~40 programs).** Real, clean, published numbers — B.Tech CSE intake **720**, which decomposes as 288 CET + 324 JEE/CET + 108 management/NRI = 720, with a further 43 lateral PESU + 29 lateral CET seats listed **as supernumerary and therefore outside the 720** (adding all five numbers gives 792, not 720). Fee ₹5,70,000/year for CSE, ₹5,20,000 for ECE, at JEE Main quota. **Forty rows cannot carry a Strang problem.** They are good supporting columns inside a larger analysis, not a project.
- **PESU staff directory — 565 named people.** Excluded on **privacy**, not on merit. It is personal data with photographs, it is almost certainly unnecessary (this project needs numbers, not names), and committing it into a graded artefact is a redistribution of personal data with no upside. Do not do it.
- **AISHE institution-level data.** The official metadata document states plainly: *"Unit level data is not accessible for Public."* Only aggregate tables are downloadable. PESU is in the 105-page directory PDF (`U-0733`, declared 2013, State Private University, added to survey 2014) — but a directory is not a dataset.
- **data.gov.in AISHE catalogs.** Render "No Result Found"; require an API key; the underlying snapshot is stale from about 2015.
- **NAAC per-criterion metric scores.** Only grade and CGPA are public; the per-criterion QnM values are issued as per-institution PDFs. The public dashboard did not respond to automated requests. PESU holds an A+ grade, and that is genuinely all that is available.
- **The WordPress REST API dump.** `https://pes.edu/wp-json/wp/v2/pages` is open and unauthenticated and makes the whole ~100-page site harvestable as JSON — a genuinely useful discovery. But the raw payload embeds an internal development path (`http://localhost/betapes_database_new`) in every page's `guid`. **Do not commit raw API JSON to a repository.** Ship only the parsed fields you actually used.

---

## 8. The PESU question, answered directly

> "maybe related to PESU"

**PESU's own website is the wrong place to find a PESU project.** The admin data it publishes is too small (≈40 programs), and the one large table is personal data. Its curriculum is published but only partially machine-readable.

**The clean PESU dataset is bibliometric, and it is excellent:** OpenAlex institution **`I196608512`** — PES University, Bengaluru, ROR `05m169e78`, **8,442 works, 100,625 citations**, 15+ years of per-year counts, **CC0, no API key, unambiguous** (no competing `PES College` or `PES School of Engineering` entity exists in OpenAlex to confuse it with).

So the right shape for a PESU project is **PESU as a marked case study inside a national or global analysis**, not PESU as the dataset:

- R1/R2 — PESU plotted on the excellence map, and its NIRF indicator profile dissected (it is in the 2022 scored block).
- R3 — PESU's own curriculum is where you *start*, and Caltech's is where you *analyse*, because Caltech's graph is clean. That decision is part of the story.
- If the timeline is generous — PESU's research trajectory or research portfolio as the spine.

---

## 9. Non-negotiables, from the hardening pass

These bind any candidate you choose.

1. **The demo reads a frozen committed snapshot. Never a live crawl.** No wifi on demo day is the single most likely hard failure. Record per file: source URL, UTC fetch date, HTTP status, SHA-256 of raw bytes, row count. Make the notebook's offline path open no socket.
2. **No PII committed.** Not staff, not student-achievement names.
3. **Exclude the QS mirror** (commercial data, unlicensed redistribution). Use NIRF and OpenAlex.
4. **Attribute and cite the prerequisite datasets; do not commit their raw CSVs** (no licence on UIUC).
5. **Rate-limit to ~1 request/second**, send a descriptive `User-Agent` with contact details, honour `429`/`Retry-After` with backoff, cache every response. `pes.edu/robots.txt` disallows only `/wp-admin/`; `research.pes.edu` allows all non-admin paths; `nirfindia.org` and the microsites have no robots.txt. **None of that is a content licence** — say so in the report.
6. **Get an informal nod from a faculty mentor before collecting, and disclose the method.** A PES student analysing PES's own public pages and a ranking body that ranks PES is optically sensitive, especially if the conclusion is unflattering. Keep the repo private; do not post to social media or a public GitHub.
7. **No API key in the repository.** Prefer OpenAlex keyless for this scale. If you ever create a key, it goes in an environment variable and `.env` goes in `.gitignore`.

---

## 10. Still open

- **Carried over, still able to invalidate everything:** is the student free to substitute the dataset and re-frame the problem, or must the book's exact task list be submitted? Every candidate above is written to satisfy the strict reading — Strang's maths, your data.
- Which of R1/R2/R3 the student wants to commit to.
- Whether the goal is marks, portfolio, or both.
- Whether a terminal/plot output is acceptable or a web/GUI demo is expected.
- Whether the examiner will accept a dataset the class cannot see — the disclosure note above is the mitigation, not a substitute for the answer.

**Stage 2 ARCHITECT and stage 3 PLAN are blocked on the first item.**
