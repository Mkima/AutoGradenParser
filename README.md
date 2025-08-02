# Garden Irrigation Analysis System

A comprehensive system for analyzing garden sensor data and providing irrigation recommendations based on optimal growing conditions for different vegetables.

## Overview

This system processes sensor data from multiple gardens, compares readings against optimal ranges for different vegetables, and provides compliance scores and irrigation recommendations. It supports temperature, moisture, light, humidity, and CO2 monitoring across multiple garden locations.


## Features

- **Multi-Garden Support**: Analyze multiple gardens with different vegetables
- **Sensor Data Processing**: Handle temperature, moisture, light, humidity, and pump sensors
- **Compliance Analysis**: Calculate how well each garden meets optimal conditions
- **Visual Reports**: Generate charts and graphs for garden performance
- **Irrigation Recommendations**: Automated suggestions based on sensor readings
- **Time Series Analysis**: Track garden conditions over time

## File Structure

src/ ├── main.py # Entry point and CLI interface 
     ├── importer.py # Data import and parsing from log files 
     └── analyzer.py # Analysis engine and reporting

data/ ├── garden_profiles.json # Optimal growing conditions for vegetables 
      ├── device_map_extended.json # Sensor configuration and mappings
      └── plant_sensor_uart_full.log # Raw sensor data logs

## Installation

### Requirements
- Python 3.7+
- pandas
- numpy
- matplotlib
- seaborn

### Setup
```bash
pip install pandas numpy matplotlib seaborn
```

### Usage
### Basic Usage
```bash
python main.py
```
### Custom Parameters
```bash
python src/main.py --input data/sensor_data.log --mapping_json data/config.json --output analysis_results
```

### Command Line Options
--input: Path to sensor data log file (default: ../data/plant_sensor_uart_full.log)
--mapping_json: Path to device mapping configuration (default: ../data/device_map_extended.json)
--output: Output directory for analysis results (default: ../data/log_analysis_{timestamp})


## Analysis Features
### Compliance Scoring
* Overall Score: Average compliance across all sensor types
* Individual Scores: Per-sensor type compliance percentage
* Status Categories:
    * Good (80%+)
    * Needs Attention (60-79%)
    * Poor (<60%)
### Visualization
* Overall compliance scores by garden
* Compliance heatmap by sensor type
* Vegetable type distribution
* Time series analysis for individual gardens
* Current vs optimal range comparisons
### Irrigation Recommendations
Automated suggestions based on sensor readings:

💧 Irrigation adjustments for moisture levels

🌡️ Temperature control recommendations

💨 Humidity and ventilation suggestions

⚠️ Sensor maintenance alerts


## Up Next:
* Add an MCP to feed the data to an LLM model for wizer analysis
* Add streamlit to explore data and charts easier.


## License 
MIT  License