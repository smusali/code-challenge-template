#!/bin/bash

# Full Statistics Recomputation Script
# Runs monthly full statistics recomputation to ensure data consistency

LOG_FILE="/var/log/analytics/yearly-stats.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting full statistics recomputation" >> "$LOG_FILE"

# Set up Django environment
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

cd /app/core_django || exit 1

# Run the yearly statistics computation command with force flag
if python manage.py compute_yearly_stats --force --verbose >> "$LOG_FILE" 2>&1; then
    echo "[$TIMESTAMP] Full statistics recomputation completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Full statistics recomputation failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$TIMESTAMP] Full statistics recomputation finished" >> "$LOG_FILE"
