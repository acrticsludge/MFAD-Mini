"""Build-time parser for the raw Cricsheet IPL snapshot (``ipl_json/*.json``).

**Not on the demo path.** The demo reads the committed ``data/matches.csv``
through :mod:`iplranking.data` and never touches this module, so the demo runs
from a clean clone with no network access. This module exists so the CSV is
re-derivable from the raw archive that is committed alongside it.

What it produces
----------------
A tidy one-row-per-match :class:`pandas.DataFrame` with the columns in
:data:`COLUMNS`, in that order.

Two schema facts that a naive reader gets wrong
----------------------------------------------
1. The winner is at ``info.outcome.winner`` — **not** ``info.winner``. Measured:
   ``info["winner"]`` raises ``KeyError: 'winner'`` in every one of the 1,243
   files, so the failure mode is a hard error on the first file, not a silently
   empty dataset. ``info.get("winner")`` returns ``None``. Here the outcome
   block is fetched once and ``winner`` is read with ``.get``.
2. ``info["season"]`` is **inconsistently typed**: measured over the whole
   snapshot, 511 files carry an ``int`` (``2009``) and 732 carry a ``str``
   (``"2007/08"``), and five season labels appear under both types. Coercing to
   ``str`` first is what makes a plain-Python distinct-season count come out at
   the measured **19** rather than 24. See ``_normalise_season`` for exactly
   where this does and does not bite.

Margins
-------
``info.outcome.by.runs`` and ``info.outcome.by.wickets`` are **mutually
exclusive and both optional**. Measured over the snapshot: 558 matches carry a
run margin, 660 carry a wicket margin, no match carries both, and the 25
matches with no winner carry neither. Both columns are emitted as pandas'
nullable ``Int64`` so a missing margin stays missing. A missing margin must
never become ``0`` — a zero run margin would be a real observation
(``0`` runs is a legal result), and silently manufacturing one would corrupt
the least-squares right-hand side.

No dataset count is hard-coded here. Every count in this module is derived from
the files on disk; the measured figures appear only in the tests, where pinning
them is the whole point.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .canon import canonical

__all__ = [
    "COLUMNS",
    "SnapshotFieldError",
    "parse_directory",
    "parse_file",
]

#: Output schema, in order. `scripts/build_snapshot.py` writes exactly these.
COLUMNS: tuple[str, ...] = (
    "match_id",
    "date",
    "season",
    "team1",
    "team2",
    "winner",
    "margin_runs",
    "margin_wickets",
    "method",
    "is_super_over",
    "canonical_team1",
    "canonical_team2",
)

#: Sort key giving a total, deterministic row order: chronological, with the
#: unique match id breaking same-day ties. The CSV row order is the row order of
#: the design matrix, so it must never depend on filesystem enumeration order.
_ROW_ORDER = ("date", "match_id")


class SnapshotFieldError(ValueError):
    """One field of one file could not be read, and which one it was.

    A build-time error has to name its file and its field or it is not an error,
    it is a rumour. This module used to raise a bare ``KeyError`` for a missing
    ``teams``/``dates`` and a bare ``ValueError`` from ``int("abc")``, neither of
    which said which of 1,243 JSON files was at fault or what was wrong with it.
    In a 1,243-file build that is the difference between a two-minute fix and a
    bisect.

    Subclasses :class:`ValueError`, so a caller that catches ``ValueError``
    anywhere still catches it, and :func:`parse_directory` keeps its single
    unhandled-error contract.

    Attributes
    ----------
    path
        The offending file, as ``path.name`` -- the file's own name, not the
        machine's directory layout.
    field
        The JSON field that could not be read, e.g. ``"info.season"``.
    reason
        What was wrong with it, in words.
    """

    def __init__(self, path: Any, field: str, reason: str) -> None:
        self.path = str(path)
        self.field = field
        self.reason = reason
        super().__init__(f"{self.path}: field {field!r}: {reason}")


def _require(info: dict[str, Any], key: str, path: Path, field: str) -> Any:
    """Return ``info[key]``, or raise :class:`SnapshotFieldError` naming both.

    A missing key is not the same failure as a malformed one, so the two messages
    differ: *missing* says which field was expected, and *not a list / not two
    entries* says what was found instead.
    """
    if key not in info:
        raise SnapshotFieldError(
            path.name,
            field,
            f"the field is missing from this file's info block; every Cricsheet "
            f"match file carries {field!r} and this one does not, so it is "
            "probably not a match file at all",
        )
    return info[key]


def _normalise_season(season: Any, *, path: Any = None, field: str = "info.season") -> str:
    """Coerce ``info["season"]`` to ``str`` before it is used or counted.

    The field is ``int`` in 511 of the snapshot's files and ``str`` in 732. The
    failure is not that two *labels* differ but that five labels are each
    recorded under **both** types in different files -- 2012, 2013, 2015, 2016
    and 2017 each appear once as an ``int`` and once or more as a ``str``.
    ``2012`` and ``"2012"`` are unequal keys, so a **plain Python set** built
    from the raw values counts those five seasons twice and returns 24 where
    the distinct-season count is 19.

    Measured 2026-10-04 over all 1,243 files: ``len(set(raw)) == 24``,
    ``len({_normalise_season(s) for s in raw}) == 19``.

    Where this matters, precisely: it matters at the **Python level**. Pandas
    infers a single ``str`` dtype from a column of mixed ``int``/``str`` values
    when it builds the frame, so the committed CSV comes out at 19 seasons
    whether or not this coercion runs -- verified by mutation. That makes the
    coercion invisible to any test that reads the CSV, and
    ``tests/test_data_invariants.py`` pins it at the Python level instead,
    where it can actually fail.

    The coercion is kept because the dispatch requires it and because it makes
    the column's type a property of the code rather than an inference left to
    pandas' dtype rules.

    Parameters
    ----------
    season
        The raw value. ``int`` and ``str`` both coerce; anything else raises.
    path, field
        Where the value came from, used only in the error message. Both are
        optional so that the normalisation can be exercised -- and is, in
        ``tests/test_data_invariants.py`` -- on a bare value with no file
        behind it.

    Raises
    ------
    SnapshotFieldError
        On a missing (``None``) season, or one that is not an ``int``, a ``str``
        or a ``float``. ``None`` used to coerce to the **string** ``'None'``,
        which invented a twentieth season rather than failing: a dataset-wide
        count would then disagree with the frame it counted, and nothing would
        say why.
    """
    if season is None:
        raise SnapshotFieldError(
            path if path is not None else "<season value>",
            field,
            "missing. A season is never null in this archive, and coercing it "
            "would write the string 'None' into the season column -- inventing a "
            "season rather than reporting a bad file",
        )
    if isinstance(season, bool) or not isinstance(season, (int, float, str)):
        raise SnapshotFieldError(
            path if path is not None else "<season value>",
            field,
            f"expected an int or a str, got {type(season).__name__} "
            f"({season!r})",
        )
    return str(season)


def _nullable_int(value: Any, *, path: Any = None, field: str = "margin") -> int | None:
    """Return ``value`` as a Python ``int``, or ``None`` when absent.

    ``None`` is preserved as ``None`` -- never coerced to 0. The distinction
    between "no run margin recorded" and "won by 0 runs" is load-bearing.

    Raises
    ------
    SnapshotFieldError
        When the value is present but not a number. ``int("abc")`` used to raise
        a bare ``ValueError`` naming neither the file nor the field, in a loop
        over 1,243 files.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise SnapshotFieldError(
            path if path is not None else "<margin value>",
            field,
            f"expected an integer or null, got the boolean {value!r}",
        )
    if isinstance(value, float) and not float(value).is_integer():
        raise SnapshotFieldError(
            path if path is not None else "<margin value>",
            field,
            f"expected an integer margin, got the fractional number {value!r}",
        )
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise SnapshotFieldError(
            path if path is not None else "<margin value>",
            field,
            f"expected an integer or null, got {type(value).__name__} "
            f"({value!r}): {error}",
        ) from error


def parse_file(path: str | Path) -> dict[str, Any]:
    """Parse one Cricsheet match JSON file into a flat record.

    The returned mapping has exactly the keys of :data:`COLUMNS`, so a whole
    directory can equivalently be assembled as
    ``pd.DataFrame([parse_file(p) for p in paths])``.

    ``margin_runs`` and ``margin_wickets`` are ``int`` or ``None``. ``winner``,
    ``method`` are ``str`` or ``None``. ``is_super_over`` is a ``bool`` and is
    ``True`` when ``info.outcome.eliminator`` is present, i.e. the match was
    decided by a Super Over eliminator rather than by the 20 overs.

    ``date`` is the *first* entry of ``info["dates"]`` -- the match's start date,
    per the archive's own README. A minority of files list a second date for a
    match abandoned on day one and completed on day two; the start date keeps
    the ordering total and meaningful.

    Every failure names **the file and the field**
    --------------------------------------------------------
    ``parse_directory`` walks 1,243 files, so an error that says only "invalid
    literal for int()" leaves the reader with 1,243 suspects. Every path
    through this function raises :class:`SnapshotFieldError`, which carries
    ``path.name`` and the JSON field:

    =======================================  ==========================================
    field                                    what raises
    =======================================  ==========================================
    ``info``                                 not a JSON object at all
    ``info.teams``                           missing, not a list of 2, or a null name
    ``info.dates``                           missing, empty, or not a list of strings
    ``info.season``                          missing (``None``) or not a number/string
    ``info.outcome.by.runs``                 present but not an integer
    ``info.outcome.by.wickets``              present but not an integer
    =======================================  ==========================================
    """
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SnapshotFieldError(
            path.name, "<document>", f"not valid JSON: {error}"
        ) from error
    if not isinstance(document, dict) or "info" not in document:
        raise SnapshotFieldError(
            path.name,
            "info",
            "the file has no top-level 'info' object, so it is not a Cricsheet "
            "match file",
        )
    info = document["info"]
    if not isinstance(info, dict):
        raise SnapshotFieldError(
            path.name,
            "info",
            f"'info' must be a JSON object, got {type(info).__name__}",
        )

    raw_teams = _require(info, "teams", path, "info.teams")
    if not isinstance(raw_teams, list) or not all(
        isinstance(name, str) and name for name in raw_teams
    ):
        raise SnapshotFieldError(
            path.name,
            "info.teams",
            f"expected a list of non-empty team-name strings, got {raw_teams!r}",
        )
    teams: list[str] = list(raw_teams)
    if len(teams) != 2:
        raise SnapshotFieldError(
            path.name,
            "info.teams",
            f"expected 2 teams, found {len(teams)}: {teams}",
        )

    outcome = info.get("outcome") or {}
    if not isinstance(outcome, dict):
        raise SnapshotFieldError(
            path.name,
            "info.outcome",
            f"expected an object or null, got {type(outcome).__name__}",
        )
    by = outcome.get("by") or {}
    if not isinstance(by, dict):
        raise SnapshotFieldError(
            path.name,
            "info.outcome.by",
            f"expected an object or null, got {type(by).__name__}",
        )

    raw_dates = _require(info, "dates", path, "info.dates")
    if not isinstance(raw_dates, list) or not raw_dates:
        raise SnapshotFieldError(
            path.name,
            "info.dates",
            f"expected a non-empty list of ISO date strings, got {raw_dates!r}",
        )
    if not all(isinstance(value, str) and value for value in raw_dates):
        raise SnapshotFieldError(
            path.name,
            "info.dates",
            f"expected a list of non-empty strings, got {raw_dates!r}",
        )
    dates: list[str] = list(raw_dates)

    team1, team2 = teams
    return {
        "match_id": path.stem,
        "date": dates[0],
        "season": _normalise_season(info.get("season"), path=path.name),
        "team1": team1,
        "team2": team2,
        "winner": outcome.get("winner"),
        "margin_runs": _nullable_int(by.get("runs"), path=path.name, field="info.outcome.by.runs"),
        "margin_wickets": _nullable_int(
            by.get("wickets"), path=path.name, field="info.outcome.by.wickets"
        ),
        "method": outcome.get("method"),
        "is_super_over": "eliminator" in outcome,
        "canonical_team1": canonical(team1),
        "canonical_team2": canonical(team2),
    }


def parse_directory(directory: str | Path) -> pd.DataFrame:
    """Parse every ``*.json`` match file in ``directory`` into one tidy frame.

    Rows are sorted chronologically by ``(date, match_id)`` so the frame is a
    deterministic function of the file set alone — byte-identical across runs on
    any machine, which the snapshot build depends on.

    Margin columns are the pandas nullable ``Int64`` dtype, so a match decided
    on wickets has ``NaN`` in ``margin_runs`` rather than a 0 that would look
    like a real observation to every downstream numeric operation.
    """
    directory = Path(directory)
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no *.json match files found in {directory}")

    records = [parse_file(path) for path in paths]
    frame = pd.DataFrame.from_records(records, columns=list(COLUMNS))

    frame["margin_runs"] = frame["margin_runs"].astype("Int64")
    frame["margin_wickets"] = frame["margin_wickets"].astype("Int64")
    frame["winner"] = frame["winner"].astype("string")
    frame["method"] = frame["method"].astype("string")
    frame["is_super_over"] = frame["is_super_over"].astype("bool")

    frame = frame.sort_values(list(_ROW_ORDER), kind="stable", ignore_index=True)
    return frame
