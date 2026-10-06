"""IPL team-name canonicalisation.

The number of unknowns in this project is ``n = 15``.

Measured on the Cricsheet IPL snapshot (1,243 JSON files, Cricsheet JSON
v1.2.0, read 2026-10-04): there are **19 distinct raw team-name strings**, and
merging exactly **four** rename pairs brings that to **15**.

Why exactly four, and why these four
------------------------------------
``Delhi Daredevils``/``Delhi Capitals``, ``Kings XI Punjab``/``Punjab Kings``
and ``Royal Challengers Bangalore``/``Royal Challengers Bengaluru`` are
franchise renames: the same entity recorded under two names by the data
provider.

``Rising Pune Supergiants`` (2016) / ``Rising Pune Supergiant`` (2017) is a
different kind of fault: a **spelling drift mid-run**, one franchise recorded
under two spellings in two consecutive seasons. Left unmerged it silently
invents a **16th unknown carrying almost no data**, which in least squares
becomes one of the most extreme coefficients in the fit — for free, from a
typo.

Why two merges are deliberately NOT made
---------------------------------------
``Gujarat Lions`` -> ``Gujarat Titans`` is *not* applied. One extra merge takes
``n`` from 15 to 14. ``Deccan Chargers`` -> ``Sunrisers Hyderabad`` is *not*
applied either; both together would take ``n`` to 13. In both cases the merge
is a claim about real-world franchise history that the data does not
establish, and the relation ``rank(A) = n - 1`` would still hold — but ``n``
and therefore every matrix dimension, every length and every measured figure
downstream would change. ``AGENTS.md`` section 4 forbids manufacturing the
link, and ``tests/test_canonicalisation.py`` pins both non-merges so a later
"cleanup" cannot quietly change the shape of the design matrix.

A third pair is *also* left alone for the same reason: ``Pune Warriors`` and
``Rising Pune Supergiant`` are two different Pune franchises, not one team.

Banned claim
------------
There is no support anywhere in this repository for "Deccan Chargers /
Rajasthan Royals became Mumbai Indians in 2011". It is false: Mumbai Indians
appears in all 19 seasons, Deccan ends in 2012 and Sunrisers begins in 2013.
It must not be added to the map and must not be repeated in the demo.
"""

from __future__ import annotations

from typing import Iterable

__all__ = ["CANONICAL_MAP", "canonical", "canonical_teams"]

#: Raw team-name string -> canonical franchise name. Measured against the
#: snapshot: 8 keys (4 pairs) covering 4 targets, so 19 raw strings become 15.
CANONICAL_MAP: dict[str, str] = {
    # Franchise renames.
    "Delhi Daredevils": "Delhi Capitals",
    "Delhi Capitals": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Punjab Kings": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Royal Challengers Bengaluru": "Royal Challengers Bengaluru",
    # Spelling drift within one season pair (2016 plural, 2017 singular).
    "Rising Pune Supergiants": "Rising Pune Supergiant",
    "Rising Pune Supergiant": "Rising Pune Supergiant",
}

# Deliberately absent, and asserted absent in the test suite:
#   "Gujarat Lions"   -> "Gujarat Titans"      (not merged; n would fall to 14)
#   "Deccan Chargers" -> "Sunrisers Hyderabad" (not merged; n would fall to 13)
#   "Pune Warriors"   -> "Rising Pune ..."    (a different franchise)
DELIBERATE_NON_MERGES: tuple[tuple[str, str], ...] = (
    ("Gujarat Lions", "Gujarat Titans"),
    ("Deccan Chargers", "Sunrisers Hyderabad"),
    ("Pune Warriors", "Rising Pune Supergiant"),
)


def canonical(name: str) -> str:
    """Return the canonical franchise name for one raw team-name string.

    Strings absent from :data:`CANONICAL_MAP` are returned unchanged, so this
    is total over any input and safe to call on data read for the first time.
    """
    return CANONICAL_MAP.get(name, name)


def canonical_teams(teams: Iterable[str]) -> list[str]:
    """Canonicalise, deduplicate and sort an iterable of raw team names.

    Returns the 15 franchise names in alphabetical order. Sorting is not
    cosmetic: every matrix in this project indexes teams by position, and the
    plan's determinism rule requires one fixed ordering everywhere. Feeding the
    19 raw snapshot strings to this function returns exactly 15 names.
    """
    return sorted({canonical(name) for name in teams})