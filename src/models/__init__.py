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
from .query import (
    CombinedQueryParams,
    DailyWeatherQueryParams,
    WeatherStationQueryParams,
    YearlyStatsQueryParams,
    create_daily_weather_query_params,
    create_weather_station_query_params,
    create_yearly_stats_query_params,
)
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
    # Query parameter models
    "WeatherStationQueryParams",
    "DailyWeatherQueryParams",
    "YearlyStatsQueryParams",
    "CombinedQueryParams",
    "create_weather_station_query_params",
    "create_daily_weather_query_params",
    "create_yearly_stats_query_params",
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
