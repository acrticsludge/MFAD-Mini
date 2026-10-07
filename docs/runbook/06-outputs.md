# 06 — Outputs

Everything the demo writes, where it goes, and how the output stays
deterministic.

## What is produced

| Artefact | Written by | Notes |
|----------|-----------|-------|
| Terminal walkthrough | `console.py` via `demo.py` | stdout, 88 columns wide when piped, `--width` to override |
| `figures/01-data.png` | stage 1 | data funnel |
| `figures/02-design-matrix.png` | stage 2 | |
| `figures/03-rref.png` | stage 3 | |
| `figures/04-structure.png` | stage 4 | |
| `figures/05-redundancy.png` | stage 5 | |
| `figures/06-qr.png` | stage 6 | Col(A) vs Row(A) |
| `figures/07-projection.png` | stage 7 | |
| `figures/08-least-squares.png` | stage 8 | |
| `figures/09-eigen.png` | stage 9 | |
| `figures/10-diagonalisation.png` | stage 10 | |
| `figures/11-ranking.png`, `12-findings.png`, `13-divergence.png` | stage 11 | |
| `report/report.html` | `report.build_report` | about 2.4 MB, self-contained |

`figures.FIGURE_NAMES` is the single list of file names. The tests check that
all 13 exist and are valid PNGs.

`figures.figure_dir()` and `report_dir()` find the repository root from the
package location, without absolute paths or environment variables, so the
artefacts always land in the same place.

## Determinism is an acceptance criterion

Two runs produce byte-identical terminal output, PNGs and report, and
`tests/test_demo.py` checks this. It is achieved by:

- using the Matplotlib `Agg` backend, selected before `pyplot` is imported (no
  window or display);
- fixed `DPI = 120`, the fixed font `DejaVu Sans`, and fixed figure sizes;
- pinning the PNG `Software` tag to `"ipl-power-ranking"`, so the bytes do not
  depend on the Matplotlib version;
- avoiding timestamps, durations, hostnames, random draws and
  environment-derived paths;
- alphabetical team order everywhere.

Figures never compute a finding. They plot numbers handed in by
`data`/`models`/`diagnostics`/`linalg_kit`, so a figure cannot disagree with
the terminal. The two exceptions, both stated in the code, are that Gram–Schmidt
is re-run to get its trace and the thin QR is recomputed for the `||q_jᵀA||`
profile.

## The report: section order

`report.build_report()` builds the page by plain stdlib string concatenation:

1. `<head>` with a single `<style>` block
2. Masthead
3. **Blocker banner**: the open instructor question
4. One section per stage, with the same formula block as the terminal (`<pre>`)
   and the base64-inlined figure
5. R² block (both denominators and the intercept correction)
6. Findings
7. Comparison table (official vs Massey vs Colley)
8. Provenance and licence position
9. **Manual checklist**: what you must do by hand
10. Footer

It contains no `<script>`, CDN, external stylesheet or font fetch. The
provenance URL appears as text, not as a `src`/`href`. The page opens with the
network off.

## Regenerating

Delete `figures/` and `report/` and run the demo again. Both are recreated.
