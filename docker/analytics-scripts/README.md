# Analytics & Scheduling Scripts

This directory contains scheduled analytics scripts that run via cron in the `analytics` Docker service to automate data processing, maintenance, and monitoring tasks.

## Overview

The analytics service provides automated background processing for the weather data engineering platform with the following capabilities:

- **Automated Statistics Computation**: Daily computation of yearly weather statistics
- **Data Maintenance**: Weekly database cleanup and optimization
- **Health Monitoring**: Continuous system health checks and alerting
- **Performance Monitoring**: Metrics export for observability
- **Log Management**: Automated log rotation and cleanup

## Cron Schedule

| Script | Schedule | Description |
|--------|----------|-------------|
| `compute-yearly-stats.sh` | Daily at 2:00 AM | Computes missing yearly statistics incrementally |
| `data-maintenance.sh` | Weekly on Sunday at 3:00 AM | Database cleanup and optimization |
| `full-stats-recompute.sh` | Monthly on 1st at 4:00 AM | Full recomputation for data consistency |
| `health-check.sh` | Every 15 minutes | System health monitoring and alerting |
| `rotate-logs.sh` | Daily at 1:00 AM | Log file rotation and cleanup |
| `update-db-stats.sh` | Every 6 hours | PostgreSQL table statistics update |
| `export-metrics.sh` | Every hour | Metrics export for monitoring systems |
| `compute-previous-year-stats.sh` | January 1st at 5:00 AM | Previous year statistics verification |

## Scripts Description

### Daily Scripts

#### `compute-yearly-stats.sh`
- **Purpose**: Computes missing yearly weather statistics from daily data
- **Features**:
  - Database connectivity checks
  - Incremental processing (only missing statistics)
  - Comprehensive error handling and logging
  - Summary reporting with data quality metrics
- **Output**: `/var/log/analytics/yearly-stats.log`

#### `rotate-logs.sh`
- **Purpose**: Manages log file sizes and retention
- **Features**:
  - Rotates logs larger than 50MB
  - Compresses rotated logs with gzip
  - Removes logs older than 30 days
  - Maintains proper file permissions
- **Configuration**: 50MB max size, 30-day retention

### Weekly Scripts

#### `data-maintenance.sh`
- **Purpose**: Database optimization and cleanup
- **Features**:
  - Cleanup old processing logs (90-day retention)
  - Cleanup old record checksums (90-day retention)
  - PostgreSQL VACUUM ANALYZE operations
  - Data consistency checks
  - Orphaned data detection
- **Output**: `/var/log/analytics/data-maintenance.log`

### Monthly Scripts

#### `full-stats-recompute.sh`
- **Purpose**: Comprehensive statistics recomputation
- **Features**:
  - Force recomputation of current and previous year
  - Missing statistics detection and computation
  - Comprehensive data validation
  - Detailed reporting and metrics
- **Target**: Ensures data consistency across all yearly statistics

### Frequent Monitoring Scripts

#### `health-check.sh` (Every 15 minutes)
- **Purpose**: Continuous system health monitoring
- **Features**:
  - Database connectivity checks
  - Disk space monitoring (alerts at 80% full)
  - Memory usage monitoring (alerts at 85% usage)
  - Cron process monitoring
  - Log file size monitoring
- **Alerting**: Critical issues logged immediately, detailed reports hourly

#### `update-db-stats.sh` (Every 6 hours)
- **Purpose**: PostgreSQL query optimization
- **Features**:
  - Table statistics updates (ANALYZE)
  - Index usage analysis
  - Missing foreign key index detection
  - Connection and performance monitoring
- **Tables**: All weather data and analytics tables

#### `export-metrics.sh` (Every hour)
- **Purpose**: Metrics export for monitoring systems
- **Features**:
  - Comprehensive system metrics in JSON format
  - Data quality metrics and completeness percentages
  - Database size and performance metrics
  - Processing activity monitoring
- **Output**: `/var/log/analytics/metrics.json`

### Annual Scripts

#### `compute-previous-year-stats.sh` (January 1st)
- **Purpose**: Ensures previous year statistics are complete
- **Features**:
  - Data availability verification
  - Statistics completeness checking
  - Force recomputation if needed
  - Data integrity validation
- **Special**: Only runs when previous year data exists

## Log Files

All scripts write to dedicated log files in `/var/log/analytics/`:

- `yearly-stats.log` - Yearly statistics computation logs
- `data-maintenance.log` - Database maintenance and cleanup logs
- `cron.log` - Health checks, log rotation, and metrics export
- `metrics.json` - Structured metrics data for monitoring
- `*-detail.log` - Detailed logs from specific operations

## Environment Variables

The analytics service respects the following environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `DJANGO_SECRET_KEY` - Django application secret
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `TZ` - Timezone for cron scheduling (default: UTC)
- `ANALYTICS_ENABLED` - Enable/disable analytics processing

## Monitoring Integration

### Health Checks
- Docker health check monitors cron process status
- Health check script provides detailed system monitoring
- Critical issues trigger immediate alerts

### Metrics Export
- JSON metrics exported hourly to `/var/log/analytics/metrics.json`
- Compatible with log aggregation systems (ELK, Splunk, etc.)
- Prometheus-compatible metrics can be derived from JSON output

### Alerting
Scripts use structured logging with severity levels:
- `CRITICAL` - Service failures requiring immediate attention
- `WARNING` - Issues requiring monitoring (disk space, performance)
- `INFO` - Normal operation status and summaries
- `DEBUG` - Detailed operation logs

## Troubleshooting

### Common Issues

1. **Cron Not Running**
   ```bash
   docker exec analytics pgrep cron
   docker exec analytics crontab -l -u app
   ```

2. **Database Connection Issues**
   ```bash
   docker logs analytics | grep "Database connection"
   ```

3. **Log File Permissions**
   ```bash
   docker exec analytics ls -la /var/log/analytics/
   ```

4. **Script Execution Issues**
   ```bash
   docker exec analytics /app/analytics-scripts/health-check.sh
   ```

### Manual Execution

Scripts can be run manually for testing:

```bash
# Run yearly stats computation
docker exec analytics /app/analytics-scripts/compute-yearly-stats.sh

# Run health check
docker exec analytics /app/analytics-scripts/health-check.sh

# Export current metrics
docker exec analytics /app/analytics-scripts/export-metrics.sh
```

### Log Analysis

Check recent activity:
```bash
# View recent health checks
docker exec analytics tail -f /var/log/analytics/cron.log

# View yearly stats processing
docker exec analytics tail -f /var/log/analytics/yearly-stats.log

# View metrics
docker exec analytics cat /var/log/analytics/metrics.json | jq .
```

## Performance Considerations

- Scripts use optimized batch processing with configurable sizes
- Database operations use transactions for consistency
- Memory usage is monitored and optimized
- Log rotation prevents disk space issues
- Error handling ensures failed jobs don't block subsequent runs

## Customization

To modify schedules or add new jobs:

1. Update `docker/analytics-cron` with new cron entries
2. Create new scripts in `docker/analytics-scripts/`
3. Rebuild the analytics container
4. Test new jobs manually before deployment

## Security

- Scripts run as non-root `app` user
- Database credentials managed via environment variables
- Log files have restricted permissions
- No external network access required for core operations
