# 01 — Setup

## What this step is

Install the fixed stack and confirm the clone is complete. There is no install
step for the project itself: `pyproject.toml` declares **no build backend**, so
nothing is built or installed.

## Command

```bash
pip install numpy pandas matplotlib pytest
```

Python **3.11+** is required (`requires-python = ">=3.11"` in
`ipl-power-ranking/pyproject.toml`). Measured on Python 3.14.7.

## Verify the clone is complete

You should have, at the repository root:

- `ipl-power-ranking/` — the package (`src/iplranking/`, `scripts/`, `tests/`)
- `data/matches.csv` and `data/provenance.json` — the committed snapshot
- `ipl_json/` — the raw Cricsheet extraction (1,243 JSON files)
- `docs/`, `AGENTS.md`, `CLAUDE.md`

## What not to do

- Do not `pip install -e .` — there is no build backend, and doing so would
  make the test run need a network fetch.
- Do not expect `python -m iplranking` to work without help — `src/` is not on
  the path by default. Use the launcher (`scripts/run_demo.py`) instead; see
  [03](03-run-the-demo.md).
