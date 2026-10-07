# 08 — Module map

Which job each file does, and the public functions you will meet.

## Entry points

| File | Role |
|------|------|
| `ipl-power-ranking/scripts/run_demo.py` | Launcher. Finds `src/` from its own `__file__`, checks that `src/iplranking/__init__.py` exists (exits 2 if not), then calls `iplranking.__main__.main()` |
| `src/iplranking/__main__.py` | CLI. argparse (`--offline`, `--figures-only`, `--width`, `--no-report`), exit codes 0/1/2/3, offline install/release, error mapping. Has a path bootstrap so it can also run as a plain script |
| `ipl-power-ranking/scripts/build_snapshot.py` | Build time only: `ipl_json/` → `data/matches.csv` + `data/provenance.json` |

## The package: `src/iplranking/`

| Module | Role | Main names |
|--------|------|-----------|
| `__init__.py` | Package docstring and `__version__ = "0.1.0"` | |
| `canon.py` | Turns 19 raw names into 15 franchises using exactly four merge pairs. Gujarat Lions/Titans and Deccan/Sunrisers are deliberately left unmerged | `canonical`, `canonical_teams` |
| `parse.py` | Build-time parser for `ipl_json/*.json`. Not on the demo path | `parse_directory`, `COLUMNS`, `SnapshotFieldError`, `_normalise_season` |
| `data.py` | The demo's only data input. Loads and validates the CSV (column check, 1,243-row truncation guard) and builds every matrix | `load_matches`, `teams`, `design_matrix` → `(A, b, teams)`, `colley_matrices` → `(W, C, M)`, `games_played`, `official_table`, `build_systems` → `Systems`, `repo_root`, `data_dir`, `matches_csv` |
| `linalg_kit.py` | Hand-written linear algebra, because the examiner reads the method | `rref` (Gauss–Jordan, partial pivoting, pivot rows), `null_space`, `row_basis`, `gram_schmidt` (classical / re-orthogonalised, with off-orthogonality trace), `power_iteration`, `col_space_basis` (thin QR), `row_space_basis`, `pinv`, `col_projector` |
| `models.py` | The two models and the variants that do not rescue them | `massey` → `MasseyFit` (three routes, `max_route_diff`, `cond_constrained`), `colley` → `ColleyFit` (`r`, `lam1`, `lam2`, `iterations`, `all_positive`), `frequency_balanced` → `BalancedFit`, `ridge`, `held_out_fit` → `HeldOutResult`, `svd_of_A` → `SvdResult` |
| `diagnostics.py` | Checks whether the fit is any good | `r_squared(b, pred, *, centred)` (keyword required), `intercept_model`, `noise_vs_signal`, `standard_errors`, `spearman`, `average_ranks`, `winner_accuracy`, `team1_won_flags`, `team1_win_share`, `team1_share_by_season`, `majority_class_accuracy`, `official_comparison`, `summary_table` |
| `console.py` | Terminal renderer; computes nothing. Supports ANSI and ASCII, with Windows VT enablement | `init`, `set_width`, `stage` (context manager), `formula`, `step`, `measured`, `table`, `mat`, `vec`, `vec_bars`, `Progress`, `sparkline`, `converge`, `verdict`, `note`, `warn`, `ok`, `bad`, `excluded`, `figure`, `timeline` |
| `demo.py` | The narration and the offline guard | `STAGES`, `run_demo` → `DemoResult`, `_stage_1` … `_stage_11`, `assert_offline`, `release_offline`, `NetworkBlockedError`, `provenance_record`, `header`, `closing` |
| `figures.py` | One PNG per stage (13 in total). Plots numbers it is given | `FIGURE_NAMES`, `f01_data_funnel` … `f13_divergence`, `figure_dir`, `report_dir` |
| `report.py` | `report/report.html` built with the stdlib, with base64 images | `build_report` |

## Data flow

```
ipl_json/*.json ──parse.py + canon.py──► data/matches.csv + provenance.json   (build time)
                                                │
data/matches.csv ──data.build_systems()──► Systems(A, b, W, C, M, teams, games, official)
                                                │
             models.py / diagnostics.py / linalg_kit.py   (computation)
                                                │
             demo._stage_1 … _stage_11 ──► console.py (terminal) + figures.py (PNGs)
                                                │
                                         report.py ──► report/report.html
```

## Other files

| File | Role |
|------|------|
| `tests/conftest.py` | Puts `src` on `sys.path` as a fallback. Defines no fixtures |
| `tests/test_*.py` | Seven files, 235 tests. See [05](05-run-the-tests.md) |
| `ipl-power-ranking/pyproject.toml` | The fixed dependency stack, `pythonpath = ["src"]`, `testpaths = ["tests"]`, no build backend, `requires-python = ">=3.11"` |
| `ipl-power-ranking/probe1.py` … `probe4.py` | **Untracked scratch scripts**, not part of the demo or the tests. See [10](10-known-issues.md) |
