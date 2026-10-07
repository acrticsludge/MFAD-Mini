# 05 — Run the tests

## What this step is

The test suite is the code gate. Every measured claim in the project is pinned
by a test instead of being stated in prose.

## Command

```bash
cd ipl-power-ranking
python -m pytest -q
```

Measured on 2026-10-07: **235 passed in about 71 s**. pytest finds the package
through `pythonpath = ["src"]` in `pyproject.toml`. `tests/conftest.py` adds
`src` to `sys.path` again as a fallback, so a bare `pytest` or a different
rootdir also works. It defines no fixtures; each test file builds its own.

Run one file or one test:

```bash
python -m pytest -q tests/test_structure.py
python -m pytest -q -k "offline or network"
```

## What each file pins

| File | Tests | Pins |
|------|------:|------|
| `test_canonicalisation.py` | 13 | The rename map is exactly the four documented pairs. 19 raw names become 15. The Rising Pune spelling drift is merged. Gujarat Lions/Titans, Deccan/Sunrisers and Pune Warriors/Rising Pune stay separate. The banned "Mumbai Indians reincarnation" claim is not implied |
| `test_data_invariants.py` | 35 | 1,243 rows, 1,218 with a winner, 25 without. 558 run-margin, 660 wicket-only, none with both. 16 Super Over, 9 no result, 23 D/L. 19 seasons, and season normalisation is load-bearing against the raw JSON. `parse_directory` agrees with the committed CSV. ISO dates, chronological order, unique IDs. Every provenance field is present and honest |
| `test_design_matrix.py` | 40 | `A`'s shape, row sums of zero, and the sign convention on specific matches (**see [10](10-known-issues.md): one of these tests pins a probable defect**). Row order. `games` sums to 1,116. Shapes, symmetry and non-negativity of `W`/`C`/`M`. `official_table` structure (2 points per win, sorted, no-winner matches excluded). `build_systems` is consistent |
| `test_structure.py` | 39 | Rank 14, nullity 1, singular values, the constant vector in the null space. Correctness of `rref` on small cases. The row basis is real rows of `A` and spans Row(A). Gram–Schmidt orthonormality, with re-orthogonalisation never worse. Power iteration converges, is deterministic and raises on non-convergence. `col_space_basis` is 558 × 15 with an outsider 15th column. `row_space_basis`, `col_projector`, and Moore–Penrose for `pinv` |
| `test_models.py` | 34 | The three LS routes agree (measured, not claimed), the centred `x` sums to zero, and the residual is orthogonal to Col(A). Colley shares are positive and sum to 1 and match `eigh`. Eigenvalues of `AᵀA` equal `σ²`. Frequency balancing makes `max|x|` worse. Ridge never improves R² and does not leave it unchanged. The held-out split is the last 3 seasons, with RMSE worse than the mean. Everything is deterministic |
| `test_diagnostics.py` | 26 | Both R² values to 4 decimals. `r_squared` cannot be called without an explicit `centred=`. Standard errors and degrees of freedom. No coefficient reaches 2σ. Spearman for all three pairs, and Massey–Colley exactly 0. Tied ranks. The official points are joined by team name, not row order. Winner accuracy. Summary/comparison tables reject misaligned input |
| `test_demo.py` | 46 | `main` returns 0, and non-zero when a stage fails. The offline block holds until released, and a network import during the run exits 1. 13 valid PNGs. No ESC bytes in piped output. The report inlines every figure, has no external resource, covers every stage, reports both R² values, the exclusions, the licence position, the refuted hypothesis, the blocker and the checklist. Files and terminal output are byte-identical across runs. Banners are in ascending order. The launcher is tested as a subprocess with no `PYTHONPATH`, from two working directories, with a negative control. A truncated snapshot is refused. Retracted phrases are absent |

`def test_` functions add up to 233. The extra 2 come from parametrisation.

## Hard rules

- Never make a test pass by weakening an assertion, skipping it or deleting
  it.
- If a number is corrected, the test **and** the narration must change
  together: the terminal, the report and the README.
- A test that pins wrong behaviour is a defect to fix on purpose, with the
  owner, not quietly. The sign-convention test in
  [10](10-known-issues.md) is the open example.
