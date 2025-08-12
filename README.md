# SVMC 72200 UKC1 Telemetry Logs

This repository contains structured data logs captured from an **SVMC 72200 e-bike controller** communicating with a **UKC1 display**. The goal is to create a consistent dataset for analysis, troubleshooting, and performance evaluation.

## Project Description

This project systematically captures and stores telemetry data from e-bike controller systems to enable:
- Performance analysis and optimization
- Troubleshooting and diagnostics
- Comparative testing across different scenarios
- Data-driven controller tuning decisions

## Folder Structure

```
svmc72200-ukc1-telemetry-logs/
├── logs/                    # Raw telemetry data files
│   └── YYYY-MM-DD/         # Date-organized log directories
│       ├── SCN_YYYY_MM_DD_XXX.log    # Raw telemetry data files
│       └── SCN_YYYY_MM_DD_XXX.metadata.json  # Associated metadata
├── index/                   # Log indexing and tracking
│   └── master_log_index.csv # Master index of all log files
└── scripts/                 # Data processing and analysis scripts
```

## Logging Methodology

### Data Collection Process
1. **Pre-Test Baseline**: Record system state from mobile app (voltage, temperatures, throttle position)
2. **Test Planning**: Define test type and parameters
3. **Data Capture**: Record telemetry during test execution
4. **Metadata Creation**: Generate metadata file with baseline readings
5. **Indexing**: Update master log index with new entries

### Metadata Fields

Each log file is accompanied by a metadata JSON file containing:

- **Scenario ID**: Unique identifier (e.g., `SCN_2025_08_12_001`)
- **Date & Time**: Test execution timestamp
- **Test Type**: Description of test sequence (e.g., "Throttle to 20 mph → coast to 10 mph → brake")
- **Notes**: Any unusual observations or conditions
- **Start Voltage**: Initial battery voltage (V)
- **Resting Throttle**: Throttle voltage at rest (V)
- **Controller Temperature**: Initial controller temperature (°C)
- **Motor Temperature**: Initial motor temperature (°C)
- **Mode Setting**: Controller mode configuration (e.g., "slide regen mode")

## Example Metadata JSON

```json
{
  "scenario_id": "SCN_2025_08_12_001",
  "date_time": "2025-08-12T14:30:00Z",
  "test_type": "Throttle to 20 mph → coast to 10 mph → brake",
  "notes": "Development environment - rear wheel off ground",
  "start_voltage": 81.43,
  "resting_throttle": 1.07,
  "controller_temperature": 31,
  "motor_temperature": 23,
  "mode_setting": "slide regen mode"
}
```

## Raw Log Data Format

The telemetry log files contain raw hexadecimal data captured directly from the SVMC 72200 controller. The data format includes:

- **File Extension**: `.log` (raw telemetry data)
- **Data Format**: Hexadecimal strings
- **Content**: Raw controller communication data
- **Processing**: Data requires parsing to extract individual parameters

### Data Processing
Raw log files can be processed to extract structured data including:
- Battery voltage
- Motor current
- Vehicle speed
- Controller temperature
- Throttle position
- Brake status
- And other telemetry parameters

### Example Raw Data
```
18F880060000000060060000000086E618F880060000000060060000000086E6...
```

## Goals

1. **Data Consistency**: Establish standardized logging procedures for reproducible results
2. **Performance Analysis**: Enable detailed analysis of controller behavior across different scenarios
3. **Troubleshooting**: Provide comprehensive data for diagnosing issues
4. **Development Testing**: Support controller development and validation in controlled environment
5. **Research**: Create a valuable dataset for e-bike controller research and optimization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

When adding new log files:
1. Follow the established naming convention
2. Include complete metadata
3. Update the master log index
4. Ensure data quality and consistency

## Data Privacy

All telemetry data is collected for research and development purposes. Personal information is not recorded or stored.
