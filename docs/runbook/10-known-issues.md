# 10 — Known issues and open audit findings

This file collects the gaps found while auditing the runbook against the code
on 2026-10-07. Each item says whether it has been measured. **No code or tests
were changed by this audit.**

## 1. Design-matrix sign convention: probable defect (measured, unreviewed)

`data.design_matrix()` builds each run-margin row like this:

```python
sign = +1.0 if winner == team1 else -1.0
A[i, team1] = sign
A[i, team2] = -sign
b[i]        = sign * margin
```

So row `i` states `sign·(x_team1 − x_team2) = sign·margin`. That simplifies to
**`x_team1 − x_team2 = margin` for every match, whoever won**. In other words,
the fit always credits the first-listed team with the win.

`tests/test_design_matrix.py::test_sign_convention_when_team2_won` pins this
exact behaviour. In match 335983 Chennai (team2) beat Punjab by 33. The test
asserts `A[Chennai] = +1`, `A[Punjab] = −1`, `b = −33`. That equation says
Chennai is **33 runs weaker** than Punjab, the team it beat.

This affects 123 of the 558 rows (the matches team2 won).

**Measured on 2026-10-07.** This was a throwaway probe, nothing was edited. The
model was re-fitted with consistent rows (`e_team1 − e_team2`, `b` signed from
team1's side):

| Quantity | Current code | Consistent sign |
|---|---|---|
| Spearman(Massey, Colley) | 0.000 | **0.443** |
| Spearman(Massey, official) | 0.093 | **0.604** |
| Centred R² | −0.2103 | −0.1556 |
| Uncentred R² | +0.0214 | +0.0656 |
| Winner accuracy | 55.02% | 59.14% |
| `max|x|` | 17.43 | 41.75 |

**Impact:** "Spearman exactly 0", the 77.96% majority-class story and several
R²/accuracy figures in the README, the report, `docs/reasonix/` and the tests
may be artefacts of this defect rather than findings about IPL data. The fix
touches `data.py`, at least one test that currently asserts the defective
behaviour, and every narrated number.

That is a scope decision for the owner. Under `AGENTS.md` §4 it must not be
"fixed" by editing a test to pass. It needs a deliberate run that corrects the
code, the tests and every narrated number together, then re-verifies the
replacements.

## 2. Instructor blocker is still open

`AGENTS.md` §2: nobody has recorded whether substituting the dataset is
allowed. The report's manual checklist lists this as item 1. Until it is
answered and recorded, the project is a demo built to support the question,
not a cleared submission.

## 3. `python -m iplranking` does not work without help

`pyproject.toml` has no `[build-system]`, so `src/` is not importable by
default. The workarounds are the launcher (`scripts/run_demo.py`), running
`python src/iplranking/__main__.py` directly (it has a path bootstrap), or
setting `PYTHONPATH=src`. The durable fix would be a build backend, which the
no-install rule rejected on purpose. See [03](03-run-the-demo.md).

## 4. Untracked scratch files in the package directory

`ipl-power-ranking/probe1.py` … `probe4.py` are ad-hoc measurement scripts.
They put `src` on `sys.path` relative to the working directory and print
diagnostics. They are **not tracked by git**, not covered by `.gitignore`, and
not part of the demo or the tests. Either delete them or move them under the
ignored `scratch/` directory.

## 5. Provenance is a manifest hash, not an archive hash

`ipl_json.zip` itself is not kept on this machine. `data/provenance.json`
therefore hashes a manifest of the extracted files and says so in
`sha256_covers` and `notes`. `http_status` honestly says "not recorded". See
[02](02-build-snapshot.md).

## 6. The "official table" is derived, not published

`data.official_table()` computes 2 points per win from the snapshot, across all
19 seasons, with no-winner matches excluded. Super Over ties would really earn
1 point each, so this is not the IPL's published table. Say so in the viva.
