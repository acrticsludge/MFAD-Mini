"""Acceptance tests for the demo, the report and the CLI.

What is pinned here and why
---------------------------
The five other test files pin the *mathematics*: the counts, the shapes, the
rank, the sign of R-squared, the Spearman values. This file pins the
**deliverable**: that ``python -m iplranking`` exits 0, that it narrates all
eleven mandated stages in the guidelines' order, that it writes thirteen valid
PNGs and a self-contained ``report.html``, and that two runs produce
byte-identical output. Those are the properties a marker sees, and none of them
is implied by the mathematics being right.

Three of these tests exist because the project has already paid for the failure
they prevent:

1. :func:`test_stage_banners_appear_in_ascending_order` and
   :func:`test_matrix_simplification_precedes_structure_of_the_space` are the
   regression test for the **stage transposition** that lived in this project's
   documents for two full runs. Matrix Simplification is stage 3 and Structure
   of the Space is stage 4; the terminal output is now the single place that
   order is written down, and it is asserted rather than reviewed.
2. :func:`test_terminal_output_reports_both_r_squared_values` and
   :func:`test_report_reports_both_r_squared_values` pin the **two denominators**.
   The inherited build audit, the handoff and the earlier spec headline only the
   uncentred ``+0.0214``; that hides that the model is worse than predicting the
   mean. Both values, each labelled with its denominator, or the run fails.
3. :func:`test_report_contains_no_external_resource_reference` pins
   **self-containment**, which ``AGENTS.md`` section 7 makes a mark-bearing
   requirement: a report that fails because a CDN is unreachable costs the same
   marks as a demo that fails because a website is down.

Section 7 was added for a fourth failure of the same kind, and it is the only
one here that runs the demo **outside** this process:
``pyproject.toml`` deliberately declares no build backend, so nothing is
installed, ``python -m iplranking`` cannot find the package, and the demo was
reachable only by exporting ``PYTHONPATH`` by hand or by running it through
pytest. A demo that needs an undocumented environment variable costs the same
marks as one that needs a website. :func:`test_launcher_exits_zero_without_an_install`
is the regression test, and its three load-bearing properties are that it runs
with an environment containing **no** ``PYTHONPATH``, from **two** working
directories, and that :func:`test_the_child_environment_cannot_import_the_package`
proves the environment is not what is making it work.

Nothing in this file weakens, skips or relaxes anything in the other five. The
suite as a whole was 187 tests green before this file existed, and 211 green
before section 7 was added; both must stay green. Run ``python -m pytest -q``
and check the count.
"""

from __future__ import annotations

import io
import numpy as np
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from iplranking import console
from iplranking import demo
from iplranking import figures as fig
from iplranking.__main__ import main

#: Every figure the demo must write, in stage order. Cross-checked against
#: ``figures.FIGURE_NAMES`` so adding a figure there without naming it in the
#: demo fails here rather than being silently skipped.
EXPECTED_FIGURES: tuple[str, ...] = (
    "01-data.png",
    "02-design-matrix.png",
    "03-rref.png",
    "04-structure.png",
    "05-redundancy.png",
    "06-qr.png",
    "07-projection.png",
    "08-least-squares.png",
    "09-eigen.png",
    "10-diagonalisation.png",
    "11-ranking.png",
    "12-findings.png",
    "13-divergence.png",
)

#: The PNG magic number, byte for byte. A file with the right extension and the
#: wrong bytes is a worse failure than a missing one, so the bytes are checked.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: The two R-squared values, as the demo prints them, each with its sign. The
#: centred one is the standard coefficient of determination and it is negative.
R2_CENTRED = "-0.2103"
R2_UNCENTRED = "+0.0214"

#: The exclusion that must be stated out loud rather than footnoted.
EXCLUSION = "EXCLUDED 25 of 1,243 matches"

#: The refuted hypothesis. If this string disappears the project has started
#: hiding the measurement that refuted an inherited prediction.
REFUTED = "refuted, and reported"


# --------------------------------------------------------------------------
# One shared run
# --------------------------------------------------------------------------


def _run_into(directory: Path) -> SimpleNamespace:
    """Run the whole CLI into *directory*, capturing stdout; return the pieces.

    ``figures.figure_dir`` and ``figures.report_dir`` are redirected rather than
    the outputs being read from the repository, so the test never depends on --
    or clobbers -- whatever a developer has already generated. Both are functions
    for exactly this reason, and this is the caller that uses it.
    """
    buffer = io.StringIO()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(fig, "figure_dir", lambda: directory / "figures")
        patch.setattr(fig, "report_dir", lambda: directory / "report")
        try:
            code = main(["--offline", "--width", "88"], stdout=buffer)
        finally:
            # The renderer keeps its stream and width in module globals. Leaving
            # them pointed at a closed StringIO would break every later test that
            # prints, and the leak would be very hard to see.
            console.init()
            console.set_width(None)
    return SimpleNamespace(
        code=code,
        text=buffer.getvalue(),
        directory=directory,
        files=sorted(p for p in directory.rglob("*") if p.is_file()),
    )


@pytest.fixture(scope="module")
def first_run(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """One full ``python -m iplranking --offline``, into a temporary directory."""
    return _run_into(tmp_path_factory.mktemp("first-run"))


@pytest.fixture(scope="module")
def report_html(first_run: SimpleNamespace) -> str:
    """The generated ``report/report.html``, read once."""
    path = first_run.directory / "report" / "report.html"
    assert path.is_file(), f"{path} was not written"
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# 1. The command succeeds
# --------------------------------------------------------------------------


def test_main_returns_zero(first_run: SimpleNamespace) -> None:
    """``python -m iplranking`` must succeed: this is the deliverable's entry point.

    A non-zero exit here fails a marker running the project, whatever the
    mathematics underneath is doing.
    """
    assert first_run.code == 0


def test_main_returns_non_zero_when_a_stage_fails(tmp_path: Path) -> None:
    """A crashed stage must not look like a finished run.

    ``Progress`` already refuses to print 100% over an aborted run, and this is
    the same rule one level up: the exit code is what a marker or a CI step
    actually reads, so a failure has to be visible in it.
    """
    errors = io.StringIO()

    def explode(**_kwargs: object) -> object:
        raise RuntimeError("simulated stage failure")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(demo, "run_demo", explode)
        code = main(["--offline"], stdout=io.StringIO(), stderr=errors)
    try:
        assert code == 2
        assert "simulated stage failure" in errors.getvalue()
    finally:
        console.init()
        console.set_width(None)


def test_assert_offline_holds_the_block_until_released() -> None:
    """The offline guard must HOLD the block for the run, then restore cleanly.

    It works by replacing ``__import__`` and ``socket.socket``, which is the
    strong way to prove the run cannot reach the network. This test was rewritten
    when the guard changed: it previously asserted that ``assert_offline``
    restored the hooks *inside itself*, which was exactly the defect -- it
    restored them before ``run_demo`` had run, so a fetch during the run would
    have succeeded while the code claimed otherwise. The contract is now
    install-and-hold, with ``release_offline`` as the only restore point, so a
    guard that leaked would still break every later import and is still pinned.
    """
    import builtins
    import socket

    original_import = builtins.__import__
    original_socket = socket.socket
    try:
        assert demo.assert_offline() is None
        # Installed and held -- NOT restored.
        assert builtins.__import__ is not original_import
        assert socket.socket is not original_socket
        # And the block is real, not cosmetic.
        import pytest

        with pytest.raises(demo.NetworkBlockedError):
            builtins.__import__("urllib.request")
        with pytest.raises(demo.NetworkBlockedError):
            socket.socket()
    finally:
        demo.release_offline()
        assert builtins.__import__ is original_import
        assert socket.socket is original_socket
        console.init()
        console.set_width(None)


def test_a_network_import_during_the_run_exits_one(monkeypatch: pytest.MonkeyPatch) -> None:
    """A network reach *inside* ``run_demo`` must stop the run with exit code 1.

    The defect this pins: the guard used to be removed before the run started, so
    the exit-1 path was unreachable and the promise in the help text was false.
    ``run_demo`` is wrapped, not replaced, so the guard is exercised exactly where
    it has to work.
    """
    import io

    real_run = demo.run_demo

    def reach_for_the_network(**kwargs: object) -> object:
        import urllib.request  # noqa: F401  -- the point of the test

        return real_run(**kwargs)  # pragma: no cover - never reached

    monkeypatch.setattr(demo, "run_demo", reach_for_the_network)
    stderr = io.StringIO()
    code = main(["--offline", "--no-report"], stdout=io.StringIO(), stderr=stderr)
    assert code == 1
    assert "offline violation" in stderr.getvalue()


def test_the_child_environment_cannot_import_the_package() -> None:
    """Negative control for the launcher tests: an empty env cannot import it.

    Without this, the launcher tests could pass because of ambient state rather
    than because ``run_demo.py`` puts ``src`` on the path itself.
    """
    import subprocess

    probe = subprocess.run(
        [sys.executable, "-c", "import iplranking"],
        capture_output=True,
        env={"SystemRoot": os.environ.get("SystemRoot", ""), "PATH": ""},
        cwd=str(REPO_ROOT),
    )
    assert probe.returncode != 0


# --------------------------------------------------------------------------
# 2. Thirteen figures, and they are real PNGs
# --------------------------------------------------------------------------


def test_thirteen_figures_were_written(first_run: SimpleNamespace) -> None:
    """One figure per stage, and three for stage 11. All thirteen, none missing."""
    written = {p.name for p in first_run.files}
    missing = [name for name in EXPECTED_FIGURES if name not in written]
    assert missing == [], f"figures not written: {missing}"
    assert len(EXPECTED_FIGURES) == 13
    assert tuple(fig.FIGURE_NAMES) == EXPECTED_FIGURES


def test_every_figure_is_a_valid_png(first_run: SimpleNamespace) -> None:
    """Magic bytes and a plausible size, for all thirteen.

    ``figures._save`` pins the ``Software`` metadata tag and never writes a
    timestamp, so byte-identity between runs is achievable; what is checked here
    is that the bytes are a PNG at all and are not a stub.
    """
    for name in EXPECTED_FIGURES:
        path = first_run.directory / "figures" / name
        assert path.is_file(), name
        raw = path.read_bytes()
        assert raw[: len(PNG_MAGIC)] == PNG_MAGIC, f"{name} is not a PNG"
        assert len(raw) > 10_000, f"{name} is only {len(raw)} bytes: a stub, not a plot"


def test_no_escape_byte_reaches_piped_output(first_run: SimpleNamespace) -> None:
    """A redirected run must contain no raw ESC, ever.

    ``console.style`` returns its argument unchanged when colour is off, which is
    the structural guarantee; this is the measurement of it. A ``0x1b`` in a
    redirected log is how a "clean" run turns into escape soup on someone
    else's machine.
    """
    assert "\x1b" not in first_run.text
    assert "\r" not in first_run.text, "a carriage return means an in-place redraw leaked into a pipe"


# --------------------------------------------------------------------------
# 3. The report is written and is self-contained
# --------------------------------------------------------------------------


def test_report_html_was_written(first_run: SimpleNamespace) -> None:
    path = first_run.directory / "report" / "report.html"
    assert path.is_file()
    assert path.stat().st_size > 200_000, "the report should carry 13 inlined PNGs"


def test_report_inlines_every_figure_as_base64(report_html: str) -> None:
    """Thirteen ``data:`` URIs and no other image source."""
    assert report_html.count("data:image/png;base64,") == 13


def test_report_contains_no_external_resource_reference(report_html: str) -> None:
    """No external CSS, no JS, no CDN, no font fetch. Self-contained or useless.

    The check parses every ``src`` and ``href`` attribute in the document and
    requires that none of them points at a scheme or a protocol-relative URL. The
    cricsheet URL *does* appear in the page -- it has to, it is the attribution
    -- but as text inside a paragraph, where a browser will not fetch it.
    """
    targets = re.findall(r"""(?:src|href)\s*=\s*["']?([^"'\s>]+)""", report_html)
    external = [
        t for t in targets
        if t.lower().startswith(("http://", "https://", "//", "ftp:", "data:text/html"))
    ]
    assert external == [], f"external resource references found: {external}"
    assert "<script" not in report_html.lower(), "the report must carry no script at all"
    assert "@import" not in report_html.lower()
    assert "url(http" not in report_html.lower().replace(" ", "")


def test_report_contains_every_stage_heading(report_html: str) -> None:
    """One section per mandated stage, in the mandated order."""
    for number, name, _ in demo.STAGES:
        assert f"Stage {number} &mdash; {name}" in report_html, f"stage {number} heading missing"
        assert f'id="stage-{number}"' in report_html, f"stage {number} section missing"
    positions = [report_html.index(f"Stage {n} &mdash; ") for n, _, _ in demo.STAGES]
    assert positions == sorted(positions), "stage sections are out of order in the report"


def test_report_reports_both_r_squared_values(report_html: str) -> None:
    """Both denominators, each labelled. Quoting one hides the finding."""
    assert R2_CENTRED in report_html, "the centred R-squared is missing"
    assert R2_UNCENTRED in report_html, "the uncentred R-squared is missing"
    assert "centred" in report_html
    assert "uncentred" in report_html


def test_report_states_the_exclusions(report_html: str) -> None:
    """25 of 1,243 with no winner, and 660 of 1,243 wicket-only. In the page."""
    assert "25 of 1,243 matches" in report_html
    assert "660 of 1,243" in report_html


def test_report_asserts_no_unread_licence_term(report_html: str) -> None:
    """Precise attribution, and no licence claim read from nowhere.

    ``AGENTS.md`` section 7: no licence statement for the match data was read
    from the primary source, so none may be asserted. The page may *mention* the
    ODC-BY claim third-party sites make, but only to say it is not proof.
    """
    lowered = report_html.lower()
    assert "no licence term asserted" in lowered
    assert "404" in report_html, "the licence block should say the site's licence path 404s"
    assert "attribution is therefore by" in lowered


def test_report_reports_the_refuted_hypothesis(report_html: str) -> None:
    """The refutation is in the deliverable, not only in a code comment."""
    assert "refuted" in report_html.lower()
    assert "17.43" in report_html and "25.64" in report_html
    assert "cricketer" not in report_html  # sanity: no placeholder text survived


# --------------------------------------------------------------------------
# 4. Determinism: two runs, byte for byte
# --------------------------------------------------------------------------


def test_two_runs_produce_byte_identical_files(
    tmp_path: Path, first_run: SimpleNamespace
) -> None:
    """Every file of run 2 is byte-identical to run 1: 13 PNGs and report.html.

    This is the acceptance criterion that keeps the honesty claims honest. If a
    timestamp, a hash of a set iteration order or a random start reached an
    artefact, the bytes would differ and this fails with the file name attached.
    """
    second = _run_into(tmp_path / "second-run")
    assert second.code == 0

    first_by_name = {p.name: p for p in first_run.files}
    second_by_name = {p.name: p for p in second.files}
    assert sorted(first_by_name) == sorted(second_by_name), (
        f"the two runs wrote different file sets: "
        f"{sorted(set(first_by_name) ^ set(second_by_name))}"
    )
    assert len(first_by_name) == 14, "13 figures + report.html"

    for name in sorted(first_by_name):
        left = first_by_name[name].read_bytes()
        right = second_by_name[name].read_bytes()
        assert left == right, f"{name} differs between two runs of the same code"


def test_two_runs_produce_byte_identical_terminal_output(
    tmp_path: Path, first_run: SimpleNamespace
) -> None:
    """The walkthrough itself is deterministic, not only the files.

    The renderer fixes its width at 88 when stdout is not a TTY precisely so
    that a redirected run cannot vary with the window it was produced in. If
    that ever regressed, a diff of two runs would show a wall of whitespace
    changes and hide the changes that matter.

    The two lines naming the report file are compared separately, because those
    are the only lines that may legitimately differ: the two runs write into two
    different directories, and the path of the artefact is not a measurement.
    Every other line -- all 42,000-odd characters of the walkthrough -- must be
    byte-identical, and the file names must agree.
    """
    second = _run_into(tmp_path / "second-run")
    assert "report.html" in first_run.text, "the run never says it wrote a report"
    assert "report.html" in second.text
    assert _narration(second.text) == _narration(first_run.text), (
        "two runs printed different terminal output"
    )
    assert len(first_run.text.splitlines()) > 300, "the walkthrough looks truncated"


def _narration(text: str) -> str:
    """The walkthrough with the report-path lines removed.

    Those lines embed the absolute output directory, which is the one thing two
    runs into different directories are *supposed* to disagree about.
    """
    return "\n".join(
        line for line in text.splitlines() if "report.html" not in line
    )


# --------------------------------------------------------------------------
# 5. Stage order -- the transposition regression test
# --------------------------------------------------------------------------


def _banner_positions(text: str) -> list[int]:
    """First offset of each stage banner, in the order the banners appear.

    The trailing ``" - "`` in the search key matters: ``"STAGE 1 - "`` cannot
    match ``"STAGE 10 - "`` or ``"STAGE 11 - "``, so stage 1 and stage 10 are
    never confused for one another.
    """
    positions: list[int] = []
    for number in range(1, len(demo.STAGES) + 1):
        key = f"STAGE {number} - "
        offset = text.find(key)
        assert offset >= 0, f"stage {number} banner never printed"
        positions.append(offset)
    return positions


def test_stage_banners_appear_in_ascending_order(first_run: SimpleNamespace) -> None:
    """Stages 1..11 first appear in ascending order.

    **This is the regression test.** Matrix Simplification and Structure of the
    Space were transposed in this project's documents for two full runs, and
    only adversarial review caught it. The terminal walkthrough is now the one
    place the order is written down, and the order is asserted here rather than
    read.
    """
    positions = _banner_positions(first_run.text)
    assert positions == sorted(positions), (
        "stage banners are out of order: "
        + ", ".join(
            f"stage {n + 1} at {pos}"
            for n, pos in enumerate(positions)
        )
    )


def test_matrix_simplification_precedes_structure_of_the_space() -> None:
    """Stage 3 is Matrix Simplification; stage 4 is Structure of the Space.

    Stated separately from the ordering assertion above so that a failure names
    the transposition instead of a list of offsets. ``AGENTS.md`` section 5
    gives the order, and the order was re-verified against page 2 of the
    guidelines PDF on 2026-10-02.
    """
    by_number = {number: name for number, name, _ in demo.STAGES}
    assert by_number[3] == "MATRIX SIMPLIFICATION"
    assert by_number[4] == "STRUCTURE OF THE SPACE"
    assert [n for n, _, _ in demo.STAGES] == list(range(1, 12))


def test_every_stage_declares_a_principle_a_formula_and_a_verdict() -> None:
    """A stage that cannot say what it is computing is not narrated.

    ``AGENTS.md`` section 10 forbids padding a stage to look rigorous; the
    complement is required here -- every stage must name the principle it
    applies, and the banner it prints must actually carry that principle rather
    than an empty slot. :class:`iplranking.console.Stage` is used through its
    public constructor, so this tests the stage list and the renderer's contract
    together, with no scraping of the run's output.
    """
    assert len(demo.STAGES) == 11
    for number, name, principle in demo.STAGES:
        assert name.strip(), f"stage {number} has no mandated name"
        assert len(principle.split()) >= 6, f"stage {number} principle is not a sentence"
        assert principle == principle.strip()
        banner = console.stage(number, name, principle).banner()
        assert f"STAGE {number}" in banner
        # The banner truncates its line at the render width, so the first 40
        # characters of the principle are what must survive onto the terminal.
        assert "principle: " in banner
        assert principle[:40] in banner


# --------------------------------------------------------------------------
# 6. The numbers the terminal must state
# --------------------------------------------------------------------------


def test_terminal_output_reports_the_exclusion(first_run: SimpleNamespace) -> None:
    """25 of 1,243 matches with no winner, stated out loud, not in a footnote."""
    assert EXCLUSION in first_run.text
    assert "660" in first_run.text
    assert "1,243" in first_run.text


def test_terminal_output_reports_both_r_squared_values(first_run: SimpleNamespace) -> None:
    """Both R-squared values appear in the terminal output.

    The centred value is the standard coefficient of determination and it is
    negative: the model is worse than predicting the mean margin. The uncentred
    value is positive and would read, on its own, as a small fit. Reporting both
    is the whole correction, so this asserts the strings, not the arithmetic --
    ``tests/test_diagnostics.py`` already pins the arithmetic.
    """
    assert R2_CENTRED in first_run.text
    assert R2_UNCENTRED in first_run.text
    assert "denominator" in first_run.text


def test_terminal_output_reports_the_refuted_hypothesis(first_run: SimpleNamespace) -> None:
    """Frequency balancing made it worse. The refutation is in the output."""
    assert REFUTED in first_run.text
    assert "17.43" in first_run.text and "25.64" in first_run.text


def test_terminal_output_reports_all_thirteen_figures(first_run: SimpleNamespace) -> None:
    """Every saved figure is cross-referenced in the walkthrough."""
    for name in EXPECTED_FIGURES:
        assert name in first_run.text, f"{name} was saved but never referenced in the output"


def test_timeline_covers_all_eleven_stages() -> None:
    """The closing stage -> figure -> key number table has one row per stage.

    Built through ``console.timeline`` on synthetic rows so this checks the
    table's shape, not the demo's data; the real table's contents are visible in
    the run and its figure list is checked above.
    """
    rows = [(f"{n} {name}", "00-x.png", "1.23") for n, name, _ in demo.STAGES]
    rendered = console.timeline(rows)
    for number, name, _ in demo.STAGES:
        assert f"{number} {name}" in rendered
    assert "stage" in rendered and "key number" in rendered
    console.init()


# --------------------------------------------------------------------------
# 7. The zero-install launcher: subprocess, no environment, two directories
# --------------------------------------------------------------------------


#: ``<repo root>``: ``tests/`` -> ``ipl-power-ranking/`` -> the root that holds
#: ``data/``, ``figures/`` and ``report/``. The same walk ``iplranking.data``
#: does, kept independent of it so a change there cannot quietly redefine it.
REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "ipl-power-ranking"

#: The one entry point a user is told to run. ``python -m iplranking`` cannot
#: work: ``pyproject.toml`` declares no build backend on purpose
#: (``AGENTS.md`` section 8), so nothing is installed and ``src/`` is not on the
#: interpreter's path. pytest gets it from ``pythonpath = ["src"]``;
#: ``python -m`` does not read ``pyproject.toml``.
LAUNCHER = PACKAGE_ROOT / "scripts" / "run_demo.py"

#: The **complete** set of environment variables a launcher subprocess is given.
#:
#: What matters here is what is absent: no ``PYTHONPATH``, no project variable,
#: no user config. Measured 2026-10-05 on this machine rather than assumed --
#: with only ``SystemRoot`` and ``PATH`` the child cannot even ``import
#: matplotlib``, because Pillow is installed in the *per-user* site-packages
#: directory (``%APPDATA%\\Python\\Python314\\site-packages``) and CPython only
#: adds that to ``sys.path`` when it can resolve ``APPDATA``.
#: ``LOCALAPPDATA``/``TEMP``/``TMP`` are carried so Matplotlib reuses its
#: existing font cache instead of building a throwaway one per run (~2 s each,
#: and a warning on stderr). None of the six has any bearing on how the package
#: is found, and :func:`test_the_child_environment_cannot_import_the_package` is
#: the proof of that rather than an assertion about it.
CHILD_ENV_KEYS: tuple[str, ...] = (
    "SystemRoot",
    "PATH",
    "APPDATA",
    "LOCALAPPDATA",
    "TEMP",
    "TMP",
)

#: Generous, because each of the three runs below is a full demo: 13 PNGs and a
#: 2.4 MB report. A hang should fail the test, not wedge the suite.
LAUNCH_TIMEOUT_SECONDS = 900


def _child_env() -> dict[str, str]:
    """An environment built from scratch, holding only :data:`CHILD_ENV_KEYS`."""
    env = {key: os.environ[key] for key in CHILD_ENV_KEYS if os.environ.get(key)}
    assert "PYTHONPATH" not in env, (
        "this environment exists to have no PYTHONPATH in it; if the parent shell "
        "sets one, the launcher tests below stop testing anything"
    )
    return env


def _launch(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """Run *script* in a subprocess, from *cwd*, with the minimal environment."""
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        env=_child_env(),
        capture_output=True,
        timeout=LAUNCH_TIMEOUT_SECONDS,
    )


def _why(run: subprocess.CompletedProcess[bytes]) -> str:
    """A failure message that carries the evidence, because 'exit 1' teaches nothing."""
    return (
        f"command: {run.args}\n"
        f"exit code: {run.returncode}\n"
        f"--- stderr ---\n{run.stderr.decode('utf-8', 'replace')[-4000:]}"
    )


def _stdout(run: subprocess.CompletedProcess[bytes]) -> str:
    """The subprocess's stdout as text.

    The round-trip is asserted so a decode can never quietly substitute
    characters and then pass a substring search. Measured: piped demo output is
    pure ASCII (0 bytes above 0x7f), because ``console`` selects its ASCII glyph
    table when the stream is not a TTY and Windows would otherwise hand a
    ``cp1252`` pipe. This is why the capture is a PIPE and not a shell
    redirect.
    """
    text = run.stdout.decode("utf-8")
    assert text.encode("utf-8") == run.stdout, "stdout is not valid UTF-8"
    return text


def _stage(root: Path) -> Path:
    """Mirror the smallest tree the demo needs into *root*; return the package root.

    The layout copied is the real one: ``<root>/ipl-power-ranking/src/iplranking``
    beside ``<root>/ipl-power-ranking/scripts/run_demo.py``, with ``<root>/data``
    next to them. ``iplranking.data`` derives its root by walking up from its own
    ``__file__``, so ``figures/`` and ``report/`` are created inside the temporary
    tree and **nothing is written into the developer's checkout** -- which is why
    the in-process tests above redirect ``figures.figure_dir`` and this one
    relocates the whole project instead.
    """
    package = root / "ipl-power-ranking"
    shutil.copytree(
        PACKAGE_ROOT / "src",
        package / "src",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (package / "scripts").mkdir(parents=True)
    shutil.copy2(LAUNCHER, package / "scripts" / LAUNCHER.name)
    shutil.copytree(REPO_ROOT / "data", root / "data")
    return package


@pytest.fixture(scope="module")
def launcher_runs(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """Three full launches of the launcher, each a real run of the whole demo.

    ``package_root`` and ``repo_root`` carry identical arguments and differ only
    in the working directory -- the pair that makes the determinism assertion
    below stronger than comparing a run with itself, and that catches a launcher
    which resolved ``src`` against ``os.getcwd()``. ``no_arguments`` covers the
    bare invocation with no flags at all.
    """
    root = tmp_path_factory.mktemp("zero-install")
    package = _stage(root)
    script = package / "scripts" / LAUNCHER.name
    runs = {
        "package_root": _launch(script, package, "--offline", "--width", "88"),
        "repo_root": _launch(script, root, "--offline", "--width", "88"),
        "no_arguments": _launch(script, package),
    }
    return SimpleNamespace(root=root, package=package, script=script, runs=runs)


def test_the_launcher_is_the_file_the_repository_ships(
    launcher_runs: SimpleNamespace,
) -> None:
    """``scripts/run_demo.py`` exists, and the staged copy is byte-for-byte it.

    Every subprocess test below runs the *staged* copy, so this is what stops
    that from quietly becoming a test of some other file: if the launcher's bytes
    change, this fails until the staged copy is refreshed, and if it is deleted
    the staging raises before a single test can pass.
    """
    assert LAUNCHER.is_file(), f"{LAUNCHER} is missing; the demo has no entry point"
    assert launcher_runs.script.read_bytes() == LAUNCHER.read_bytes()


def test_the_child_environment_cannot_import_the_package(tmp_path: Path) -> None:
    """The negative control: this environment does **not** make the demo work.

    Without it, every other test in this section could pass on the strength of
    something leaking out of pytest's own ``pythonpath = ["src"]`` setting rather
    than of the launcher. Run from the repository root with the same minimal
    environment, ``import iplranking`` must fail; anything that makes it succeed
    has added a rescue path, and the launcher's own result proves nothing.
    """
    probe = subprocess.run(
        [sys.executable, "-c", "import iplranking"],
        cwd=str(REPO_ROOT),
        env=_child_env(),
        capture_output=True,
        timeout=LAUNCH_TIMEOUT_SECONDS,
    )
    assert probe.returncode != 0, (
        "the package imported with no PYTHONPATH and no install; the launcher "
        "tests in this section would then be measuring the environment, not the "
        "launcher"
    )
    assert b"iplranking" in probe.stderr


@pytest.mark.parametrize("label", ["package_root", "repo_root"])
def test_launcher_exits_zero_without_an_install(
    launcher_runs: SimpleNamespace, label: str
) -> None:
    """The regression test for the defect: ``python scripts/run_demo.py`` works.

    Measured 2026-10-05 with no environment and no install step,
    ``python -m iplranking`` failed with ``No module named iplranking``, because
    ``pyproject.toml`` declares no build backend on purpose and ``python -m``
    does not read ``pyproject.toml``. ``pyproject.toml`` was not changed -- the
    decision in ``AGENTS.md`` section 8 is right -- so the entry point was fixed
    instead.

    Both working directories are exercised, and they are not equivalent: the
    launcher sits one level below the package root, so a ``cwd``-relative ``src``
    resolves correctly from one of them and fails from the other.
    """
    run = launcher_runs.runs[label]
    assert run.returncode == 0, _why(run)
    assert run.stderr == b"", "the demo wrote to stderr on a clean run:\n" + _why(run)


@pytest.mark.parametrize("label", ["package_root", "repo_root", "no_arguments"])
def test_launcher_narrates_all_eleven_stages_in_order(
    launcher_runs: SimpleNamespace, label: str
) -> None:
    """Banners ``STAGE 1 - `` through ``STAGE 11 - ``, first seen in order.

    Read out of real subprocess stdout with :func:`_banner_positions`, the same
    helper the in-process ordering test uses, so "the stages are in order" is
    one assertion in this project rather than two that can disagree. That helper
    also searches for the trailing ``" - "``, which is what keeps ``STAGE 1``
    from matching ``STAGE 10``.
    """
    text = _stdout(launcher_runs.runs[label])
    positions = _banner_positions(text)
    assert positions == sorted(positions), (
        f"stage banners are out of order in the {label} run: "
        + ", ".join(f"stage {n} at {pos}" for n, pos in enumerate(positions))
    )
    assert len(text.splitlines()) > 300, "the walkthrough looks truncated"


def test_launcher_output_is_byte_identical_across_working_directories(
    launcher_runs: SimpleNamespace,
) -> None:
    """Two runs, two directories, identical bytes. Determinism is not local.

    ``AGENTS.md`` section 4: an unmeasured claim about this project has already
    cost real work twice. This is the measured version -- same code, same
    arguments, different ``cwd``, byte-identical stdout -- so a path that leaked
    the working directory into the output cannot get through. The report-path
    lines are excluded by :func:`_narration` because the two runs do write to two
    different directories, and that path is not a measurement.
    """
    left = launcher_runs.runs["package_root"]
    right = launcher_runs.runs["repo_root"]
    assert left.returncode == 0, _why(left)
    assert right.returncode == 0, _why(right)
    assert left.stdout == right.stdout, (
        "the launcher printed different bytes from two different working "
        "directories; first difference at offset "
        f"{next((i for i, (a, b) in enumerate(zip(left.stdout, right.stdout)) if a != b), min(len(left.stdout), len(right.stdout)))}"
    )


def test_launcher_runs_with_no_arguments_at_all(launcher_runs: SimpleNamespace) -> None:
    """``python scripts/run_demo.py`` on its own is a full, successful run.

    Not an edge case to be tolerated but the invocation a marker will actually
    type. The absence of the ``--offline`` banner is asserted too, so this also
    pins that the launcher forwards the arguments it is given rather than
    supplying flags of its own.
    """
    run = launcher_runs.runs["no_arguments"]
    assert run.returncode == 0, _why(run)
    text = _stdout(run)
    assert "offline mode:" not in text, (
        "--offline was not passed, so its confirmation must not appear: the "
        "launcher must not invent flags"
    )
    assert "data/matches.csv" in text.replace("\\", "/"), (
        "the demo did not report reading the committed snapshot"
    )


def test_launcher_prints_nothing_of_its_own(
    launcher_runs: SimpleNamespace, first_run: SimpleNamespace
) -> None:
    """The launcher's output is the demo's output, byte for byte.

    Compared against the in-process run above, which calls the same ``main()``
    with no launcher in the path at all. A launcher that greeted the user, or
    printed a hint, or reordered anything, fails here. ``_narration`` drops only
    the lines naming the output directory, because the two runs write to two
    different places.
    """
    launched = _stdout(launcher_runs.runs["package_root"])
    assert _narration(launched) == _narration(first_run.text), (
        "the launcher altered the demo's output; it must add nothing"
    )


def test_launcher_writes_its_artefacts_beside_the_package(
    launcher_runs: SimpleNamespace,
) -> None:
    """13 PNGs and the report, in the relocated tree, and nowhere else.

    Two things at once. The demo really did run end to end outside pytest, and
    it resolved its output directories from its own location rather than from the
    directory it happened to be started in -- the same rule the launcher's
    ``sys.path`` line follows, checked on the write side.
    """
    root = launcher_runs.root
    figures = sorted(p.name for p in (root / "figures").glob("*.png"))
    assert tuple(figures) == EXPECTED_FIGURES, (
        f"the launcher run wrote {figures}, not the thirteen expected figures"
    )
    report = root / "report" / "report.html"
    assert report.is_file() and report.stat().st_size > 200_000
    assert not (launcher_runs.package / "figures").exists(), (
        "the run wrote figures into the working directory it was started from"
    )


def test_launcher_forwards_its_arguments_to_the_cli(
    launcher_runs: SimpleNamespace,
) -> None:
    """``--help`` reaches the real parser, and does so before any data is read.

    Cheap, and it separates "the arguments arrived" from "the demo succeeded":
    argparse prints help and exits 0 without loading the snapshot, so this is
    instant while :func:`test_launcher_runs_with_no_arguments_at_all` is not.

    The usage line says ``python -m iplranking``, not ``run_demo.py``, and that
    is deliberate rather than an oversight: :func:`test_launcher_prints_nothing_of_its_own`
    requires the launcher's output to be byte-identical to the module form's, so
    the program name cannot be rewritten.
    """
    run = _launch(launcher_runs.script, launcher_runs.root, "--help")
    assert run.returncode == 0, _why(run)
    text = _stdout(run)
    assert "python -m iplranking" in text
    for flag in ("--offline", "--figures-only", "--width", "--no-report"):
        assert flag in text, f"{flag} is missing from the launcher's --help"


def test_launcher_says_where_it_looked_when_the_package_is_absent(
    tmp_path: Path,
) -> None:
    """A wrong layout gets a named path, not ``No module named iplranking``.

    The bare ``ModuleNotFoundError`` is indistinguishable from the defect this
    launcher exists to fix, so the launcher checks the one file it needs and
    reports the absolute path it expected. Costs nothing on the happy path and is
    the difference between a five-minute fix and a lost demo.
    """
    lonely = tmp_path / "mislabelled" / "scripts"
    lonely.mkdir(parents=True)
    copy = lonely / LAUNCHER.name
    shutil.copy2(LAUNCHER, copy)
    expected = tmp_path / "mislabelled" / "src" / "iplranking" / "__init__.py"

    run = _launch(copy, lonely, "--offline")
    assert run.returncode == 2, _why(run)
    message = run.stderr.decode("utf-8")
    assert str(expected) in message, message
    assert "No module named" not in message, (
        "the launcher fell through to the import error it exists to replace"
    )

# --------------------------------------------------------------------------
# 9. The correction pass: the numbers the project got wrong and fixed
# --------------------------------------------------------------------------


def test_intercept_model_is_the_stage_4_gauge_freedom(first_run: SimpleNamespace) -> None:
    """The negative centred R^2 is structural, and the correction is measured.

    ``A @ 1 = 0`` exactly, so ``A x`` has mean zero while ``mean(b) = +18.04``:
    the fit is 17.30 runs low on *every* match by construction. Adding the one
    constant column ``A`` was never allowed moves centred R^2 from -0.2103 to
    +0.0181. Both numbers are pinned, and so is the fact that the corrected value
    is *still* no signal.
    """
    from iplranking.data import build_systems
    from iplranking.diagnostics import intercept_model, r_squared

    systems = build_systems()
    fit = intercept_model(systems.A, systems.b)

    assert fit.r_squared_centred == pytest.approx(0.0181, abs=5e-5)
    assert fit.intercept == pytest.approx(18.1369, abs=5e-5)
    assert fit.ss_res == pytest.approx(753087.7, abs=0.5)
    assert fit.mean_b == pytest.approx(18.0358, abs=5e-5)
    assert fit.mean_fitted == pytest.approx(0.7344, abs=5e-5)
    assert fit.bias == pytest.approx(17.301479527687835, abs=1e-9)

    # The correction improves the fit and does not rescue it. Both halves matter:
    # asserting only the first would let a future edit call +0.018 "a working
    # model".
    plain = r_squared(systems.b, systems.A @ fit.x * 0.0 + systems.A @ _massey_x(systems), centred=True)
    assert plain < fit.r_squared_centred < 0.05


def _massey_x(systems: object) -> object:
    """The no-intercept least-squares vector, for the comparison above."""
    from iplranking import models

    return models.massey(systems.A, systems.b).x


def test_the_bias_is_arithmetic_not_statistical(first_run: SimpleNamespace) -> None:
    """``mean(b) - mean(A x)`` is the whole correction in one subtraction.

    ``A`` has no intercept *and cannot have one*: every row sums to zero. So the
    model's inability to fit the dataset's level is a property of the matrix, not
    of the data or the noise.
    """
    from iplranking.data import build_systems
    from iplranking.diagnostics import intercept_model

    systems = build_systems()
    assert np.allclose(systems.A.sum(axis=1), 0.0)

    fit = intercept_model(systems.A, systems.b)
    assert fit.bias == pytest.approx(fit.mean_b - fit.mean_fitted, abs=1e-9)
    assert fit.bias > 17.0


def test_noise_and_signal_are_the_same_kind_of_quantity(first_run: SimpleNamespace) -> None:
    """The corrected ratio: two *spreads*, not a data spread against a coefficient.

    The retired figure compared ``std(b)`` (which contains the +18-run level and
    the signal) against ``std(x)`` (a coefficient spread) and called it
    signal-to-noise. Measured here on one scale: 40.79 unexplained against 5.98
    fitted.
    """
    from iplranking.data import build_systems
    from iplranking import models
    from iplranking.diagnostics import noise_vs_signal

    systems = build_systems()
    fit = models.massey(systems.A, systems.b)
    signal = noise_vs_signal(systems.A, systems.b, fit.x)

    assert signal.residual_spread == pytest.approx(40.7850, abs=5e-4)
    assert signal.fitted_spread == pytest.approx(5.9805, abs=5e-4)
    assert signal.ratio == pytest.approx(6.8196, abs=5e-4)
    assert signal.ratio > 1.0


def test_the_model_has_negative_skill_against_the_majority_class() -> None:
    """55.02% loses to 77.96%, so the model is worse than a constant guess.

    The majority baseline is 77.96% -- the first-listed team won 435 of the 558
    run-margin matches. A raw-winner-against-canonical-team1 comparison gives
    62.19%, which scores 88 renamed-franchise wins as losses; that number is
    pinned here only as the *wrong* one, so a future edit cannot reintroduce it.
    """
    from iplranking.data import build_systems, load_matches
    from iplranking import models
    from iplranking.diagnostics import team1_win_share, winner_accuracy
    from iplranking.canon import canonical

    matches = load_matches()
    systems = build_systems()
    fit = models.massey(systems.A, systems.b)

    accuracy = winner_accuracy(systems.A @ fit.x, systems.b)
    share = team1_win_share(matches)

    assert share == pytest.approx(0.7796, abs=5e-5)
    assert accuracy == pytest.approx(0.5502, abs=5e-5)
    assert accuracy < share, "the model beats a constant guess; the finding changed"

    rows = matches[matches.margin_runs.notna() & matches.winner.notna()]
    wrong = rows[rows.canonical_team1.astype(str) == rows.winner.astype(str).map(canonical)]
    assert len(wrong) == 435
    assert round(len(wrong) / len(rows), 4) != pytest.approx(0.6219, abs=1e-4)


def test_the_held_out_split_is_degenerate_from_2018_onward() -> None:
    """Nine consecutive seasons where the first-listed team won every match.

    Pinning this is what stops the 43.2% held-out figure being read as a clean
    out-of-sample estimate, and it is the reason the demo prints the per-season
    table instead of taking the drift on trust.
    """
    from iplranking.data import load_matches
    from iplranking.diagnostics import team1_share_by_season

    share = team1_share_by_season(load_matches())

    assert len(share) == 19
    for season in ("2018", "2019", "2020/21", "2021", "2022", "2023", "2024", "2025", "2026"):
        assert share[season] == pytest.approx(1.0, abs=1e-12), season
    assert share["2007/08"] == pytest.approx(0.542, abs=5e-4)
    assert share["2012"] < 0.5


def test_ridge_does_not_leave_r_squared_invariant() -> None:
    """The retracted claim, pinned as retracted.

    An earlier spec asserted that ridge leaves R^2 unchanged "as a theorem". The
    narrow truth is that the *unregularised* solution minimises ``||Ax - b||``;
    ridge is a constrained fit and on this data is strictly worse. Measured: the
    centred value falls monotonically to -0.2324.
    """
    from iplranking.data import build_systems
    from iplranking import models
    from iplranking.diagnostics import r_squared

    systems = build_systems()
    worst = models.ridge(systems.A, systems.b, 1000.0)
    value = r_squared(systems.b, systems.A @ worst, centred=True)

    assert value == pytest.approx(-0.2324, abs=5e-5)
    plateau = r_squared(systems.b, systems.A @ models.ridge(systems.A, systems.b, 10.0), centred=True)
    assert value < plateau, "ridge stopped hurting; the retraction needs revisiting"


def test_a_truncated_snapshot_is_refused(tmp_path: Path) -> None:
    """A CSV with every column but too few rows must not load silently."""
    from iplranking.data import load_matches

    short = tmp_path / "matches.csv"
    original = REPO_ROOT / "data" / "matches.csv"
    lines = original.read_text(encoding="utf-8").splitlines()
    short.write_text("\n".join(lines[:100]) + "\n", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        load_matches(short)
    assert "1243" in str(excinfo.value)
    assert str(len(lines) - 1) in str(excinfo.value)


def test_the_terminal_no_longer_makes_the_retracted_claims(first_run: SimpleNamespace) -> None:
    """The strings the correction pass retired must not come back.

    Each one was a measured falsehood: "five times" (the ratio is 6.82 on one
    scale), "SNR 0.19" (a data spread over a coefficient spread), "worse than a
    coin flip" (the baseline is 77.96%, not 50%), and the ridge-invariance claim.
    """
    text = first_run.text
    for retired in ("five times", "SNR 0.19", "worse than a coin flip", "worse than the 50%"):
        assert retired not in text, f"retracted claim {retired!r} is back in the narration"

    # And the corrected numbers are present, so the retirement is a replacement
    # rather than a deletion.
    assert "0.0181" in text
    assert "77.96" in text or "78.0" in text
    assert "40.79" in text
    assert "6.82" in text


def test_the_report_carries_the_blocker_and_the_manual_checklist(report_html: str) -> None:
    """The open question and the hand-off list must be on the page, not implied.

    ``AGENTS.md`` section 2 makes the instructor question a hard gate on the whole
    project. A report that buried it would be the quiet omission the rules
    forbid, so its verbatim text and the checklist heading are pinned here.
    """
    assert "What you must do by hand" in report_html
    assert "Open blocker" in report_html
    assert "college football" in report_html
    assert "must submit the book&#x27;s task list" in report_html or "task list on college football" in report_html
    assert "GATING" in report_html


def test_the_report_carries_both_r_squared_values_and_the_correction(report_html: str) -> None:
    """Both denominators AND the intercept correction, so neither can be dropped."""
    assert "-0.2103" in report_html
    assert "+0.0214" in report_html or "0.0214" in report_html
    assert "+0.0181" in report_html
    assert "intercept" in report_html.lower()

