# Weather Data Engineering CLI Tools

A comprehensive command-line interface for weather data processing with advanced structured logging capabilities.

## Overview

This directory contains two main CLI tools:

1. **`ingest_weather_data.py`** - Ingests weather station data files with validation and error handling
2. **`compute_yearly_stats.py`** - Computes yearly weather statistics from daily data

Both tools feature robust error handling, structured logging, and Django integration for production use.

---

## Weather Data Ingestion (`ingest_weather_data.py`)

### Features

#### 🏗️ Data Processing
- **Batch Processing**: Configurable batch sizes for optimal performance
- **Data Validation**: Comprehensive validation of temperature relationships and data integrity
- **Error Recovery**: Robust error handling with detailed logging and graceful degradation
- **Django Integration**: Full support for Django ORM models with transaction safety
- **Duplicate Detection**: Automatic handling of duplicate records with conflict resolution

#### 📊 Structured Logging
- **Multiple Log Formats**: Simple, structured, and JSON formats
- **Dual Output**: Console and rotating file logging
- **Log Rotation**: Automatic log file rotation (10MB max, 5 backups)
- **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Contextual Information**: Function names, line numbers, timestamps, and modules

#### 🔧 Performance Monitoring
- **Real-time Progress**: Live progress tracking with processing rates
- **Performance Metrics**: Records per second, batch timings, file processing times
- **Resource Usage**: Memory-efficient batch processing
- **Detailed Statistics**: Comprehensive final summary reports

#### 🛡️ Data Quality
- **Temperature Validation**: Ensures max temp >= min temp
- **Precipitation Validation**: Handles negative values and missing data
- **Date Validation**: Robust date parsing with error reporting
- **Missing Value Handling**: Proper handling of -9999 sentinel values

### Usage

#### Basic Usage

```bash
# Default ingestion
python scripts/ingest_weather_data.py

# Specify data directory
python scripts/ingest_weather_data.py --data-dir wx_data

# Dry run (no database changes)
python scripts/ingest_weather_data.py --dry-run
```

#### Advanced Usage

```bash
# Full ingestion with logging
python scripts/ingest_weather_data.py \
    --data-dir wx_data \
    --log-level INFO \
    --log-file logs/weather_ingestion.log \
    --batch-size 2000 \
    --clear

# JSON structured logging
python scripts/ingest_weather_data.py \
    --log-format json \
    --log-file logs/weather_ingestion.json \
    --log-level DEBUG

# High-performance processing
python scripts/ingest_weather_data.py \
    --batch-size 5000 \
    --progress-interval 500 \
    --log-level WARNING
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--data-dir` | Directory containing weather data files | `wx_data` |
| `--log-level` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `--log-file` | Path to log file (optional) | Console only |
| `--log-format` | Log format (simple, structured, json) | `structured` |
| `--batch-size` | Records per batch | `1000` |
| `--clear` | Clear existing data before import | `False` |
| `--dry-run` | Parse files without database changes | `False` |
| `--progress-interval` | Progress reporting interval | `1000` |

---

## Yearly Statistics Computation (`compute_yearly_stats.py`)

### Features

#### 📊 Statistical Aggregation
- **Temperature Statistics**: Average, minimum, and maximum temperatures
- **Precipitation Statistics**: Total, average, and maximum precipitation
- **Data Quality Metrics**: Record counts and completeness percentages
- **Batch Processing**: Efficient processing of station-year combinations
- **Incremental Updates**: Skip existing statistics or force recomputation

#### 🎯 Flexible Filtering
- **Year Filtering**: Target specific years or year ranges
- **Station Filtering**: Process specific weather stations
- **Selective Processing**: Clear existing data or force recomputation
- **Dry Run Mode**: Test computations without database changes

#### 🔧 Performance & Monitoring
- **Progress Tracking**: Real-time batch processing progress
- **Performance Metrics**: Processing rates and timing statistics
- **Error Handling**: Graceful error recovery with detailed reporting
- **Resource Management**: Memory-efficient batch processing

### Usage

#### Basic Usage

```bash
# Compute all yearly statistics
python scripts/compute_yearly_stats.py

# Compute for specific year
python scripts/compute_yearly_stats.py --year 2023

# Compute for specific station
python scripts/compute_yearly_stats.py --station USC00110072
```

#### Advanced Usage

```bash
# Compute for year range with logging
python scripts/compute_yearly_stats.py \
    --start-year 2020 \
    --end-year 2023 \
    --log-level INFO \
    --log-file logs/yearly_stats.log

# Clear existing and recompute
python scripts/compute_yearly_stats.py \
    --clear \
    --year 2023 \
    --batch-size 50

# Force recompute existing statistics
python scripts/compute_yearly_stats.py \
    --force-recompute \
    --station USC00110072 \
    --log-level DEBUG

# Dry run with JSON logging
python scripts/compute_yearly_stats.py \
    --dry-run \
    --log-format json \
    --log-file logs/yearly_stats.json
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--year` | Compute statistics for specific year | All years |
| `--station` | Compute statistics for specific station | All stations |
| `--start-year` | Starting year for range (inclusive) | All years |
| `--end-year` | Ending year for range (inclusive) | All years |
| `--batch-size` | Station-year combinations per batch | `100` |
| `--clear` | Clear existing statistics before computing | `False` |
| `--force-recompute` | Force recomputation of existing statistics | `False` |
| `--dry-run` | Compute without saving to database | `False` |
| `--log-level` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `--log-file` | Path to log file (optional) | Console only |
| `--log-format` | Log format (simple, structured, json) | `structured` |
| `--progress-interval` | Progress reporting interval | `10` |

### Statistics Computed

For each station-year combination, the following statistics are computed:

#### Temperature Statistics
- **Average Maximum Temperature**: Mean of daily maximum temperatures
- **Average Minimum Temperature**: Mean of daily minimum temperatures
- **Maximum Temperature**: Highest daily maximum temperature
- **Minimum Temperature**: Lowest daily minimum temperature

#### Precipitation Statistics
- **Total Precipitation**: Sum of all daily precipitation
- **Average Precipitation**: Mean daily precipitation (excluding missing values)
- **Maximum Precipitation**: Highest daily precipitation

#### Data Quality Metrics
- **Total Records**: Total number of daily records
- **Records with Temperature**: Count of records with valid temperature data
- **Records with Precipitation**: Count of records with valid precipitation data
- **Temperature Completeness**: Percentage of records with temperature data
- **Precipitation Completeness**: Percentage of records with precipitation data

### Example Output

```
📊 Starting yearly weather statistics computation
📋 Found 1,245 station-year combinations to process
📦 Processing batch 1/13 (100 combinations)
   ✅ Batch 1 completed in 0.45s
📦 Processing batch 2/13 (100 combinations)
   ✅ Batch 2 completed in 0.42s
...
🎉 Yearly statistics computation complete!
📊 Processing Summary:
   • Duration: 5.67 seconds
   • Combinations processed: 1,245/1,245
   • Successful computations: 1,245
   • Failed computations: 0
   • Processing rate: 219.58 combinations/second
   • Success rate: 100.00%
📋 Database verification:
   • Total yearly statistics in DB: 1,245
```

---

## Common Features

### Log Formats

#### Simple Format
```
2025-07-08 19:10:45,123 - INFO - Starting weather data ingestion process
```

#### Structured Format
```
2025-07-08 19:10:45,123 | INFO     | weather_ingestion    | run                 :267  | Starting weather data ingestion process
```

#### JSON Format
```json
{
  "timestamp": "2025-07-08 19:10:45,123",
  "level": "INFO",
  "module": "weather_ingestion",
  "message": "Starting weather data ingestion process",
  "function": "run",
  "line": 267
}
```

### Performance Benchmarks

#### Ingestion Performance
- **Processing Rate**: 140,000+ records/second
- **File Processing**: ~0.07 seconds per file
- **Memory Usage**: Efficient batch processing minimizes memory footprint
- **Success Rate**: 99.96% with robust error handling

#### Statistics Computation Performance
- **Processing Rate**: 200+ station-year combinations/second
- **Memory Usage**: Optimized aggregation queries
- **Success Rate**: 100% for clean data

### Error Handling

Both tools provide comprehensive error handling for:

#### Data Quality Issues
- **Temperature Validation**: `Max temp (-167) < Min temp (189)`
- **Date Format Errors**: `Invalid date format '20150230'`
- **Missing Field Errors**: `Invalid format - expected 4 fields, got 3`
- **Precipitation Validation**: `Negative precipitation (-50)`

#### System Errors
- **File Access**: Missing or corrupted data files
- **Database Errors**: Connection issues or constraint violations
- **Memory Issues**: Batch size optimization for large datasets

### Architecture

#### Core Components

**Ingestion Tool**:
1. **WeatherDataIngestorConfig**: Configuration management
2. **WeatherDataLogger**: Advanced logging setup
3. **WeatherDataMetrics**: Performance tracking
4. **WeatherDataParser**: Data validation and parsing
5. **WeatherDataIngestor**: Main processing orchestration

**Statistics Tool**:
1. **YearlyStatsConfig**: Configuration management
2. **YearlyStatsLogger**: Advanced logging setup
3. **YearlyStatsMetrics**: Performance tracking
4. **YearlyStatsComputer**: Main computation orchestration

#### Data Flow

**Ingestion Flow**:
1. **Validation**: Data directory and file access checks
2. **Discovery**: Weather station file enumeration
3. **Processing**: Batch processing with transaction safety
4. **Validation**: Real-time data quality checks
5. **Storage**: Efficient bulk database operations
6. **Reporting**: Comprehensive metrics and summaries

**Statistics Flow**:
1. **Validation**: Filter and parameter validation
2. **Discovery**: Station-year combination identification
3. **Processing**: Batch aggregation with transaction safety
4. **Computation**: Statistical calculations with data quality metrics
5. **Storage**: Efficient bulk database operations
6. **Reporting**: Comprehensive metrics and summaries

### Dependencies

#### Required
- Python 3.11+
- Django (for database operations)
- PostgreSQL (recommended database)

#### Optional
- Virtual environment (recommended)
- Docker (for containerized deployment)

### Output Files

#### Log Files
- **Console Output**: Real-time progress and status
- **Rotating Logs**: `logs/*.log` (with backups)
- **JSON Logs**: `logs/*.json` (structured format)

#### Database
- **WeatherStation**: Station metadata
- **DailyWeather**: Daily weather observations
- **YearlyWeatherStats**: Aggregated yearly statistics
- **Metrics**: Processing statistics and quality reports

### Best Practices

#### Performance Optimization
- Use appropriate batch sizes based on system resources
- Enable file logging for production environments
- Monitor progress with appropriate intervals
- Use dry-run mode for testing and validation

#### Data Quality
- Review warning logs for data quality issues
- Implement regular data validation checks
- Monitor success rates and error patterns
- Use structured logging for automated monitoring

#### Production Deployment
- Use JSON logging for log aggregation systems
- Implement log rotation and retention policies
- Monitor processing rates and performance metrics
- Set up alerting for error conditions

### Troubleshooting

#### Common Issues

1. **Django Import Errors**
   - Ensure Django is installed and configured
   - Check DJANGO_SETTINGS_MODULE environment variable
   - Use `--dry-run` for testing without Django

2. **Performance Issues**
   - Adjust batch size based on system resources
   - Monitor memory usage during processing
   - Use appropriate log levels to reduce overhead

3. **Data Quality Warnings**
   - Review temperature relationship validations
   - Check for corrupted or malformed data files
   - Validate date formats and missing values

#### Debug Mode
```bash
# Enable debug logging for ingestion
python scripts/ingest_weather_data.py \
    --log-level DEBUG \
    --log-file logs/debug.log \
    --dry-run

# Enable debug logging for statistics
python scripts/compute_yearly_stats.py \
    --log-level DEBUG \
    --log-file logs/stats_debug.log \
    --dry-run
```

### Contributing

The tools are designed for extensibility:

- Add new validation rules in parsers
- Extend metrics collection in metrics classes
- Implement custom logging formats in logger classes
- Add new data sources or computation methods

### License

This project is part of the Weather Data Engineering API and follows the same licensing terms.
