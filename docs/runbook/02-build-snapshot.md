# 02 — Build the data snapshot

## What this step is

You only run this at build time. The demo never reads the raw archive: its only
input is the committed `data/matches.csv`. This step rebuilds that CSV and its
provenance record from `ipl_json/`, which shows the snapshot can be reproduced
from a clean clone with no network.

Both outputs are **generated and committed on purpose**, as `.gitignore`
explains. A clone without `data/matches.csv` makes the demo exit 2 with a
message telling you to run this script.

## Command

```bash
python ipl-power-ranking/scripts/build_snapshot.py
```

The script finds the repository root from its own location
(`Path(__file__).parents[2]`), so you can run it from any directory.

## Pipeline

1. `parse.parse_directory()` (`src/iplranking/parse.py`) reads every
   `ipl_json/*.json` in sorted order.
2. For each match it reads `info.outcome.winner`, `info.outcome.by.runs` /
   `.wickets`, `info.outcome.method`, the Super Over flag and the season. It
   uses `parse._require()` for mandatory fields, which raises
   `SnapshotFieldError` naming the file and the field.
3. `parse._normalise_season()` turns every season into a `str`.
4. `canon.canonical()` adds the `canonical_team1` / `canonical_team2` columns.
5. Rows are sorted by `(date, match_id)` and written with a fixed column order
   (`parse.COLUMNS`), fixed dtypes and a fixed line terminator.
6. The script hashes the manifest and writes `provenance.json`.

## Outputs

**`data/matches.csv`** has 1,243 rows with these columns: `match_id`, `date`,
`season`, `team1`, `team2`, `winner`, `margin_runs`, `margin_wickets`,
`method`, `is_super_over`, `canonical_team1`, `canonical_team2`.

**`data/provenance.json`** has these fields:

| Field | Value |
|---|---|
| `source_url` | `https://cricsheet.org/downloads/ipl_json.zip` |
| `archive_name` | `ipl_json.zip` |
| `cricsheet_version` | `1.2.0` |
| `utc_fetch_date` | `2026-10-02` |
| `http_status` | "not recorded (archive not retained on this machine)". It is not set to a made-up 200 |
| `sha256` | hash of a **manifest** of the extracted files, not of the zip |
| `sha256_covers` | the manifest rule: sorted `<relpath>:<size>` lines |
| `row_count`, `file_count` | 1243, 1243, both computed rather than typed in |
| `licence` | undetermined, deliberately not asserted |
| `notes` | why the archive digest could not be computed |

The output is deterministic: the same input set gives byte-identical files.
Running the script again should leave `git status` clean.

## How to check provenance

Run the builder, then confirm that `git diff data/` is empty and that the
`sha256` it reports matches the committed one.

## Load-time guards (`data.py`)

The demo checks the CSV every time it loads it:

- If a required column is missing, it raises `ValueError` ("regenerate with
  `scripts/build_snapshot.py`").
- If the row count is not 1,243 (`EXPECTED_MATCHES`), it treats the file as
  truncated and raises `ValueError`. This is a corruption check only; no other
  count is hard-coded.
- If the file is missing, it raises `FileNotFoundError`. The CLI turns all of
  these into `cannot start: …` and exit code 2.

## The two schema facts a naive reader gets wrong

1. The winner is at `info.outcome.winner`, **not** `info.winner`. Reading
   `info["winner"]` raises `KeyError` in all 1,243 files.
2. `info["season"]` has mixed types: an `int` in 511 files and a `str` in 732,
   with five season labels appearing as both. Convert to `str` before counting
   distinct seasons, or you get 24 instead of 19.

## Licence position

No licence term for match data was found on the primary source. The licence
path on cricsheet.org returns 404, and the only ODC-BY statement there covers
the separate Register dataset. Attribution is by file name, source URL and
retrieval date only.
