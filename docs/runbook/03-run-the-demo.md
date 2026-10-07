# 03 — Run the demo

## What this step is

This is the deliverable. One command walks all eleven mandated stages in
`AGENTS.md` §5 order. Each stage prints a banner, a formula, the live
computation, the measured numbers and a verdict. The run also saves 13 PNG
figures and writes a self-contained HTML report.

## Command

```bash
python ipl-power-ranking/scripts/run_demo.py --offline
```

Run it from the repository root as above, or like this:

```bash
cd ipl-power-ranking
python scripts/run_demo.py --offline
```

A full run with the report took **15 s** when measured on 2026-10-07. After
that run `git status` showed the tracked `figures/` and `report/` unchanged,
which confirms the output is byte-identical between runs.

## Three ways to invoke it

| Invocation | Works from a clean clone? |
|---|---|
| `python ipl-power-ranking/scripts/run_demo.py` | **yes**. This is the recommended form |
| `python ipl-power-ranking/src/iplranking/__main__.py` | yes. `__main__.py` has a path bootstrap |
| `python -m iplranking` | **no**, unless `PYTHONPATH=src` is set (`$env:PYTHONPATH='src'` in PowerShell) from `ipl-power-ranking/` |

`pyproject.toml` has no build backend, so `src/` is not on the interpreter path
by default. The launcher finds `ipl-power-ranking/src` from its own
`__file__`, never from the working directory, and puts it on `sys.path`. It
then calls the same `main()`. It prints nothing of its own, and its exit code
is the demo's. If the package is not where it expects, it says where it looked
and exits 2.

## Flags

All arguments are passed through to the CLI unchanged.

| Flag | Effect |
|---|---|
| *(none)* | full default run |
| `--offline` | blocks network imports and sockets for the whole run, and fails with exit 1 if anything reaches for them. See [07](07-offline-guard.md) |
| `--width N` | render width, clamped to 64–100. Piped output defaults to a fixed 88 |
| `--figures-only` | skips the opening banner and the closing summary. All 11 stages still run and every artefact is still written |
| `--no-report` | skips `report/report.html` |
| `--help` | usage |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Every stage completed and every artefact was written |
| 1 | `--offline` was requested and something reached for the network (`NetworkBlockedError`) |
| 2 | A stage, figure or report failed. This includes `cannot start: …` for a missing or invalid snapshot (`FileNotFoundError`/`ValueError`) |
| 3 | Bad command line (argparse) |

`main()` never raises: other exceptions print a traceback to stderr and return 2.

## What happens inside `__main__.main()`

1. The arguments are parsed. `console.init(stdout)` chooses Unicode or ASCII
   glyphs and colour or no colour, and on Windows enables VT mode where it
   can. A piped run never contains a raw ESC byte. `console.set_width()`
   applies `--width`.
2. With `--offline`, `demo.assert_offline()` installs the network block
   **before** the run.
3. `demo.run_demo()` loads the snapshot, fits both models, runs `_stage_1` …
   `_stage_11` in order and returns a `DemoResult`. See
   [04](04-the-eleven-stages.md) for each stage.
4. Unless `--no-report` is given, `report.build_report(result)` writes
   `report/report.html`. It is imported only at this point, so a failure while
   building the report cannot break the terminal walkthrough.
5. In the `finally` block, `demo.release_offline()` restores the hooks.

The run is deterministic. Nothing on the path prints a timestamp, duration,
hostname or random number, and width is fixed at 88 when stdout is not a TTY.
Two runs produce byte-identical terminal output, PNGs and report.
