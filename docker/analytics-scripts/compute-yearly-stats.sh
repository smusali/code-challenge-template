#!/bin/bash

# Compute Yearly Statistics
# This script runs the yearly statistics computation for any missing or incomplete data

LOG_FILE="/var/log/analytics/yearly-stats.log"

echo "$(date): Starting yearly statistics computation" >> "$LOG_FILE"

# Set up Django environment
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

# Change to the Django project directory
cd /app/core_django || exit 1

# Run the yearly statistics computation command
if python manage.py compute_yearly_stats --verbose >> "$LOG_FILE" 2>&1; then
    echo "$(date): Yearly statistics computation completed successfully" >> "$LOG_FILE"
else
    echo "$(date): ERROR: Yearly statistics computation failed" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Yearly statistics computation job finished" >> "$LOG_FILE"
