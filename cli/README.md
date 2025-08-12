# Interactive Capture CLI

Run an interactive, step-by-step capture processing flow that prompts for baseline inputs, verifies `capture/capture.txt`, auto-generates a scenario ID, moves the file into the `logs/` structure, writes metadata, and updates the master index CSV.

## Usage

```bash
python cli/interactive_capture.py
```

You will be prompted to:

- Confirm the detected system date/time or override it
- Enter `test_type` and optional `notes`
- Optionally enter baseline values (nulls are allowed):
  - `start_voltage` (V)
  - `resting_throttle` (V)
  - `controller_temperature` (°C)
  - `motor_temperature` (°C)
  - `slide_regen_mode_enabled` (yes/no)
  - `pas_level` (0-5)
- Ensure `capture/capture.txt` is present
  - If missing, you can choose to use `capture - test.txt` instead (if present), or proceed metadata-only
- After each run, optionally commit and push changes to Git

## Multi-log sessions

- After each log, the CLI asks if you want to process another.
- Prompts show previous values as defaults; press Enter to reuse.

The program will then:

- Auto-generate a scenario ID: `SCN_YYYY_MM_DD_XXX`
- Move `capture/capture.txt` to `logs/YYYY-MM-DD/SCN_YYYY_MM_DD_XXX.log`
- Write `logs/YYYY-MM-DD/SCN_YYYY_MM_DD_XXX.metadata.json`
- Update `index/master_log_index.csv` (creating if missing)
- Print a summary of actions

## Configuration

Edit `cli/config.py` to adjust:

- `GITHUB_REPO`: Owner/repo string for GitHub links in the index. Leave empty to omit links.

## Notes

- The CLI validates numeric inputs with reasonable ranges to prevent typos. Leave blank to store `null` in metadata.
- The date/time is stored as `YYYY-MM-DDTHH:MM:00Z` without converting local time to UTC.
- The tool is self-contained within `cli/` and does not require other scripts.
