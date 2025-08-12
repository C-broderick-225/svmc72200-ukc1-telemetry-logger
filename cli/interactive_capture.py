#!/usr/bin/env python3
"""
Interactive CLI to process a capture.txt into the logs structure with metadata and index update.

Flow:
 1) Use current system date/time (with confirmation) or let user override
 2) Auto-generate scenario ID: SCN_YYYY_MM_DD_XXX (next available for date)
 3) Prompt for required fields with validation and optional nulls
 4) Verify `capture/capture.txt` exists (fixed path), prompt user to place it if missing
 5) Move capture into logs/YYYY-MM-DD/SCN_YYYY_MM_DD_XXX.log
 6) Write metadata JSON alongside
 7) Update master index CSV
 8) Show a summary of actions and results

Notes:
 - Designed to be run from anywhere; paths are resolved relative to the repo root
 - Validation ranges are intentionally generous but catch common typos
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# --------------------------- Configuration ---------------------------------

# Ensure project root is importable so `cli.config` can be imported even when
# running this script directly (python cli/interactive_capture.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Try absolute import first, then package-relative
try:
    from cli.config import GITHUB_REPO as REPO_GITHUB_PATH  # type: ignore
except Exception:
    try:
        from .config import GITHUB_REPO as REPO_GITHUB_PATH  # type: ignore
    except Exception:
        # Fallback default if config cannot be imported
        REPO_GITHUB_PATH = ""

# Validation ranges (inclusive)
VOLTAGE_MIN, VOLTAGE_MAX = 0.0, 120.0
THROTTLE_MIN, THROTTLE_MAX = 0.0, 5.0
CTRL_TEMP_MIN, CTRL_TEMP_MAX = -20, 120
MOTOR_TEMP_MIN, MOTOR_TEMP_MAX = -20, 150


# ---------------------------- Data Models ----------------------------------

@dataclass
class MetadataInputs:
    test_type: str
    notes: str
    start_voltage: Optional[float]
    resting_throttle: Optional[float]
    controller_temperature: Optional[int]
    motor_temperature: Optional[int]
    slide_regen_mode_enabled: bool
    pas_level: int


# ---------------------------- Utilities ------------------------------------

def get_project_root() -> Path:
    """Resolve the project root as the parent of this file's directory."""
    # cli/ is one level under the repo root
    return Path(__file__).resolve().parents[1]


def prompt_yes_no(message: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{message} {suffix} ").strip().lower()
        if response == "" and default is not None:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please enter 'y' or 'n'.")


def prompt_str(message: str, allow_empty: bool = False, default: Optional[str] = None) -> str:
    while True:
        hint = f" [{default}]" if default is not None else ""
        val = input(f"{message}{hint} ").strip()
        if val == "" and default is not None:
            return default
        if val or allow_empty:
            return val
        print("This field cannot be empty.")


def prompt_float_optional(message: str, min_value: float, max_value: float, default: Optional[float] = None) -> Optional[float]:
    while True:
        hint = " (blank for null)"
        if default is not None:
            hint = f" [default={default}] (Enter=reuse, 'null'=null)"
        raw = input(f"{message}{hint} ").strip().lower()
        if raw == "" and default is not None:
            return default
        if raw == "":
            return None
        if raw == "null":
            return None
        try:
            val = float(raw)
        except ValueError:
            print("Please enter a number or leave blank.")
            continue
        if val < min_value or val > max_value:
            print(f"Value out of range ({min_value} to {max_value}). Try again.")
            continue
        return val


def prompt_int_optional(message: str, min_value: int, max_value: int, default: Optional[int] = None) -> Optional[int]:
    while True:
        hint = " (blank for null)"
        if default is not None:
            hint = f" [default={default}] (Enter=reuse, 'null'=null)"
        raw = input(f"{message}{hint} ").strip().lower()
        if raw == "" and default is not None:
            return default
        if raw == "":
            return None
        if raw == "null":
            return None
        try:
            val = int(raw)
        except ValueError:
            print("Please enter an integer or leave blank.")
            continue
        if val < min_value or val > max_value:
            print(f"Value out of range ({min_value} to {max_value}). Try again.")
            continue
        return val


def prompt_int_range(message: str, min_value: int, max_value: int, default: Optional[int] = None) -> int:
    """Prompt for a required integer within range. If default provided, Enter reuses it."""
    while True:
        hint = f" [{default}]" if default is not None else ""
        raw = input(f"{message}{hint} ").strip()
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
        except ValueError:
            print("Please enter an integer.")
            continue
        if val < min_value or val > max_value:
            print(f"Value out of range ({min_value} to {max_value}). Try again.")
            continue
        return val


def parse_date(prompt_label: str, default_date: Optional[datetime] = None) -> str:
    """Prompt for a date in YYYY-MM-DD. Returns the string in that format."""
    while True:
        raw = prompt_str(
            f"{prompt_label} (YYYY-MM-DD){' [' + default_date.strftime('%Y-%m-%d') + ']' if default_date else ''}:",
            allow_empty=bool(default_date),
        )
        if raw == "" and default_date:
            return default_date.strftime("%Y-%m-%d")
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def parse_time(prompt_label: str, default_time: Optional[datetime] = None) -> str:
    """Prompt for a time in HH:MM 24-hour. Returns HH:MM."""
    while True:
        raw = prompt_str(
            f"{prompt_label} (HH:MM){' [' + default_time.strftime('%H:%M') + ']' if default_time else ''}:",
            allow_empty=bool(default_time),
        )
        if raw == "" and default_time:
            return default_time.strftime("%H:%M")
        try:
            dt = datetime.strptime(raw, "%H:%M")
            return dt.strftime("%H:%M")
        except ValueError:
            print("Invalid time format. Please use HH:MM (24-hour).")


def generate_scenario_id(for_date: str, logs_dir: Path) -> str:
    """Generate next scenario ID SCN_YYYY_MM_DD_XXX for given date.

    Scans existing .log files within logs/YYYY-MM-DD/ to determine the next index.
    """
    date_token = for_date.replace("-", "_")
    prefix = f"SCN_{date_token}_"
    next_idx = 1
    if logs_dir.exists():
        pattern = re.compile(rf"^SCN_{re.escape(date_token)}_(\d{{3}})\.log$")
        for path in logs_dir.glob("*.log"):
            m = pattern.match(path.name)
            if m:
                try:
                    idx = int(m.group(1))
                    if idx >= next_idx:
                        next_idx = idx + 1
                except ValueError:
                    continue
    return f"{prefix}{next_idx:03d}"


def list_metadata_only_scenarios(logs_dir: Path, for_date: str) -> list[str]:
    """Return scenario IDs for which a metadata file exists but the log file does not."""
    candidates: list[str] = []
    if not logs_dir.exists():
        return candidates
    for metadata_path in logs_dir.glob("*.metadata.json"):
        scenario_id = metadata_path.stem.replace(".metadata", "")
        log_path = logs_dir / f"{scenario_id}.log"
        if not log_path.exists():
            # Only consider scenarios matching the date prefix
            date_token = for_date.replace("-", "_")
            if scenario_id.startswith(f"SCN_{date_token}_"):
                candidates.append(scenario_id)
    # Sort by numeric suffix ascending
    def suffix_num(sid: str) -> int:
        try:
            return int(sid.rsplit("_", 1)[-1])
        except Exception:
            return 0
    candidates.sort(key=suffix_num)
    return candidates


def prompt_select_from_list(title: str, options: list[str]) -> Optional[str]:
    """Prompt the user to select one option from a list.

    Returns the selected value or None if the user chooses to skip.
    """
    print(title)
    for idx, opt in enumerate(options, start=1):
        print(f"  {idx}) {opt}")
    print("  0) Create a new scenario ID")
    while True:
        choice = input("Select an option [0..{n}]: ".format(n=len(options))).strip()
        if choice == "0" or choice == "":
            return None
        try:
            num = int(choice)
        except ValueError:
            print("Enter a number from the list.")
            continue
        if 1 <= num <= len(options):
            return options[num - 1]
        print("Invalid selection. Try again.")


def choose_or_generate_scenario_id(for_date: str, logs_dir: Path) -> str:
    """Offer reuse of metadata-only scenarios for the date, else generate next ID."""
    existing = list_metadata_only_scenarios(logs_dir, for_date)
    if len(existing) == 1:
        reuse = prompt_yes_no(
            f"Reuse existing metadata-only scenario '{existing[0]}' for this date?",
            default=True,
        )
        if reuse:
            return existing[0]
    elif len(existing) > 1:
        selected = prompt_select_from_list(
            "Select a metadata-only scenario to reuse, or create a new one:", existing
        )
        if selected:
            return selected
    # Fallback: create a new one
    return generate_scenario_id(for_date, logs_dir)


def ensure_capture_available(capture_path: Path) -> tuple[str, Optional[Path]]:
    """Check for capture file.

    Returns:
        "capture"        -> capture exists and user confirmed using it
        "metadata_only"  -> user chose to proceed without capture to create only metadata

    Exits the program on explicit abort.
    """
    print(f"Expected capture file at: {capture_path}")
    while True:
        if capture_path.exists():
            size = capture_path.stat().st_size
            print(f"Found capture.txt ({size} bytes).")
            if size == 0:
                print("Warning: capture.txt is empty (0 bytes).")
            if prompt_yes_no("Proceed with this file?", default=True):
                return "capture", capture_path
            else:
                print("Place the correct capture.txt and press Enter to check again...")
                input()
                continue
        else:
            print("capture.txt not found at the expected path.")

            # Offer using 'capture - test.txt' if present
            test_path = capture_path.parent / "capture - test.txt"
            if test_path.exists():
                size = test_path.stat().st_size
                print(f"Found alternate file: '{test_path.name}' ({size} bytes).")
                if size == 0:
                    print("Warning: alternate file is empty (0 bytes).")
                if prompt_yes_no(f"Use '{test_path.name}' instead?", default=True):
                    return "capture", test_path

            if prompt_yes_no("Retry after placing the file?", default=True):
                print("Press Enter when the file is in place...")
                input()
                continue
            # Offer metadata-only path
            if prompt_yes_no("Create only the metadata file without a capture?", default=False):
                return "metadata_only", None
            print("Aborting at user request.")
            sys.exit(1)


def move_capture(capture_path: Path, destination_log: Path) -> None:
    destination_log.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(capture_path), str(destination_log))


def write_metadata(metadata_path: Path, scenario_id: str, date_str: str, time_str: str, inputs: MetadataInputs) -> None:
    metadata = {
        "scenario_id": scenario_id,
        # Store in UTC-style string with 'Z' but do not convert local time
        "date_time": f"{date_str}T{time_str}:00Z",
        "test_type": inputs.test_type,
        "notes": inputs.notes,
        "start_voltage": inputs.start_voltage,
        "resting_throttle": inputs.resting_throttle,
        "controller_temperature": inputs.controller_temperature,
        "motor_temperature": inputs.motor_temperature,
        "slide_regen_mode_enabled": inputs.slide_regen_mode_enabled,
        "pas_level": inputs.pas_level,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        # Keep deterministic key order for readability
        import json

        json.dump(metadata, f, indent=2)


def offer_git_commit_push(project_root: Path, files: list[Path], scenario_id: str, test_type: str) -> None:
    """Offer to commit and push changes to git.

    Adds the provided files, commits with a standard message, and pushes.
    Silently returns if git is not available or the directory is not a repo.
    """
    print()
    if not prompt_yes_no("Commit and push changes now?", default=False):
        print("Skipping git commit/push. Remember to commit and push later.")
        return

    try:
        # Ensure we are in the repo directory for git commands
        file_args = [str(p.relative_to(project_root)) for p in files if p is not None]
        if not file_args:
            print("No files to commit.")
            return

        subprocess.run(["git", "-C", str(project_root), "add", "--"] + file_args, check=True)
        commit_msg = f"Add scenario {scenario_id}: {test_type}"
        subprocess.run(["git", "-C", str(project_root), "commit", "-m", commit_msg], check=False)
        subprocess.run(["git", "-C", str(project_root), "push"], check=False)
        print("Git commit/push attempted. Review output above for any errors.")
    except Exception as e:
        print(f"Git operation skipped or failed: {e}")


def update_master_index(
    index_path: Path,
    date_str: str,
    time_str: str,
    scenario_id: str,
    test_type: str,
    log_path: Path,
    metadata_path: Path,
) -> None:
    # Calculate file_size and record_count
    file_size = log_path.stat().st_size if log_path.exists() else 0
    record_count = 0
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            record_count = sum(1 for line in f if line.strip())

    # Prepare links (POSIX paths)
    if REPO_GITHUB_PATH:
        log_link = (
            f"https://github.com/{REPO_GITHUB_PATH}/blob/main/" + log_path.as_posix()
        )
        metadata_link = (
            f"https://github.com/{REPO_GITHUB_PATH}/blob/main/" + metadata_path.as_posix()
        )
    else:
        log_link = ""
        metadata_link = ""

    index_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date",
        "filename",
        "file_size",
        "record_count",
        "metadata_file",
        "created_at",
        "test_description",
        "log_link",
        "metadata_link",
    ]

    # Load existing rows if any
    rows = []
    if index_path.exists() and index_path.stat().st_size > 0:
        with open(index_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

    # Find existing row by filename (unique per scenario)
    filename = f"{scenario_id}.log"
    existing_idx = next((i for i, r in enumerate(rows) if r.get("filename") == filename), None)

    # Preserve created_at if updating
    created_at_value = f"{date_str}T{time_str}:00Z"
    if existing_idx is not None:
        existing = rows[existing_idx]
        if existing.get("created_at"):
            created_at_value = existing["created_at"]

        # Update row in place
        rows[existing_idx] = {
            "date": date_str,
            "filename": filename,
            "file_size": file_size,
            "record_count": record_count,
            "metadata_file": f"{scenario_id}.metadata.json",
            "created_at": created_at_value,
            "test_description": test_type,
            "log_link": log_link,
            "metadata_link": metadata_link,
        }
    else:
        # Append new row
        rows.append(
            {
                "date": date_str,
                "filename": filename,
                "file_size": file_size,
                "record_count": record_count,
                "metadata_file": f"{scenario_id}.metadata.json",
                "created_at": created_at_value,
                "test_description": test_type,
                "log_link": log_link,
                "metadata_link": metadata_link,
            }
        )

    # Write back all rows with header
    with open(index_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def collect_inputs(default_dt: datetime, prev: Optional[MetadataInputs]) -> tuple[str, str, MetadataInputs]:
    # Date/Time: default to system, allow override
    use_system = prompt_yes_no(
        f"Use system date/time {default_dt.strftime('%Y-%m-%d %H:%M')}?", default=True
    )
    if use_system:
        date_str = default_dt.strftime("%Y-%m-%d")
        time_str = default_dt.strftime("%H:%M")
    else:
        date_str = parse_date("Enter date", default_dt)
        time_str = parse_time("Enter time", default_dt)

    # Fields (no additional beyond baseline + mode)
    test_type = prompt_str("Test type (brief description):", default=(prev.test_type if prev else None))
    notes = prompt_str("Notes (observations/conditions):", allow_empty=True, default=(prev.notes if prev else None))
    start_voltage = prompt_float_optional(
        f"Start voltage (V) {VOLTAGE_MIN}-{VOLTAGE_MAX}:", VOLTAGE_MIN, VOLTAGE_MAX, default=(prev.start_voltage if prev else None)
    )
    resting_throttle = prompt_float_optional(
        f"Resting throttle (V) {THROTTLE_MIN}-{THROTTLE_MAX}:",
        THROTTLE_MIN,
        THROTTLE_MAX,
        default=(prev.resting_throttle if prev else None),
    )
    controller_temperature = prompt_int_optional(
        f"Controller temperature (°C) {CTRL_TEMP_MIN}-{CTRL_TEMP_MAX}:",
        CTRL_TEMP_MIN,
        CTRL_TEMP_MAX,
        default=(prev.controller_temperature if prev else None),
    )
    motor_temperature = prompt_int_optional(
        f"Motor temperature (°C) {MOTOR_TEMP_MIN}-{MOTOR_TEMP_MAX}:",
        MOTOR_TEMP_MIN,
        MOTOR_TEMP_MAX,
        default=(prev.motor_temperature if prev else None),
    )
    slide_regen_mode_enabled = prompt_yes_no(
        "Slide regen mode enabled?",
        default=(prev.slide_regen_mode_enabled if prev else True),
    )
    pas_level = prompt_int_range("PAS level (0-5):", 0, 5, default=(prev.pas_level if prev else None))

    inputs = MetadataInputs(
        test_type=test_type,
        notes=notes,
        start_voltage=start_voltage,
        resting_throttle=resting_throttle,
        controller_temperature=controller_temperature,
        motor_temperature=motor_temperature,
        slide_regen_mode_enabled=slide_regen_mode_enabled,
        pas_level=pas_level,
    )

    return date_str, time_str, inputs


def main() -> int:
    project_root = get_project_root()
    capture_path = project_root / "capture" / "capture.txt"

    prev_inputs: Optional[MetadataInputs] = None

    while True:
        now = datetime.now()
        date_str, time_str, inputs = collect_inputs(now, prev_inputs)

        # Choose existing metadata-only scenario or auto-generate next ID
        logs_dir = project_root / "logs" / date_str
        scenario_id = choose_or_generate_scenario_id(date_str, logs_dir)
        log_path = logs_dir / f"{scenario_id}.log"
        metadata_path = logs_dir / f"{scenario_id}.metadata.json"
        index_path = project_root / "index" / "master_log_index.csv"

        print("\nPlanned outputs:")
        print(f"  Scenario ID: {scenario_id}")
        print(f"  Log file:    {log_path}")
        print(f"  Metadata:    {metadata_path}")
        print(f"  Index CSV:   {index_path}")

        # Determine capture availability/intent
        print()
        mode, selected_capture = ensure_capture_available(capture_path)

        if mode == "capture":
            print("\nPlanned outputs:")
            print(f"  Scenario ID: {scenario_id}")
            print(f"  Log file:    {log_path}")
            print(f"  Metadata:    {metadata_path}")
            print(f"  Index CSV:   {index_path}")

            if not prompt_yes_no("Proceed to move file, write metadata, and update index?", True):
                print("Aborted by user before processing.")
                return 1

            # Execute full operations
            # Move the chosen capture source (capture.txt or 'capture - test.txt')
            move_capture(selected_capture if selected_capture else capture_path, log_path)
            write_metadata(metadata_path, scenario_id, date_str, time_str, inputs)
            update_master_index(
                index_path,
                date_str,
                time_str,
                scenario_id,
                inputs.test_type,
                log_path,
                metadata_path,
            )

            # Summary
            print("\nDone. Summary:")
            size = log_path.stat().st_size if log_path.exists() else 0
            print(f"  Moved capture -> {log_path.name} ({size} bytes)")
            print(f"  Wrote metadata -> {metadata_path.name}")
            print(f"  Updated index -> {index_path}")
            print(f"  Created at: {date_str}T{time_str}:00Z")

            # Offer git commit/push
            offer_git_commit_push(
                project_root,
                files=[log_path, metadata_path, index_path],
                scenario_id=scenario_id,
                test_type=inputs.test_type,
            )

        else:
            # Metadata-only path
            logs_dir.mkdir(parents=True, exist_ok=True)
            write_metadata(metadata_path, scenario_id, date_str, time_str, inputs)
            # Update index even without a log file (size and record_count will be 0)
            update_master_index(
                index_path,
                date_str,
                time_str,
                scenario_id,
                inputs.test_type,
                log_path,
                metadata_path,
            )

            print("\nDone (metadata only). Summary:")
            print(f"  Wrote metadata -> {metadata_path}")
            print("  Log move skipped (no capture.txt)")
            print(f"  Updated index -> {index_path}")
            print(f"  Created at: {date_str}T{time_str}:00Z")

            # Offer git commit/push
            offer_git_commit_push(
                project_root,
                files=[metadata_path, index_path],
                scenario_id=scenario_id,
                test_type=inputs.test_type,
            )

        # Save inputs for potential reuse
        prev_inputs = inputs

        # Ask to process another log in the same session
        if not prompt_yes_no("\nProcess another log?", default=False):
            break

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)


