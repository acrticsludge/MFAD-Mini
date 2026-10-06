"""One-shot snapshot builder: raw Cricsheet JSON -> committed CSV + provenance.

    python scripts/build_snapshot.py

Writes two files and nothing else:

* ``data/matches.csv``       — the only file the demo ever reads.
* ``data/provenance.json``   — the provenance record `AGENTS.md` section 7
                               requires, which did not exist in this
                               repository before this run.

This script is **not** on the demo path. It is re-runnable from a clean clone
because the raw archive contents are committed at ``ipl_json/``.

Determinism
-----------
Same input file set -> byte-identical output. Achieved by: iterating files in
sorted order, sorting rows by ``(date, match_id)``, fixing the column order and
the dtypes, and writing with a fixed line terminator. Re-running the script
must leave the working tree clean.

The hash: what is honestly covered
----------------------------------
``AGENTS.md`` section 7 asks for the SHA-256 of the downloaded archive. **The
downloaded ``ipl_json.zip`` is not retained on this machine** — only its
extracted contents are. Rather than invent a hash for a file nobody has, this
script computes the SHA-256 of a *deterministic manifest of the extracted file
set*: the 1,243 relative filenames, sorted, hashed as the UTF-8 concatenation of
``f"{relpath}:{size_bytes}"`` lines. The field ``sha256_covers`` says exactly
that, in words, and ``http_status`` records that no HTTP fetch happened in this
run rather than carrying a fabricated 200. Re-running the script on the same
extraction reproduces the hash; adding or editing any file changes it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "ipl-power-ranking" / "src"))

from iplranking.parse import COLUMNS, parse_directory  # noqa: E402

# --- Provenance constants -------------------------------------------------
# These are claims about *where the data came from*, not counts derived from
# the data. Every count in provenance.json is computed below from the file set
# on disk; none is hard-coded.

SOURCE_URL = "https://cricsheet.org/downloads/ipl_json.zip"
ARCHIVE_NAME = "ipl_json.zip"
CRICKSHEET_VERSION = "1.2.0"
HTTP_STATUS = "not recorded (archive not retained on this machine)"
SHA256_COVERS = (
    "deterministic manifest of extracted files: sorted '<relpath>:<size>' lines"
)
SHA256_NOTE = (
    "The downloaded ipl_json.zip is not retained on this machine, only its "
    "extracted contents, so the archive's own SHA-256 could not be computed. "
    "This hash covers instead a deterministic manifest of the extracted file "
    "set: every *.json file under ipl_json/, named by its path relative to "
    "ipl_json/, sorted lexicographically, hashed as the UTF-8 concatenation of "
    "'<relpath>:<size_in_bytes>' lines each terminated by a newline. It is a "
    "check on the extracted snapshot, not a substitute for the archive digest. "
    "Re-running the builder on the same extraction reproduces it; adding, "
    "editing or deleting any file changes it."
)
LICENCE = (
    "Undetermined for the match data, and deliberately not asserted. No licence "
    "statement for Cricsheet match data was found on cricsheet.org; the site's "
    "/licence/ path returns 404. The only explicit ODC-BY statement on the site "
    "covers the separate Register dataset, not match data. Four third-party "
    "sites assert ODC-BY 1.0 for match data, which is corroboration but not "
    "proof, because none of them is the primary source. Attribution is "
    "therefore by file name and URL only: "
    f"{ARCHIVE_NAME} from {SOURCE_URL}, Cricsheet JSON format version "
    f"{CRICKSHEET_VERSION}."
)

RAW_DIR = REPO_ROOT / "ipl_json"
OUT_CSV = REPO_ROOT / "data" / "matches.csv"
OUT_PROVENANCE = REPO_ROOT / "data" / "provenance.json"


def manifest_sha256(raw_dir: Path) -> tuple[str, int, list[str]]:
    """Hash the extracted file set deterministically.

    Returns ``(hexdigest, file_count, relpaths)``. The manifest is the sorted
    list of ``"<relpath>:<size>"`` lines, so it pins both the *names* and the
    byte *sizes* of every extracted match file.
    """
    paths = sorted(p for p in raw_dir.glob("*.json") if p.is_file())
    lines = [f"{p.relative_to(raw_dir).as_posix()}:{p.stat().st_size}" for p in paths]
    if not lines:
        raise FileNotFoundError(f"no *.json files under {raw_dir}")
    manifest = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(manifest).hexdigest(), len(paths), lines


def build(frame, *, sha256: str, file_count: int) -> None:
    """Write the CSV and the provenance record. Mutates nothing else."""
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Fixed column order, fixed dtypes, fixed line terminator => byte-stable.
    frame.loc[:, list(COLUMNS)].to_csv(
        OUT_CSV,
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
    )

    provenance = {
        "source_url": SOURCE_URL,
        "archive_name": ARCHIVE_NAME,
        "cricsheet_version": CRICKSHEET_VERSION,
        "utc_fetch_date": str(UTC_FETCH_DATE),
        "http_status": HTTP_STATUS,
        "sha256": sha256,
        "sha256_covers": SHA256_COVERS,
        "row_count": int(len(frame)),
        "file_count": int(file_count),
        "licence": LICENCE,
        "notes": SHA256_NOTE,
    }
    OUT_PROVENANCE.write_text(
        json.dumps(provenance, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


# The archive's own README states the format version and the match total. The
# retrieval date is the date this repository's copy was extracted, recorded in
# AGENTS.md as the 2026-10-02 measurement; it is a provenance statement, not a
# derived count.
UTC_FETCH_DATE = date(2026, 10, 2)


def main() -> int:
    if not RAW_DIR.is_dir():
        print(f"error: raw snapshot missing at {RAW_DIR}", file=sys.stderr)
        return 1

    digest, file_count, _ = manifest_sha256(RAW_DIR)
    frame = parse_directory(RAW_DIR)

    if len(frame) != file_count:
        print(
            f"error: parsed {len(frame)} rows from {file_count} files; "
            "one row per file was expected",
            file=sys.stderr,
        )
        return 1

    build(frame, sha256=digest, file_count=file_count)

    print(f"wrote {OUT_CSV.relative_to(REPO_ROOT)}   rows={len(frame)}")
    print(f"wrote {OUT_PROVENANCE.relative_to(REPO_ROOT)}  files={file_count}")
    print(f"sha256({SHA256_COVERS}) = {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
