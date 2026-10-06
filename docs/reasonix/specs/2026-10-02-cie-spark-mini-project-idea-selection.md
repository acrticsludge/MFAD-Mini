# Spec — CIE SPARK mini-project idea selection

> **SUPERSEDED IN PART — the stage list in this document is wrong. Do not use it for the stage order.**
>
> It gives **Structure of the Space = 2** and **Matrix Simplification = 3**, and calls that "verbatim order from the guidelines diagram". The mandate is the other way round: **Matrix Simplification (3) before Structure of the Space (4)** — re-verified twice against page 2 of `UE25MA242A_MFAD -Mini-Project Guidelines.pdf` on 2026-10-02. The "verbatim" claim was never checked against the source, and the transposed order was copied into `AGENTS.md`, the F1 spec and the F1 plan for two full runs before adversarial review caught it.
>
> **Authoritative:** `docs/reasonix/INDEX.md` (lessons) and `docs/reasonix/specs/2026-10-02-ipl-power-ranking-f1.md` §5 (the corrected 11-stage table).
>
> Everything else below is **retained unchanged as history** — this document is not to be rewritten, because the fact that the error happened is part of the record.

- **Slug:** 2026-10-02-cie-spark-mini-project-idea-selection
- **Course:** UE25MA242A — Mathematical Foundation for AI & Data Science, PES University, CSE
- **Stage run:** stage 0 ORIENT complete. Stages 1-3 in progress.
- **Declared risk:** low. Read-only research so far. Floor raised to `medium` by the plugin on file observation.
- **Adapter:** generic [fallback] — no project rules, run unguarded. `docsRoot` not declared, so documentation is not gate-enforced here; it is written anyway because the next session needs it.

## 0. The three source documents (what they actually say)

| Document | What it establishes |
|---|---|
| `UE25MA242A -MFAD Mini-project Problem Statements.pdf` | **14 fixed problems.** The student may choose among them, not invent one. All 14 are verbatim Gilbert Strang, *Linear Algebra and Its Applications* projects-book chapters. |
| `UE25MA242A_MFAD -Mini-Project Guidelines.pdf` | **A mandated 11-stage LA workflow** and a marking scheme: 5 marks demo + 5 marks viva. Not doing derivations, proofs or manual calculation. |
| `LA-Projects-Book-Python_full.pdf` | The 187-page Strang projects book itself — lab-manual style, with prescribed variable names (`C`, `D`, `ImJPG`, …) per project. This is the *reference*, not the boundary. |

### The mandated 11-stage workflow (verbatim order from the guidelines diagram)

```
REAL-WORLD DATA
  1  Matrix Representation          (Systems of Linear Equations / Linear Transformations)
  2  Structure of the Space        (Vector Spaces → Subspaces → Basis → Rank & Nullity)
  3  Matrix Simplification         (Gaussian Elimination / RREF / LU Decomposition)
  4  Remove Redundancy             (Linear Independence → Basis Selection)
  5  Orthogonalization             (Orthogonal Vectors → Gram–Schmidt → Orthogonal Bases)
  6  Projection                    (Orthogonal Projections → Projection onto Subspaces)
  7  Prediction / Approximation    (Least Squares Solution)
  8  Pattern Discovery             (Eigenvalues & Eigenvectors)
  9  System Simplification         (Diagonalization of Matrix / Symmetric Matrix)
 10  Final Application Output      (Predictions / Compression / Trends / Noise Reduction / Modeling)
```

Demo outputs the examiner explicitly expects to see explained: matrix representation of data; RREF / matrix simplification; **basis and orthogonal basis formation**; projection-based prediction; least squares estimation; eigenvalue/eigenvector analysis; final reduced model or application output.

## 1. Goal

Choose one of the 14 assigned problems and fix a real-world data framing for it such that:

1. It solves a **genuine problem**, not a tutorial exercise.
2. It is **unlike the obvious pick** — the uniqueness of the classmate who does the same thing should be close to zero.
3. It builds **fast** on a clean stack the student already can drive.
4. It **covers the mandated LA workflow honestly**, because that is what both halves of the marking scheme interrogate.

## 2. Acceptance criteria for the decision

- [x] All 14 problems read from the source documents, not from memory.
- [x] The constraint set extracted: fixed problem list, mandated workflow, 10-mark split, viva style.
- [x] Per-problem dataset feasibility assessed with **URLs verified live**, not invented.
- [x] Pipeline integrity assessed stage-by-stage per candidate — which stages are load-bearing vs bolted on.
- [x] Stack fixed and minimal.
- [ ] A single winner chosen by the student, with the alternative held in reserve.
- [ ] Confirmation of the one constraint that can invalidate everything: **is the student required to submit the book's prescribed tasks, or free to re-frame with their own dataset?**

## 3. Out of scope for this run

- Writing any project code. Stage 4 IMPLEMENT is a separate, later run.
- Downloading and preprocessing the chosen dataset.
- Report writing, viva rehearsal, PPT/demo script.
- Any change to the student's existing coursework in `DSA/`, `CN/`, `Web Dev Projects/`.

## 4. Findings so far — the central tension

Three independent research passes produced a genuine conflict, and resolving it is the job.

- **Novelty pass** says the saturated picks are problems **2, 3, 6, 11, 12, 14** — image filters, PCA-on-faces, PageRank, SVD-on-images. Problems **1 and 4** are too trivial to carry a "real problem". Leaving **5, 8, 9, 13** (and defensibly 7, 10) as the live field.
- **Pipeline pass** scored every mandated stage as CORE / LIGHT / FAKE for each candidate, and found **no single Strang problem exercises all 11 stages honestly**:

| Candidate | Strang # | CORE stages | Missing / bolted |
|---|---|---|---|
| Sports ranking | 5 | 7 | Gram–Schmidt, eigen, diagonalization |
| Climate fit | 8 | 7 | eigen, diagonalization |
| Movie/choice rec | 7 | 6 | Gaussian elimination, basis selection (light) |
| Social networks | 13 | 4 | Gaussian elimination, Gram–Schmidt, projection, least squares |
| Chaos game | 10 | 4 | Gram–Schmidt, projection, least squares, elimination |
| 3D graphics | 9 | 4 | elimination, least squares, diagonalization |

**The tension:** the problems with the best uniqueness have the *worst* LA-pipeline integrity, and the problems with the best pipeline integrity are either saturated or land on US/EU datasets every classmate will also reach for.

**The resolution being carried into the shortlist:** uniqueness must come from the **dataset and framing**, not the mathematics — the math is fixed by the assignment. So the target is a candidate that sits high on pipeline integrity *and* is carried by a dataset no classmate would think to touch.

## 5. Assumption recorded (per clarify-first, bound the interview)

The most conservative reading is assumed while awaiting the student: **the student is free to substitute the dataset and re-frame the real problem, as long as the LA workflow and the named problem are honoured.** If the course in fact mandates the book's exact task list, the shortlist collapses to problems 5, 8 and 7 on default datasets and Indian data must be dropped. This is recorded as an open blocker, not resolved.