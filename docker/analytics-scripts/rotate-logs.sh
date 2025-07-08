#!/bin/bash

# Log Rotation Script
# Rotates analytics logs daily to prevent disk space issues

LOG_FILE="/var/log/analytics/cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting log rotation" >> "$LOG_FILE"

# Log directory
LOG_DIR="/var/log/analytics"
DATE_SUFFIX=$(date +%Y%m%d)

# Rotate each log file
for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ] && [ -s "$log_file" ]; then
        base_name=$(basename "$log_file" .log)

        # Create rotated log file
        rotated_file="${LOG_DIR}/${base_name}.log.${DATE_SUFFIX}"

        # Copy current log to rotated file
        cp "$log_file" "$rotated_file"

        # Truncate original log file
        true > "$log_file"

        # Compress rotated file
        gzip -f "$rotated_file" 2>/dev/null || true

        echo "[$TIMESTAMP] Rotated log: $base_name.log" >> "$LOG_FILE"
    fi
done

# Clean up old rotated logs (keep last 7 days)
find "$LOG_DIR" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true

echo "[$TIMESTAMP] Log rotation completed" >> "$LOG_FILE"
