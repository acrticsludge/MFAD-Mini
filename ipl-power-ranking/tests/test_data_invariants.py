"""Invariant tests pinning the measured shape of the committed snapshot.

Every number asserted here was **measured** against the Cricsheet IPL snapshot
(`ipl_json/`, Cricsheet JSON v1.2.0) and is pinned so that no later change can
quietly move it. They are assertions, not prose: `AGENTS.md` section 4 requires
that every count in this project be computed by a test rather than written down
and trusted, and section 5's "19 seasons, not 24" warning is enforced by
`test_season_count_is_nineteen` below.

These tests read **only** `data/matches.csv` and `data/provenance.json` — the
committed snapshot, exactly as the demo does. They never touch the network and
never re-parse the raw `ipl_json/`, so they pin what was committed rather than
what happens to be on disk.

All figures measured 2026-10-04 against 1,243 JSON files.
"""

from __future__ import annotations

import json
import pathlib
import re

import pandas as pd
import pytest

from iplranking.canon import canonical
from iplranking.data import load_matches

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
MATCHES_CSV = DATA_DIR / "matches.csv"
PROVENANCE_JSON = DATA_DIR / "provenance.json"

# --- The measured figures, pinned -----------------------------------------
EXPECTED_ROWS = 1243
EXPECTED_WITH_WINNER = 1218
EXPECTED_RUN_MARGIN = 558
EXPECTED_WICKET_ONLY = 660
EXPECTED_NO_WINNER = 25
EXPECTED_SUPER_OVER = 16
EXPECTED_NO_RESULT = 9
EXPECTED_DL = 23
EXPECTED_RAW_TEAM_STRINGS = 19
EXPECTED_SEASONS = 19
EXPECTED_CANONICAL_TEAMS = 15


@pytest.fixture(scope="module")
def matches() -> pd.DataFrame:
    """The committed snapshot, read exactly as the demo reads it."""
    assert MATCHES_CSV.is_file(), f"committed snapshot missing: {MATCHES_CSV}"
    # match_id pinned as str: it is a file stem, and a text column round-trips
    # losslessly whatever a future Cricsheet drop puts in it.
    return pd.read_csv(MATCHES_CSV, dtype={"match_id": "string"})


# --------------------------------------------------------------------------
# Row counts
# --------------------------------------------------------------------------


def test_row_count(matches: pd.DataFrame) -> None:
    assert len(matches) == EXPECTED_ROWS


def test_matches_with_a_winner(matches: pd.DataFrame) -> None:
    assert int(matches["winner"].notna().sum()) == EXPECTED_WITH_WINNER


def test_matches_with_no_winner(matches: pd.DataFrame) -> None:
    """25 of 1,243 have no winner. Stated out loud in the demo, not hidden."""
    assert int(matches["winner"].isna().sum()) == EXPECTED_NO_WINNER


# --------------------------------------------------------------------------
# The central design constraint: the 558 / 660 split
# --------------------------------------------------------------------------


def test_run_margin_rows(matches: pd.DataFrame) -> None:
    assert int(matches["margin_runs"].notna().sum()) == EXPECTED_RUN_MARGIN


def test_wicket_only_rows(matches: pd.DataFrame) -> None:
    assert int(matches["margin_wickets"].notna().sum()) == EXPECTED_WICKET_ONLY


def test_no_match_carries_both_margin_types(matches: pd.DataFrame) -> None:
    """558 + 660 = 1218 = every match with a winner. Exclusive and total.

    This is what makes it legitimate to treat the two populations as the two
    datasets of the two models rather than as overlapping views of one.
    """
    both = matches["margin_runs"].notna() & matches["margin_wickets"].notna()
    neither = matches["margin_runs"].isna() & matches["margin_wickets"].isna()
    assert int(both.sum()) == 0
    assert int(neither.sum()) == EXPECTED_NO_WINNER
    assert EXPECTED_RUN_MARGIN + EXPECTED_WICKET_ONLY == EXPECTED_WITH_WINNER


def test_missing_margins_are_never_zero(matches: pd.DataFrame) -> None:
    """A missing margin must stay missing.

    The margins arrive in an empty CSV cell, which pandas reads as NaN. If any
    loader ever coerced NaN to 0 it would invent "won by 0 runs" observations in
    the least-squares right-hand side, and 0 is a *legal* run margin, so nothing
    downstream would complain.
    """
    for column in ("margin_runs", "margin_wickets"):
        values = matches[column].dropna()
        assert len(values) > 0
        assert not (values == 0).any(), f"{column} contains a literal 0"


def test_no_zero_run_margins_among_present_values(matches: pd.DataFrame) -> None:
    """Measured: the 558 run margins run from 1 to 146 runs, none of them 0."""
    runs = matches["margin_runs"].dropna()
    assert int(runs.min()) >= 1
    assert int(runs.max()) == 146


# --------------------------------------------------------------------------
# Outcome taxonomy
# --------------------------------------------------------------------------


def test_super_over_count(matches: pd.DataFrame) -> None:
    """`info.outcome.eliminator` present. All of these are Super Over ties."""
    assert int(matches["is_super_over"].sum()) == EXPECTED_SUPER_OVER


def test_no_result_count(matches: pd.DataFrame) -> None:
    """9 abandoned matches: no winner, and not decided by a Super Over.

    The committed schema has no `outcome.result` column, and the spec fixes the
    column list, so this count is *derived*: every no-winner match is either a
    Super Over tie (16) or a `no result` abandonment (9). Super Over ties always
    carry `result == "tie"` in the raw snapshot, so no-winner minus super-over
    isolates the abandonments exactly.
    """
    abandoned = matches["winner"].isna() & ~matches["is_super_over"]
    assert int(abandoned.sum()) == EXPECTED_NO_RESULT
    # And the split is exhaustive, with nothing unclassified.
    assert EXPECTED_SUPER_OVER + EXPECTED_NO_RESULT == EXPECTED_NO_WINNER


def test_super_over_matches_never_have_a_winner(matches: pd.DataFrame) -> None:
    """Structural: an eliminator marks a tie, so `winner` must be absent."""
    assert int(matches.loc[matches["is_super_over"], "winner"].notna().sum()) == 0


def test_dl_method_count(matches: pd.DataFrame) -> None:
    """`info.outcome.method == "D/L"` — 23 rain-reduced results."""
    assert int((matches["method"] == "D/L").sum()) == EXPECTED_DL


def test_no_result_matches_have_no_method(matches: pd.DataFrame) -> None:
    """A match abandoned outright has no D/L or other method recorded."""
    abandoned = matches["winner"].isna() & ~matches["is_super_over"]
    assert int(matches.loc[abandoned, "method"].notna().sum()) == 0


# --------------------------------------------------------------------------
# Teams
# --------------------------------------------------------------------------


def test_raw_distinct_team_strings(matches: pd.DataFrame) -> None:
    """19 before canonicalisation. The rename map's input."""
    raw = set(matches["team1"]) | set(matches["team2"])
    assert len(raw) == EXPECTED_RAW_TEAM_STRINGS


def test_canonical_team_count(matches: pd.DataFrame) -> None:
    """n = 15 after canonicalisation. This is the number of unknowns."""
    canonical = set(matches["canonical_team1"]) | set(matches["canonical_team2"])
    assert len(canonical) == EXPECTED_CANONICAL_TEAMS


def test_canonicalisation_reduces_by_exactly_four(matches: pd.DataFrame) -> None:
    """19 raw -> 15 canonical: exactly the four documented rename pairs."""
    raw = set(matches["team1"]) | set(matches["team2"])
    canonical = set(matches["canonical_team1"]) | set(matches["canonical_team2"])
    assert len(raw) - len(canonical) == 4


def test_both_teams_always_canonicalised(matches: pd.DataFrame) -> None:
    """Every raw name has a canonical column value, and no row is null."""
    assert int(matches["canonical_team1"].isna().sum()) == 0
    assert int(matches["canonical_team2"].isna().sum()) == 0


def test_canonical_pair_is_the_renamed_raw_pair(matches: pd.DataFrame) -> None:
    """The canonical columns are a pure function of the raw ones, row by row.

    The map's *contents* are pinned independently in
    `test_canonicalisation.py`; what matters here is that the snapshot was built
    through it rather than by hand, so a stale CSV would show up as a mismatch.
    """
    for raw_column, canonical_column in (
        ("team1", "canonical_team1"),
        ("team2", "canonical_team2"),
    ):
        observed = set(zip(matches[raw_column], matches[canonical_column]))
        expected = {(raw, canonical(raw)) for raw in set(matches[raw_column])}
        assert observed == expected


# --------------------------------------------------------------------------
# Seasons — the normalising test
# --------------------------------------------------------------------------


def test_season_count_is_nineteen(matches: pd.DataFrame) -> None:
    """19 distinct seasons, counted on the **normalised** column.

    Pinned on the committed CSV. Note what this test does *not* and cannot
    cover: the ``str`` coercion in ``parse._normalise_season`` is invisible
    here, because pandas infers a single ``str`` dtype from a mixed ``int``/
    ``str`` column when the frame is built, so the CSV is byte-identical with
    and without the coercion (verified by mutation on 2026-10-04). The coercion
    is pinned at the Python level by
    `test_season_normalisation_is_load_bearing_in_python`, which does fail
    without it. This test guards the committed value.
    """
    seasons = matches["season"].dropna().astype(str)
    assert len(set(seasons)) == EXPECTED_SEASONS


def test_every_season_label_is_a_string(matches: pd.DataFrame) -> None:
    """The CSV column itself must be textual; an int column means the coercion
    was skipped somewhere in the build."""
    assert all(isinstance(v, str) for v in matches["season"].dropna().unique())


def test_seasons_span_the_full_archive(matches: pd.DataFrame) -> None:
    """First and last seasons of the snapshot, as labels."""
    seasons = set(matches["season"].dropna().astype(str))
    assert min(seasons) == "2007/08"
    assert max(seasons) == "2026"


RAW_SNAPSHOT = REPO_ROOT / "ipl_json"


@pytest.mark.skipif(
    not RAW_SNAPSHOT.is_dir(),
    reason="raw ipl_json/ snapshot not present; the committed-CSV tests still run",
)
def test_raw_season_field_is_genuinely_mixed_type(matches: pd.DataFrame) -> None:
    """Guard the guard: the `str` coercion is not a no-op on this snapshot.

    This is the only test here that opens the raw archive, because it is the
    only one that needs to. It confirms the premise of
    `test_season_count_is_nineteen`: if `info["season"]` really were always a
    `str`, that test would be a tautology rather than a guard.

    Measured on the snapshot: the field is `int` in some files and `str` in
    others, and at least one label appears under both types. The numeral for
    the miscount a naive reader produces is deliberately **not** asserted here;
    the point of this test is the mixed typing, not a particular wrong answer.
    """
    kinds: set[type] = set()
    labels_by_type: dict[type, set[str]] = {}
    for path in sorted(RAW_SNAPSHOT.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            season = json.load(handle)["info"]["season"]
        kinds.add(type(season))
        labels_by_type.setdefault(type(season), set()).add(str(season))

    assert len(kinds) > 1, (
        "info['season'] is now single-typed; the normalisation in "
        "parse._normalise_season may no longer be load-bearing"
    )
    # At least one label must appear under more than one type, otherwise a plain
    # Python set built from the raw values would not over-count at all.
    int_labels = labels_by_type.get(int, set())
    str_labels = labels_by_type.get(str, set())
    assert int_labels & str_labels, (
        "no season label appears under both int and str; the over-count "
        "test above is no longer meaningful"
    )


@pytest.mark.skipif(
    not RAW_SNAPSHOT.is_dir(),
    reason="raw ipl_json/ snapshot not present; the committed-CSV tests still run",
)
def test_season_normalisation_is_load_bearing_in_python() -> None:
    """Pins ``parse._normalise_season`` where it can actually fail.

    Measured 2026-10-04 over all 1,243 files:

    * ``len(set(raw_values))``               -> **24**
    * ``len({_normalise_season(v) ...})``     -> **19**

    The gap is five season labels (2012, 2013, 2015, 2016, 2017) each recorded
    under both ``int`` and ``str``, which are unequal set keys. This is the only
    place the coercion can be observed failing: once pandas has built a frame it
    infers one ``str`` dtype, so the committed CSV is 19 seasons either way.
    Revert the coercion in ``parse._normalise_season`` and *this* test fails
    while ``test_season_count_is_nineteen`` still passes — which is the point of
    having both.
    """
    from iplranking.parse import _normalise_season

    raw = []
    for path in sorted(RAW_SNAPSHOT.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            raw.append(json.load(handle)["info"]["season"])

    naive = len(set(raw))
    normalised = len({_normalise_season(season) for season in raw})

    assert naive == 24, (
        "the unnormalised over-count is no longer 24; the int/str split in this "
        f"snapshot has changed (now {naive}) and this test needs re-measuring"
    )
    assert normalised == EXPECTED_SEASONS
    assert naive > normalised


@pytest.mark.skipif(
    not RAW_SNAPSHOT.is_dir(),
    reason="raw ipl_json/ snapshot not present; the committed-CSV tests still run",
)
def test_parse_directory_frame_agrees_with_the_committed_csv() -> None:
    """Re-parsing the raw archive reproduces the committed snapshot exactly.

    This is the re-derivability half of the provenance claim: the CSV is not a
    hand-edited artefact, it is what ``scripts/build_snapshot.py`` produces. It
    is also the test that would catch a ``parse.py`` change silently altering the
    snapshot, since the committed CSV would then be stale.
    """
    from iplranking.parse import COLUMNS, parse_directory

    parsed = parse_directory(RAW_SNAPSHOT)
    committed = load_matches()

    assert list(parsed.columns) == list(COLUMNS)
    assert len(parsed) == len(committed)
    for column in COLUMNS:
        if column in ("margin_runs", "margin_wickets"):
            left = parsed[column].astype("float64").reset_index(drop=True)
            right = committed[column].astype("float64").reset_index(drop=True)
        else:
            # `Series.equals` treats NaN/NA as equal when in the same place,
            # which a plain `==` comparison does not.
            left = parsed[column].astype("string").fillna("<NA>").reset_index(drop=True)
            right = (
                committed[column].astype("string").fillna("<NA>").reset_index(drop=True)
            )
        assert left.equals(right), f"column {column!r} differs from the CSV"


# --------------------------------------------------------------------------
# Date ordering — the CSV row order is the design-matrix row order
# --------------------------------------------------------------------------


def test_dates_are_iso_formatted(matches: pd.DataFrame) -> None:
    dates = matches["date"].astype(str)
    assert dates.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()


def test_csv_is_sorted_chronologically(matches: pd.DataFrame) -> None:
    """Row order is the design matrix's row order, so it must be total."""
    dates = matches["date"].astype(str)
    assert dates.is_monotonic_increasing


def test_match_ids_are_unique(matches: pd.DataFrame) -> None:
    assert int(matches["match_id"].nunique()) == EXPECTED_ROWS


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def provenance() -> dict:
    assert PROVENANCE_JSON.is_file(), f"provenance record missing: {PROVENANCE_JSON}"
    return json.loads(PROVENANCE_JSON.read_text(encoding="utf-8"))


def test_provenance_parses(provenance: dict) -> None:
    assert isinstance(provenance, dict)


def test_provenance_has_every_required_field(provenance: dict) -> None:
    """`AGENTS.md` section 7: the snapshot ships with its provenance."""
    required = {
        "source_url",
        "cricsheet_version",
        "utc_fetch_date",
        "http_status",
        "sha256",
        "sha256_covers",
        "row_count",
        "file_count",
        "licence",
    }
    assert required <= set(provenance)


def test_provenance_row_count_matches_the_csv(
    provenance: dict, matches: pd.DataFrame
) -> None:
    assert provenance["row_count"] == len(matches)


def test_provenance_sha256_is_64_hex_characters(provenance: dict) -> None:
    digest = provenance["sha256"]
    assert isinstance(digest, str)
    assert re.fullmatch(r"[0-9a-f]{64}", digest), f"not a sha256 hex digest: {digest!r}"


def test_provenance_does_not_assert_an_http_status_it_did_not_receive(
    provenance: dict,
) -> None:
    """No fetch happened in the run that wrote this file, so no 200.

    The archive is not retained on this machine. Writing `200` here would be a
    fabricated provenance claim, which is the exact class of error
    `AGENTS.md` section 4 exists to prevent.
    """
    assert provenance["http_status"] != 200
    assert "not recorded" in provenance["http_status"].lower()


def test_provenance_says_what_the_hash_covers(provenance: dict) -> None:
    """`AGENTS.md` section 7 and spec section 6: the record must be explicit
    that the hash covers the extracted file set, not the archive."""
    covers = provenance["sha256_covers"].lower()
    assert "manifest" in covers
    assert "extracted" in covers


def test_provenance_does_not_assert_a_licence_term(provenance: dict) -> None:
    """`AGENTS.md` section 7: never assert a licence not read from the source.

    ODC-BY may be *mentioned* — it has to be, to explain that the only ODC-BY
    statement on the site covers the Register dataset and not match data — but
    it must not be attached to the match data as this archive's terms.
    """
    licence = provenance["licence"]
    assert "odc-by" in licence.lower()  # mentioned, and disclaimed
    assert "register" in licence.lower()  # scoped to the other dataset
    assert "match data" in licence.lower()
    # The archive must not be described as licensed under ODC-BY.
    assert not re.search(r"licen[cs]ed under\s+odc", licence, flags=re.IGNORECASE)


def test_provenance_names_the_source_precisely(provenance: dict) -> None:
    """Attribution is by archive name, URL and format version — nothing more."""
    assert provenance["source_url"] == "https://cricsheet.org/downloads/ipl_json.zip"
    assert provenance["cricsheet_version"] == "1.2.0"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", provenance["utc_fetch_date"])