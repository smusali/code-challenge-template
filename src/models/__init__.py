"""
Pydantic models for the Weather Data Engineering API.

This package contains Pydantic models for request/response validation
corresponding to the Django ORM models.
"""

from .common import (
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    SystemStatusResponse,
)
from .crops import CropYieldCreate, CropYieldResponse, CropYieldUpdate
from .simple_weather import (
    CurrentWeather,
    DataQualityMetrics,
    PrecipitationStats,
    RegionalStats,
    SimpleWeatherResponse,
    SimpleWeatherStation,
    SystemOverview,
    SystemStatsResponse,
    TemperatureStats,
    TemporalStats,
    WeatherHistory,
    WeatherLocationResponse,
    WeatherSearchResult,
    WeatherStats,
    WeatherSummary,
)
from .weather import (
    DailyWeatherCreate,
    DailyWeatherResponse,
    DailyWeatherUpdate,
    WeatherStationCreate,
    WeatherStationResponse,
    WeatherStationUpdate,
    YearlyWeatherStatsResponse,
)

__all__ = [
    # Weather models
    "WeatherStationCreate",
    "WeatherStationUpdate",
    "WeatherStationResponse",
    "DailyWeatherCreate",
    "DailyWeatherUpdate",
    "DailyWeatherResponse",
    "YearlyWeatherStatsResponse",
    # Simple Weather models
    "SimpleWeatherStation",
    "CurrentWeather",
    "WeatherSummary",
    "WeatherHistory",
    "WeatherLocationResponse",
    "WeatherSearchResult",
    "WeatherStats",
    "SimpleWeatherResponse",
    # System Statistics models
    "SystemOverview",
    "TemperatureStats",
    "PrecipitationStats",
    "DataQualityMetrics",
    "RegionalStats",
    "TemporalStats",
    "SystemStatsResponse",
    # Crop models
    "CropYieldCreate",
    "CropYieldUpdate",
    "CropYieldResponse",
    # Common models
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
    "SystemStatusResponse",
]
