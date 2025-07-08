# Weather Data Engineering CLI Tool

A comprehensive command-line interface for ingesting weather station data with advanced structured logging capabilities.

## Overview

The `ingest_weather_data.py` script provides a robust, production-ready tool for processing weather station data files with comprehensive error handling, data validation, and structured logging.

## Features

### 🏗️ Data Processing
- **Batch Processing**: Configurable batch sizes for optimal performance
- **Data Validation**: Comprehensive validation of temperature relationships and data integrity
- **Error Recovery**: Robust error handling with detailed logging and graceful degradation
- **Django Integration**: Full support for Django ORM models with transaction safety
- **Duplicate Detection**: Automatic handling of duplicate records with conflict resolution

### 📊 Structured Logging
- **Multiple Log Formats**: Simple, structured, and JSON formats
- **Dual Output**: Console and rotating file logging
- **Log Rotation**: Automatic log file rotation (10MB max, 5 backups)
- **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Contextual Information**: Function names, line numbers, timestamps, and modules

### 🔧 Performance Monitoring
- **Real-time Progress**: Live progress tracking with processing rates
- **Performance Metrics**: Records per second, batch timings, file processing times
- **Resource Usage**: Memory-efficient batch processing
- **Detailed Statistics**: Comprehensive final summary reports

### 🛡️ Data Quality
- **Temperature Validation**: Ensures max temp >= min temp
- **Precipitation Validation**: Handles negative values and missing data
- **Date Validation**: Robust date parsing with error reporting
- **Missing Value Handling**: Proper handling of -9999 sentinel values

## Usage

### Basic Usage

```bash
# Default ingestion
python scripts/ingest_weather_data.py

# Specify data directory
python scripts/ingest_weather_data.py --data-dir wx_data

# Dry run (no database changes)
python scripts/ingest_weather_data.py --dry-run
```

### Advanced Usage

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

## Command Line Options

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

## Log Formats

### Simple Format
```
2025-07-08 19:10:45,123 - INFO - Starting weather data ingestion process
```

### Structured Format
```
2025-07-08 19:10:45,123 | INFO     | weather_ingestion    | run                 :267  | Starting weather data ingestion process
```

### JSON Format
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

## Performance Benchmarks

### Typical Performance
- **Processing Rate**: 140,000+ records/second
- **File Processing**: ~0.07 seconds per file
- **Memory Usage**: Efficient batch processing minimizes memory footprint
- **Success Rate**: 99.96% with robust error handling

### Example Output
```
📊 Processing Summary:
   • Duration: 12.38 seconds
   • Files processed: 167/167
   • Records processed: 1,729,220/1,729,957
   • Processing rate: 139,652.17 records/second
   • Success rate: 99.96%
```

## Error Handling

The tool provides comprehensive error handling for:

### Data Quality Issues
- **Temperature Validation**: `Max temp (-167) < Min temp (189)`
- **Date Format Errors**: `Invalid date format '20150230'`
- **Missing Field Errors**: `Invalid format - expected 4 fields, got 3`
- **Precipitation Validation**: `Negative precipitation (-50)`

### System Errors
- **File Access**: Missing or corrupted data files
- **Database Errors**: Connection issues or constraint violations
- **Memory Issues**: Batch size optimization for large datasets

## Architecture

### Core Components

1. **WeatherDataIngestorConfig**: Configuration management
2. **WeatherDataLogger**: Advanced logging setup
3. **WeatherDataMetrics**: Performance tracking
4. **WeatherDataParser**: Data validation and parsing
5. **WeatherDataIngestor**: Main processing orchestration

### Data Flow

1. **Validation**: Data directory and file access checks
2. **Discovery**: Weather station file enumeration
3. **Processing**: Batch processing with transaction safety
4. **Validation**: Real-time data quality checks
5. **Storage**: Efficient bulk database operations
6. **Reporting**: Comprehensive metrics and summaries

## Dependencies

### Required
- Python 3.11+
- Django (for database operations)
- PostgreSQL (recommended database)

### Optional
- Virtual environment (recommended)
- Docker (for containerized deployment)

## Output Files

### Log Files
- **Console Output**: Real-time progress and status
- **Rotating Logs**: `logs/weather_ingestion.log` (with backups)
- **JSON Logs**: `logs/weather_ingestion.json` (structured format)

### Database
- **WeatherStation**: Station metadata
- **DailyWeather**: Daily weather observations
- **Metrics**: Processing statistics and quality reports

## Best Practices

### Performance Optimization
- Use batch sizes between 1000-5000 for optimal performance
- Enable file logging for production environments
- Monitor progress with appropriate intervals
- Use dry-run mode for testing and validation

### Data Quality
- Review warning logs for data quality issues
- Implement regular data validation checks
- Monitor success rates and error patterns
- Use structured logging for automated monitoring

### Production Deployment
- Use JSON logging for log aggregation systems
- Implement log rotation and retention policies
- Monitor processing rates and performance metrics
- Set up alerting for error conditions

## Troubleshooting

### Common Issues

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

### Debug Mode
```bash
# Enable debug logging
python scripts/ingest_weather_data.py \
    --log-level DEBUG \
    --log-file logs/debug.log \
    --dry-run
```

## Contributing

The tool is designed for extensibility:

- Add new validation rules in `WeatherDataParser`
- Extend metrics collection in `WeatherDataMetrics`
- Implement custom logging formats in `WeatherDataLogger`
- Add new data sources in `WeatherDataIngestor`

## License

This project is part of the Weather Data Engineering API and follows the same licensing terms.
