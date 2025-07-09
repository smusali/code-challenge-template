"""
Query parameter models for the Weather Data Engineering API.

This module contains Pydantic models for combining filtering, sorting,
and pagination parameters in API endpoints.
"""


from fastapi import Query
from pydantic import BaseModel, Field

from src.utils.filtering import FilterParams
from src.utils.pagination import PaginationParams
from src.utils.sorting import SortParams


class WeatherStationQueryParams(BaseModel):
    """Query parameters for weather station endpoints."""

    # Search and filtering
    search: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Search term for station name or ID",
        example="Chicago",
    )
    states: list[str] = Field(
        default_factory=list, description="Filter by state codes", example=["IL", "IA"]
    )
    has_recent_data: bool | None = Field(
        None,
        description="Filter stations with recent data (last 30 days)",
        example=True,
    )

    # Pagination
    page: int = Field(default=1, ge=1, le=10000, description="Page number", example=1)
    page_size: int = Field(
        default=20, ge=1, le=1000, description="Items per page", example=20
    )

    # Sorting
    sort_by: str = Field(
        default="station_id", description="Field to sort by", example="name"
    )
    sort_order: str = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order", example="asc"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "search": "Chicago",
                "states": ["IL", "IA"],
                "has_recent_data": True,
                "page": 1,
                "page_size": 20,
                "sort_by": "name",
                "sort_order": "asc",
            }
        }


class DailyWeatherQueryParams(BaseModel):
    """Query parameters for daily weather data endpoints."""

    # Date filtering
    start_date: str | None = Field(
        None, description="Start date (YYYY-MM-DD)", example="2023-01-01"
    )
    end_date: str | None = Field(
        None, description="End date (YYYY-MM-DD)", example="2023-12-31"
    )
    year: int | None = Field(
        None, ge=1800, le=2100, description="Filter by year", example=2023
    )
    month: int | None = Field(
        None, ge=1, le=12, description="Filter by month", example=6
    )

    # Weather filtering
    min_temp: float | None = Field(
        None, description="Minimum temperature (Celsius)", example=-10.0
    )
    max_temp: float | None = Field(
        None, description="Maximum temperature (Celsius)", example=40.0
    )
    min_precipitation: float | None = Field(
        None, ge=0.0, description="Minimum precipitation (mm)", example=0.0
    )
    max_precipitation: float | None = Field(
        None, ge=0.0, description="Maximum precipitation (mm)", example=100.0
    )

    # Location filtering
    station_ids: list[str] = Field(
        default_factory=list,
        description="Filter by station IDs",
        example=["USC00110072", "USC00110187"],
    )
    states: list[str] = Field(
        default_factory=list, description="Filter by state codes", example=["IL", "IA"]
    )

    # Data quality filtering
    has_temperature: bool | None = Field(
        None, description="Filter records with temperature data", example=True
    )
    has_precipitation: bool | None = Field(
        None, description="Filter records with precipitation data", example=True
    )

    # Pagination
    page: int = Field(default=1, ge=1, le=10000, description="Page number", example=1)
    page_size: int = Field(
        default=50, ge=1, le=1000, description="Items per page", example=50
    )

    # Sorting
    sort_by: str = Field(default="date", description="Field to sort by", example="date")
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort order", example="desc"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "min_temp": -10.0,
                "max_temp": 40.0,
                "states": ["IL", "IA"],
                "has_temperature": True,
                "page": 1,
                "page_size": 50,
                "sort_by": "date",
                "sort_order": "desc",
            }
        }


class YearlyStatsQueryParams(BaseModel):
    """Query parameters for yearly statistics endpoints."""

    # Year filtering
    start_year: int | None = Field(
        None, ge=1800, le=2100, description="Start year (inclusive)", example=2020
    )
    end_year: int | None = Field(
        None, ge=1800, le=2100, description="End year (inclusive)", example=2023
    )
    years: list[int] = Field(
        default_factory=list,
        description="Specific years to include",
        example=[2020, 2021, 2022, 2023],
    )

    # Statistics filtering
    min_avg_temp: float | None = Field(
        None, description="Minimum average temperature (Celsius)", example=5.0
    )
    max_avg_temp: float | None = Field(
        None, description="Maximum average temperature (Celsius)", example=25.0
    )
    min_total_precipitation: float | None = Field(
        None, ge=0.0, description="Minimum total precipitation (mm)", example=300.0
    )
    max_total_precipitation: float | None = Field(
        None, ge=0.0, description="Maximum total precipitation (mm)", example=1500.0
    )

    # Location filtering
    station_ids: list[str] = Field(
        default_factory=list,
        description="Filter by station IDs",
        example=["USC00110072", "USC00110187"],
    )
    states: list[str] = Field(
        default_factory=list, description="Filter by state codes", example=["IL", "IA"]
    )

    # Data quality filtering
    min_data_completeness: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Minimum data completeness percentage",
        example=80.0,
    )

    # Pagination
    page: int = Field(default=1, ge=1, le=10000, description="Page number", example=1)
    page_size: int = Field(
        default=100, ge=1, le=1000, description="Items per page", example=100
    )

    # Sorting
    sort_by: str = Field(default="year", description="Field to sort by", example="year")
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort order", example="desc"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_year": 2020,
                "end_year": 2023,
                "min_avg_temp": 5.0,
                "max_avg_temp": 25.0,
                "states": ["IL", "IA"],
                "min_data_completeness": 80.0,
                "page": 1,
                "page_size": 100,
                "sort_by": "year",
                "sort_order": "desc",
            }
        }


class CombinedQueryParams(BaseModel):
    """Combined query parameters with filters, pagination, and sorting."""

    filters: FilterParams = Field(
        default_factory=FilterParams, description="Filter parameters"
    )
    pagination: PaginationParams = Field(
        default_factory=PaginationParams, description="Pagination parameters"
    )
    sorting: SortParams = Field(
        default_factory=SortParams, description="Sorting parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "date_range": {
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                    },
                    "temperature_range": {"min_value": -10.0, "max_value": 40.0},
                    "location": {"states": ["IL", "IA"]},
                },
                "pagination": {"page": 1, "page_size": 50},
                "sorting": {"sort_by": "date", "sort_order": "desc"},
            }
        }


def create_weather_station_query_params(
    search: str | None = Query(None, description="Search term"),
    states: list[str] = Query(default_factory=list, description="State codes"),
    has_recent_data: bool | None = Query(None, description="Has recent data"),
    page: int = Query(1, ge=1, le=10000, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("station_id", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
) -> WeatherStationQueryParams:
    """Dependency function for weather station query parameters."""
    return WeatherStationQueryParams(
        search=search,
        states=states,
        has_recent_data=has_recent_data,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def create_daily_weather_query_params(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    year: int | None = Query(None, ge=1800, le=2100, description="Filter by year"),
    month: int | None = Query(None, ge=1, le=12, description="Filter by month"),
    min_temp: float | None = Query(None, description="Minimum temperature"),
    max_temp: float | None = Query(None, description="Maximum temperature"),
    min_precipitation: float | None = Query(
        None, ge=0.0, description="Min precipitation"
    ),
    max_precipitation: float | None = Query(
        None, ge=0.0, description="Max precipitation"
    ),
    station_ids: list[str] = Query(default_factory=list, description="Station IDs"),
    states: list[str] = Query(default_factory=list, description="State codes"),
    has_temperature: bool | None = Query(None, description="Has temperature data"),
    has_precipitation: bool | None = Query(None, description="Has precipitation data"),
    page: int = Query(1, ge=1, le=10000, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("date", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
) -> DailyWeatherQueryParams:
    """Dependency function for daily weather query parameters."""
    return DailyWeatherQueryParams(
        start_date=start_date,
        end_date=end_date,
        year=year,
        month=month,
        min_temp=min_temp,
        max_temp=max_temp,
        min_precipitation=min_precipitation,
        max_precipitation=max_precipitation,
        station_ids=station_ids,
        states=states,
        has_temperature=has_temperature,
        has_precipitation=has_precipitation,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def create_yearly_stats_query_params(
    start_year: int | None = Query(None, ge=1800, le=2100, description="Start year"),
    end_year: int | None = Query(None, ge=1800, le=2100, description="End year"),
    years: list[int] = Query(default_factory=list, description="Specific years"),
    min_avg_temp: float | None = Query(None, description="Minimum average temperature"),
    max_avg_temp: float | None = Query(None, description="Maximum average temperature"),
    min_total_precipitation: float | None = Query(
        None, ge=0.0, description="Min total precipitation"
    ),
    max_total_precipitation: float | None = Query(
        None, ge=0.0, description="Max total precipitation"
    ),
    station_ids: list[str] = Query(default_factory=list, description="Station IDs"),
    states: list[str] = Query(default_factory=list, description="State codes"),
    min_data_completeness: float | None = Query(
        None, ge=0.0, le=100.0, description="Min completeness %"
    ),
    page: int = Query(1, ge=1, le=10000, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("year", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
) -> YearlyStatsQueryParams:
    """Dependency function for yearly statistics query parameters."""
    return YearlyStatsQueryParams(
        start_year=start_year,
        end_year=end_year,
        years=years,
        min_avg_temp=min_avg_temp,
        max_avg_temp=max_avg_temp,
        min_total_precipitation=min_total_precipitation,
        max_total_precipitation=max_total_precipitation,
        station_ids=station_ids,
        states=states,
        min_data_completeness=min_data_completeness,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
