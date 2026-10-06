# Dispatch — fix: the demo must run from a clean shell with zero install

## The defect, measured by the orchestrator 2026-10-05

```
> cd ipl-power-ranking
> python -m iplranking --offline
No module named iplranking
```

The demo itself is complete and correct — with `PYTHONPATH=src` it runs all 11 narrated stages, writes 13 PNGs and a 2.35 MB self-contained `report/report.html`. **Do not rewrite `demo.py`.** The only problem is the entry point.

**Cause:** `pyproject.toml` deliberately declares **no build backend** so that nothing has to be installed and nothing needs the network. That is a good decision under `AGENTS.md` §8 and the offline rule — **keep it**. But pytest finds the package via `pythonpath = ["src"]`, and `python -m` does not read `pyproject.toml`. So the module is unreachable outside pytest.

`AGENTS.md` §7: *"A demo that fails because a website is down costs 5 marks."* A demo that needs an undocumented environment variable costs the same.

## Blast radius — create/modify ONLY these three files

1. **`ipl-power-ranking/scripts/run_demo.py`** — **create it.** A zero-install launcher.
2. **`ipl-power-ranking/tests/test_demo.py`** — add tests for it.
3. **`ipl-power-ranking/README.md`** — create it (short; see below).

Do NOT modify `pyproject.toml`, `demo.py`, `figures.py`, `report.py`, `console.py`, `data.py`, `models.py`, `diagnostics.py`, `linalg_kit.py`, `canon.py`, `parse.py`, or any existing test file. Do not run `git add`/`commit`/`push`. Do not edit anything under `docs/`.

Environment: Python 3.14.7, numpy/pandas/matplotlib/pytest installed, no SciPy. No venv, no pip install, no network.

## 1. `scripts/run_demo.py`

Must work from **any** working directory, with **no environment variable set and nothing installed**:

```python
#!/usr/bin/env python3
"""Run the IPL power ranking demo with no install step and no network.

`pyproject.toml` declares no build backend on purpose (`AGENTS.md` §8), so the
package is not installed and `python -m iplranking` cannot find it. pytest finds
it via `pythonpath = ["src"]`; `python -m` does not read pyproject. This
launcher puts `src` on `sys.path` itself and hands over to the same entry point.
"""
```

Resolve `src` **from `__file__`**, never from `os.getcwd()`, then `from iplranking.demo import main` and `raise SystemExit(main())`. Forward all CLI args unchanged, so `python scripts/run_demo.py --offline` and `--width 88` both work. Handle being run with no arguments. Print nothing extra of its own — the demo's own output is the deliverable and must stay byte-identical to `python -m iplranking`.

Keep it short. A launcher is not a place for logic.

## 2. Tests to add to `tests/test_demo.py`

- `run_demo.py` **runs as a subprocess and exits 0**, invoked from **two different working directories** — one being `ipl-power-ranking/`, one being the repository root. This is the regression test for the defect; it must fail without the launcher.
- The subprocess's stdout contains the mandated stage banners 1..11 in ascending order.
- It is invoked with an **empty environment** (`env=` containing only what is strictly needed to find the interpreter, e.g. `{"SystemRoot": ..., "PATH": ...}`) so that no ambient `PYTHONPATH` can rescue it. This is what makes the test meaningful — a launcher that only works because the developer's shell exports `PYTHONPATH` is not fixed.
- **Determinism:** stdout of two subprocess runs is byte-identical.
- Use `sys.executable` for the interpreter path. Use `tmp_path` for any output redirect. Keep the existing 211 tests untouched and passing.

## 3. `README.md` (repo root or `ipl-power-ranking/` — your judgement, state which you chose and why)

Short and honest. Must contain, verbatim-ish:

- what the project is (Strang #5, reframed onto IPL, two models on two datasets) and **the headline finding**
- prerequisites (Python 3.11+, numpy/pandas/matplotlib/pytest)
- **how to run the demo**, as the literal copy-pasteable commands, including the zero-install launcher as the primary path
- how to run the tests
- what the outputs are (`figures/*.png`, `report/report.html`) and that the HTML is self-contained
- the provenance/licence position in one paragraph: Cricsheet, precise attribution, **no licence term asserted that was not read from the primary source**
- **the open blocker**: the instructor question about whether dataset substitution is permitted is **unanswered**, and the code exists so the question can be asked with evidence in hand
- a pointer to `docs/reasonix/` for the full spec, plan and reports

Do not overclaim. Do not say "production ready". Do not claim the finding is published — it is not.

## Verify before reporting — paste verbatim
```
cd C:\Anubhav\MFAD-Mini
python ipl-power-ranking\scripts\run_demo.py --offline
cd ipl-power-ranking
python -m pytest -q
```
Also prove the "no ambient PYTHONPATH" property explicitly:
```
cd C:\Anubhav\MFAD-Mini
Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
$env:PYTHONPATH=""
python ipl-power-ranking\scripts\run_demo.py --offline
```

## Report back
1. Verbatim pytest final line and total test count.
2. Verbatim first ~15 and last ~10 lines of the launcher run.
3. Proof that it ran with `PYTHONPATH` empty.
4. Which README path you chose and why.
5. Any measured number that disagreed with the project docs, with both values.
6. Confirmation you touched only the three allowed files.