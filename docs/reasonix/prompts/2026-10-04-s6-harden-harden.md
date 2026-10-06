# Dispatch — stage 6 HARDEN (free-tier, `loop-free-harden`)

**Read first:** `AGENTS.md` in full (it is binding), then `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` §6 acceptance criteria.

You are the mandatory security and observability pass. **Report gaps. Do not edit any file.** You have no write authority in this dispatch.

## What was built

A Python 3 numerical-analysis coursework project at `C:\Anubhav\MFAD-Mini`:
- package `iplranking` at `ipl-power-ranking/src/iplranking/` — data parsing, canonicalisation, design matrices, hand-written RREF/Gram–Schmidt/power iteration, three least-squares routes, Colley eigenvector, diagnostics, an ANSI console renderer, 13 Matplotlib figures, a self-contained HTML report, and a narrated 11-stage demo.
- 224 pytest tests, all green.
- data: `data/matches.csv` (1,243 rows) and `data/provenance.json`.
- outputs: `figures/*.png` (13) and `report/report.html` (~2.35 MB, 13 PNGs base64-inlined).
- entry point: `python ipl-power-ranking/scripts/run_demo.py --offline` (zero install, nothing in site-packages).

`AGENTS.md` §8 fixes the stack: Python 3 + NumPy + Pandas + Matplotlib + pytest. No web framework, no database, no front end. Everything must run from a clean clone with no network.

## What to check, in this project-specific sense

Stages 6, 8 and 9 are **re-scoped for coursework** per `CLAUDE.md` §11 and §13. "Hardening" here does **not** mean TLS, auth, or container hardening — there is no server. Judge it against what can actually go wrong on demo day and in the viva:

1. **Offline integrity.** Does the demo path import or open anything network-capable? Check for `requests`, `urllib`, `http`, `socket`, CDN URLs, remote fonts in the HTML. The `--offline` flag claims to block network imports and socket construction — **verify that claim is real** by reading the implementation, and state whether it is genuine enforcement or cosmetic.
2. **Path safety.** No absolute paths, no machine-specific environment variables, no `os.getcwd()` dependence, no user-specific paths in any committed file. Paths must resolve from `__file__`. Verify `figures.figure_dir()` / `report_dir()` / `run_demo.py` do this.
3. **Untrusted input.** The parser reads 1,243 external JSON files. Does it validate types, or would a malformed field raise an opaque error? Does any exception message leak an absolute path or a machine detail? Are `int`/`str` coercions on `season` safe against a `None`?
4. **Determinism and reproducibility.** Two runs must be byte-identical. Look for: unseeded randomness, dict/set iteration order affecting output, timestamps in figures or HTML, hash-order dependence, `id()`, PID, `PYTHONHASHSEED` sensitivity, and float formatting that varies by platform. **The most likely real defect is set/dict iteration order leaking into output** — check every `set` that gets sorted late or not at all.
5. **Data integrity.** Does anything mutate the committed snapshot? Is the CSV regenerated on import (it must not be)? Does the demo write into `data/`?
6. **Provenance and licence honesty.** Read `data/provenance.json`. It must not assert a licence term not read from the primary source (`AGENTS.md` §7), must not claim an HTTP status or hash it cannot support, and must state what the SHA-256 actually covers. Report any overclaim verbatim.
7. **Output safety.** `report.html` inlines 2.35 MB of base64 into one file — any escaping failure that could break the file, or inject unescaped user/data text into HTML? Check that all interpolated values are escaped.
8. **Failure behaviour.** What does a user see if `data/matches.csv` is missing or corrupt? Does the error say which invariant failed and with what numbers (`CLAUDE.md` §19), or is it a bare traceback?
9. **Resource safety.** Any unbounded loop, any file handle left open, any `plt.show()` that would block a headless demo? Confirm the `Agg` backend is forced.
10. **Secrets / personal data.** Scan for credentials, tokens, absolute user paths, and any player-name personal data beyond what the public Cricsheet files already contain (`CLAUDE.md` §11).

## Method

Read the code. Run things read-only if you need to (`python -m pytest -q`, the launcher, `git status`). **Do not modify, create or delete any file in the repository.** If you need scratch space use `C:\Users\anubh\AppData\Local\Temp\opencode\`.

## Report format

Return a **findings list**, most severe first. For each:
- **severity** — `blocker` / `should-fix` / `note`
- **file:line**
- **what is wrong**, quoted verbatim where it is a claim
- **why it matters for a 10-mark demo or viva**
- **the specific minimal fix** (describe it; do not apply it)

Then a one-line verdict: `HARDEN: clean`, or `HARDEN: findings` with the count.

**Do not invent findings to look thorough.** An empty findings list is a valid, respectable result if the code is clean. Distinguish clearly between what you *measured* and what you *inferred*. If you assert something is a security problem, quote the line that proves it.