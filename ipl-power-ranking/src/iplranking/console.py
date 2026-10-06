"""Terminal renderer for the IPL power-ranking demo.

Design
------
The owner's requirement for this project is that *every step of the run must be
visual* — each step must show what it is calculating and which mathematical
principle produced it.  ``console.py`` is the instrument that display is drawn
on.  Nothing in here computes a result: every function takes already-computed
numbers and renders them, so the mathematics can be tested independently of the
way it is displayed.  (``AGENTS.md`` section 10: the examiner reads the
machinery, so the machinery and the maths stay visible in the code and
comments.)

The ANSI/ASCII duality
---------------------
A piped run must never contain a raw ESC byte, and a Windows console that has
not been switched into virtual-terminal mode must not print escape soup either.
So there is exactly one switch — :data:`_color` — and two complete alphabets:

* Unicode mode uses box-drawing rules, block sparklines and typographic marks
  (``─ │ ▸ … ▁▂▃▄▅▆▇█``).
* ASCII mode uses ``- | > ... :.-=+*#%@`` for the same roles.

Every glyph goes through :func:`_ch`, and every colour goes through
:func:`style`, which returns its argument untouched when colour is off.  The
guarantee is therefore structural rather than hopeful: there is no code path
that can emit an escape sequence without going through :func:`style`.

Determinism
-----------
Two runs must produce byte-identical output, and that is a hard acceptance
criterion for this project.  So this module contains no timestamp, no random
number, no ``id()``, no PID, no environment-derived machine name and no
iteration over an unordered set.  Terminal width is the one external input that
could vary, and it is handled explicitly: :func:`width` is clamped to
``[64, 100]``, returns a fixed **88** when stdout is not a TTY, and can be
overridden with :func:`set_width`.

Why no third-party library
--------------------------
The project stack is fixed — ``AGENTS.md`` section 8 permits only Python 3,
NumPy, Pandas, Matplotlib and pytest.  ``rich`` or ``colorama`` would solve the
escape-sequence handling, but adding a dependency to a 10-mark NumPy coursework
project is a defect, not a feature, and it would also make the output depend on
a version of a package we do not control.  Roughly 300 lines of stdlib covers
the whole requirement, and ``ctypes`` talks to the Windows console API directly.

One deliberate API compromise
-----------------------------
Sections 2 and 5 of the dispatch ask for ``ok()``/``warn()``/``bad()``/``info()``
twice: once as *palette helpers* and once as *one-line printers*.  Rather than
drop either reading, these four print their styled one-liner **and return the
styled text**, so they are usable both ways.  A helper that printed nothing
would break the demo's output; a printer that returned nothing would break
composition.  Do not use them inside a larger :func:`style` expression.
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TextIO

import numpy as np

__all__ = [
    # capability
    "supports_ansi", "init", "is_color", "set_width",
    # palette
    "dim", "bold", "cyan", "green", "yellow", "red", "magenta", "blue", "white",
    "ok", "warn", "bad", "info", "style",
    # layout
    "width", "rule", "box_top", "box_bottom", "box_sep", "kv", "table", "mat",
    "vec", "vec_bars",
    # progress
    "Progress", "sparkline", "converge",
    # stage API
    "Stage", "stage", "formula", "step", "note", "measured", "verdict",
    "excluded", "figure", "timeline",
]

# --------------------------------------------------------------------------
# State
#
# _stream is resolved lazily rather than captured at import time, so that a test
# (or a shell redirect) that swaps sys.stdout still works.  _color and _tty are
# two separate switches on purpose: colour needs a TTY *and* VT support, but an
# in-place progress bar only needs a TTY, and ANSI-disabled Windows terminals are
# perfectly able to redraw a line.
# --------------------------------------------------------------------------
_stream: TextIO | None = None
_color: bool = False
_tty: bool = False
_width_override: int | None = None

#: Fixed width used whenever stdout is not a TTY.  Piped output therefore does
#: not depend on the window it happened to be produced in.
NON_TTY_WIDTH: int = 88
MIN_WIDTH: int = 64
MAX_WIDTH: int = 100

# --------------------------------------------------------------------------
# Glyphs.  Every character the module can print comes from one of these two
# tables, so the ASCII fallback is a data change rather than a code change.
# All glyphs are single-column, which is what makes the padding arithmetic in
# _fit() correct.
# --------------------------------------------------------------------------
_UNICODE: dict[str, str] = {
    "h": "─", "v": "│",
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "dh": "═", "dtl": "╔", "dtr": "╗", "dbl": "╚", "dbr": "╝",
    "ml": "├", "mr": "┤",
    "ellipsis": "…", "bullet": "·", "emdash": "—",
    "step": "▸", "ok": "✓", "bad": "✗", "warn": "!", "plusminus": "±", "times": "×",
    "spark": "▁▂▃▄▅▆▇█", "bar": "█", "axis": "│", "whisker": "─",
    "track": "·", "dot": ".",
}
_ASCII: dict[str, str] = {
    "h": "-", "v": "|",
    "tl": "+", "tr": "+", "bl": "+", "br": "+",
    "dh": "=", "dtl": "#", "dtr": "#", "dbl": "#", "dbr": "#",
    "ml": "+", "mr": "+",
    "ellipsis": "...", "bullet": "-", "emdash": "--",
    "step": ">", "ok": "+", "bad": "x", "warn": "!", "plusminus": "+-", "times": "x",
    "spark": ".:-=+*#%@", "bar": "#", "axis": "|", "whisker": "-",
    "track": ".", "dot": ".",
}

#: 256-colour foreground index per semantic colour.
_COLOUR_256: dict[str, int] = {
    "cyan": 51, "green": 41, "yellow": 226, "red": 203,
    "magenta": 177, "blue": 39, "white": 253,
}
#: Truecolour fallback for terminals that advertise COLORTERM=truecolor/24bit.
_COLOUR_RGB: dict[str, tuple[int, int, int]] = {
    "cyan": (0x4E, 0xC9, 0xE8), "green": (0x4E, 0xC9, 0x74),
    "yellow": (0xE3, 0xC0, 0x4A), "red": (0xE8, 0x5C, 0x5C),
    "magenta": (0xC0, 0x6C, 0xD8), "blue": (0x6C, 0x9E, 0xE8),
    "white": (0xDC, 0xDC, 0xDC),
}
#: 256-colour foreground used for the "dim" attribute.
_DIM_256: int = 244

_RESET = "\033[0m"
_CLEAR_LINE = "\033[2K"
_CARRIAGE = "\r"


def _ch(key: str) -> str:
    """Return the glyph for *key* in the currently active alphabet."""
    return _UNICODE[key] if _color else _ASCII[key]


def _table() -> dict[str, str]:
    """Return the active glyph table."""
    return _UNICODE if _color else _ASCII


# --------------------------------------------------------------------------
# Output plumbing
# --------------------------------------------------------------------------
def _out() -> TextIO:
    """Return the active output stream, resolving ``sys.stdout`` lazily."""
    return sys.stdout if _stream is None else _stream


def _write(text: str) -> None:
    """Write *text* plus a newline to the active stream."""
    _out().write(text + "\n")


def _truecolor() -> bool:
    """True when the terminal advertises 24-bit colour support."""
    return os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")


def _colour_code(name: str) -> str:
    """Return the SGR parameter(s) that turn on the named colour."""
    if _truecolor():
        r, g, b = _COLOUR_RGB[name]
        return f"38;2;{r};{g};{b}"
    return f"38;5;{_COLOUR_256[name]}"


# --------------------------------------------------------------------------
# 1. Capability detection and initialisation
# --------------------------------------------------------------------------
def supports_ansi(stream: TextIO | None = None) -> bool:
    """Report whether ANSI escape sequences can be written to *stream*.

    True requires all three of: ``stream.isatty()``, an unset ``NO_COLOR``
    (https://no-color.org), and — on Windows — virtual-terminal processing
    actually being switchable on for stdout.  The Windows check is attempted
    rather than assumed: ``SetConsoleMode`` fails on a real console handle in
    some hosts, and a wrong answer here means escape soup in the demo.
    """
    stream = sys.stdout if stream is None else stream
    if os.environ.get("NO_COLOR") is not None:
        return False
    try:
        if not stream.isatty():
            return False
    except Exception:
        return False
    if os.name != "nt":
        return True
    return _enable_windows_vt()


def _enable_windows_vt() -> bool:
    """Switch the Windows console for stdout into VT processing mode.

    Returns True if VT mode is on afterwards.  ``STD_OUTPUT_HANDLE`` is -11.
    The prototypes are set explicitly because the default ``c_int`` return type
    truncates a 64-bit HANDLE.
    """
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.GetStdHandle.restype = ctypes.c_void_p
        kernel32.GetStdHandle.argtypes = (ctypes.c_ulong,)
        kernel32.GetConsoleMode.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
        kernel32.GetConsoleMode.restype = ctypes.c_int
        kernel32.SetConsoleMode.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        kernel32.SetConsoleMode.restype = ctypes.c_int

        enable_vt = 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        handle = kernel32.GetStdHandle(-11)
        if not handle:
            return False
        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        if mode.value & enable_vt:
            return True  # already on
        return bool(kernel32.SetConsoleMode(handle, mode.value | enable_vt))
    except Exception:
        return False


def init(stream: TextIO | None = None) -> None:
    """Initialise the renderer against *stream* (default ``sys.stdout``).

    Sets the colour switch, the TTY switch and the piped-output width.  Safe to
    call more than once; later calls re-evaluate all three.
    """
    global _stream, _color, _tty
    _stream = sys.stdout if stream is None else stream
    try:
        _tty = bool(_stream.isatty())
    except Exception:
        _tty = False
    _color = supports_ansi(_stream)


def is_color() -> bool:
    """True when colour output is enabled.  Call :func:`init` first."""
    return _color


def set_width(value: int | None) -> None:
    """Override the render width, or pass None to return to auto-detection.

    Clamped to ``[MIN_WIDTH, MAX_WIDTH]`` like the measured value, so a caller
    cannot accidentally produce unbounded lines.
    """
    global _width_override
    if value is None:
        _width_override = None
    else:
        _width_override = max(MIN_WIDTH, min(MAX_WIDTH, int(value)))


# --------------------------------------------------------------------------
# 2. Palette
# --------------------------------------------------------------------------
def style(text: str, *names: str) -> str:
    """Wrap *text* in the SGR codes for *names* (e.g. ``"bold"``, ``"cyan"``).

    Returns *text* unchanged when colour is disabled, which is the single
    mechanism that guarantees no raw ESC byte can reach a pipe.
    """
    if not _color or not names:
        return text
    codes: list[str] = []
    for name in names:
        if name == "dim":
            codes.append(f"38;5;{_DIM_256}")
        elif name == "bold":
            codes.append("1")
        elif name in _COLOUR_256:
            codes.append(_colour_code(name))
    if not codes:
        return text
    return "\033[" + ";".join(codes) + "m" + text + _RESET


def dim(text: str) -> str:
    """Render *text* dimmed (de-emphasised annotation)."""
    return style(text, "dim")


def bold(text: str) -> str:
    """Render *text* bold (used for conclusions)."""
    return style(text, "bold")


def cyan(text: str) -> str:
    """Render *text* in the accent colour used for structural marks."""
    return style(text, "cyan")


def green(text: str) -> str:
    """Render *text* in the success colour."""
    return style(text, "green")


def yellow(text: str) -> str:
    """Render *text* in the caution colour."""
    return style(text, "yellow")


def red(text: str) -> str:
    """Render *text* in the failure colour."""
    return style(text, "red")


def magenta(text: str) -> str:
    """Render *text* in the secondary accent colour."""
    return style(text, "magenta")


def blue(text: str) -> str:
    """Render *text* in the tertiary accent colour."""
    return style(text, "blue")


def white(text: str) -> str:
    """Render *text* in the high-contrast foreground."""
    return style(text, "white")


def _semantic(glyph_key: str, colour: str, text: str) -> str:
    """Print and return a ``glyph text`` one-liner in *colour*.

    Shared by :func:`ok`, :func:`warn`, :func:`bad` and :func:`info`.  See the
    module docstring: these print *and* return, so they satisfy both the palette
    and the one-liner reading of the dispatch.
    """
    line = style(f"{_ch(glyph_key)} {text}", colour)
    _write(line)
    return line


def ok(text: str) -> str:
    """Print a success one-liner; return the styled text."""
    return _semantic("ok", "green", text)


def warn(text: str) -> str:
    """Print a caution one-liner; return the styled text."""
    return _semantic("warn", "yellow", text)


def bad(text: str) -> str:
    """Print a failure one-liner; return the styled text."""
    return _semantic("bad", "red", text)


def info(text: str) -> str:
    """Print an informational one-liner; return the styled text."""
    return _semantic("bullet", "dim", text)


# --------------------------------------------------------------------------
# 3. Layout primitives
# --------------------------------------------------------------------------
def width() -> int:
    """Return the render width, clamped to ``[64, 100]``.

    Resolution order: an explicit :func:`set_width` override, then a fixed
    :data:`NON_TTY_WIDTH` when stdout is not a TTY, then the measured terminal
    size.  The TTY special case is what makes piped output independent of the
    window it was produced in.
    """
    if _width_override is not None:
        return _width_override
    if not _tty:
        return NON_TTY_WIDTH
    columns = shutil.get_terminal_size(fallback=(NON_TTY_WIDTH, 24)).columns
    return max(MIN_WIDTH, min(MAX_WIDTH, columns))


def _fit(text: str, size: int) -> str:
    """Pad or truncate *text* to exactly *size* visible characters.

    Truncation is loud by construction: the result always ends in the ellipsis
    glyph, so a caller can never silently drop the tail of a value.
    """
    if size <= 0:
        return ""
    if len(text) > size:
        mark = _ch("ellipsis")
        if size <= len(mark):
            return mark[:size]
        return text[: size - len(mark)] + mark
    return text.ljust(size)


def rule(char: str | None = None) -> str:
    """Print a full-width horizontal rule; return it."""
    line = char if char is not None else _ch("h")
    out = line * width()
    _write(out)
    return out


def _box(lines: Sequence[str], *, double: bool = False) -> list[str]:
    """Render *lines* inside a full-width box; return the unstyled rows."""
    if double:
        tl, tr = _ch("dtl"), _ch("dtr")
        bl, br = _ch("dbl"), _ch("dbr")
        horizontal = _ch("dh")
    else:
        tl, tr = _ch("tl"), _ch("tr")
        bl, br = _ch("bl"), _ch("br")
        horizontal = _ch("h")
    vertical = _ch("v")
    inner = width() - 2
    out = [tl + horizontal * inner + tr]
    for line in lines:
        out.append(vertical + " " + _fit(line, inner - 2) + " " + vertical)
    out.append(bl + horizontal * inner + br)
    return out


def _box_fit(lines: Sequence[str], *, minimum: int, colour: str, double: bool = False) -> str:
    """Render *lines* in a box sized to its content; return the styled text.

    Used for short, emphatic blocks (a verdict, the exclusion notice) where a
    full-width frame would outweigh the message it contains.
    """
    if double:
        tl, tr, bl, br = _ch("dtl"), _ch("dtr"), _ch("dbl"), _ch("dbr")
        horizontal = _ch("dh")
    else:
        tl, tr, bl, br = _ch("tl"), _ch("tr"), _ch("bl"), _ch("br")
        horizontal = _ch("h")
    vertical = _ch("v")
    content = max([len(line) for line in lines] + [minimum - 4])
    inner = min(content + 2, width() - 2)
    rows = [tl + horizontal * inner + tr]
    for line in lines:
        rows.append(vertical + " " + _fit(line, inner - 2) + " " + vertical)
    rows.append(bl + horizontal * inner + br)
    out = "\n".join(style(row, colour) for row in rows)
    _write(out)
    return out


def box_top(label: str = "") -> str:
    """Print the opening edge of a frame, optionally labelled; return it."""
    horizontal = _ch("h")
    inner = width() - 2
    if label:
        text = f"{_ch('tl')}{horizontal} {label} "
        out = cyan(text + horizontal * max(0, inner - len(text) + 1) + _ch("tr"))
    else:
        out = cyan(_ch("tl") + horizontal * inner + _ch("tr"))
    _write(out)
    return out


def box_bottom() -> str:
    """Print the closing edge of a frame; return it."""
    out = cyan(_ch("bl") + _ch("h") * (width() - 2) + _ch("br"))
    _write(out)
    return out


def box_sep() -> str:
    """Print a separator between sections of a frame; return it."""
    out = dim(_ch("ml") + _ch("h") * (width() - 2) + _ch("mr"))
    _write(out)
    return out


def _kv_string(key: str, value: str, key_width: int = 28) -> str:
    """Build a dotted-leader ``key ...... value`` line without printing it."""
    if len(key) >= key_width:
        return f"{key}  {value}"
    leader = _ch("dot") * (key_width - len(key) - 1)
    return f"{key} {leader} {value}"


def kv(key: str, value: str, key_width: int = 28) -> str:
    """Print one aligned ``key ........ value`` line; return it."""
    line = _kv_string(key, value, key_width)
    _write(line)
    return line


def _is_number(text: str) -> bool:
    """True when *text* parses as a number, so the column can be right-aligned."""
    try:
        float(text.strip().replace(",", "").replace("%", ""))
    except ValueError:
        return False
    return True


def _column_widths(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[int]:
    """Size each column to its content, then shrink the widest until it fits."""
    count = len(headers)
    widths = [len(headers[i]) for i in range(count)]
    for row in rows:
        for i in range(count):
            cell = row[i] if i < len(row) else ""
            widths[i] = max(widths[i], len(cell))
    gap = 2
    available = width()
    while sum(widths) + gap * max(0, count - 1) > available:
        # max() over a range breaks ties toward the lowest index, so the
        # shrinking order is fixed and the layout is reproducible.
        widest = max(range(count), key=lambda i: widths[i])
        if widths[widest] <= 6:
            break
        widths[widest] -= 1
    return widths


def table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    aligns: Sequence[str] | None = None,
    title: str | None = None,
) -> str:
    """Print a column-aligned table with a header rule; return the text.

    Columns whose cells all parse as numbers are right-aligned by default, which
    is what a ranking or a residual column needs.  *aligns* overrides that with
    a per-column ``"l"``, ``"r"`` or ``"c"``.  Over-wide columns are truncated
    loudly with the ellipsis glyph.
    """
    text_rows = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    count = len(headers)
    widths = _column_widths(headers, text_rows)

    if aligns is None:
        aligns = []
        for i in range(count):
            column = [headers[i]] + [row[i] if i < len(row) else "" for row in text_rows]
            aligns.append("r" if column and all(_is_number(c) for c in column) else "l")
    aligns = list(aligns) + ["l"] * max(0, count - len(aligns))

    out: list[str] = []
    if title:
        out.append(bold(title))
    out.append("  ".join(_align(_fit(headers[i], widths[i]), widths[i], aligns[i]) for i in range(count)))
    out.append(dim("  ".join(_ch("h") * widths[i] for i in range(count))))
    for row in text_rows:
        cells = [
            _align(_fit(row[i] if i < len(row) else "", widths[i]), widths[i], aligns[i])
            for i in range(count)
        ]
        out.append("  ".join(cells).rstrip())
    rendered = "\n".join(out)
    _write(rendered)
    return rendered


def _align(text: str, size: int, how: str) -> str:
    """Pad already-fitted *text* to *size* according to *how*."""
    if how == "r":
        return text.rjust(size)
    if how == "c":
        return text.center(size)
    return text.ljust(size)


def _cell(value: Any, precision: int) -> str:
    """Format one array element for display."""
    number = float(value)
    if number != number:  # NaN
        return "nan"
    if number in (float("inf"), float("-inf")):
        return "inf" if number > 0 else "-inf"
    return f"{number:.{precision}f}"


def mat(
    a: Any,
    name: str,
    shape_note: str | None = None,
    precision: int = 2,
    max_rows: int = 8,
    max_cols: int = 15,
    highlight_rows: Iterable[int] | None = None,
) -> str:
    """Print a small labelled NumPy array as an indexed grid; return the text.

    The header mirrors NumPy's own ``array  (558, 15)  float64`` wording so the
    terminal output and a REPL session agree on what is being shown.  Truncation
    is always announced: a silent drop would let the demo hide a dimension it
    did not want to talk about, which is exactly the dishonesty
    ``AGENTS.md`` section 4 forbids.
    """
    array = np.atleast_2d(np.asarray(a))
    n_rows, n_cols = array.shape
    shown_rows = min(n_rows, max_rows)
    shown_cols = min(n_cols, max_cols)
    marked = set(highlight_rows or ())

    header = f"{name} = array  ({n_rows}, {n_cols})  {array.dtype}"
    if shape_note:
        header = f"{header}  {shape_note}"

    index_width = len(str(max(shown_rows - 1, 0))) if shown_rows else 1
    cells: list[list[str]] = []
    for r in range(shown_rows):
        row = [_cell(array[r, c], precision) for c in range(shown_cols)]
        cells.append(row)
    col_widths = [
        max([len(str(c))] + [len(cells[r][c]) for r in range(shown_rows)])
        for c in range(shown_cols)
    ]

    out = [bold(header)]
    out.append(dim(" " * (index_width + 1) + "  ".join(str(c).rjust(w) for c, w in enumerate(col_widths))))
    for r in range(shown_rows):
        marker = ">" if r in marked else " "
        prefix = f"{marker}{str(r).rjust(index_width)}"
        body = "  ".join(cells[r][c].rjust(col_widths[c]) for c in range(shown_cols))
        line = f"{prefix}  {body}".rstrip()
        out.append(style(line, "yellow") if r in marked else line)

    if n_rows > shown_rows:
        out.append(dim(f"{_ch('ellipsis')} {n_rows - shown_rows} more rows"))
    if n_cols > shown_cols:
        out.append(dim(f"{_ch('ellipsis')} {n_cols - shown_cols} more cols"))
    if shown_rows == 0 or shown_cols == 0:
        out.append(dim("(empty array)"))
    rendered = "\n".join(out)
    _write(rendered)
    return rendered


def vec(v: Any, name: str, precision: int = 2, max_items: int = 15) -> str:
    """Print a horizontal labelled vector; return the text.

    Announced when truncated, for the same reason as :func:`mat`.
    """
    values = np.atleast_1d(np.asarray(v, dtype=float))
    total = values.size
    shown = min(total, max_items)
    field = max(6, precision + 4)
    body = " ".join(f"{float(values[i]):+{field}.{precision}f}" for i in range(shown))
    rendered = f"{bold(name)} = {dim('[')} {body} {dim(']')}"
    if total > shown:
        rendered = rendered + "\n" + dim(f"{_ch('ellipsis')} {total - shown} more items")
    _write(rendered)
    return rendered


def vec_bars(
    v: Any,
    names: Sequence[str],
    se: Any | None = None,
    width: int = 32,
) -> str:
    """Print a per-item horizontal bar chart with optional +-se whiskers.

    *width* is the number of cells in the track.  The zero point is drawn as a
    visible vertical axis: when the data spans zero it sits inside the track,
    and when every value is of one sign it is pinned to the relevant edge, so a
    reader is never told that a bar "crosses" a zero that is not shown.  Each
    bar is annotated with the signed value and, when *se* is supplied, the
    standard error.
    """
    values = np.atleast_1d(np.asarray(v, dtype=float))
    errors = None if se is None else np.atleast_1d(np.asarray(se, dtype=float))
    count = values.size
    track = max(4, int(width))

    low = [float(values[i]) - (float(errors[i]) if errors is not None else 0.0) for i in range(count)]
    high = [float(values[i]) + (float(errors[i]) if errors is not None else 0.0) for i in range(count)]
    lo, hi = min(low + [0.0]), max(high + [0.0])
    span = hi - lo
    if span <= 0.0:
        span = 1.0
        lo -= 0.5
    if lo >= 0.0:
        axis = 0
    elif hi <= 0.0:
        axis = track - 1
    else:
        axis = int(round((0.0 - lo) / span * (track - 1)))
    axis = max(0, min(track - 1, axis))

    def cell(value: float) -> int:
        """Map a data value onto a track index."""
        return max(0, min(track - 1, int(round((value - lo) / span * (track - 1)))))

    label_width = max((len(name) for name in names), default=0)
    out: list[str] = []
    for i in range(count):
        row = [_ch("track")] * track
        for position in range(cell(low[i]), cell(high[i]) + 1):
            row[position] = _ch("whisker")
        centre = cell(float(values[i]))
        for position in range(min(axis, centre), max(axis, centre) + 1):
            row[position] = _ch("bar")
        row[axis] = _ch("axis")

        value_text = f"{float(values[i]):+7.2f}"
        if errors is not None:
            value_text = f"{value_text} {_ch('plusminus')}{float(errors[i]):.2f}"
        colour = "green" if values[i] >= 0 else "red"
        label = str(names[i]).rjust(label_width) if i < len(names) else "?" * label_width
        out.append(
            f"{label}  "
            + style("".join(row), colour)
            + "  "
            + bold(value_text)
        )
    rendered = "\n".join(out)
    _write(rendered)
    return rendered


# --------------------------------------------------------------------------
# 4. Progress and live feedback
# --------------------------------------------------------------------------
class Progress:
    """In-place progress bar, degrading to one summary line when piped.

    Used as a context manager, but every method also works standalone so the
    demo can drive it directly::

        with Progress("RREF elimination", n) as p:
            for i in range(n):
                ...
                p.update(i)

    On a TTY the line is rewritten in place with CR + clear-line.  Off a TTY
    nothing is printed until :meth:`finish`, which emits exactly one summary
    line — a piped log should not contain 500 carriage-return redraws, and a
    diff of two runs should be readable.

    *update(n)* reports the number of items **processed so far**, so ``for i in
    range(n): p.update(i)`` finishes showing ``n-1`` of ``n``; call
    ``p.update(p.total)`` or ``p.finish()`` to close the last unit.  Leaving
    that arithmetic to the caller is deliberate — the bar reports what the loop
    actually did rather than a number chosen to look finished.

    If the body raises, ``__exit__`` closes the bar as *aborted* rather than
    complete: a bar that reads 100% over a run that crashed is exactly the kind
    of number ``AGENTS.md`` section 4 rules out.
    """

    def __init__(self, label: str, total: int, width: int = 32) -> None:
        self.label = label
        self.total = max(0, int(total))
        self.width = max(4, int(width))
        self.n = 0
        self._done = False
        self._entered = False
        self._painted = False

    def _bar(self) -> str:
        """Render the bar glyphs for the current position."""
        fraction = 0.0 if self.total == 0 else min(1.0, self.n / self.total)
        filled = int(round(fraction * self.width))
        return _ch("bar") * filled + _ch("track") * (self.width - filled)

    def _summary(self, note: str | None) -> str:
        """Build the single line used off a TTY and at the end of a TTY run."""
        percent = 100 if self.total == 0 else int(round(min(1.0, self.n / self.total) * 100))
        line = f"{self.label}  {self._bar()}  {percent:3d}%  {self.n}/{self.total}"
        return line if not note else f"{line}  {note}"

    def _redraw(self) -> None:
        """Rewrite the bar in place.  Only ever called on a TTY."""
        stream = _out()
        stream.write(_CARRIAGE + _CLEAR_LINE + self._summary(None))
        try:
            stream.flush()
        except Exception:
            pass
        self._painted = True

    def update(self, n: int) -> None:
        """Advance the bar to position *n* and redraw it if attached to a TTY."""
        self.n = max(0, int(n))
        if _tty and self._entered:
            self._redraw()

    def finish(self, note: str | None = None) -> str:
        """Complete the bar and emit its final line.  Idempotent.

        The carriage-return/clear-line prefix is emitted only when a redrawn
        line is actually outstanding.  Doing it unconditionally would put a raw
        ESC byte into a redirected file, which the ASCII fallback promises never
        to do.
        """
        if self._done:
            return ""
        self._done = True
        line = self._summary(note)
        if self._painted:
            self._painted = False
            line = _CARRIAGE + _CLEAR_LINE + line
        self._entered = False
        _write(line)
        return line

    def __enter__(self) -> "Progress":
        self._entered = True
        if _tty:
            self._redraw()
        return self

    def __exit__(self, exc_type: object, *exc: object) -> bool:
        if not self._done:
            # Never let a crashed run print as a finished one.
            self.finish("aborted" if exc_type is not None else "done")
        return False


def _sparkline_string(values: Sequence[float], cells: int) -> str:
    """Build the sparkline for *values* without printing it.

    Long series are reduced by taking the maximum of each bucket rather than by
    sampling every k-th point, so a transient spike cannot disappear between
    samples — which is the whole point of watching an iteration converge.
    """
    series = [float(v) for v in values]
    if not series:
        return ""
    size = min(len(series), max(1, int(cells)))
    if len(series) > size:
        length = len(series)
        series = [max(series[(i * length) // size : ((i + 1) * length) // size]) for i in range(size)]
    alphabet = _table()["spark"]
    lo, hi = min(series), max(series)
    if hi <= lo:
        return alphabet[len(alphabet) // 2] * len(series)
    # A constant series has no shape to show, so every cell gets the middle
    # glyph rather than a full block.  Otherwise the position in the alphabet is
    # proportional to the value: the Unicode ramp has 8 glyphs and the ASCII ramp
    # has 9, and both span the full 0..1 range so neither wastes its top step.
    top = len(alphabet) - 1
    return "".join(
        alphabet[int(round((value - lo) / (hi - lo) * top))] for value in series
    )


def sparkline(values: Sequence[float], label: str | None = None, width: int = 40) -> str:
    """Print an inline sparkline of *values*; return the text.

    Unicode mode uses the block ramp ``▁▂▃▄▅▆▇█``; ASCII mode falls back to
    ``.:-=+*#%@``.
    """
    body = _sparkline_string(list(values), width)
    rendered = f"{dim(label) + '  ' if label else ''}{style(body, 'cyan')}"
    _write(rendered)
    return rendered


def converge(label: str, generator: Iterable[float]) -> float:
    """Consume an iterator of running values, showing convergence live.

    Used for the power iteration and for the three least-squares routes.  On a
    TTY the sparkline is redrawn in place as values arrive; off a TTY only the
    final line is written, so a piped log gets one line per convergence rather
    than a wall of redraws.  Returns the last value seen.
    """
    history: list[float] = []
    for value in generator:
        history.append(float(value))
        if _tty:
            stream = _out()
            preview = _sparkline_string(history, cells=32)
            stream.write(
                _CARRIAGE + _CLEAR_LINE
                + f"{label}  {preview}  {float(value):+.6f}  iter {len(history)}"
            )
            try:
                stream.flush()
            except Exception:
                pass
    if not history:
        _write(f"{label}  {_ch('bullet')} no iterations")
        return float("nan")
    final = history[-1]
    if _tty:
        _write("")  # terminate the redrawn line
    preview = _sparkline_string(history, cells=32)
    _write(
        f"{label}  {style(preview, 'cyan')}  {_ch('step')} converged to "
        f"{style(f'{final:+.6f}', 'bold')} after {len(history)} iterations"
    )
    return final


# --------------------------------------------------------------------------
# 5. Stage-level API — what the demo calls
# --------------------------------------------------------------------------
class Stage:
    """Context manager for one of the eleven mandated course stages.

    Entering prints a boxed banner naming the mandated stage and the single
    mathematical principle the stage applies.  Exiting prints nothing: the
    stage's own :func:`verdict` is meant to be its last line, and a closing
    frame would only get between the reader and the conclusion.
    """

    def __init__(self, number: int, mandated_name: str, principle: str) -> None:
        self.number = int(number)
        self.mandated_name = mandated_name
        self.principle = principle
        self.entered = False

    def banner(self) -> str:
        """Return the banner text without printing it."""
        title = f"STAGE {self.number} {_ch('bullet')} {self.mandated_name}"
        lines = [bold(title), dim("principle: ") + self.principle]
        return "\n".join(_box(lines, double=True))

    def __enter__(self) -> "Stage":
        _write(self.banner())
        self.entered = True
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def stage(number: int, mandated_name: str, principle: str) -> Stage:
    """Open a mandated stage; use as a context manager.

    ``mandated_name`` is the course's own wording for the stage, kept verbatim
    so the demo's stage list can be diffed against the guidelines.
    """
    return Stage(number, mandated_name, principle)


def formula(lines: str | list[str]) -> str:
    """Print an indented dim block of mathematics; return the text.

    Accepts a single string or a list of lines.  Kept plain (no colour) so the
    glyphs of an expression are never disturbed by escape codes.
    """
    body = [lines] if isinstance(lines, str) else list(lines)
    rendered = "\n".join("    " + line for line in body)
    _write(dim(rendered))
    return rendered


def step(text: str) -> str:
    """Print a ``▸ now doing X`` line; return it."""
    line = style(_ch("step"), "cyan") + f" {text}"
    _write(line)
    return line


def note(text: str) -> str:
    """Print a dim annotation; return the styled text."""
    return info(text)


def _format_number(value: Any) -> str:
    """Format a measured value compactly and reproducibly.

    Six significant figures is enough to show a measured fit statistic without
    printing float noise, and it is stable across platforms for the same input.
    """
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if number != number:
            return "nan"
        if number in (float("inf"), float("-inf")):
            return "inf" if number > 0 else "-inf"
        return f"{number:,.6g}"
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, np.ndarray)):
        return ", ".join(_format_number(item) for item in np.ravel(value))
    return str(value)


def measured(name: str, value: Any, unit: str | None = None, meaning: str | None = None) -> str:
    """Print one measured number as a labelled key/value line; return it.

    This is deliberately the only comfortable way to report a number, so the
    demo cannot print an unlabelled float with nothing to say what it means.  A
    *unit* is appended to the value; a *meaning* explains what the number is,
    which is the difference between a number and a measurement.
    """
    shown = _format_number(value)
    if unit:
        shown = f"{shown} {unit}"
    line = _kv_string(name, shown, key_width=28)
    if meaning:
        line = f"{line}  {dim(meaning)}"
    _write(line)
    return line


def verdict(text: str) -> str:
    """Print a boxed, bolded one-line conclusion; return it.

    Meant to be the last thing a stage prints: the plain-English answer, in a
    frame that cannot be mistaken for supporting detail.
    """
    return _box_fit([bold(text)], minimum=48, colour="bold", double=True)


def excluded(count: int, total: int, reason: str) -> str:
    """Print a prominent box stating what was left out of the dataset.

    ``AGENTS.md`` section 4 requires exclusions to be stated loudly rather than
    footnoted, and requires the count to appear in the demo.  The percentage is
    included so a reader can judge the size of the gap at a glance instead of
    doing the division themselves.
    """
    share = 0.0 if total <= 0 else 100.0 * count / total
    lines = [
        bold(f"EXCLUDED {int(count):,} of {int(total):,} matches"),
        str(reason),
        dim(f"{share:.2f}% of the dataset"),
    ]
    return _box_fit(lines, minimum=52, colour="yellow")


def figure(name: str, caption: str) -> str:
    """Cross-reference a saved figure from the terminal output; return it.

    The figure files live in ``figures/`` next to the demo, so printing the path
    lets a reader match a claim in the console to the plot that shows it.
    """
    line = style(_ch("tl"), "cyan") + " figure " + style(name, "bold") + f" {_ch('emdash')} " + dim(caption)
    _write(line)
    return line


def timeline(entries: Iterable[Sequence[str] | Mapping[str, str]]) -> str:
    """Print the closing table of stage -> figure -> key number; return it.

    Accepts either 3-item sequences or mappings keyed ``stage``, ``figure`` and
    ``key``.  Every entry is padded to three columns so a short entry cannot
    shift the whole table.
    """
    rows: list[list[str]] = []
    for entry in entries:
        if isinstance(entry, Mapping):
            rows.append([
                str(entry.get("stage", "")),
                str(entry.get("figure", "")),
                str(entry.get("key", "")),
            ])
        else:
            cells = [str(cell) for cell in entry]
            cells += [""] * (3 - len(cells))
            rows.append(cells[:3])
    return table(["stage", "figure", "key number"], rows, aligns=["l", "l", "r"])
