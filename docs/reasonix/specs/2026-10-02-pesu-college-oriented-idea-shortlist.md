# Spec — PESU / college-oriented MFAD mini-project shortlist

- **Slug:** 2026-10-02-pesu-college-oriented-idea-shortlist
- **Course:** UE25MA242A — Mathematical Foundation for AI & Data Science, PES University, CSE
- **Continues:** `2026-10-02-cie-spark-mini-project-idea-selection` (read its spec + shortlist before starting)
- **Declared risk:** low (research only). Floor raised to `medium` by the plugin on file observation.
- **Adapter:** generic [fallback] — unguarded, no `docsRoot`, so documentation is not gate-enforced. Written anyway.

## 0. The hard constraint, re-verified from source

`UE25MA242A -MFAD Mini-project Problem Statements.pdf` was text-extracted directly this run (pypdf 6.19.0, 1 page). The 14 problems are fixed; the student chooses among them, they do not invent one:

1 Basic matrix ops · 2 Matrix ops + image manipulation · 3 Matrix mult/inversion/photo filters · 4 Solving linear systems · **5 Linear equations + college football team ranking** · 6 Convolution/inner product/image processing · 7 Norms, angles, movie choices · 8 Interpolation/extrapolation, climate change · 9 Orthogonal matrices + 3D graphics · 10 Discrete dynamical systems/Chaos Game · 11 Projections, eigenvectors, PCA, face recognition · 12 Eigenvalues + PageRank · 13 Social networks, clustering, eigenvalue · 14 SVD + image compression

**The prior run's numbering is confirmed correct.** This matters: the entire prior shortlist rests on it, and a wrong mapping would have invalidated everything. Two framings in the prior shortlist are worth noting as *rescuable*: #5's title is literally "**college** football team ranking" — the college angle is native to the assignment, not imposed on it.

The mandated 11-stage LA workflow and the 5+5 demo/viva split are unchanged from the prior spec.

## 1. Goal

Extend the shortlist into the **college / campus domain**, with PESU as the preferred lens, such that each new candidate:

1. maps to one of the 14 fixed Strang problems,
2. covers the mandated 11-stage workflow **honestly** — the prior run's central finding was that no single problem does, so this is the binding constraint, not dataset novelty,
3. uses **publicly fetchable** data, verified live with a real URL and a real row count,
4. survives the mandatory harden pass (PII, licensing, offline demo, academic integrity).

## 2. Acceptance criteria

- [x] Constraint re-read from the source PDF, not from the prior run's summary.
- [x] PESU's public data surface mapped, with the WordPress REST API identified as an open JSON surface.
- [x] Indian higher-education public data assessed (AISHE / NIRF / data.gov.in / UGC / NAAC), PESU's presence in each established.
- [x] College-domain open datasets found outside India, verified fetchable, with matrix shapes.
- [x] Whether PESU itself can be plotted on a public university-indicator matrix — established.
- [x] Hardening pass run before the shortlist was written; BLOCKER findings folded in.
- [x] Adversarial review run **after** the shortlist was written. It returned `blocked`. A second review ran after the first round of corrections and **also returned `blocked`**. Four of its findings were confirmed first-hand and corrected (NIRF collinearity; the Jordan-block identity; **and — this time — the identity I used to replace the first one, which was also false**; the vacuous "remove redundancy" stage). R1 was **withdrawn** after NIRF's published weights were shown to make its least-squares core circular. The PESU fee finding was **rejected** — `pes.edu/fee/` states INR 5,70,000/Anum verbatim (the 5,50,000 was last year's published figure, not a fabrication).
- [ ] **A third review of the second-round corrections has not been run.** The two blocking defects in the second review are now fixed, but that fix is unverified by a fresh node. Treat stage 7 as **not yet green**.
- [x] Every recommended dataset carries a URL, a licence position, and an offline-snapshot plan.

## 3. Out of scope

- Writing code, downloading datasets, or building the pipeline. That is stage 4 of a later run.
- Re-litigating the prior run's F1 (IPL). **It stands, and it is not beaten.** The first draft of the shortlist claimed R1 beat it on pipeline integrity; adversarial review showed that rested on a false collinearity claim, and the claim is withdrawn. F1 and R1 are now scored the same (~7–8 CORE). R1's advantage is that it produces a *finding* rather than a method. This run adds college-domain options; it does not overturn the incumbent.
- Any collection of PESU **internal** data (ERP, attendance, marks, timetables). Not available, not sought, and not appropriate.

## 4. Findings — the three that changed the answer

**F-A. Saturation is a property of the demo, not the mathematics.** The prior run killed #11 (PCA + face recognition) as "the most-attempted project in this book". True of the demo, false of the method. The mandated math is PCA, and PCA on university indicator profiles is untouched. Same rescue it applied to SVD-on-air-quality (F3), applied to a much larger matrix.

**F-B. REVERSED BY ADVERSARIAL REVIEW — do not rely on this.** The first draft of this spec claimed that re-framing #5 onto NIRF's 5-column indicator matrix gives *better* pipeline integrity than the prior run's incumbent (F1 = IPL). That claim was built on the assertion that NIRF's five indicators are strongly collinear, making the null space ~4-dimensional. **This was false.** Measured on 200 real NIRF 2022 Engineering rows: `rank(X_c) = 5`, `nullity(X_c) = 0`, condition number 4.89, max off-diagonal correlation 0.769. The indicators are moderately correlated, not collinear, and R1 scores ~7–8 CORE — the same as F1, not better. The residual claim that made it sound strong was substituted with a *verified* one: `nullity(X_cᵀ) = 195`, i.e. 200 universities occupy a 5-dimensional space, and the leading singular value σ₁ = 385.0 against σ₂ = 133.5 gives a measurable 2.9× "general excellence" axis. **The corrected argument is honest and still viable; the original superlative is withdrawn.**

**F-C. PESU's own website is the wrong place to find a PESU project.** The genuinely large, clean, licence-safe PESU dataset is *bibliometric* — OpenAlex `I196608512`, 8,442 works, 15 years, CC0, no API key. The admin data PESU publishes (intake ~40 programs, fee ~40 programs) is too small to carry any Strang problem, and the one large table on the site (565 named staff) is personal data. So "make it a PESU project" is best served by using PESU *as a case study inside* a national analysis, not by mining PESU's own pages for the dataset.

**F-B. R1 IS WITHDRAWN — do not rely on any part of the first draft of this claim.** The first draft claimed re-framing #5 onto NIRF's 5-column indicator matrix gives *better* pipeline integrity than F1. That rested on an unmeasured assertion that NIRF's five indicators are strongly collinear. **False:** on 200 parsed rows `rank(X_c) = 5`, `nullity(X_c) = 0`, condition number 4.89, max off-diagonal correlation 0.769. Worse, R1's premise is **circular** — NIRF *publishes* its weights (Engineering 0.30/0.30/0.20/0.10/0.10), so least-squares recovers them by construction and the residual is rounding noise: 0.007 for PESU 2022, 0.006 for IIT Madras 2025. **R1 produces no finding and is withdrawn.** See F-G for the row-provenance caveat on the measurement itself.

**F-D. A second false claim in R3 — and my first correction of it was ALSO false.** The first draft asserted "the number of Jordan blocks equals the number of maximal chains." **False** (it is `nullity(A) = n − rank(A)`; the DAG 1→3, 2→3, 2→4 gives 2 blocks but 3 maximal paths). I then "corrected" it to "`nullity(A^k)` = number of blocks of size ≥ k", which is **also false**: `nullity(A^k) = Σ min(sᵢ, k)`, not `Σ 1[sᵢ ≥ k]`, so the two agree only at k = 1. The correct identity is the **first difference**: number of blocks of size exactly k is `nullity(A^k) − nullity(A^(k−1))`, with `nullity(A⁰) = 0`. Verified on `blocks=(3,1)` → 2, 1, 1. The nilpotence claim (`Aᵏ = 0` past the longest path) is **true** and kept. **Lesson: verify the replacement, not just the original.**

**F-G. The 200-row measurement has unexplained provenance.** NIRF publishes sub-scores only for the top 100 of each category, so 200 parsed rows from a single page means two scored blocks were pooled (Engineering and University), not 200 Engineering institutions. Which two was not verified. The rank and singular values are robust to this; the per-university reading is not.

**F-E. "College-oriented" is a stretch, and the spec should say so.** R1 and R2 analyse national university rankings; R3 uses Caltech's curriculum. That is higher-education statistics, not campus life. Campus-life data — attendance, timetables, mess, hostels, transport — is not public, which is the reason no candidate here is genuinely campus-scoped. Conceding this is better than implying coverage the data does not support.

## 5. Hardening constraints carried into the shortlist (from the stage-6 node)

These are binding on any candidate that gets recommended:

- **Demo must read a frozen committed snapshot only.** No live crawl at demo time. Provenance recorded per file: source URL, UTC fetch date, HTTP status, SHA-256, row count.
- **The QS World University Rankings GitHub mirror is excluded.** QS is a commercial product; a third-party mirror is not a licensed distribution channel. Substituted with NIRF (government-published) and OpenAlex (CC0).
- **No PII committed.** `staff.pes.edu` (565 named individuals with photos) and student-achievement news are excluded. The project needs numbers, not names.
- **The UIUC prerequisite CSV carries no licence** (`"license": null` in the GitHub API). Attribute and cite; do not commit the raw file.
- **The 4.5 GB Leiden dump is out of scope** for a 10-mark project. Use the per-indicator file or a documented sample.
- **NIRF has no robots.txt and no explicit reuse licence.** Public record, but attribute precisely (year, category, table URL, retrieval date) and rate-limit to ~1 req/s.
- **Academic-integrity disclosure is required**, and the student should get an informal nod from a faculty mentor before collecting. The repo stays private.

`pes.edu/robots.txt` disallows only `/wp-admin/`; `research.pes.edu/robots.txt` allows all non-admin paths. `nirfindia.org` and the PESU microsites return 404 for robots.txt. So nothing in scope is technically blocked — but robots-permitted is not the same as licensed, and the report should say so.

## 6. Assumption recorded

Carried forward unresolved from the prior run, because it can still invalidate everything: **is the student free to substitute the dataset and re-frame the real problem, as long as the LA workflow and the named problem are honoured, or must the book's exact task list be submitted?** The most conservative reading is assumed: the student may re-frame the dataset but must honour the named problem. Every candidate in the shortlist is written to satisfy the strict reading — the maths is Strang's maths, only the data is the student's.
