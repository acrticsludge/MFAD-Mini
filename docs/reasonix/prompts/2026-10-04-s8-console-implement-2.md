# Dispatch — S8: the visual console renderer (`console.py`)

**Read first:** `AGENTS.md` §10 ("Keep the maths visible in code and comments; the examiner reads the machinery"), `docs/reasonix/specs/2026-10-04-ipl-power-ranking-visual-build.md` §1 and §4, `docs/reasonix/plans/2026-10-04-ipl-power-ranking-visual-build.md` §4.

**Blast radius — you may create/modify ONLY:** `ipl-power-ranking/src/iplranking/console.py`. That is one file. Touching anything else is a breach — stop and report. Do NOT run `git add`/`commit`/`push`. Do NOT edit anything under `docs/`. Do NOT import from `parse.py`, `data.py`, `models.py`, `linalg_kit.py` or `diagnostics.py` — other nodes own those and they may not exist yet. `console.py` must be **completely self-contained**, depending only on the standard library, `numpy`, and `os`/`sys`.

**Environment:** system Python 3.14.7 with numpy 2.5.2 already installed. Do NOT create a venv, do NOT pip install anything.

## Why this exists

The owner's requirement for the whole project: *every step of the run must be visual — each step must show what it is calculating and which math principle is used.* `console.py` is the renderer that makes that true in the terminal. Another node is building the mathematics; you are building the instrument it is displayed on. Your file is imported by everything else, so keep the API small, obvious and stable.

## Requirements

### 1. Must degrade gracefully
- `supports_ansi(stream) -> bool`: `True` if `stream.isatty()` and `NO_COLOR` is unset, and on Windows VT processing is available. On Windows, enable it via `ctypes.windll.kernel32.SetConsoleMode` on `STDOUT` (handle `-11`) with the flag `0x0004` (`ENABLE_VIRTUAL_TERMINAL_PROCESSING`); if that fails, return `False`.
- When ANSI is unavailable, **strip every escape sequence** and fall back to ASCII box-drawing characters. Output must never contain raw `ESC` bytes when piping to a file.
- Expose `init(stream=sys.stdout) -> None` and a module-level `is_color()`.

### 2. Palette and styling
256-colour and truecolour codes with a no-colour fallback for each: `dim`, `bold`, `cyan`, `green`, `yellow`, `red`, `magenta`, `blue`, `white`, plus semantic `ok()`, `warn()`, `bad()`, `info()`. Include a small set of team-colour helpers? No — keep it generic. Provide `style(text, *names)` for composing.

### 3. Layout primitives
- `width()` — terminal width, clamped to `[64, 100]` so output is stable in a narrow window and not absurd on a 4K monitor. Use `shutil.get_terminal_size()`.
- `rule(char="─")`, `box_top()`, `box_bottom()`, `box_sep()` — a consistent frame.
- `kv(key, value, key_width=28)` — aligned `key ......... value` line.
- `table(headers, rows, aligns=None, title=None)` — clean column-aligned table with a header rule, numeric right-alignment by default.
- `mat(a, name, shape_note=None, precision=2, max_rows=8, max_cols=15, highlight_rows=None)` — render a small NumPy array as a labelled grid with row/column indices. Print `array  (558, 15)  float64` in the header, exactly like NumPy. Truncate loudly: if truncated, print a `… N more rows` line — never silently drop data.
- `vec(v, name, precision=2, max_items=15)` — a horizontal vector with labels, and `vec_bars(v, names, se=None, width=32)` — a **per-item bar chart with optional ±se whiskers**, zero marked with a centre axis. This is used for the ranking with standard errors and must be readable at a glance.

### 4. Progress and live feedback
- `Progress(label, total, width=32)` — a context manager rendering an in-place bar. Writes `\r`, clears with `\033[2K`, redraws on each `update(n)`. On a non-TTY it must print a **final single summary line** instead of 500 redraws (so piped output is clean and diffable). `finish(note=None)`.
- `sparkline(values, label=None, width=40)` — inline Unicode block sparkline `▁▂▃▄▅▆▇█`, ASCII fallback `.:-=+*#%@`.
- `converge(label, generator)` — consume an iterator of floats, print a live sparkline of the running value and the final converged value plus the iteration count. Used for power iteration and for the three least-squares routes converging.
- Never let a progress bar leave a partial line in a piped log.

### 5. Stage-level API — this is the part the demo calls
```python
stage(number: int, mandated_name: str, principle: str) -> Stage
```
returns a context manager that prints, for the mandated stage:
- a boxed banner: `STAGE 8 · Prediction / Approximation`, the principle in one line, e.g. `principle: least squares — orthogonal projection of b onto Col(A)`
- on entry, nothing else; the demo then writes the body.

Also:
- `formula(lines: str | list[str])` — a monospace, dim, indented block for the maths. The demo writes e.g. `x̂ = argmin ‖Ax − b‖`. Accept a list of lines.
- `step(text: str)` — a `▸` line for "now doing X".
- `note(text)`, `warn(text)`, `bad(text)`, `ok(text)` — semantic one-liners.
- `measured(name, value, unit=None, meaning=None)` — a `kv` line used for every measured number, so the demo can never print an unlabelled float. Enforce by making it the only way the demo reports numbers.
- `verdict(text)` — a boxed, bolded one-line conclusion in plain English. The last thing printed in a stage.
- `excluded(count, total, reason)` — a prominent box: `EXCLUDED 25 of 1,243 matches — 16 Super Over ties + 9 no result`. `AGENTS.md` §4 requires exclusions be stated loudly, not footnoted. Include the percentage.
- `figure(name, caption)` — `┌ figure figures/08-least-squares.png — <caption>` so the terminal output and the figures directory cross-reference.
- `timeline(entries)` — at the very end, a table of `stage → figure → key number`.

### 6. Quality bar
- Module docstring explaining the design, the ANSI/ASCII duality and why no third-party library is used (the project stack is fixed: `AGENTS.md` §8).
- Every public function type-annotated.
- **Deterministic output** — no timestamps, no random, no `id()`, nothing machine-specific. Two runs must produce identical bytes. This is a hard acceptance criterion.
- Width clamping must not depend on the actual terminal when it would change the content: content lines must be padded to the clamped width, so piped output is stable regardless of the window.
- If `width()` returns different values between runs, the demo's determinism test fails — so make the width overridable and, in non-TTY mode, **default to 88** regardless of the real terminal size.

## Verify before you report
Run this and paste the verbatim output:
```
cd C:\Anubhav\MFAD-Mini\ipl-power-ranking
python -c "import sys; sys.path.insert(0,'src'); from iplranking import console; console.init(); s=console.stage(8,'Prediction / Approximation','least squares is the orthogonal projection of b onto Col(A)'); s.__enter__(); console.formula('x_hat = argmin ||A x - b||'); console.step('solving via numpy.linalg.lstsq'); console.measured('R2 (centred)', -0.2103, meaning='standard coefficient of determination'); console.measured('R2 (uncentred)', 0.0214, meaning='1 - SSres/SStot with uncentred SS_tot'); console.excluded(25,1243,'16 Super Over ties + 9 no result'); import numpy as np; console.mat(np.eye(4),'A'); console.vec_bars(np.array([1.2,-0.4,3.1,0.0]),['CSK','DC','MI','RCB'],se=np.array([0.5,0.5,1.5,0.5])); p=console.Progress('RREF elimination', 100); [p.update(i) for i in range(100)]; p.finish(); console.sparkline([0,1,4,9,16,25,36,49]); console.verdict('The obvious approach does not work.'); s.__exit__(None,None,None)"
```
Then run the same command twice with output redirected to two files and confirm they are byte-identical (`fc` or `Get-FileHash`). Report both hashes.

## Report back
1. The verbatim output of the verification command.
2. Both file hashes and whether they matched.
3. Any requirement you could not meet and why.
4. Confirmation that you created/modified only `console.py`.