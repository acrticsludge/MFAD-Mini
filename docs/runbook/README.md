# Runbook — IPL Power Ranking

This runbook describes how every part of the project runs: what each step
does, the command to run it, the files involved and what it produces. Read it
top to bottom to follow the pipeline in order, or open a single file for one
step.

| # | Step | How often |
|---|------|-----------|
| [01](01-setup.md) | Set up the environment | once |
| [02](02-build-snapshot.md) | Rebuild `data/matches.csv` from the raw archive and check provenance | rarely |
| [03](03-run-the-demo.md) | Run the demo end to end: invocations, flags, exit codes, internals | every demo |
| [04](04-the-eleven-stages.md) | What the demo computes at each stage, and how the matrices are built | reference |
| [05](05-run-the-tests.md) | Run the test suite, and what each test file pins | every change |
| [06](06-outputs.md) | Figures, report layout, determinism | reference |
| [07](07-offline-guard.md) | How `--offline` is enforced and tested | reference |
| [08](08-module-map.md) | Which source file does which job, plus the data flow | reference |
| [09](09-troubleshooting.md) | Error messages and their fixes | as needed |
| [10](10-known-issues.md) | **Open audit findings**, including a probable sign-convention defect | read before the viva |

## Quick path

```bash
pip install numpy pandas matplotlib pytest
python ipl-power-ranking/scripts/run_demo.py --offline   # demo
cd ipl-power-ranking && python -m pytest -q              # 235 tests
```

The binding rules are in `AGENTS.md`, and the design history is in
`docs/reasonix/`. This runbook covers how the code runs as of the 2026-10-07
audit, not why it was built this way. Claims here were checked against the
source and a test run on 2026-10-07 (235 passed).
