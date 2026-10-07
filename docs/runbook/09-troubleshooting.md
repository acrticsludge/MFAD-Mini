# 09 — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No module named iplranking` | You ran `python -m iplranking`, and `src/` is not on the path | Use `python ipl-power-ranking/scripts/run_demo.py`, or set `PYTHONPATH=src` from `ipl-power-ranking/` |
| `run_demo.py: no uninstalled package at …`, exit 2 | The launcher was moved, or the package directory is missing | Keep the layout `<root>/ipl-power-ranking/scripts/run_demo.py` and `<root>/ipl-power-ranking/src/iplranking/` |
| `cannot start: committed snapshot not found …`, exit 2 | `data/matches.csv` is missing | `python ipl-power-ranking/scripts/build_snapshot.py` |
| `cannot start: … has N rows; the committed snapshot has 1243`, exit 2 | The CSV is truncated or was built from a different archive | Rebuild the snapshot, then check `row_count` in `data/provenance.json` |
| `cannot start: … missing required column(s)`, exit 2 | The CSV schema is out of date | Rebuild the snapshot |
| `… was built with a different canonicalisation map …` | `canon.py` was edited but the CSV was not rebuilt | Rebuild the snapshot, or undo the map change. Changing the map changes `n` and invalidates every figure (`AGENTS.md` §7) |
| `offline violation: …`, exit 1 | Code on the demo path imported a network module or opened a socket | Remove the fetch. The demo must read only the CSV |
| Escape codes (`←[1m`) in a Windows console | The console has no VT support | Harmless. Piped output is plain ASCII. Use Windows Terminal for colour |
| Figures differ between runs | Something non-deterministic was added (timestamp, random draw, environment path, unpinned metadata) | `python -m pytest -q tests/test_demo.py -k byte_identical` |
| `SnapshotFieldError` during the build | A raw JSON file is missing a required field | The message names the file and the field. Check that `ipl_json/` is complete (1,243 files) |
| Tests slow (~70 s) | `test_demo.py` runs the full demo several times, including as subprocesses | Expected. Use `-k` to run a subset |
