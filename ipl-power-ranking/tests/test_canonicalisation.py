"""Canonicalisation tests.

These pin the *number of unknowns*, n = 15, and the two deliberate
non-merges. Both exist so a future agent cannot "tidy" the rename map:
every extra merge silently changes n, which changes the shape of A from
(558, 15) to (558, 14) and invalidates every already-measured figure in
the project.

Counts asserted here were measured against `ipl_json/` on 2026-10-04.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from iplranking.canon import CANONICAL_MAP, canonical, canonical_teams

# The 19 distinct raw team-name strings in the Cricsheet IPL snapshot.
# Measured: 19 files-level team strings across 1,243 matches.
RAW_TEAM_STRINGS: tuple[str, ...] = (
    "Chennai Super Kings",
    "Deccan Chargers",
    "Delhi Capitals",
    "Delhi Daredevils",
    "Gujarat Lions",
    "Gujarat Titans",
    "Kings XI Punjab",
    "Kochi Tuskers Kerala",
    "Kolkata Knight Riders",
    "Lucknow Super Giants",
    "Mumbai Indians",
    "Pune Warriors",
    "Punjab Kings",
    "Rajasthan Royals",
    "Rising Pune Supergiant",
    "Rising Pune Supergiants",
    "Royal Challengers Bangalore",
    "Royal Challengers Bengaluru",
    "Sunrisers Hyderabad",
)

# The 4 rename pairs of `AGENTS.md` section 7, as {raw: canonical}.
EXPECTED_MAP: dict[str, str] = {
    "Delhi Daredevils": "Delhi Capitals",
    "Delhi Capitals": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Punjab Kings": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Royal Challengers Bengaluru": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
    "Rising Pune Supergiant": "Rising Pune Supergiant",
}


# --------------------------------------------------------------------------
# The map itself
# --------------------------------------------------------------------------


def test_map_is_exactly_the_four_documented_rename_pairs() -> None:
    """4 pairs = 8 raw strings -> 4 canonical names, so n drops by 4."""
    assert CANONICAL_MAP == EXPECTED_MAP


def test_map_collapses_exactly_four_distinct_names() -> None:
    """The number of *distinct targets* is what decides the reduction."""
    distinct_targets = sorted(set(CANONICAL_MAP.values()))
    assert len(distinct_targets) == 4


def test_every_map_key_is_a_raw_string_in_the_snapshot() -> None:
    """A key that never occurs would be a silently dead entry."""
    assert set(CANONICAL_MAP) <= set(RAW_TEAM_STRINGS)
    assert set(CANONICAL_MAP.values()) <= set(RAW_TEAM_STRINGS)


def test_canonical_is_idempotent_and_total() -> None:
    """`canonical(canonical(x)) == canonical(x)` and unknown names pass through."""
    for raw, expected in EXPECTED_MAP.items():
        assert canonical(raw) == expected
        assert canonical(expected) == expected
    assert canonical("Kochi Tuskers Kerala") == "Kochi Tuskers Kerala"


# --------------------------------------------------------------------------
# n = 15
# --------------------------------------------------------------------------


def test_raw_snapshot_has_nineteen_distinct_team_strings() -> None:
    assert len(RAW_TEAM_STRINGS) == 19


def test_canonical_teams_yields_fifteen() -> None:
    """n = 15, measured. Not 10 (that is one season's squad size)."""
    teams = canonical_teams(RAW_TEAM_STRINGS)
    assert len(teams) == 15


def test_canonical_teams_is_sorted_and_deduplicated() -> None:
    """Determinism: the same input must give the same order every run."""
    teams = canonical_teams(RAW_TEAM_STRINGS)
    assert teams == sorted(teams)
    assert len(teams) == len(set(teams))
    # Duplicated input must not duplicate output.
    assert canonical_teams(list(RAW_TEAM_STRINGS) * 3) == teams


# --------------------------------------------------------------------------
# The documented trap: the mid-run spelling drift
# --------------------------------------------------------------------------


def test_rising_pune_spelling_drift_is_merged() -> None:
    """One franchise, two strings (2016 plural / 2017 singular).

    Left unmerged, this invents a 16th unknown with almost no data.
    """
    assert canonical("Rising Pune Supergiants") == canonical("Rising Pune Supergiant")
    assert canonical("Rising Pune Supergiant") == "Rising Pune Supergiant"


# --------------------------------------------------------------------------
# The deliberate non-merges — protected so n cannot drift
# --------------------------------------------------------------------------


def test_gujarat_lions_and_gujarat_titans_stay_separate() -> None:
    """Deliberate non-merge. Merging them would take n from 15 to 14."""
    assert canonical("Gujarat Lions") != canonical("Gujarat Titans")
    assert "Gujarat Lions" in canonical_teams(RAW_TEAM_STRINGS)
    assert "Gujarat Titans" in canonical_teams(RAW_TEAM_STRINGS)


def test_deccan_chargers_and_sunrisers_hyderabad_stay_separate() -> None:
    """Deliberate non-merge. Deccan ends in 2012, Sunrisers begins in 2013.

    There is NO evidence these are the same franchise, and merging them would
    take n from 15 to 13.
    """
    assert canonical("Deccan Chargers") != canonical("Sunrisers Hyderabad")
    assert "Deccan Chargers" in canonical_teams(RAW_TEAM_STRINGS)
    assert "Sunrisers Hyderabad" in canonical_teams(RAW_TEAM_STRINGS)


def test_pune_warriors_is_not_rising_pune() -> None:
    """Two Pune franchises. Only the Rising Pune spelling drift is merged."""
    assert canonical("Pune Warriors") != canonical("Rising Pune Supergiant")


# --------------------------------------------------------------------------
# The banned claim, as an executable assertion
# --------------------------------------------------------------------------


def test_banned_mumbai_indians_reincarnation_claim_is_not_implied() -> None:
    """`AGENTS.md` section 7 bans claiming DD/RR "became MI in 2011".

    It is false: Mumbai Indians appears in all 19 seasons. The map must not
    mention them, and the three franchises stay distinct unknowns.
    """
    assert "Mumbai Indians" not in CANONICAL_MAP
    assert canonical("Mumbai Indians") == "Mumbai Indians"
    assert len(
        {
            canonical("Delhi Daredevils"),
            canonical("Rajasthan Royals"),
            canonical("Mumbai Indians"),
        }
    ) == 3


# --------------------------------------------------------------------------
# Against the raw snapshot itself, when it is present
# --------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_SNAPSHOT = REPO_ROOT / "ipl_json"


@pytest.mark.skipif(
    not RAW_SNAPSHOT.is_dir(),
    reason="raw ipl_json/ snapshot not present; the derived-count tests still run",
)
def test_canonical_teams_over_the_whole_raw_snapshot_is_fifteen() -> None:
    """Read all 1,243 files, collect every team string, canonicalise, expect 15."""
    names: set[str] = set()
    for path in RAW_SNAPSHOT.glob("*.json"):
        with path.open(encoding="utf-8") as handle:
            info = json.load(handle)["info"]
        names.update(info["teams"])
    assert len(names) == 19
    assert len(canonical_teams(names)) == 15
