"""
Simplified Weather API endpoints for /api/weather.

This module provides a streamlined, user-friendly weather API with simplified
response formats and easy-to-use endpoints for common weather queries.
"""

import logging
from datetime import datetime, timedelta

from django.db.models import Avg, Max, Min, Q, Sum
from django.shortcuts import get_object_or_404
from fastapi import APIRouter, HTTPException, Query, status

from core_django.models.models import DailyWeather, WeatherStation, YearlyWeatherStats
from core_django.utils.units import (
    calculate_data_completeness,
    tenths_to_celsius,
    tenths_to_millimeters,
)
from src.models.simple_weather import (
    CurrentWeather,
    SimpleWeatherResponse,
    SimpleWeatherStation,
    WeatherHistory,
    WeatherLocationResponse,
    WeatherSearchResult,
    WeatherStats,
    WeatherSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def convert_station_to_simple(station: WeatherStation) -> SimpleWeatherStation:
    """Convert Django WeatherStation to SimpleWeatherStation."""
    return SimpleWeatherStation(
        id=station.station_id,
        name=station.name,
        latitude=float(station.latitude) if station.latitude else None,
        longitude=float(station.longitude) if station.longitude else None,
        elevation=float(station.elevation) if station.elevation else None,
        state=station.state,
    )


def generate_weather_conditions(
    temp_max: float | None, temp_min: float | None, precipitation: float | None
) -> str:
    """Generate a simple weather conditions description."""
    conditions = []

    if temp_max is not None:
        if temp_max > 30:
            conditions.append("hot")
        elif temp_max > 20:
            conditions.append("warm")
        elif temp_max > 10:
            conditions.append("mild")
        elif temp_max > 0:
            conditions.append("cool")
        else:
            conditions.append("cold")

    if precipitation is not None and precipitation > 0:
        if precipitation > 25:
            conditions.append("heavy rain")
        elif precipitation > 10:
            conditions.append("moderate rain")
        elif precipitation > 1:
            conditions.append("light rain")
        else:
            conditions.append("trace rain")
    elif precipitation is not None:
        conditions.append("dry")

    return ", ".join(conditions) if conditions else "conditions unknown"


@router.get("/", response_model=SimpleWeatherResponse)
async def weather_api_root():
    """
    Root endpoint for the simplified weather API.

    Provides information about available weather endpoints.
    """
    return SimpleWeatherResponse(
        success=True,
        message="Weather API - Simple weather data access",
        data={
            "description": "Simplified weather API for easy data access",
            "version": "1.0.0",
            "endpoints": {
                "current": "/api/weather/current/{station_id}",
                "location": "/api/weather/location/{station_id}",
                "search": "/api/weather/search",
                "recent": "/api/weather/recent/{station_id}",
                "stats": "/api/weather/stats/{station_id}",
            },
            "example_station": "USC00110072",
        },
        timestamp=datetime.now(),
    )


@router.get("/current/{station_id}", response_model=CurrentWeather)
async def get_current_weather(station_id: str):
    """
    Get current weather conditions for a specific station.

    Returns the most recent weather data available for the station.
    """
    try:
        # Get weather station
        station = get_object_or_404(WeatherStation, station_id=station_id)

        # Get most recent weather data
        recent_weather = (
            DailyWeather.objects.filter(station=station).order_by("-date").first()
        )

        if not recent_weather:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No weather data found for station {station_id}",
            )

        # Calculate data age
        data_age_hours = (datetime.now().date() - recent_weather.date).days * 24

        # Convert temperatures
        temp_max_c = recent_weather.max_temp_celsius
        temp_min_c = recent_weather.min_temp_celsius
        precip_mm = recent_weather.precipitation_mm

        # Build temperature data
        temperature = None
        if temp_max_c is not None or temp_min_c is not None:
            temperature = {}
            if temp_max_c is not None:
                temperature["max_celsius"] = temp_max_c
                temperature["max_fahrenheit"] = round(
                    celsius_to_fahrenheit(temp_max_c), 1
                )
            if temp_min_c is not None:
                temperature["min_celsius"] = temp_min_c
                temperature["min_fahrenheit"] = round(
                    celsius_to_fahrenheit(temp_min_c), 1
                )

        # Generate conditions description
        conditions = generate_weather_conditions(temp_max_c, temp_min_c, precip_mm)

        # Build response
        simple_station = convert_station_to_simple(station)

        current_weather = CurrentWeather(
            station=simple_station,
            date=recent_weather.date,
            temperature=temperature,
            precipitation=precip_mm,
            conditions=conditions,
            data_age_hours=data_age_hours if data_age_hours >= 0 else 0,
        )

        logger.info(f"Retrieved current weather for station {station_id}")
        return current_weather

    except Exception as e:
        logger.error(f"Error getting current weather for {station_id}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving current weather: {str(e)}",
        )


@router.get("/location/{station_id}", response_model=WeatherLocationResponse)
async def get_weather_by_location(
    station_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of recent days to include"),
):
    """
    Get comprehensive weather data for a specific location.

    Includes current conditions, recent history, and summary statistics.
    """
    try:
        # Get weather station
        station = get_object_or_404(WeatherStation, station_id=station_id)
        simple_station = convert_station_to_simple(station)

        # Get recent weather data
        start_date = datetime.now().date() - timedelta(days=days)
        recent_data = DailyWeather.objects.filter(
            station=station, date__gte=start_date
        ).order_by("-date")

        if not recent_data.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No recent weather data found for station {station_id}",
            )

        # Get current weather (most recent)
        current_record = recent_data.first()
        data_age_hours = (datetime.now().date() - current_record.date).days * 24

        temp_max_c = current_record.max_temp_celsius
        temp_min_c = current_record.min_temp_celsius
        precip_mm = current_record.precipitation_mm

        temperature = None
        if temp_max_c is not None or temp_min_c is not None:
            temperature = {}
            if temp_max_c is not None:
                temperature["max_celsius"] = temp_max_c
                temperature["max_fahrenheit"] = round(
                    celsius_to_fahrenheit(temp_max_c), 1
                )
            if temp_min_c is not None:
                temperature["min_celsius"] = temp_min_c
                temperature["min_fahrenheit"] = round(
                    celsius_to_fahrenheit(temp_min_c), 1
                )

        current = CurrentWeather(
            station=simple_station,
            date=current_record.date,
            temperature=temperature,
            precipitation=precip_mm,
            conditions=generate_weather_conditions(temp_max_c, temp_min_c, precip_mm),
            data_age_hours=data_age_hours if data_age_hours >= 0 else 0,
        )

        # Build recent history
        recent_history = []
        for record in recent_data[1:]:  # Skip first (current) record
            history_item = WeatherHistory(
                date=record.date,
                temperature_max=record.max_temp_celsius,
                temperature_min=record.min_temp_celsius,
                precipitation=record.precipitation_mm,
            )
            recent_history.append(history_item)

        # Calculate summary statistics
        temp_data = [r for r in recent_data if r.max_temp_celsius is not None]
        precip_data = [r for r in recent_data if r.precipitation_mm is not None]

        summary = None
        if temp_data or precip_data:
            temp_avg = None
            temp_range = None
            precip_total = None

            if temp_data:
                max_temps = [r.max_temp_celsius for r in temp_data]
                min_temps = [
                    r.min_temp_celsius
                    for r in temp_data
                    if r.min_temp_celsius is not None
                ]
                all_temps = max_temps + min_temps
                temp_avg = sum(all_temps) / len(all_temps) if all_temps else None
                temp_range = {
                    "min": min(all_temps) if all_temps else None,
                    "max": max(all_temps) if all_temps else None,
                }

            if precip_data:
                precip_values = [r.precipitation_mm for r in precip_data]
                precip_total = sum(precip_values)

            summary = WeatherSummary(
                location=f"{station.name or station_id}, {station.state or 'Unknown'}",
                period=f"Last {days} days",
                temperature_avg=round(temp_avg, 1) if temp_avg else None,
                temperature_range=temp_range,
                precipitation_total=round(precip_total, 1) if precip_total else None,
                data_points=len(recent_data),
            )

        response = WeatherLocationResponse(
            station=simple_station,
            current=current,
            recent_history=recent_history,
            summary=summary,
        )

        logger.info(f"Retrieved location weather for {station_id} ({days} days)")
        return response

    except Exception as e:
        logger.error(f"Error getting location weather for {station_id}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving location weather: {str(e)}",
        )


@router.get("/search", response_model=WeatherSearchResult)
async def search_weather_stations(
    q: str = Query(..., description="Search query for station name, ID, or location"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
):
    """
    Search for weather stations by name, ID, or location.

    Returns a list of matching weather stations.
    """
    try:
        # Search stations by ID, name, or state
        queryset = WeatherStation.objects.filter(
            Q(station_id__icontains=q) | Q(name__icontains=q) | Q(state__icontains=q)
        )[:limit]

        stations = [convert_station_to_simple(station) for station in queryset]

        # Get total count (for larger queries, this could be optimized)
        total_results = WeatherStation.objects.filter(
            Q(station_id__icontains=q) | Q(name__icontains=q) | Q(state__icontains=q)
        ).count()

        result = WeatherSearchResult(
            query=q,
            total_results=total_results,
            stations=stations,
        )

        logger.info(
            f"Weather station search for '{q}' returned {len(stations)} results"
        )
        return result

    except Exception as e:
        logger.error(f"Error searching weather stations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching weather stations: {str(e)}",
        )


@router.get("/recent/{station_id}", response_model=list[WeatherHistory])
async def get_recent_weather(
    station_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of recent days"),
):
    """
    Get recent weather history for a specific station.

    Returns daily weather observations for the specified number of days.
    """
    try:
        # Get weather station
        station = get_object_or_404(WeatherStation, station_id=station_id)

        # Get recent weather data
        start_date = datetime.now().date() - timedelta(days=days)
        recent_data = DailyWeather.objects.filter(
            station=station, date__gte=start_date
        ).order_by("-date")

        if not recent_data.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No recent weather data found for station {station_id}",
            )

        # Convert to response format
        history = []
        for record in recent_data:
            history_item = WeatherHistory(
                date=record.date,
                temperature_max=record.max_temp_celsius,
                temperature_min=record.min_temp_celsius,
                precipitation=record.precipitation_mm,
            )
            history.append(history_item)

        logger.info(f"Retrieved {len(history)} recent weather records for {station_id}")
        return history

    except Exception as e:
        logger.error(f"Error getting recent weather for {station_id}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recent weather: {str(e)}",
        )


@router.get("/stats/{station_id}", response_model=WeatherStats)
async def get_weather_statistics(
    station_id: str,
    year: int | None = Query(None, description="Specific year for statistics"),
):
    """
    Get weather statistics for a specific station and period.

    Returns temperature and precipitation statistics with data quality metrics.
    """
    try:
        # Get weather station
        station = get_object_or_404(WeatherStation, station_id=station_id)

        # Determine period
        if year:
            period = str(year)
            # Try to get yearly stats first
            yearly_stats = YearlyWeatherStats.objects.filter(
                station=station, year=year
            ).first()

            if yearly_stats:
                # Use pre-calculated stats
                temp_stats = {
                    "avg_max": yearly_stats.avg_max_temp_celsius,
                    "avg_min": yearly_stats.avg_min_temp_celsius,
                    "highest": yearly_stats.max_temp_celsius,
                    "lowest": yearly_stats.min_temp_celsius,
                }

                precip_stats = {
                    "total": yearly_stats.total_precipitation_mm,
                    "average_daily": yearly_stats.avg_precipitation_mm,
                    "highest_daily": yearly_stats.max_precipitation_mm,
                }

                quality_stats = {
                    "completeness": calculate_data_completeness(
                        yearly_stats.records_with_temp, yearly_stats.total_records
                    ),
                    "total_observations": yearly_stats.total_records,
                    "temperature_observations": yearly_stats.records_with_temp,
                    "precipitation_observations": yearly_stats.records_with_precipitation,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No statistics found for station {station_id} in year {year}",
                )
        else:
            # Calculate stats for all available data
            period = "All time"
            all_data = DailyWeather.objects.filter(station=station)

            if not all_data.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No weather data found for station {station_id}",
                )

            # Calculate temperature stats
            temp_data = all_data.filter(max_temp__isnull=False, min_temp__isnull=False)

            temp_stats = None
            if temp_data.exists():
                temp_aggregates = temp_data.aggregate(
                    avg_max=Avg("max_temp"),
                    avg_min=Avg("min_temp"),
                    highest=Max("max_temp"),
                    lowest=Min("min_temp"),
                )

                temp_stats = {
                    "avg_max": tenths_to_celsius(temp_aggregates["avg_max"]),
                    "avg_min": tenths_to_celsius(temp_aggregates["avg_min"]),
                    "highest": tenths_to_celsius(temp_aggregates["highest"]),
                    "lowest": tenths_to_celsius(temp_aggregates["lowest"]),
                }

            # Calculate precipitation stats
            precip_data = all_data.filter(precipitation__isnull=False)

            precip_stats = None
            if precip_data.exists():
                precip_aggregates = precip_data.aggregate(
                    total=Sum("precipitation"),
                    avg_daily=Avg("precipitation"),
                    highest=Max("precipitation"),
                )

                precip_stats = {
                    "total": tenths_to_millimeters(precip_aggregates["total"]),
                    "average_daily": tenths_to_millimeters(
                        precip_aggregates["avg_daily"]
                    ),
                    "highest_daily": tenths_to_millimeters(
                        precip_aggregates["highest"]
                    ),
                }

            # Calculate data quality
            total_records = all_data.count()
            temp_records = temp_data.count()
            precip_records = precip_data.count()

            quality_stats = {
                "completeness": calculate_data_completeness(
                    temp_records, total_records
                ),
                "total_observations": total_records,
                "temperature_observations": temp_records,
                "precipitation_observations": precip_records,
            }

        stats = WeatherStats(
            location=station_id,
            period=period,
            temperature=temp_stats,
            precipitation=precip_stats,
            data_quality=quality_stats,
        )

        logger.info(f"Retrieved weather statistics for {station_id} ({period})")
        return stats

    except Exception as e:
        logger.error(f"Error getting weather statistics for {station_id}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving weather statistics: {str(e)}",
        )
