#!/bin/bash

# Export Analytics Metrics Script
# Exports key metrics for monitoring every hour

LOG_FILE="/var/log/analytics/cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting metrics export" >> "$LOG_FILE"

# Set up Django environment
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH="/app:$PYTHONPATH"

cd /app/core_django || exit 1

if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from core_django.models.models import WeatherData, YearlyWeatherStats, WeatherStation
from django.db.models import Count, Min, Max
from datetime import datetime

try:
    # Get current metrics
    weather_records = WeatherData.objects.count()
    yearly_stats = YearlyWeatherStats.objects.count()
    active_stations = WeatherStation.objects.count()

    year_range = WeatherData.objects.aggregate(
        min_year=Min('year'),
        max_year=Max('year')
    )

    # Export metrics in a format suitable for monitoring
    print(f'METRIC weather_records_total {weather_records}')
    print(f'METRIC yearly_stats_total {yearly_stats}')
    print(f'METRIC active_stations_total {active_stations}')
    print(f'METRIC data_year_range_min {year_range[\"min_year\"] or 0}')
    print(f'METRIC data_year_range_max {year_range[\"max_year\"] or 0}')
    print(f'METRIC export_timestamp {int(datetime.now().timestamp())}')

    print('Metrics exported successfully')

except Exception as e:
    print(f'Metrics export failed: {e}')
    exit(1)
" >> "$LOG_FILE" 2>&1; then
    echo "[$TIMESTAMP] Metrics export completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ERROR: Metrics export failed" >> "$LOG_FILE"
    exit 1
fi

echo "[$TIMESTAMP] Metrics export finished" >> "$LOG_FILE"
