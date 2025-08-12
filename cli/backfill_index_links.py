#!/usr/bin/env python3
"""
Backfill or fix GitHub links (log_link, metadata_link) in index/master_log_index.csv
using the repository setting from cli/config.py.

Usage:
    python cli/backfill_index_links.py

This will update every row to ensure links are full GitHub URLs pointing to:
  - logs/<date>/<filename>
  - logs/<date>/<metadata_file>
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from cli.config import GITHUB_REPO  # type: ignore
except Exception:  # pragma: no cover
    print("Error: Unable to import cli.config. Ensure you run from the repo root.")
    sys.exit(1)


def main() -> int:
    if not GITHUB_REPO:
        print("Error: GITHUB_REPO is empty in cli/config.py; cannot construct links.")
        return 1

    index_path = PROJECT_ROOT / "index" / "master_log_index.csv"
    if not index_path.exists() or index_path.stat().st_size == 0:
        print(f"No index file found or it is empty: {index_path}")
        return 0

    # Read existing rows
    with open(index_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    # Ensure required columns exist in header
    required = {
        "date",
        "filename",
        "metadata_file",
        "log_link",
        "metadata_link",
    }
    missing = [c for c in required if c not in fieldnames]
    if missing:
        print(
            "Error: CSV is missing required columns: " + ", ".join(missing) +
            ". Please ensure header matches README."
        )
        return 1

    # Update links
    for row in rows:
        date_str = row.get("date", "").strip()
        filename = row.get("filename", "").strip()
        metadata_file = row.get("metadata_file", "").strip()

        # Build POSIX-style relative paths
        log_rel = Path("logs") / date_str / filename
        meta_rel = Path("logs") / date_str / metadata_file

        row["log_link"] = f"https://github.com/{GITHUB_REPO}/blob/main/{log_rel.as_posix()}"
        row["metadata_link"] = f"https://github.com/{GITHUB_REPO}/blob/main/{meta_rel.as_posix()}"

    # Write back
    with open(index_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated links for {len(rows)} row(s) in {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


