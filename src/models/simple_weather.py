"""
Simplified weather models for the /api/weather endpoint.

This module provides streamlined Pydantic models for easy weather data access
with simplified response formats and user-friendly field names.
"""

from datetime import date as DateType
from datetime import datetime

from pydantic import BaseModel, Field


class SimpleWeatherStation(BaseModel):
    """Simplified weather station model."""

    id: str = Field(..., description="Station identifier")
    name: str | None = Field(None, description="Station name")
    latitude: float | None = Field(None, description="Latitude in decimal degrees")
    longitude: float | None = Field(None, description="Longitude in decimal degrees")
    elevation: float | None = Field(None, description="Elevation in meters")
    state: str | None = Field(None, description="State abbreviation")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "USC00110072",
                "name": "Chicago Weather Station",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "elevation": 182.0,
                "state": "IL",
            }
        }


class CurrentWeather(BaseModel):
    """Current weather conditions model."""

    station: SimpleWeatherStation = Field(
        ..., description="Weather station information"
    )
    date: DateType = Field(..., description="Date of observation")
    temperature: dict | None = Field(None, description="Temperature readings")
    precipitation: float | None = Field(
        None, description="Precipitation in millimeters"
    )
    conditions: str | None = Field(None, description="Weather conditions summary")
    data_age_hours: int | None = Field(None, description="Hours since last update")

    class Config:
        json_schema_extra = {
            "example": {
                "station": {
                    "id": "USC00110072",
                    "name": "Chicago Weather Station",
                    "latitude": 41.8781,
                    "longitude": -87.6298,
                    "elevation": 182.0,
                    "state": "IL",
                },
                "date": "2024-01-15",
                "temperature": {
                    "max_celsius": 8.5,
                    "min_celsius": -2.1,
                    "max_fahrenheit": 47.3,
                    "min_fahrenheit": 28.2,
                },
                "precipitation": 2.5,
                "conditions": "Light rain, cool",
                "data_age_hours": 6,
            }
        }


class WeatherSummary(BaseModel):
    """Weather summary for a location."""

    location: str = Field(..., description="Location name or identifier")
    period: str = Field(..., description="Summary period")
    temperature_avg: float | None = Field(
        None, description="Average temperature in Celsius"
    )
    temperature_range: dict | None = Field(None, description="Temperature range")
    precipitation_total: float | None = Field(
        None, description="Total precipitation in mm"
    )
    data_points: int = Field(0, description="Number of data points in summary")

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Chicago, IL",
                "period": "Last 7 days",
                "temperature_avg": 12.5,
                "temperature_range": {"min": -5.2, "max": 28.1},
                "precipitation_total": 15.7,
                "data_points": 7,
            }
        }


class WeatherHistory(BaseModel):
    """Historical weather data."""

    date: DateType = Field(..., description="Date of observation")
    temperature_max: float | None = Field(
        None, description="Maximum temperature in Celsius"
    )
    temperature_min: float | None = Field(
        None, description="Minimum temperature in Celsius"
    )
    precipitation: float | None = Field(
        None, description="Precipitation in millimeters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-15",
                "temperature_max": 8.5,
                "temperature_min": -2.1,
                "precipitation": 2.5,
            }
        }


class WeatherLocationResponse(BaseModel):
    """Weather data for a specific location."""

    station: SimpleWeatherStation = Field(..., description="Weather station")
    current: CurrentWeather | None = Field(None, description="Current conditions")
    recent_history: list[WeatherHistory] = Field(
        default_factory=list, description="Recent weather history"
    )
    summary: WeatherSummary | None = Field(None, description="Period summary")

    class Config:
        json_schema_extra = {
            "example": {
                "station": {
                    "id": "USC00110072",
                    "name": "Chicago Weather Station",
                    "latitude": 41.8781,
                    "longitude": -87.6298,
                    "elevation": 182.0,
                    "state": "IL",
                },
                "current": {
                    "station": {},
                    "date": "2024-01-15",
                    "temperature": {"max_celsius": 8.5, "min_celsius": -2.1},
                    "precipitation": 2.5,
                    "conditions": "Light rain, cool",
                    "data_age_hours": 6,
                },
                "recent_history": [
                    {
                        "date": "2024-01-14",
                        "temperature_max": 12.1,
                        "temperature_min": 1.5,
                        "precipitation": 0.0,
                    }
                ],
                "summary": {
                    "location": "Chicago, IL",
                    "period": "Last 7 days",
                    "temperature_avg": 12.5,
                    "precipitation_total": 15.7,
                    "data_points": 7,
                },
            }
        }


class WeatherSearchResult(BaseModel):
    """Weather search result."""

    stations: list[SimpleWeatherStation] = Field(
        default_factory=list, description="Matching weather stations"
    )
    total_results: int = Field(0, description="Total number of results")
    query: str = Field(..., description="Search query used")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Chicago",
                "total_results": 3,
                "stations": [
                    {
                        "id": "USC00110072",
                        "name": "Chicago Weather Station",
                        "latitude": 41.8781,
                        "longitude": -87.6298,
                        "state": "IL",
                    }
                ],
            }
        }


class WeatherStats(BaseModel):
    """Weather statistics for a location and period."""

    location: str = Field(..., description="Location identifier")
    period: str = Field(..., description="Statistics period")
    temperature: dict | None = Field(None, description="Temperature statistics")
    precipitation: dict | None = Field(None, description="Precipitation statistics")
    data_quality: dict | None = Field(None, description="Data quality metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "location": "USC00110072",
                "period": "2023",
                "temperature": {
                    "avg_max": 18.5,
                    "avg_min": 8.2,
                    "highest": 35.6,
                    "lowest": -18.3,
                },
                "precipitation": {
                    "total": 945.2,
                    "average_daily": 2.6,
                    "highest_daily": 89.4,
                },
                "data_quality": {"completeness": 94.2, "total_observations": 365},
            }
        }


class WeatherForecast(BaseModel):
    """Simple weather forecast (placeholder for future implementation)."""

    station_id: str = Field(..., description="Weather station ID")
    forecast_date: DateType = Field(..., description="Forecast date")
    predicted_high: float | None = Field(
        None, description="Predicted high temperature in Celsius"
    )
    predicted_low: float | None = Field(
        None, description="Predicted low temperature in Celsius"
    )
    precipitation_chance: float | None = Field(
        None, ge=0, le=100, description="Precipitation probability"
    )
    conditions: str | None = Field(None, description="Predicted conditions")
    confidence: float | None = Field(
        None, ge=0, le=100, description="Forecast confidence"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "USC00110072",
                "forecast_date": "2024-01-16",
                "predicted_high": 12.5,
                "predicted_low": 3.2,
                "precipitation_chance": 30.0,
                "conditions": "Partly cloudy",
                "confidence": 75.0,
            }
        }


class WeatherAlert(BaseModel):
    """Weather alert or notification."""

    alert_id: str = Field(..., description="Alert identifier")
    station_id: str = Field(..., description="Weather station ID")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    issued_at: datetime = Field(..., description="When alert was issued")
    expires_at: datetime | None = Field(None, description="When alert expires")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "ALERT_001",
                "station_id": "USC00110072",
                "alert_type": "extreme_temperature",
                "severity": "moderate",
                "message": "Temperatures below -10°C expected",
                "issued_at": "2024-01-15T14:30:00Z",
                "expires_at": "2024-01-16T06:00:00Z",
            }
        }


class SimpleWeatherResponse(BaseModel):
    """Generic simple weather response wrapper."""

    success: bool = Field(True, description="Request success status")
    message: str = Field("OK", description="Response message")
    data: dict | None = Field(None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Weather data retrieved successfully",
                "data": {"temperature": 15.5, "conditions": "Sunny"},
                "timestamp": "2024-01-15T12:00:00Z",
            }
        }


# System-wide weather statistics models
class SystemOverview(BaseModel):
    """System-wide overview statistics."""

    total_stations: int = Field(..., description="Total number of weather stations")
    active_stations: int = Field(..., description="Stations with recent data")
    total_observations: int = Field(..., description="Total weather observations")
    date_range: dict[str, DateType | None] = Field(
        ..., description="Date range of available data"
    )
    states_covered: list[str] = Field(
        default_factory=list, description="List of states with weather stations"
    )
    geographic_coverage: dict[str, float] = Field(
        ..., description="Geographic coverage statistics"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_stations": 245,
                "active_stations": 231,
                "total_observations": 1250000,
                "date_range": {"earliest": "1950-01-01", "latest": "2024-12-31"},
                "states_covered": ["IL", "IA", "WI", "IN", "MN", "MO"],
                "geographic_coverage": {
                    "latitude_range": 35.7,
                    "longitude_range": 42.3,
                    "elevation_range": 1847.2,
                },
            }
        }


class TemperatureStats(BaseModel):
    """System-wide temperature statistics."""

    overall: dict[str, float] = Field(..., description="Overall temperature statistics")
    extremes: dict[str, dict] = Field(
        ..., description="Temperature extremes by location"
    )
    averages_by_state: dict[str, dict] = Field(
        ..., description="Average temperatures by state"
    )
    seasonal_patterns: dict[str, dict] = Field(
        ..., description="Seasonal temperature patterns"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall": {
                    "mean_temperature": 12.4,
                    "coldest_recorded": -42.8,
                    "hottest_recorded": 47.2,
                    "standard_deviation": 18.7,
                },
                "extremes": {
                    "coldest_location": {
                        "station_id": "USC00117551",
                        "temperature": -42.8,
                        "date": "1996-02-02",
                        "state": "MN",
                    },
                    "hottest_location": {
                        "station_id": "USC00134735",
                        "temperature": 47.2,
                        "date": "2012-07-14",
                        "state": "IA",
                    },
                },
                "averages_by_state": {
                    "IL": {"mean": 11.8, "winter": -3.2, "summer": 25.1},
                    "IA": {"mean": 9.7, "winter": -6.1, "summer": 23.8},
                },
                "seasonal_patterns": {
                    "spring": {"avg": 12.3, "trend": "warming"},
                    "summer": {"avg": 24.7, "trend": "stable"},
                    "autumn": {"avg": 13.1, "trend": "cooling"},
                    "winter": {"avg": -4.2, "trend": "warming"},
                },
            }
        }


class PrecipitationStats(BaseModel):
    """System-wide precipitation statistics."""

    overall: dict[str, float] = Field(
        ..., description="Overall precipitation statistics"
    )
    extremes: dict[str, dict] = Field(..., description="Precipitation extremes")
    regional_patterns: dict[str, dict] = Field(
        ..., description="Regional precipitation patterns"
    )
    drought_flood_metrics: dict[str, int] = Field(
        ..., description="Drought and flood event metrics"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall": {
                    "annual_average": 914.2,
                    "daily_average": 2.5,
                    "wettest_day_recorded": 203.7,
                    "longest_dry_spell": 89,
                },
                "extremes": {
                    "wettest_location": {
                        "station_id": "USC00115768",
                        "precipitation": 203.7,
                        "date": "2008-06-12",
                        "state": "IA",
                    },
                    "driest_region": {"state": "WY", "annual_average": 312.4},
                },
                "regional_patterns": {
                    "IL": {"annual_avg": 965.2, "wettest_month": "May"},
                    "IA": {"annual_avg": 842.7, "wettest_month": "June"},
                },
                "drought_flood_metrics": {
                    "extreme_dry_days": 1247,
                    "extreme_wet_days": 892,
                    "flood_events": 156,
                },
            }
        }


class DataQualityMetrics(BaseModel):
    """Comprehensive data quality metrics."""

    completeness: dict[str, float] = Field(..., description="Data completeness metrics")
    coverage: dict[str, dict] = Field(..., description="Temporal and spatial coverage")
    reliability: dict[str, float] = Field(..., description="Data reliability metrics")
    freshness: dict[str, int] = Field(..., description="Data freshness indicators")

    class Config:
        json_schema_extra = {
            "example": {
                "completeness": {
                    "overall": 87.3,
                    "temperature": 91.2,
                    "precipitation": 83.4,
                    "last_30_days": 94.7,
                },
                "coverage": {
                    "temporal": {
                        "years_covered": 74,
                        "continuous_coverage": "1950-2024",
                        "gaps_identified": 23,
                    },
                    "spatial": {
                        "states_covered": 6,
                        "density_per_100km2": 0.8,
                        "rural_urban_ratio": 3.2,
                    },
                },
                "reliability": {
                    "outlier_detection_score": 96.8,
                    "consistency_score": 92.1,
                    "validation_pass_rate": 89.3,
                },
                "freshness": {
                    "stations_updated_today": 187,
                    "stations_updated_this_week": 231,
                    "average_lag_hours": 18,
                },
            }
        }


class RegionalStats(BaseModel):
    """Regional weather statistics."""

    state: str = Field(..., description="State abbreviation")
    station_count: int = Field(..., description="Number of stations in state")
    temperature: dict[str, float] = Field(..., description="Temperature statistics")
    precipitation: dict[str, float] = Field(..., description="Precipitation statistics")
    data_quality: float = Field(..., description="Data quality score for region")
    notable_features: list[str] = Field(
        default_factory=list, description="Notable climate features"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "state": "IL",
                "station_count": 42,
                "temperature": {
                    "annual_mean": 11.8,
                    "winter_mean": -3.2,
                    "summer_mean": 25.1,
                    "record_high": 47.2,
                    "record_low": -37.8,
                },
                "precipitation": {
                    "annual_total": 965.2,
                    "wettest_month_avg": 112.3,
                    "driest_month_avg": 45.7,
                },
                "data_quality": 91.2,
                "notable_features": [
                    "Continental climate",
                    "Tornado alley proximity",
                    "Great Lakes influence",
                ],
            }
        }


class TemporalStats(BaseModel):
    """Temporal weather statistics."""

    period: str = Field(..., description="Time period (year, month, season)")
    period_value: str = Field(..., description="Specific period value")
    observations: int = Field(..., description="Number of observations in period")
    temperature: dict[str, float] = Field(..., description="Temperature statistics")
    precipitation: dict[str, float] = Field(..., description="Precipitation statistics")
    notable_events: list[str] = Field(
        default_factory=list, description="Notable weather events"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "period": "year",
                "period_value": "2023",
                "observations": 89450,
                "temperature": {
                    "mean": 13.1,
                    "anomaly": +1.8,
                    "record_days": 12,
                },
                "precipitation": {
                    "total": 1087.3,
                    "anomaly": +15.2,
                    "extreme_events": 8,
                },
                "notable_events": [
                    "Record June heatwave",
                    "Severe flooding in August",
                    "Unusually warm winter",
                ],
            }
        }


class SystemStatsResponse(BaseModel):
    """Complete system statistics response."""

    generated_at: datetime = Field(
        default_factory=datetime.now, description="When statistics were generated"
    )
    overview: SystemOverview = Field(..., description="System overview statistics")
    temperature: TemperatureStats = Field(..., description="Temperature statistics")
    precipitation: PrecipitationStats = Field(
        ..., description="Precipitation statistics"
    )
    data_quality: DataQualityMetrics = Field(..., description="Data quality metrics")
    regional_breakdown: list[RegionalStats] = Field(
        default_factory=list, description="Statistics by region/state"
    )
    temporal_breakdown: list[TemporalStats] = Field(
        default_factory=list, description="Statistics by time period"
    )
    computation_time_ms: float = Field(
        ..., description="Time taken to compute statistics"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "generated_at": "2024-01-15T12:00:00Z",
                "overview": {
                    "total_stations": 245,
                    "active_stations": 231,
                    "total_observations": 1250000,
                },
                "temperature": {"overall": {"mean_temperature": 12.4}},
                "precipitation": {"overall": {"annual_average": 914.2}},
                "data_quality": {"completeness": {"overall": 87.3}},
                "regional_breakdown": [{"state": "IL", "station_count": 42}],
                "temporal_breakdown": [{"period": "year", "period_value": "2023"}],
                "computation_time_ms": 234.7,
            }
        }
