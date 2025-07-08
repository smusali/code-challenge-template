#!/bin/bash

# Database Statistics Update Script
# Updates database statistics every 6 hours for query optimization

LOG_FILE="/var/log/analytics/data-maintenance.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting database statistics update" >> "$LOG_FILE"

# Set up Django environment
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

cd /app/core_django || exit 1

# Update database statistics for query optimization
if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connection

try:
    with connection.cursor() as cursor:
        # Update table statistics
        cursor.execute('VACUUM ANALYZE;')
        print('Database statistics updated successfully')
except Exception as e:
    print(f'Database statistics update failed: {e}')
    exit(1)
" >> "$LOG_FILE" 2>&1; then
    echo "[$TIMESTAMP] Database statistics update completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Database statistics update failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$TIMESTAMP] Database statistics update finished" >> "$LOG_FILE"
