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
