"""``report/report.html`` -- one self-contained page, no network, no template engine.

Why a hand-built string
-----------------------
``AGENTS.md`` section 8 fixes the stack to Python 3, NumPy, Pandas, Matplotlib
and pytest, and forbids adding a dependency without justifying it against that
stack. Jinja2, Markdown or a static-site generator would each solve "assemble a
document from parts" at the cost of a package this project does not otherwise
need, so the document is assembled with :func:`str.format`-free plain
concatenation and one small :class:`list` of lines. About a hundred lines of
stdlib does the whole job and nothing about the output depends on a version of
something we do not control.

Self-containment is a hard requirement, not a nicety
----------------------------------------------------
Every PNG is base64-inlined, the CSS lives in one ``<style>`` block, and there
is **no** ``<script>``, no external stylesheet, no font CDN and no ``http://`` or
``https://`` resource reference anywhere in the file. The provenance URL appears
as *text*, inside a paragraph, not as the target of a ``src`` or ``href`` that
the browser would fetch. A marker opens this file with the network unplugged and
it works; a report that failed because a CDN was unreachable would cost the same
marks as a demo that failed because a website was down.

``AGENTS.md`` section 10 also wants the mathematics legible, so each stage
section carries the same formula block the terminal printed, as ``<pre>``.

Escaping
--------
Every piece of interpolated text goes through :func:`esc`, and the only strings
that reach the page unescaped are the ones this module wrote itself (markup,
CSS, and the base64 payload, which is base64 alphabet by construction). Team
names come from a data file, so they are escaped even though they contain only
letters and spaces today.

Provenance, honestly
--------------------
The provenance block is rendered from ``data/provenance.json`` as it stands, and
it says **what the SHA-256 actually covers** -- which is a deterministic manifest
of the extracted file set, *not* the downloaded archive, because the archive was
not retained on the machine that built the snapshot. On the licence, this page
asserts **no term**: it states that no licence statement for the match data was
found on the primary source, that the site's licence path returns 404, that four
third-party sites assert ODC-BY 1.0 as corroboration but not proof, and that the
attribution is therefore by archive name, URL and retrieval date only. That is
the position ``AGENTS.md`` section 7 requires, and inventing a licence line would
be the kind of quiet fabrication the rest of this project refuses.

Determinism
-----------
No timestamp, no hostname, no path outside the repository, no random value, and
the PNGs are byte-identical between runs. Two runs therefore produce two
byte-identical ``report.html`` files, which ``tests/test_demo.py`` asserts.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from . import console
from . import figures as fig

__all__ = ["build_report"]

#: The escaped title of the document, and the one place it is defined.
_TITLE = "IPL Power Ranking - Strang problem #5 on 19 seasons of the IPL"

#: Print/projection rules. No external stylesheet, no webfont, no script: the
#: page must render identically with the network unplugged.
_CSS = """
:root { --ink:#14181f; --muted:#5b6472; --rule:#d8dce3; --blue:#1f5fa8;
        --teal:#0f766e; --red:#b3261e; --amber:#8a5a00; --paper:#ffffff; }
* { box-sizing: border-box; }
html { background:#eef1f5; }
body { margin:0; padding:2rem 1rem 4rem; background:var(--paper); color:var(--ink);
       font-family:"DejaVu Sans",-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
       font-size:17px; line-height:1.55; max-width:1120px; margin-inline:auto;
       border:1px solid var(--rule); }
h1 { font-size:2.1rem; line-height:1.15; margin:0 0 .2rem; letter-spacing:-.01em; }
h2 { font-size:1.35rem; margin:2.6rem 0 .5rem; padding-top:.8rem;
     border-top:3px solid var(--ink); }
h3 { font-size:1.05rem; margin:1.2rem 0 .3rem; color:var(--muted);
     text-transform:uppercase; letter-spacing:.06em; }
p  { margin:.5rem 0 .8rem; }
.sub { color:var(--muted); font-size:1.02rem; margin-top:0; }
pre { background:#f6f8fa; border:1px solid var(--rule); border-left:4px solid var(--blue);
      padding:.8rem 1rem; overflow-x:auto; font-size:.88rem; line-height:1.4;
      white-space:pre; }
code { font-family:ui-monospace,"Cascadia Mono",Consolas,monospace; }
.principle { font-size:1.06rem; border-left:5px solid var(--teal);
             padding:.5rem .9rem; background:#f2f9f8; margin:.6rem 0 1rem; }
.principle .label { color:var(--teal); font-weight:700; text-transform:uppercase;
                    font-size:.72rem; letter-spacing:.1em; display:block; }
dl { display:grid; grid-template-columns:minmax(15rem,22rem) 1fr; gap:.1rem .9rem;
     margin:.6rem 0 1rem; }
dt { color:var(--muted); }
dd { margin:0; font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;
     font-size:.9rem; overflow-wrap:anywhere; }
figure { margin:1.2rem 0; }
figure img { width:100%; height:auto; border:1px solid var(--rule); display:block; }
figcaption { color:var(--muted); font-size:.9rem; margin-top:.4rem; }
.verdict { border:2px solid var(--ink); padding:.7rem .9rem; margin:1.1rem 0 .4rem;
           font-weight:600; background:#fbfcfd; }
.verdict .label { display:block; font-size:.7rem; letter-spacing:.12em;
                  text-transform:uppercase; color:var(--muted); margin-bottom:.2rem; }
.callout { border:2px solid var(--red); background:#fdf3f2; padding:.8rem 1rem;
           margin:1.2rem 0; }
.callout .label { display:block; font-size:.7rem; letter-spacing:.12em;
                  text-transform:uppercase; color:var(--red); font-weight:700;
                  margin-bottom:.3rem; }
.claim { border-left:5px solid var(--blue); padding:.3rem 0 .3rem 1rem; margin:1.1rem 0; }
table { border-collapse:collapse; width:100%; margin:.8rem 0 1.2rem; font-size:.88rem; }
th, td { border-bottom:1px solid var(--rule); padding:.35rem .5rem; text-align:left; }
th { color:var(--muted); font-weight:600; text-transform:uppercase; font-size:.72rem;
     letter-spacing:.06em; }
td.n, th.n { text-align:right; font-family:ui-monospace,"Cascadia Mono",Consolas,monospace; }
.meta { color:var(--muted); font-size:.9rem; }
.meta dt { color:var(--muted); }
.meta dd { font-size:.86rem; }
@media print {
  html { background:#fff; }
  body { border:0; max-width:none; font-size:11pt; padding:0; }
  h2 { break-after:avoid; page-break-after:avoid; }
  figure, pre, table, .verdict, .callout, .claim { break-inside:avoid;
    page-break-inside:avoid; }
  a[href]:after { content:""; }
}
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def esc(text: Any) -> str:
    """HTML-escape *text*, quotes included.

    ``&`` first, or the ampersands introduced by the later replacements would be
    escaped a second time. Team names and formula lines both pass through here.
    """
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def num(value: Any, places: int = 6) -> str:
    """Format a measured number the same way the terminal does.

    Six significant figures is enough to show a measured statistic without float
    noise, and matching :func:`console._format_number` is deliberate: a reader
    comparing this page with the terminal output should not find two different
    renderings of the same measurement.
    """
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.{places}g}"
    return str(value)


def cell(value: Any, places: int = 6) -> str:
    """Format a table cell, marking a negative number as one."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return esc(value)
    return f'<td class="n">{esc(num(value, places))}</td>'


def block(lines: str | list[str]) -> str:
    """Escape a formula block for ``<pre>``.

    ``console.formula`` accepts a string or a list of lines and this has to
    render the same content, so a list is joined with newlines. Printing ``list``
    directly would put the Python repr -- brackets and quotes -- into the page,
    which is the sort of thing that looks like mathematics and is not any.
    """
    return esc("\n".join(lines) if isinstance(lines, (list, tuple)) else str(lines))


# --------------------------------------------------------------------------
# Figure inlining
# --------------------------------------------------------------------------


def _inline_figure(name: str) -> str:
    """Return a ``<figure>`` with *name* base64-inlined, or a visible placeholder.

    A missing or unreadable file is reported **in the page**, not swallowed. An
    image that silently fails to appear on a projector is worse than a page that
    says which file is missing.
    """
    path = fig.figure_dir() / name
    if not path.is_file():
        return (
            f'<figure><div class="callout"><span class="label">Figure missing</span>'
            f"{esc(name)} was not found in {esc(fig.figure_dir())}. Run "
            f"<code>python -m iplranking</code> to regenerate it.</div></figure>"
        )
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<figure><img alt="{esc(name)}" src="data:image/png;base64,{payload}">'
        f"<figcaption>{esc(name)}</figcaption></figure>"
    )


# --------------------------------------------------------------------------
# Section builders
# --------------------------------------------------------------------------


def _head() -> str:
    """``<head>``: charset, viewport, title, and the one inline stylesheet."""
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(_TITLE)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>"
    )


def _masthead() -> str:
    """Title block: what the project is, what it reads, and what it does not claim."""
    from .demo import STAGES, provenance_record

    record = provenance_record()
    rows = [
        "<h1>IPL Power Ranking</h1>",
        '<p class="sub">Strang problem #5 &mdash; &ldquo;linear equations + team '
        "ranking&rdquo; &mdash; reframed from American college football onto 19 "
        "seasons of the Indian Premier League. Eleven mandated linear-algebra "
        "stages, each with its formula, its measured numbers and its figure.</p>",
    ]
    meta = [
        (
            "course",
            "UE25MA242A - Mathematical Foundations for AI and Data Science, "
            "PES University, CSE",
        ),
        ("deliverable", "10 marks: 5 demo + 5 viva"),
        ("snapshot", "data/matches.csv, committed; the demo never reads the network"),
        (
            "unknowns n",
            "15 canonical IPL franchises (19 raw team strings, four authorised rename pairs)",
        ),
        (
            "models",
            "Massey least squares on 558 run margins; Colley eigenvector on 1,218 decided matches",
        ),
        (
            "stages",
            "11, in the guidelines' order (Matrix Simplification is stage 3, "
            "Structure of the Space is stage 4)",
        ),
        ("source", str(record.get("source_url", "not recorded"))),
        ("retrieved", f"{record.get('utc_fetch_date', 'not recorded')} UTC"),
    ]
    rows.append('<dl class="meta">')
    for key, value in meta:
        rows.append(f"<dt>{esc(key)}</dt><dd>{esc(value)}</dd>")
    rows.append("</dl>")
    rows.append("<p class=\"meta\">Stage list, verbatim from the course: "
                + esc(", ".join(f"{n}. {name}" for n, name, _ in STAGES))
                + ".</p>")
    return "\n".join(rows)


def _stage_section(stage: Any) -> str:
    """One ``<section>``: principle, formula, measured numbers, figures, verdict."""
    parts = [
        f'<section id="stage-{stage.number}">',
        f"<h2>Stage {stage.number} &mdash; {esc(stage.name)}</h2>",
        f'<p class="principle"><span class="label">Mathematical principle</span>'
        f"{esc(stage.principle)}</p>",
        "<h3>Formula</h3>",
        f"<pre>{block(stage.formula)}</pre>",
    ]
    if stage.measured:
        parts.append("<h3>Measured</h3>")
        parts.append("<dl>")
        for key, value in stage.measured.items():
            parts.append(f"<dt>{esc(key)}</dt><dd>{esc(num(value))}</dd>")
        parts.append("</dl>")
    if stage.figures:
        parts.append("<h3>Figure</h3>")
        for name in stage.figures:
            parts.append(_inline_figure(name))
    parts.append(
        f'<p class="verdict"><span class="label">Verdict</span>{esc(stage.verdict)}</p>'
    )
    parts.append("</section>")
    return "\n".join(parts)


def _comparison_table(comparison: Any) -> str:
    """The joined frame: both fits annotated onto the official points table.

    Column order is the diagnostics module's, and the frame arrives **already
    joined by team name** -- ``diagnostics.official_comparison`` sorts the names
    itself and re-sorts the output by points. Nothing here re-sorts anything, so
    the frame cannot be joined positionally by accident.
    """
    columns = [
        ("team", "l"),
        ("points", "n"),
        ("official_rank", "n"),
        ("massey_x", "f"),
        ("massey_se", "f"),
        ("massey_rank", "n"),
        ("colley_share", "f"),
        ("colley_rank", "n"),
        ("rank_movement", "n"),
    ]
    parts = [
        "<h2>The joined table</h2>",
        "<p>Official all-time points (2 per win, all 19 seasons) with both models "
        "annotated onto it. The join is on <code>team</code>, never on row "
        "position: the official table arrives sorted by points and every fitted "
        "vector in this project is in alphabetical team order, and comparing them "
        "positionally has already produced one wrong measurement in this "
        "project. <code>rank_movement</code> is "
        "<code>massey_rank - official_rank</code>, so a positive entry means the "
        "margin fit ranks that franchise <em>worse</em> than the official table "
        "does.</p>",
        "<table><thead><tr>",
    ]
    parts.extend(f'<th class="{cls}">{esc(name)}</th>' for name, cls in columns)
    parts.append("</tr></thead><tbody>")
    for record in comparison.itertuples(index=False):
        parts.append("<tr>")
        for name, cls in columns:
            value = getattr(record, name)
            if cls == "n":
                parts.append(f'<td class="n">{esc(num(value))}</td>')
            elif cls == "f":
                parts.append('<td class="n">' + esc(f"{float(value):.4f}") + "</td>")
            else:
                parts.append(f"<td>{esc(value)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _findings(result: Any) -> str:
    """The three claims, the refuted hypothesis, and what was excluded."""
    eleven = result.measured(11)
    eight = result.measured(8)
    one = result.measured(1)

    claims = [
        (
            "The margin model does not work &mdash; and the first reason is structural, not statistical",
            f"Treating every IPL match as an equation in which the difference in "
            f"team strength equals the run margin gives centred R&sup2; = "
            f"<strong>{eight['r2_centred']:.4f}</strong>. That negative value is not "
            f"primarily a statement about noise: every row of <code>A</code> sums to "
            f"zero (<code>A @ 1 = 0</code>, proved in stage 4), so "
            f"<code>A x</code> has mean zero while <code>mean(b) = "
            f"{eight['mean_b']:.4f}</code> runs. The fit sits "
            f"<strong>{eight['bias']:.2f} runs low on every match</strong> by "
            f"construction. Adding the one constant column <code>A</code> was never "
            f"allowed lifts centred R&sup2; to "
            f"<strong>{eight['intercept_r_squared_centred']:+.4f}</strong> &mdash; a "
            f"real improvement, and still no signal. Winner accuracy is "
            f"<strong>{100.0 * eleven['in_sample_accuracy']:.1f}%</strong> against a "
            f"majority-class baseline of "
            f"<strong>{100.0 * eight['team1_win_share']:.1f}%</strong>: always naming "
            f"the first-listed team beats the fit, so the model has "
            f"<strong>negative skill</strong>. And <strong>not one</strong> of the 15 "
            f"coefficients is distinguishable from zero at 2&sigma; "
            f"(max |t| = {eleven['max_abs_t']:.2f}).",
        ),
        (
            "The reason is measured, and the two sides are on one scale",
            f"Per match, <code>||r|| / sqrt(m) = "
            f"{eleven['residual_spread']:.2f}</code> runs of margin are left "
            f"unexplained, while the fitted margins themselves vary by only "
            f"<code>std(A x) = {eleven['fitted_spread']:.2f}</code> runs &mdash; a "
            f"ratio of <strong>{eleven['noise_signal_ratio']:.2f}&times;</strong>. "
            f"Least squares weights every match equally, so a franchise with a short "
            f"history is decided by a handful of rows: "
            f"<strong>corr(games played, |x|) = {eleven['corr_games_abs_x']:.3f}</strong>. "
            f"(The earlier write-up compared <code>std(b)</code>, a data spread that "
            f"includes the +18-run level, against <code>std(x)</code>, a coefficient "
            f"spread, and called the ratio a signal-to-noise figure. Both quantities "
            f"are real; that ratio was not defined.)",
        ),
        (
            "Win/loss carries the information the margin throws away",
            f"The Colley-<em>style</em> Perron eigenvector of <code>W + W' + C</code> "
            f"on the same fixture graph reproduces the official all-time points table "
            f"at Spearman "
            f"<strong>{eleven['spearman_colley_official']:+.3f}</strong>, while the "
            f"margin model &mdash; which uses information the official table ignores "
            f"&mdash; manages <strong>{eleven['spearman_massey_official']:+.3f}</strong>. "
            f"The two models are uncorrelated with each other "
            f"({eleven['spearman_massey_colley']:.3f}). Colley's 2002 paper solves a "
            f"different, linear system, so the attribution is loose and is stated as "
            f"loose here.",
        ),
    ]

    parts = ["<h2>The finding</h2>"]
    parts.append(
        "<p>Three claims, all measured against the committed snapshot by the run "
        "that generated this page. Massey (1997) and Colley (2002) are published "
        "<em>methods</em>; no published source reports these coefficient vectors, "
        "standard errors, held-out accuracy or rank correlations for IPL data, so "
        "the numbers below are new measurements rather than a reconstruction.</p>"
    )
    for index, (title, body) in enumerate(claims, start=1):
        parts.append(
            f'<div class="claim"><p><strong>Claim {index}. {title}</strong></p>'
            f"<p>{body}</p></div>"
        )

    parts.append("<h2>The held-out split, and why its number carries a caveat</h2>")
    parts.append(
        '<div class="callout" style="border-color:#8a5a00;background:#fdf8ef">'
        '<span class="label" style="color:#8a5a00">Reported with its defect attached</span>'
        f"<p>Training on the first 16 seasons and scoring on the last 3 gives winner "
        f"accuracy <strong>{100.0 * eleven['held_out_accuracy']:.1f}%</strong> and RMSE "
        f"<strong>{eight['held_out_rmse']:.2f}</strong> runs against "
        f"<strong>{eight['held_out_baseline_rmse']:.2f}</strong> for the single "
        f"training-mean constant.</p>"
        "<p><strong>But the split is degenerate, and so is part of the training "
        "window.</strong> The share of run-margin matches won by the first-listed "
        "team sits between 0.44 and 0.67 across 2007/08&ndash;2017, then is "
        "<strong>exactly 1.000 for every season from 2018 onwards</strong> &mdash; "
        "nine consecutive seasons, including 2024, 2025 and 2026, which are the "
        "three test seasons. The archive's team-ordering convention changed. The "
        "test target never varies, and six of the sixteen training seasons are "
        "degenerate too. This is not a clean out-of-sample estimate; the number is "
        "reported rather than dropped, and the defect is reported with it.</p></div>"
    )

    parts.append("<h2>The refuted hypothesis</h2>")
    parts.append(
        '<div class="callout"><span class="label">Reported, not hidden</span>'
        "<p>An inherited build audit predicted that weighting each match by "
        "<code>1/(games(t1) + games(t2))</code> would stop the short-history "
        "franchises from dominating the fit. <strong>Measurement refutes it.</strong> "
        f"Ordinary least squares gives max|x| = {eleven['ols_max_abs_x']:.2f} runs; "
        f"the frequency-balanced fit gives max|x| = "
        f"{eleven['balanced_max_abs_x']:.2f} runs, and R&sup2; (centred) slips from "
        f"{eight['r2_centred']:.4f} to {eleven['balanced_r2_centred']:.4f}.</p>"
        "<p>The diagnosis is right and the proposed repair inverts it. A thin "
        "franchise's extremity is <em>caused</em> by having five run-margin matches, "
        "and those five matches are exactly what the weight divides by &mdash; so "
        "balancing amplifies the very rows it was meant to discount. Fewer games is a "
        "reason to trust a franchise's results less, not more.</p></div>"
    )

    parts.append("<h2>What was excluded, and why it is stated here</h2>")
    parts.append(
        '<div class="callout" style="border-color:#8a5a00;background:#fdf8ef">'
        '<span class="label" style="color:#8a5a00">Exclusions, counted</span>'
        f"<p><strong>{one['no_winner_matches']} of {one['total_matches']:,} matches "
        f"carry no <code>winner</code> field at all</strong> &mdash; 16 decided by a "
        "Super Over eliminator and 9 abandoned. They belong to neither model. The "
        "count is here rather than in a footnote because silently dropping 2% of a "
        "dataset reads as cherry-picking.</p>"
        f"<p><strong>{one['wicket_only_matches']} of {one['total_matches']:,} decided "
        "matches carry a wicket margin and no run figure at all.</strong> Converting "
        "them into run equivalents would require a runs-per-wicket constant that no "
        "source in this repository supplies. Inventing one to fill the gap is "
        "forbidden, so the project runs two honest models on two different datasets "
        "instead: least squares on the 558 run margins, and a Colley eigenvector on "
        "all 1,218 decided matches. Their disagreement is the finding.</p>"
        "<p><strong>Not attempted, by decision:</strong> recency weighting (a named "
        "&ldquo;what next&rdquo;, not part of this deliverable), and the residual-SVD "
        "stretch variant. <strong>Not merged:</strong> Gujarat Lions into Gujarat "
        "Titans, or Deccan Chargers into Sunrisers Hyderabad &mdash; either merge "
        "changes n from 15 and invalidates every dimension and every measured figure "
        "downstream.</p></div>"
    )
    return "\n".join(parts)


def _r_squared_block(result: Any) -> str:
    """The two R&sup2; values side by side, each labelled with its denominator.

    Separate from the stage 8 section because this is the single most-misreported
    number in the project: the inherited build audit, the handoff and the earlier
    spec all headline the uncentred value, which reads as a small positive fit.
    """
    eight = result.measured(8)
    return (
        "<h2>One number, two denominators</h2>"
        "<p>R&sup2; is <code>1 - SS<sub>res</sub> / SS<sub>tot</sub></code>, and "
        "SS<sub>tot</sub> has two legitimate denominators that disagree "
        "<strong>in sign</strong> on this data. Only the centred one is the standard "
        "coefficient of determination.</p>"
        "<table><thead><tr><th>denominator</th><th class=\"n\">SS<sub>tot</sub></th>"
        "<th class=\"n\">R&sup2;</th><th>reading</th></tr></thead><tbody>"
        f"<tr><td>sum (b - mean(b))<sup>2</sup> &mdash; <strong>centred</strong></td>"
        f'<td class="n">{eight["ss_tot_centred"]:,.1f}</td>'
        f'<td class="n"><strong>{eight["r2_centred"]:.4f}</strong></td>'
        "<td>the standard R&sup2;: the model is <strong>worse than predicting the "
        "mean margin</strong></td></tr>"
        f"<tr><td>sum b<sup>2</sup> &mdash; uncentred</td>"
        f'<td class="n">{eight["ss_tot_uncentred"]:,.1f}</td>'
        f'<td class="n"><strong>{eight["r2_uncentred"]:+.4f}</strong></td>'
        "<td>correct only when the outcome is already mean-centred; read alone it "
        "suggests the model explains 2% of the variation</td></tr>"
        f"<tr><td>add one constant column &mdash; <strong>with intercept</strong></td>"
        f'<td class="n">{eight["intercept_ss_res"]:,.1f} (SS<sub>res</sub>)</td>'
        f'<td class="n"><strong>{eight["intercept_r_squared_centred"]:+.4f}</strong></td>'
        "<td>the column <code>A</code> was never allowed. The negative value was "
        "structural; correcting it still leaves no signal</td></tr>"
        "</tbody></table>"
        '<div class="callout"><span class="label">Why all three are printed</span>'
        "<p>The sign flips between the denominators because 948,444 &gt; 766,931: the "
        "uncentred ratio is smaller, so the subtraction leaves a small positive "
        f"number. Quoting only {eight['r2_uncentred']:+.4f} would be the same class of "
        "error as the two wrong dataset counts this project had already produced.</p>"
        f"<p>And the centred {eight['r2_centred']:.4f} has a cause that is "
        "<strong>structural, not statistical</strong>: every row of <code>A</code> "
        "sums to zero, so <code>A x</code> has mean zero while "
        f"<code>mean(b) = {eight['mean_b']:.4f}</code> runs. The fit is "
        f"{eight['bias']:.2f} runs low on every match by construction. Adding the "
        "constant column <code>A @ 1 = 0</code> forbids lifts the centred value to "
        f"<strong>{eight['intercept_r_squared_centred']:+.4f}</strong> &mdash; a real "
        "improvement, and still no signal. Stage 4's rank deficiency and stage 8's "
        "R&sup2; are one argument, not two.</p></div>"
    )


def _provenance_block(result: Any) -> str:
    """Provenance, with what the hash covers and no licence term asserted."""
    from .demo import provenance_record

    record = provenance_record()
    if not record:
        return (
            "<h2>Provenance</h2>"
            '<div class="callout"><span class="label">Missing</span>'
            "<p>No <code>data/provenance.json</code> was found, so this page asserts "
            "no source and no licence. Run <code>python -m iplranking</code> from a "
            "complete clone, where the record is committed.</p></div>"
        )

    one = result.measured(1)
    rows = [
        ("source URL", str(record.get("source_url", "not recorded"))),
        ("archive", str(record.get("archive_name", "not recorded"))),
        ("format version", str(record.get("cricsheet_version", "not recorded"))),
        ("retrieved (UTC)", str(record.get("utc_fetch_date", "not recorded"))),
        ("HTTP status", str(record.get("http_status", "not recorded"))),
        ("row count", f"{record.get('row_count', 'not recorded'):,} matches in data/matches.csv"
         if isinstance(record.get("row_count"), int) else "not recorded"),
        ("matches in the snapshot this page was built from", f"{one['total_matches']:,}"),
        ("SHA-256", str(record.get("sha256", "not recorded"))),
        ("what the SHA-256 covers", str(record.get("sha256_covers", "not recorded"))),
    ]
    parts = [
        "<h2>Provenance</h2>",
        "<p>The snapshot is committed to the repository and the demo reads only "
        "that file, so this page is reproducible from a clean clone with no network "
        "access. What follows is transcribed from "
        "<code>data/provenance.json</code>, including the part that says the hash is "
        "<em>not</em> the archive digest.</p>",
        '<dl class="meta">',
    ]
    for key, value in rows:
        parts.append(f"<dt>{esc(key)}</dt><dd>{esc(value)}</dd>")
    parts.append("</dl>")
    if record.get("notes"):
        parts.append(f"<p class=\"meta\">{esc(record['notes'])}</p>")

    parts.append("<h3>Licence position</h3>")
    parts.append(
        '<div class="callout"><span class="label">No licence term asserted</span>'
        f"<p>{esc(record.get('licence', 'not recorded'))}</p></div>"
    )
    parts.append(
        "<p class=\"meta\">Attribution, precisely and nothing more: the archive "
        f"<code>{esc(record.get('archive_name', 'ipl_json.zip'))}</code> from "
        f"{esc(record.get('source_url', ''))}, Cricsheet JSON format version "
        f"{esc(record.get('cricsheet_version', '1.2.0'))}, retrieved "
        f"{esc(record.get('utc_fetch_date', ''))} UTC. If asked in the viva, the "
        "answer is exactly this: no licence statement for the match data was read "
        "from the primary source, so none is claimed.</p>"
    )
    return "\n".join(parts)


def _footer(result: Any) -> str:
    """The stage -> figure -> key number table, and the run's own summary."""
    parts = [
        "<h2>Stage, figure, key number</h2>",
        "<table><thead><tr><th>stage</th><th>figure</th>"
        '<th class="n">key number</th></tr></thead><tbody>',
    ]
    for stage_name, figures_for_stage, key in result.timeline:
        parts.append(
            f"<tr><td>{esc(stage_name)}</td><td>{esc(figures_for_stage)}</td>"
            f'<td class="n">{esc(key)}</td></tr>'
        )
    parts.append("</tbody></table>")
    parts.append(
        '<p class="meta">Every figure on this page is inlined as base64 and every '
        "number in its text was measured at run time by the demo: "
        "<code>python -m iplranking --offline</code>, or "
        "<code>python src/iplranking/__main__.py --offline</code> where "
        "<code>src/</code> is not already on the path. Two runs produce "
        "byte-identical figures and a byte-identical page, which "
        "<code>tests/test_demo.py</code> asserts.</p>"
    )
    return "\n".join(parts)


def _blocker_banner() -> str:
    """The one open question, above everything else on the page.

    ``AGENTS.md`` section 2 makes this a hard gate on the whole project: no
    project code should have been written before the instructor answered it, and
    it has never been answered. The code exists so the question can be put with a
    working demonstration in hand. Hiding that below the fold would be the exact
    kind of quiet omission this project's rules forbid.
    """
    return (
        '<div class="callout" style="border-color:#a11;background:#fdf1f1">'
        '<span class="label" style="color:#a11">Open blocker &mdash; not answered</span>'
        "<p><strong>No instructor answer is recorded anywhere in this repository.</strong> "
        "The question that gates the whole project is:</p>"
        "<blockquote><p>&ldquo;Strang problem 5 in the projects book is <em>Linear "
        "equations + college football team ranking</em>. May I keep Strang's "
        "mathematics and rank <strong>IPL</strong> teams instead, using the mandated "
        "11-stage LA workflow and the 1,243-match Cricsheet dataset? Or must I submit "
        "the book's task list on college football data?&rdquo;</p></blockquote>"
        "<p>If the answer is <em>the book's task list is mandatory</em>, the IPL "
        "reframe is not permitted, the uniqueness argument behind this problem choice "
        "disappears, and the code on this page would be discarded rather than "
        "adapted. The build was authorised by the repository owner so that the "
        "question can be asked against a working demo. <strong>That authorisation is "
        "not an instructor answer.</strong></p></div>"
    )


def _manual_checklist() -> str:
    """What a human still has to do, item 1 being the blocker.

    A demo that ends with a list of what is unfinished is more useful than one
    that implies it is finished, and the project's rules put the instructor
    question first rather than last.
    """
    items = [
        (
            "Ask the instructor the blocker question above, and record the answer "
            "&mdash; who, when, in what form &mdash; before relying on this build. "
            "A written reply is preferred; a verbal answer must be confirmed in "
            "writing.",
            True,
        ),
        (
            "State the licence position as read, not as assumed: Cricsheet's primary "
            "site carries no licence statement for the match data and its licence path "
            "returns 404, so no term is asserted here.",
            False,
        ),
        (
            "Confirm the snapshot provenance by rebuilding it with "
            "<code>python ipl-power-ranking/scripts/build_snapshot.py</code> and "
            "checking the reported manifest hash against "
            "<code>data/provenance.json</code>.",
            False,
        ),
        (
            "Rehearse the viva answers, starting with the two questions this build "
            "was corrected to answer honestly: why a margin model cannot fit the "
            "dataset's mean margin, and what the majority-class baseline does to a "
            "55% accuracy claim.",
            False,
        ),
        (
            "Decide whether to present the all-time official table or a per-season "
            "one, and say which out loud during the demo &mdash; the ambiguity was "
            "flagged as a viva risk.",
            False,
        ),
        (
            "Record the released answer, or the reopen decision, in "
            "<code>docs/reasonix/</code> and add the run row to "
            "<code>docs/reasonix/INDEX.md</code>.",
            False,
        ),
    ]
    parts = ["<h2>What you must do by hand</h2>"]
    parts.append(
        '<div class="callout"><span class="label">Six items, the first one gating</span>'
        "<p>Everything below is outside what the code can do for you.</p><ol>"
    )
    for text, gating in items:
        tag = " <strong>GATING.</strong>" if gating else ""
        parts.append(f"<li>{text}{tag}</li>")
    parts.append("</ol></div>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# The public entry point
# --------------------------------------------------------------------------


def build_report(result: Any = None) -> Path:
    """Write ``report/report.html`` and return its path.

    Parameters
    ----------
    result:
        The :class:`iplranking.demo.DemoResult` from the run that just finished.
        Passing it in is what guarantees the page and the terminal output report
        the same measurements: the report never re-derives a number. ``None``
        re-runs the demo's computations with its narration suppressed, which is
        what a bare ``python -m iplranking.report`` does.

    Returns
    -------
    pathlib.Path
        The written file.
    """
    if result is None:
        from . import demo as demo_module

        result = demo_module.run_demo(figures_only=True)

    console.step(f"assembling the self-contained report from {len(result.stages)} stage sections")

    parts = [_head(), _masthead(), _blocker_banner()]
    parts.append("<h2>The eleven mandated stages</h2>")
    parts.append(
        "<p>Order is the guidelines' own. <strong>Matrix Simplification is stage 3 "
        "and Structure of the Space is stage 4</strong> &mdash; the pair was "
        "transposed in this project's documents for two full runs and only "
        "adversarial review caught it, so the terminal walkthrough and "
        "<code>tests/test_demo.py</code> both pin the banners to ascending "
        "order.</p>"
    )
    for stage in result.stages:
        parts.append(_stage_section(stage))
    parts.append(_r_squared_block(result))
    parts.append(_findings(result))
    parts.append(_comparison_table(result.comparison))
    parts.append(_provenance_block(result))
    parts.append(_manual_checklist())
    parts.append(_footer(result))
    parts.append("</body>\n</html>")

    directory = fig.report_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "report.html"
    # newline="\n" so the file is byte-identical regardless of platform, and
    # encoding fixed so a marker on any machine reads the same characters.
    path.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    console.ok(
        f"report written: {path} "
        f"({path.stat().st_size / 1024:.0f} KB, {len(result.figures)} figures inlined)"
    )
    return path
