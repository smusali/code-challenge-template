#!/bin/bash

# Data Maintenance Script
# Runs weekly data cleanup and optimization tasks

LOG_FILE="/var/log/analytics/data-maintenance.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting data maintenance" >> "$LOG_FILE"

# Set up Django environment
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

cd /app/core_django || exit 1

{
    echo "[$TIMESTAMP] Cleaning up old log entries..."
    find /var/log/analytics -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true

    echo "[$TIMESTAMP] Running database optimization..."
} >> "$LOG_FILE"

if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('ANALYZE;')
        print('Database analysis completed')
except Exception as e:
    print(f'Database optimization failed: {e}')
    exit(1)
" >> "$LOG_FILE" 2>&1; then
    echo "[$TIMESTAMP] Database optimization completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Database optimization failed" >> "$LOG_FILE"
    exit 1
fi

{
    echo "[$TIMESTAMP] Checking for data consistency..."
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from core_django.models.models import WeatherData, YearlyWeatherStats
from django.db.models import Count

# Check for missing yearly stats
weather_years = WeatherData.objects.values('year').distinct().count()
stats_years = YearlyWeatherStats.objects.values('year').distinct().count()

print(f'Weather data years: {weather_years}')
print(f'Stats years: {stats_years}')

if weather_years > stats_years:
    print(f'WARNING: {weather_years - stats_years} years missing stats')
else:
    print('Data consistency check passed')
"
    echo "[$TIMESTAMP] Data maintenance completed"
} >> "$LOG_FILE" 2>&1
