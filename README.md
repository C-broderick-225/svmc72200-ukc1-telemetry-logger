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
│       ├── SCN_YYYY_MM_DD_XXX.csv    # Telemetry data files
│       └── SCN_YYYY_MM_DD_XXX.metadata.json  # Associated metadata
├── index/                   # Log indexing and tracking
│   └── master_log_index.csv # Master index of all log files
└── scripts/                 # Data processing and analysis scripts
```

## Logging Methodology

### Data Collection Process
1. **Scenario Planning**: Define test parameters and environmental conditions
2. **Setup Documentation**: Record vehicle configuration and controller settings
3. **Data Capture**: Record telemetry during test execution
4. **Metadata Creation**: Generate comprehensive metadata file
5. **Indexing**: Update master log index with new entries

### Metadata Fields

Each log file is accompanied by a metadata JSON file containing:

- **Scenario ID**: Unique identifier (e.g., `SCN_2025_08_12_001`)
- **Date & Time**: Test execution timestamp
- **Start Voltage**: Initial battery voltage
- **Test Type**: Description of test sequence (e.g., "Throttle to 20 mph → coast to 10 mph → brake")
- **Environmental Conditions**: 
  - Temperature
  - Wind conditions
  - Slope/grade
- **Vehicle Setup**: 
  - Controller settings
  - Tire size and pressure
  - Load configuration
  - Other relevant parameters
- **Notes**: Any unusual observations or conditions

## Example Metadata JSON

```json
{
  "scenario_id": "SCN_2025_08_12_001",
  "date_time": "2025-08-12T14:30:00Z",
  "start_voltage": 48.2,
  "test_type": "Throttle to 20 mph → coast to 10 mph → brake",
  "environmental_conditions": {
    "temperature_c": 22.5,
    "wind_speed_mph": 5.2,
    "wind_direction": "NW",
    "slope_percent": 2.1,
    "humidity_percent": 65
  },
  "vehicle_setup": {
    "controller_settings": {
      "max_current_a": 25,
      "max_speed_mph": 28,
      "assist_level": 3
    },
    "tire_size": "26x2.1",
    "tire_pressure_psi": 35,
    "load_kg": 85,
    "battery_capacity_wh": 504
  },
  "notes": "Slight headwind during coast phase, otherwise normal conditions"
}
```

## CSV Column Descriptions

The telemetry CSV files contain the following columns:

| Column | Description | Units | Data Type |
|--------|-------------|-------|-----------|
| timestamp | Recording timestamp | ISO 8601 | String |
| voltage | Battery voltage | V | Float |
| current | Motor current | A | Float |
| speed | Vehicle speed | mph | Float |
| power | Motor power output | W | Float |
| temperature | Controller temperature | °C | Float |
| throttle_position | Throttle input position | % | Integer |
| brake_status | Brake engagement status | Boolean | Integer |
| assist_level | PAS assist level | Level | Integer |
| cadence | Pedal cadence | RPM | Float |
| distance | Cumulative distance | miles | Float |
| trip_time | Trip duration | seconds | Integer |

## Goals

1. **Data Consistency**: Establish standardized logging procedures for reproducible results
2. **Performance Analysis**: Enable detailed analysis of controller behavior across different scenarios
3. **Troubleshooting**: Provide comprehensive data for diagnosing issues
4. **Optimization**: Support data-driven controller tuning and setup decisions
5. **Research**: Create a valuable dataset for e-bike performance research

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
