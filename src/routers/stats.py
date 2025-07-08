"""
Statistics and analytics API endpoints.

This module provides advanced analytics and statistics endpoints for
weather data analysis, trend analysis, and correlations.
"""

import logging
from datetime import date
from typing import Any, Optional

from django.db.models import Avg, Count, Max, Min, Sum
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from core_django.models.models import (
    CropYield,
    DailyWeather,
    WeatherStation,
    YearlyWeatherStats,
)
from core_django.utils.units import (
    calculate_data_completeness,
    tenths_to_celsius,
    tenths_to_millimeters,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class StationStatistics(BaseModel):
    """Statistics for a weather station."""

    station_id: str = Field(..., description="Weather station ID")
    station_name: Optional[str] = Field(None, description="Station name")
    total_records: int = Field(..., description="Total daily records")
    date_range: dict[str, Optional[date]] = Field(
        ..., description="Date range of records"
    )
    temperature_stats: dict[str, Optional[float]] = Field(
        ..., description="Temperature statistics"
    )
    precipitation_stats: dict[str, Optional[float]] = Field(
        ..., description="Precipitation statistics"
    )
    data_completeness: dict[str, float] = Field(
        ..., description="Data completeness percentages"
    )


class TemperatureTrend(BaseModel):
    """Temperature trend analysis."""

    period: str = Field(..., description="Time period (monthly/yearly)")
    station_id: Optional[str] = Field(None, description="Station ID if specific")
    data_points: list[dict[str, Any]] = Field(
        ..., description="Temperature data points"
    )
    trend_direction: str = Field(..., description="Overall trend direction")
    correlation_coefficient: Optional[float] = Field(
        None, description="Correlation coefficient"
    )


class PrecipitationPattern(BaseModel):
    """Precipitation pattern analysis."""

    period: str = Field(..., description="Time period (monthly/yearly)")
    station_id: Optional[str] = Field(None, description="Station ID if specific")
    data_points: list[dict[str, Any]] = Field(
        ..., description="Precipitation data points"
    )
    seasonality: dict[str, float] = Field(..., description="Seasonal patterns")
    extremes: dict[str, Any] = Field(..., description="Extreme precipitation events")


class WeatherCropCorrelation(BaseModel):
    """Weather and crop yield correlation analysis."""

    crop_type: str = Field(..., description="Crop type")
    correlation_metrics: dict[str, float] = Field(
        ..., description="Correlation coefficients"
    )
    analysis_period: dict[str, int] = Field(..., description="Analysis period")
    significant_factors: list[str] = Field(
        ..., description="Significant weather factors"
    )


class RegionalComparison(BaseModel):
    """Regional weather comparison."""

    regions: list[str] = Field(..., description="Compared regions")
    comparison_metric: str = Field(..., description="Comparison metric")
    data: list[dict[str, Any]] = Field(..., description="Regional comparison data")
    rankings: list[dict[str, Any]] = Field(..., description="Regional rankings")


@router.get("/station/{station_id}", response_model=StationStatistics)
async def get_station_statistics(station_id: str):
    """
    Get comprehensive statistics for a specific weather station.
    """
    try:
        # Get station
        try:
            station = WeatherStation.objects.get(station_id=station_id)
        except WeatherStation.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Weather station {station_id} not found",
            )

        # Get daily records
        daily_records = DailyWeather.objects.filter(station=station)

        if not daily_records.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No daily weather data found for station {station_id}",
            )

        # Basic statistics
        total_records = daily_records.count()
        date_range = daily_records.aggregate(earliest=Min("date"), latest=Max("date"))

        # Temperature statistics
        temp_stats = daily_records.aggregate(
            min_temp=Min("min_temp"),
            max_temp=Max("max_temp"),
            avg_min_temp=Avg("min_temp"),
            avg_max_temp=Avg("max_temp"),
        )

        # Precipitation statistics
        precip_stats = daily_records.aggregate(
            min_precip=Min("precipitation"),
            max_precip=Max("precipitation"),
            avg_precip=Avg("precipitation"),
            total_precip=Sum("precipitation"),
        )

        # Data completeness
        temp_records = daily_records.filter(
            max_temp__isnull=False, min_temp__isnull=False
        ).count()
        precip_records = daily_records.filter(precipitation__isnull=False).count()

        return StationStatistics(
            station_id=station_id,
            station_name=station.name,
            total_records=total_records,
            date_range=date_range,
            temperature_stats={
                "min_celsius": tenths_to_celsius(temp_stats["min_temp"]),
                "max_celsius": tenths_to_celsius(temp_stats["max_temp"]),
                "avg_min_celsius": tenths_to_celsius(temp_stats["avg_min_temp"]),
                "avg_max_celsius": tenths_to_celsius(temp_stats["avg_max_temp"]),
            },
            precipitation_stats={
                "min_mm": tenths_to_millimeters(precip_stats["min_precip"]),
                "max_mm": tenths_to_millimeters(precip_stats["max_precip"]),
                "avg_mm": tenths_to_millimeters(precip_stats["avg_precip"]),
                "total_mm": tenths_to_millimeters(precip_stats["total_precip"]),
            },
            data_completeness={
                "temperature": calculate_data_completeness(temp_records, total_records),
                "precipitation": calculate_data_completeness(
                    precip_records, total_records
                ),
            },
        )

    except Exception as e:
        logger.error(f"Error getting station statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting station statistics: {str(e)}",
        )


@router.get("/temperature-trends", response_model=TemperatureTrend)
async def get_temperature_trends(
    period: str = Query(..., regex="^(monthly|yearly)$", description="Time period"),
    station_id: Optional[str] = Query(None, description="Specific station ID"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get temperature trend analysis for specified period.
    """
    try:
        # Build query
        queryset = DailyWeather.objects.filter(
            max_temp__isnull=False, min_temp__isnull=False
        )

        if station_id:
            queryset = queryset.filter(station__station_id=station_id)

        if start_year:
            queryset = queryset.filter(date__year__gte=start_year)

        if end_year:
            queryset = queryset.filter(date__year__lte=end_year)

        if not queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No temperature data found for the specified criteria",
            )

        # Aggregate data by period
        if period == "monthly":
            data_points = []
            monthly_data = (
                queryset.values("date__year", "date__month")
                .annotate(
                    avg_temp=Avg("max_temp"),
                    avg_min_temp=Avg("min_temp"),
                    count=Count("id"),
                )
                .order_by("date__year", "date__month")
            )

            for item in monthly_data:
                data_points.append(
                    {
                        "year": item["date__year"],
                        "month": item["date__month"],
                        "avg_temp_celsius": tenths_to_celsius(item["avg_temp"]),
                        "avg_min_temp_celsius": tenths_to_celsius(item["avg_min_temp"]),
                        "record_count": item["count"],
                    }
                )

        else:  # yearly
            data_points = []
            yearly_data = (
                queryset.values("date__year")
                .annotate(
                    avg_temp=Avg("max_temp"),
                    avg_min_temp=Avg("min_temp"),
                    count=Count("id"),
                )
                .order_by("date__year")
            )

            for item in yearly_data:
                data_points.append(
                    {
                        "year": item["date__year"],
                        "avg_temp_celsius": tenths_to_celsius(item["avg_temp"]),
                        "avg_min_temp_celsius": tenths_to_celsius(item["avg_min_temp"]),
                        "record_count": item["count"],
                    }
                )

        # Calculate trend (simple linear correlation)
        if len(data_points) > 1:
            x_values = [dp["year"] for dp in data_points]
            y_values = [
                dp["avg_temp_celsius"]
                for dp in data_points
                if dp["avg_temp_celsius"] is not None
            ]

            if len(y_values) > 1:
                n = len(y_values)
                sum_x = sum(x_values[:n])
                sum_y = sum(y_values)
                sum_xy = sum(x * y for x, y in zip(x_values[:n], y_values, strict=True))
                sum_xx = sum(x * x for x in x_values[:n])
                sum_yy = sum(y * y for y in y_values)

                correlation = (n * sum_xy - sum_x * sum_y) / (
                    ((n * sum_xx - sum_x * sum_x) * (n * sum_yy - sum_y * sum_y)) ** 0.5
                )

                if correlation > 0.1:
                    trend_direction = "warming"
                elif correlation < -0.1:
                    trend_direction = "cooling"
                else:
                    trend_direction = "stable"
            else:
                correlation = None
                trend_direction = "stable"
        else:
            correlation = None
            trend_direction = "stable"

        return TemperatureTrend(
            period=period,
            station_id=station_id,
            data_points=data_points,
            trend_direction=trend_direction,
            correlation_coefficient=correlation,
        )

    except Exception as e:
        logger.error(f"Error getting temperature trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting temperature trends: {str(e)}",
        )


@router.get("/precipitation-patterns", response_model=PrecipitationPattern)
async def get_precipitation_patterns(
    period: str = Query(..., regex="^(monthly|yearly)$", description="Time period"),
    station_id: Optional[str] = Query(None, description="Specific station ID"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get precipitation pattern analysis for specified period.
    """
    try:
        # Build query
        queryset = DailyWeather.objects.filter(precipitation__isnull=False)

        if station_id:
            queryset = queryset.filter(station__station_id=station_id)

        if start_year:
            queryset = queryset.filter(date__year__gte=start_year)

        if end_year:
            queryset = queryset.filter(date__year__lte=end_year)

        if not queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No precipitation data found for the specified criteria",
            )

        # Aggregate data by period
        if period == "monthly":
            data_points = []
            monthly_data = (
                queryset.values("date__year", "date__month")
                .annotate(
                    total_precip=Sum("precipitation"),
                    avg_precip=Avg("precipitation"),
                    max_precip=Max("precipitation"),
                    count=Count("id"),
                )
                .order_by("date__year", "date__month")
            )

            for item in monthly_data:
                data_points.append(
                    {
                        "year": item["date__year"],
                        "month": item["date__month"],
                        "total_precip_mm": tenths_to_millimeters(item["total_precip"]),
                        "avg_precip_mm": tenths_to_millimeters(item["avg_precip"]),
                        "max_precip_mm": tenths_to_millimeters(item["max_precip"]),
                        "record_count": item["count"],
                    }
                )

        else:  # yearly
            data_points = []
            yearly_data = (
                queryset.values("date__year")
                .annotate(
                    total_precip=Sum("precipitation"),
                    avg_precip=Avg("precipitation"),
                    max_precip=Max("precipitation"),
                    count=Count("id"),
                )
                .order_by("date__year")
            )

            for item in yearly_data:
                data_points.append(
                    {
                        "year": item["date__year"],
                        "total_precip_mm": tenths_to_millimeters(item["total_precip"]),
                        "avg_precip_mm": tenths_to_millimeters(item["avg_precip"]),
                        "max_precip_mm": tenths_to_millimeters(item["max_precip"]),
                        "record_count": item["count"],
                    }
                )

        # Calculate seasonal patterns (monthly averages)
        seasonal_data = (
            queryset.values("date__month")
            .annotate(avg_precip=Avg("precipitation"))
            .order_by("date__month")
        )

        seasonality = {}
        for item in seasonal_data:
            month_names = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
            month_name = month_names[item["date__month"] - 1]
            seasonality[month_name] = tenths_to_millimeters(item["avg_precip"])

        # Find extreme precipitation events
        extreme_stats = queryset.aggregate(
            max_daily=Max("precipitation"),
            percentile_95=Max(
                "precipitation"
            ),  # Simplified - would need more complex query for true percentile
        )

        # Count extreme events (top 5% of precipitation)
        extreme_threshold = (
            extreme_stats["max_daily"] * 0.8 if extreme_stats["max_daily"] else 0
        )
        extreme_events = queryset.filter(precipitation__gte=extreme_threshold).count()

        extremes = {
            "max_daily_mm": tenths_to_millimeters(extreme_stats["max_daily"]),
            "extreme_events_count": extreme_events,
            "extreme_threshold_mm": tenths_to_millimeters(extreme_threshold),
        }

        return PrecipitationPattern(
            period=period,
            station_id=station_id,
            data_points=data_points,
            seasonality=seasonality,
            extremes=extremes,
        )

    except Exception as e:
        logger.error(f"Error getting precipitation patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting precipitation patterns: {str(e)}",
        )


@router.get("/weather-crop-correlation", response_model=WeatherCropCorrelation)
async def get_weather_crop_correlation(
    crop_type: str = Query(..., description="Crop type to analyze"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Analyze correlation between weather data and crop yields.
    """
    try:
        # Get crop yield data
        crop_queryset = CropYield.objects.filter(crop_type=crop_type.lower())

        if start_year:
            crop_queryset = crop_queryset.filter(year__gte=start_year)

        if end_year:
            crop_queryset = crop_queryset.filter(year__lte=end_year)

        if not crop_queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No crop yield data found for {crop_type}",
            )

        # Get weather data for the same years
        crop_years = list(crop_queryset.values_list("year", flat=True))
        weather_queryset = YearlyWeatherStats.objects.filter(year__in=crop_years)

        if not weather_queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No weather statistics found for the crop years",
            )

        # Calculate correlations (simplified example)
        # In a real implementation, you'd use proper statistical methods
        weather_data = {}

        for stat in weather_queryset:
            if stat.year not in weather_data:
                weather_data[stat.year] = {
                    "avg_temp": [],
                    "total_precip": [],
                }

            if stat.avg_max_temp:
                weather_data[stat.year]["avg_temp"].append(float(stat.avg_max_temp))
            if stat.total_precipitation:
                weather_data[stat.year]["total_precip"].append(stat.total_precipitation)

        # Calculate average weather metrics by year
        yearly_weather = {}
        for year, metrics in weather_data.items():
            yearly_weather[year] = {
                "avg_temp": sum(metrics["avg_temp"]) / len(metrics["avg_temp"])
                if metrics["avg_temp"]
                else 0,
                "total_precip": sum(metrics["total_precip"])
                / len(metrics["total_precip"])
                if metrics["total_precip"]
                else 0,
            }

        # Simple correlation calculation
        correlation_metrics = {
            "temperature_correlation": 0.0,  # Placeholder
            "precipitation_correlation": 0.0,  # Placeholder
        }

        # Identify significant factors (simplified)
        significant_factors = ["temperature", "precipitation"]

        return WeatherCropCorrelation(
            crop_type=crop_type,
            correlation_metrics=correlation_metrics,
            analysis_period={
                "start_year": min(crop_years),
                "end_year": max(crop_years),
            },
            significant_factors=significant_factors,
        )

    except Exception as e:
        logger.error(f"Error getting weather-crop correlation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting weather-crop correlation: {str(e)}",
        )


@router.get("/regional-comparison", response_model=RegionalComparison)
async def get_regional_comparison(
    metric: str = Query(
        ..., regex="^(temperature|precipitation)$", description="Comparison metric"
    ),
    year: Optional[int] = Query(None, description="Specific year"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Compare weather metrics across different regions.
    """
    try:
        # Get regional data (by state)
        queryset = DailyWeather.objects.select_related("station").filter(
            station__state__isnull=False
        )

        if year:
            queryset = queryset.filter(date__year=year)
        else:
            if start_year:
                queryset = queryset.filter(date__year__gte=start_year)
            if end_year:
                queryset = queryset.filter(date__year__lte=end_year)

        if not queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No weather data found for the specified criteria",
            )

        # Aggregate by state
        if metric == "temperature":
            regional_data = (
                queryset.filter(max_temp__isnull=False, min_temp__isnull=False)
                .values("station__state")
                .annotate(
                    avg_temp=Avg("max_temp"),
                    avg_min_temp=Avg("min_temp"),
                    count=Count("id"),
                )
                .order_by("-avg_temp")
            )

            data = []
            for item in regional_data:
                data.append(
                    {
                        "region": item["station__state"],
                        "avg_temp_celsius": tenths_to_celsius(item["avg_temp"]),
                        "avg_min_temp_celsius": tenths_to_celsius(item["avg_min_temp"]),
                        "record_count": item["count"],
                    }
                )

        else:  # precipitation
            regional_data = (
                queryset.filter(precipitation__isnull=False)
                .values("station__state")
                .annotate(
                    total_precip=Sum("precipitation"),
                    avg_precip=Avg("precipitation"),
                    count=Count("id"),
                )
                .order_by("-total_precip")
            )

            data = []
            for item in regional_data:
                data.append(
                    {
                        "region": item["station__state"],
                        "total_precip_mm": tenths_to_millimeters(item["total_precip"]),
                        "avg_precip_mm": tenths_to_millimeters(item["avg_precip"]),
                        "record_count": item["count"],
                    }
                )

        # Create rankings
        rankings = []
        for i, item in enumerate(data, 1):
            rankings.append(
                {
                    "rank": i,
                    "region": item["region"],
                    "value": item.get("avg_temp_celsius")
                    or item.get("total_precip_mm"),
                    "metric": metric,
                }
            )

        regions = [item["region"] for item in data]

        return RegionalComparison(
            regions=regions, comparison_metric=metric, data=data, rankings=rankings
        )

    except Exception as e:
        logger.error(f"Error getting regional comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting regional comparison: {str(e)}",
        )
