#!/bin/bash

# Health Check Script
# Monitors system health and logs status

LOG_FILE="/var/log/analytics/cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting health check" >> "$LOG_FILE"

# Check if cron is running
if pgrep cron > /dev/null; then
    echo "[$TIMESTAMP] HEALTH: Cron daemon is running" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Cron daemon is not running" >> "$LOG_FILE"
    exit 1
fi

# Check database connectivity
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

cd /app/core_django || exit 1
if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('Database connection: OK')
except Exception as e:
    print(f'Database connection: FAILED - {e}')
    exit(1)
" >> "$LOG_FILE" 2>&1; then
    echo "[$TIMESTAMP] HEALTH: Database connection is OK" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Database connection failed" >> "$LOG_FILE"
    exit 1
fi

# Check disk space
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 90 ]; then
    echo "[$TIMESTAMP] HEALTH: Disk usage is OK ($disk_usage%)" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] WARNING: Disk usage is high ($disk_usage%)" >> "$LOG_FILE"
fi

# Check log file sizes
log_dir="/var/log/analytics"
if [ -d "$log_dir" ]; then
    for log_file in "$log_dir"/*.log; do
        if [ -f "$log_file" ]; then
            size=$(stat -c%s "$log_file" 2>/dev/null || echo 0)
            if [ "$size" -gt 104857600 ]; then  # 100MB
                echo "[$TIMESTAMP] WARNING: Log file $(basename "$log_file") is large (${size} bytes)" >> "$LOG_FILE"
            fi
        fi
    done
fi

echo "[$TIMESTAMP] Health check completed" >> "$LOG_FILE"
