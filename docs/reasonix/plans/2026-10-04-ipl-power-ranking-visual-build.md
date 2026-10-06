# Plan — visual end-to-end build of the IPL power ranking

- **Slug:** `2026-10-04-ipl-power-ranking-visual-build`
- **Spec:** `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md`
- **Basis:** stage-2 measurements. Every target number in this plan is measured, so a red test means the code is wrong.

## 0. Ground rules

- **Sequential by data dependency.** The design matrix must exist before anything linear-algebra runs.
- **Tests first for each slice.** The invariant tests pin the measured facts so nothing below can drift.
- **The visual renderer is a deliverable, not decoration.** It carries the examiner's reading of the machinery, per `CLAUDE.md` §10.
- **Hand-written linear algebra where the guidelines name it** (RREF, Gram–Schmidt, power iteration) so the maths is legible; NumPy where the book uses it (`lstsq`, `svd`, `eigh`).

## 1. Layout

```text
ipl-power-ranking/
  pyproject.toml
  src/iplranking/
    __init__.py
    canon.py          # the four-pair rename map, n=15
    parse.py          # ipl_json/*.json -> tidy DataFrame   (build-time only)
    data.py           # load committed CSV, build A, b, W, C   (offline)
    linalg_kit.py     # RREF, Gram-Schmidt, null space, row basis   (hand-written)
    models.py         # Massey 3 routes, Colley power iteration, balancing, ridge
    diagnostics.py    # R2 both denominators, SEs, t-stats, held-out, Spearman, official table
    console.py        # ANSI visual renderer: banners, math panels, bars, sparklines
    figures.py        # one figure per mandated stage
    report.py         # self-contained report/report.html
    demo.py           # orchestrates all 11 stages; python -m iplranking.demo
  scripts/
    build_snapshot.py # one-shot: ipl_json -> data/matches.csv + data/provenance.json
  tests/
    test_data_invariants.py
    test_canonicalisation.py
    test_design_matrix.py
    test_structure.py
    test_models.py
    test_diagnostics.py
data/matches.csv        data/provenance.json
figures/                report/report.html
```

`scripts/build_snapshot.py` is **not** on the demo path. The demo reads `data/matches.csv` and nothing else, so it runs offline from a clean clone.

## 2. Ordered slices

| # | Slice | Files | Gate |
|---|---|---|---|
| S1 | Scaffold, `.gitignore`, baseline commit, `pyproject.toml` | `.gitignore`, `pyproject.toml` | `git log` non-empty; `pytest --version` ok |
| S2 | `canon.py` + `parse.py` + `build_snapshot.py` → CSV + provenance | `canon.py`, `parse.py`, `build_snapshot.py`, `data/*` | counts match §2 of spec |
| S3 | Invariant tests | `tests/test_data_invariants.py`, `test_canonicalisation.py` | `pytest -q` green |
| S4 | `data.py` — `A`, `b`, `W`, `C`, official table | `data.py`, `tests/test_design_matrix.py` | shapes + signs asserted at the build boundary |
| S5 | `linalg_kit.py` — RREF, null space, row basis, Gram–Schmidt | `linalg_kit.py`, `tests/test_structure.py` | `rank=14`, `nullity=1`, orthonormal to 1e-10 |
| S6 | `models.py` — 3 least-squares routes, Colley, balancing, ridge | `models.py`, `tests/test_models.py` | three routes agree to 1e-10; Colley positive |
| S7 | `diagnostics.py` — R² both denominators, SE, t-stat, held-out, Spearman | `diagnostics.py`, `tests/test_diagnostics.py` | §4 numbers pinned |
| S8 | `console.py` — the visual renderer | `console.py` | renders on a non-TTY pipe without crashing |
| S9 | `figures.py` + `demo.py` — all 11 stages visual | `figures.py`, `demo.py` | 11 figures; two runs byte-identical |
| S10 | `report.py` — self-contained HTML | `report.py`, `report/report.html` | opens with no network |
| S11 | Docs: README, INDEX row, AGENTS.md corrections, report, handoff | `README.md`, `docs/**`, `AGENTS.md` | docs describe what exists |
| S12 | Full gate, harden, review | — | `pytest -q` green, review `ship` |

## 3. The 11 mandated stages → modules and figures

Order per `AGENTS.md` §5, re-verified 2026-10-02 against page 2 of the guidelines PDF.

| # | Stage | Module | Figure |
|---|---|---|---|
| 1 | Real-world data | `parse`, `data` | `01-data.png` — the 1,243 → 558/660 split |
| 2 | Matrix representation | `data` | `02-design-matrix.png` — `A` as a heatmap with `±1` |
| 3 | Matrix simplification | `linalg_kit.rref` | `03-rref.png` — RREF, singular row exposed |
| 4 | Structure of the space | `linalg_kit` | `04-structure.png` — singular values, null direction |
| 5 | Remove redundancy | `linalg_kit.row_basis` | `05-redundancy.png` — 14 of 558 rows highlighted |
| 6 | Orthogonalization | `linalg_kit.gram_schmidt` | `06-qr.png` — `Col(A)` vs `Row(A)`, two spaces |
| 7 | Projection | `models` | `07-projection.png` — `b`, its projection, the residual |
| 8 | Prediction / approximation | `models`, `diagnostics` | `08-least-squares.png` — fitted vs actual, `R²` |
| 9 | Pattern discovery | `models.colley` | `09-eigen.png` — power-iteration convergence + spectrum |
| 10 | System simplification | `models.svd` | `10-diagonalisation.png` — `AᵀA = VΣ²Vᵀ` |
| 11 | Final application output | `demo`, `figures` | `11-ranking.png`, `12-findings.png`, `13-divergence.png` |

## 4. What each stage shows in the terminal

The owner's requirement is that each step shows *what it is calculating* and *which principle it uses*. Per stage the renderer emits:

1. A stage banner: number, mandated name, the linear-algebra principle in one line.
2. The formula, typeset in ASCII.
3. **Live computation** — what is actually running:
   - stage 3: elimination step counter with a progress bar
   - stage 5: rows tested / rows kept as a running fraction
   - stage 6: Gram–Schmidt orthogonality residual shrinking per step
   - stage 7: projection residual norm as `b` is decomposed
   - stage 8: three routes converging to the same `x`, per-team bars with `±se` whiskers
   - stage 9: power-iteration convergence sparkline, iterations to tolerance
   - stage 10: singular-value spectrum plotted as it is computed
4. The numbers, printed.
5. A verdict line in plain English.

## 5. Determinism

Fixed team ordering (alphabetical) everywhere iteration order could change a result; no stochastic step anywhere; Matplotlib `Agg` backend and a fixed figure DPI; two runs compared with a hash of every PNG.

## 6. Not in this plan

- Residual-SVD stretch variant — held (`AGENTS.md` §10).
- Recency weighting — held (spec D4).
- Wicket→run conversion — refused on integrity grounds.
- Any dependency beyond NumPy, Pandas, Matplotlib, pytest. The HTML report is assembled by string formatting; no template engine.