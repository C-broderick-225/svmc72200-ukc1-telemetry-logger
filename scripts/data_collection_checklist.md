# Data Collection Checklist

## Before Each Test

### 1. Record System Baseline (from mobile app)
- [ ] **Start Voltage** (V)
- [ ] **Resting Throttle** (V) 
- [ ] **Controller Temperature** (°C)
- [ ] **Motor Temperature** (°C)
- [ ] **Mode Setting** (e.g., "slide regen mode")

### 2. Test Information
- [ ] **Date & Time** (ISO 8601 format)
- [ ] **Test Type** (describe the test sequence)
- [ ] **Notes** (any unusual conditions)

### 3. File Management
- [ ] Generate **Scenario ID** (SCN_YYYY_MM_DD_XXX format)
- [ ] Rename capture.txt to SCN_YYYY_MM_DD_XXX.log
- [ ] Create metadata JSON file
- [ ] Update master_log_index.csv with test description and hyperlinks
- [ ] Place files in correct date folder

## Example Scenario ID Generation
- Date: 2025-08-12
- Test number: 001
- Scenario ID: `SCN_2025_08_12_001`

## Required Data Format
- **Voltage**: Float (e.g., 81.43)
- **Temperature**: Integer (e.g., 31)
- **Throttle**: Float (e.g., 1.07)
- **Date/Time**: ISO 8601 (e.g., "2025-08-12T14:30:00Z")
