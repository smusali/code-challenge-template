#!/bin/bash

# Compute Previous Year Statistics Script
# Forces yearly stats computation for previous year (run once in January)

LOG_FILE="/var/log/analytics/yearly-stats.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting previous year statistics computation" >> "$LOG_FILE"

# Set up Django environment
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

cd /app/core_django || exit 1

# Get previous year
PREVIOUS_YEAR=$(($(date +%Y) - 1))

echo "[$TIMESTAMP] Computing statistics for previous year: $PREVIOUS_YEAR" >> "$LOG_FILE"

# Run the yearly statistics computation command for previous year
if python manage.py compute_yearly_stats --year "$PREVIOUS_YEAR" --force --verbose >> "$LOG_FILE" 2>&1; then
    echo "[$TIMESTAMP] Previous year ($PREVIOUS_YEAR) statistics computation completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Previous year ($PREVIOUS_YEAR) statistics computation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$TIMESTAMP] Previous year statistics computation finished" >> "$LOG_FILE"
