# Dispatch — S2/S3/S4: data layer, design matrices, invariant tests

**Read first, in this order:** `AGENTS.md` (binding), `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` (§0, §2, §3, §6), `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` (§1, §2, §3).

**Blast radius — you may create/modify ONLY these:**
`ipl-power-ranking/pyproject.toml`, `ipl-power-ranking/src/iplranking/__init__.py`, `ipl-power-ranking/src/iplranking/canon.py`, `ipl-power-ranking/src/iplranking/parse.py`, `ipl-power-ranking/src/iplranking/data.py`, `ipl-power-ranking/scripts/build_snapshot.py`, `ipl-power-ranking/tests/conftest.py`, `ipl-power-ranking/tests/test_data_invariants.py`, `ipl-power-ranking/tests/test_canonicalisation.py`, `ipl-power-ranking/tests/test_design_matrix.py`, `data/matches.csv`, `data/provenance.json`.

Touching anything else is a breach — stop and report. Do NOT run `git add`, `git commit`, or `git push`. Do NOT edit any file under `docs/`. Do NOT modify `console.py`, `figures.py`, `report.py`, `demo.py`, `linalg_kit.py`, `models.py`, `diagnostics.py` — other nodes own those.

**Environment:** system Python 3.14.7 already has numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.2, pytest 9.1.1. Do NOT create a venv, do NOT pip install anything. Work with the system interpreter.

**Run tests from** `C:\Anubhav\MFAD-Mini\ipl-power-ranking` with `python -m pytest -q`.

## What to build

### 1. `canon.py`
- `CANONICAL_MAP: dict[str, str]` with **exactly four** rename pairs, per `AGENTS.md` §7:
  `Delhi Daredevils`/`Delhi Capitals`→`Delhi Capitals`; `Kings XI Punjab`/`Punjab Kings`→`Punjab Kings`; `Royal Challengers Bangalore`/`Royal Challengers Bengaluru`→`Royal Challengers Bengaluru`; `Rising Pune Supergiants`/`Rising Pune Supergiant`→`Rising Pune Supergiant`.
- **Do NOT** merge `Gujarat Lions`→`Gujarat Titans` or `Deccan Chargers`→`Sunrisers Hyderabad`.
- `canonical(name: str) -> str`, and `canonical_teams(teams: Iterable[str]) -> list[str]` (sorted, deduplicated) giving **n = 15**.
- A module-level docstring stating that `n = 15` and why each deliberate non-merge exists.

### 2. `parse.py` — reads `ipl_json/*.json` (build-time only, never on the demo path)
- Read all 1,243 files. Per `AGENTS.md` §7 the winner is at `info.outcome.winner` — `info["winner"]` raises `KeyError` in every file. Margin at `info.outcome.by.runs` / `.by.wickets`. `method` at `info.outcome.method`.
- `info["season"]`: coerce to `str` before use. **Measured note:** on this snapshot it is always already a `str`, so the naive count also returns 19 — normalise anyway, but do not claim the "24" figure anywhere.
- Output a tidy `pandas.DataFrame` with exactly these columns, in this order:
  `match_id, date, season, team1, team2, winner, margin_runs, margin_wickets, method, is_super_over, canonical_team1, canonical_team2`
- `margin_runs` and `margin_wickets` must be **nullable** (`Int64` or float with NaN) — 558 have runs, 660 do not. Never let a missing margin silently become 0.
- `is_super_over` from `info.outcome.eliminator` (16 rows).
- Expose `parse_directory(dir) -> DataFrame` and `parse_file(path) -> dict`.

### 3. `scripts/build_snapshot.py`
- One-shot. `python scripts/build_snapshot.py` writes `data/matches.csv` (repo root) and `data/provenance.json`.
- `provenance.json` fields, all required by `AGENTS.md` §7: `source_url` (`https://cricsheet.org/downloads/ipl_json.zip`), `cricsheet_version` (`"1.2.0"`), `utc_fetch_date`, `http_status`, `sha256`, `sha256_covers`, `row_count`, `file_count`, `licence`.
- **CRITICAL HONESTY REQUIREMENT:** the downloaded archive `ipl_json.zip` is **not retained on this machine** — the extracted files are. You must **not invent a hash**. Compute the SHA-256 of a **deterministic manifest** of the extracted file set instead: sort the 1,243 relative filenames, and hash the concatenation of `f"{relpath}:{size}"` lines in UTF-8, recording in `sha256_covers` exactly that string, e.g. `"deterministic manifest of extracted files: sorted '<relpath>:<size>' lines"`. Put the explanatory note in a `notes` field too. Set `http_status` to the string `"not recorded (archive not retained on this machine)"` — do **not** put 200, because no HTTP fetch happened in this run.
- `licence`: the honest sentence — no licence statement for the match data was found on cricsheet.org; `/licence/` returns 404; only the *Register* dataset carries an explicit ODC-BY statement; third-party sites assert ODC-BY 1.0 but that is not the primary source. **Do not assert ODC-BY as fact for match data.**
- Make it deterministic: same input → byte-identical CSV.

### 4. `data.py` — the demo's only data entry point
Reads **only** `data/matches.csv`. Never touches the network, never reads `ipl_json/`. Resolve the repo root robustly from `__file__` (the package lives at `ipl-power-ranking/src/iplranking/`, so repo root is three parents up). Allow an override via an optional parameter, not an env var.
- `load_matches() -> pd.DataFrame`
- `teams() -> list[str]` (n = 15, **alphabetically sorted** for determinism)
- `design_matrix() -> tuple[np.ndarray, np.ndarray, list[str]]` → `(A, b, teams)`
  - `A` shape **(558, 15)**, float. `A[i,j] = +1` if team `j` won match `i`, `−1` if it lost. Row `i` is the run-margin match `i`, in the CSV's row order.
  - `b[i]` = **signed** run margin: `+margin_runs` if `team1` won, `−margin_runs` if `team2` won.
  - Only rows with a non-null `margin_runs` and a `winner`.
  - **Assert the shape and `A.sum(axis=1) == 0` at the boundary where `A` is built.** Raise with the actual numbers in the message.
- `colley_matrices() -> tuple[np.ndarray, np.ndarray, np.ndarray]` → `(W, C, M)` over **all 1,218** winner matches:
  - `W[i,j]` = matches team `i` beat team `j`. `W.sum() == 1218`.
  - `C[i,j]` = matches played between `i` and `j`, `C[i,i] == 0`, symmetric.
  - `M = W + W.T + C`, entrywise non-negative.
- `games_played() -> np.ndarray` — games per team **within the 558 run-margin subset** (this is what the frequency weighting uses).
- `official_table() -> pd.DataFrame` — all-time, **2 points per win**, one row per canonical team, columns `team, wins, points`, sorted by points desc then team asc. `points.sum() == 2436`. Document in the docstring that this is the **all-19-seasons** table, 2 points per win, ties/no-results excluded because they have no `winner` — and that the demo says so out loud.
- `build_systems() -> Systems` — a small frozen dataclass holding `matches, A, b, W, C, M, teams, games, official` so the demo loads once.

### 5. Tests — these are the gate, write them strictly
`tests/conftest.py`: add `src` to `sys.path` (or rely on `pyproject.toml`'s `pythonpath` setting — your choice, must work with a bare `python -m pytest -q` from `ipl-power-ranking/`).

`tests/test_canonicalisation.py` — assert:
- the map has exactly 4 merge pairs
- `canonical_teams` yields **15**
- `Rising Pune Supergiant` and `Rising Pune Supergiants` canonicalise to the same string (the documented trap)
- `Gujarat Lions != Gujarat Titans` and `Deccan Chargers != Sunrisers Hyderabad` (the deliberate non-merges must be protected by a test, or a future agent will "tidy" them and change `n`)

`tests/test_data_invariants.py` — assert, from the committed CSV:
`1243` rows, `1218` with a winner, `558` run-margin, `660` wicket-only, `25` no-winner, `16` super-over, `9` `no result`, `23` D/L, `19` raw distinct team strings, `19` seasons after normalisation, `15` canonical teams. Also assert `provenance.json` parses, its `row_count` equals the CSV row count, and its `sha256` is a 64-hex-char string.

`tests/test_design_matrix.py` — assert `A.shape == (558, 15)`, `A` values ∈ {−1, +1}, `np.allclose(A.sum(axis=1), 0)`, `b` has **no zero entries** (margin is never 0 when present — verify this and if it is false, say so loudly rather than deleting the assertion), `|b|` matches `margin_runs` exactly, sign convention correct on a hand-checked example, `W.sum() == 1218`, `C` symmetric with zero diagonal, `M >= 0`, `official_table().points.sum() == 2436`, and `games_played().sum() == 1116` (2 × 558).

### 6. `pyproject.toml`
Minimal, no build backend requirement that needs network. Include `[tool.pytest.ini_options] pythonpath = ["src"]` and `testpaths = ["tests"]`. Project name `iplranking`, `requires-python = ">=3.11"`.

## Rules
- **NEVER make a test pass by editing, skipping, deleting or weakening an assertion.** If a measured number disagrees with the spec, STOP and report the discrepancy with both values. That is the single most important rule in this dispatch — the repository's whole history is two runs lost to unmeasured numbers.
- Derive every count from the data. No hard-coded dataset constants in `data.py`/`parse.py` — only in the **tests**, where pinning them is the entire point.
- Keep the maths legible: explicit shapes in comments, named variables, no magic numbers.
- Type annotations where informative. Docstrings that state what the function computes and any measured figure it depends on.

## Report back
1. The exact command you ran and its verbatim final line.
2. Any measured number that **disagreed** with the spec, with both values.
3. Anything you could not do and why.
4. Confirmation that you touched no file outside the blast radius.