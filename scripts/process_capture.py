#!/usr/bin/env python3
"""
Process capture.txt files into structured log files.

This script processes raw capture.txt files from the capture/ directory
and converts them into properly named log files in the logs/YYYY-MM-DD/ structure.

Usage:
    python scripts/process_capture.py [scenario_id] [date] [time] [test_type] [notes]
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

def process_capture(scenario_id, date, time, test_type, notes):
    """
    Process a capture.txt file into a structured log.
    
    Args:
        scenario_id (str): Scenario ID (e.g., SCN_2025_08_12_003)
        date (str): Date in YYYY-MM-DD format
        time (str): Time in HH:MM format
        test_type (str): Description of the test
        notes (str): Additional notes
    """
    
    # Paths
    capture_file = Path("capture/capture.txt")
    logs_dir = Path(f"logs/{date}")
    log_file = logs_dir / f"{scenario_id}.log"
    metadata_file = logs_dir / f"{scenario_id}.metadata.json"
    
    # Check if capture file exists
    if not capture_file.exists():
        print(f"Error: {capture_file} not found!")
        return False
    
    # Create logs directory if it doesn't exist
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Move and rename capture file
    shutil.move(str(capture_file), str(log_file))
    print(f"✓ Moved capture.txt to {log_file}")
    
    # Create metadata file
    metadata_content = f'''{{
  "scenario_id": "{scenario_id}",
  "date_time": "{date}T{time}:00Z",
  "test_type": "{test_type}",
  "notes": "{notes}",
  "start_voltage": 0.0,
  "resting_throttle": 0.0,
  "controller_temperature": 0,
  "motor_temperature": 0,
  "mode_setting": "e.g., slide regen mode"
}}'''
    
    with open(metadata_file, 'w') as f:
        f.write(metadata_content)
    print(f"✓ Created metadata file: {metadata_file}")
    
    # Update master log index
    update_master_index(scenario_id, date, time, test_type, log_file, metadata_file)
    
    print(f"✓ Successfully processed {scenario_id}")
    return True

def update_master_index(scenario_id, date, time, test_type, log_file, metadata_file):
    """Update the master log index CSV file."""
    
    index_file = Path("index/master_log_index.csv")
    
    # Read existing content
    with open(index_file, 'r') as f:
        lines = f.readlines()
    
    # Create new entry
    log_link = f"https://github.com/C-broderick-225/svmc72200-ukc1-telemetry-logs/blob/main/{log_file}"
    metadata_link = f"https://github.com/C-broderick-225/svmc72200-ukc1-telemetry-logs/blob/main/{metadata_file}"
    
    new_entry = f'{date},{scenario_id}.log,0,0,{scenario_id}.metadata.json,{date}T{time}:00Z,"{test_type}",{log_link},{metadata_link}\n'
    
    # Add to end of file (before any trailing newlines)
    lines.append(new_entry)
    
    # Write back
    with open(index_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✓ Updated master log index")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python scripts/process_capture.py [scenario_id] [date] [time] [test_type] [notes]")
        print("Example: python scripts/process_capture.py SCN_2025_08_12_003 2025-08-12 14:30 'Throttle test' 'Development environment'")
        sys.exit(1)
    
    scenario_id = sys.argv[1]
    date = sys.argv[2]
    time = sys.argv[3]
    test_type = sys.argv[4]
    notes = sys.argv[5]
    
    success = process_capture(scenario_id, date, time, test_type, notes)
    if success:
        print("\n🎉 Processing complete! Don't forget to:")
        print("1. Update metadata with actual baseline readings")
        print("2. Commit and push changes to GitHub")
    else:
        sys.exit(1)
