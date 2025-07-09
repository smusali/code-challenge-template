"""
Enhanced endpoints with filtering, pagination, and sorting capabilities.

This module demonstrates the new query utilities by providing enhanced versions
of existing endpoints with comprehensive filtering, sorting, and pagination.
"""

import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core_django.models.models import DailyWeather, WeatherStation, YearlyWeatherStats
from src.models.query import (
    DailyWeatherQueryParams,
    WeatherStationQueryParams,
    YearlyStatsQueryParams,
    create_daily_weather_query_params,
    create_weather_station_query_params,
    create_yearly_stats_query_params,
)
from src.models.weather import (
    DailyWeatherResponse,
    WeatherStationResponse,
    YearlyWeatherStatsResponse,
)
from src.utils.filtering import (
    DateRangeFilter,
    FilterParams,
    NumericRangeFilter,
    StateFilter,
    TextSearchFilter,
    apply_filters,
    parse_date_safely,
    validate_date_range_consistency,
    validate_filter_compatibility,
)
from src.utils.pagination import PaginatedResponse, PaginationParams, paginate_queryset
from src.utils.sorting import SortParams, apply_sorting, get_available_sort_fields

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/weather-stations", response_model=PaginatedResponse[WeatherStationResponse]
)
async def list_weather_stations_filtered(
    request: Request,
    query_params: WeatherStationQueryParams = Depends(
        create_weather_station_query_params
    ),
) -> PaginatedResponse[WeatherStationResponse]:
    """
    List weather stations with advanced filtering, sorting, and pagination.

    Supports:
    - Text search across station names and IDs
    - State-based filtering
    - Recent data availability filtering
    - Flexible sorting on multiple fields
    - Pagination with navigation links
    """
    try:
        # Start with base queryset
        queryset = WeatherStation.objects.all()

        # Apply text search
        if query_params.search:
            search_filter = TextSearchFilter(
                search=query_params.search, search_fields=["name", "station_id"]
            )
            queryset = search_filter.apply_to_queryset(queryset, ["name", "station_id"])

        # Apply state filtering
        if query_params.states:
            state_filter = StateFilter(states=query_params.states)
            queryset = state_filter.apply_to_queryset(queryset, "state")

        # Apply recent data filter with proper timezone handling
        if query_params.has_recent_data is not None:
            from django.utils import timezone

            # Use timezone-aware current date to avoid timezone issues
            current_date = timezone.now().date()
            recent_cutoff = current_date - timedelta(days=30)

            if query_params.has_recent_data:
                queryset = queryset.filter(
                    daily_records__date__gte=recent_cutoff
                ).distinct()
            else:
                queryset = queryset.exclude(
                    daily_records__date__gte=recent_cutoff
                ).distinct()

        # Apply sorting
        sort_params = SortParams(
            sort_by=query_params.sort_by, sort_order=query_params.sort_order
        )
        queryset = apply_sorting(queryset, sort_params, "weather_station")

        # Apply pagination
        pagination_params = PaginationParams(
            page=query_params.page, page_size=query_params.page_size
        )

        paginated_result = paginate_queryset(queryset, pagination_params, request)

        # Convert to response models
        station_responses = [
            WeatherStationResponse.from_orm(station)
            for station in paginated_result.items
        ]

        # Return paginated response
        return PaginatedResponse[WeatherStationResponse](
            items=station_responses,
            pagination=paginated_result.pagination,
            links=paginated_result.links,
        )

    except Exception as e:
        logger.error(f"Error listing weather stations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving weather stations: {str(e)}",
        )


@router.get("/daily-weather", response_model=PaginatedResponse[DailyWeatherResponse])
async def list_daily_weather_filtered(
    request: Request,
    query_params: DailyWeatherQueryParams = Depends(create_daily_weather_query_params),
) -> PaginatedResponse[DailyWeatherResponse]:
    """
    List daily weather records with comprehensive filtering.

    Supports:
    - Date range filtering (start_date, end_date, year, month)
    - Temperature range filtering
    - Precipitation range filtering
    - Station and state filtering
    - Data availability filtering
    - Flexible sorting and pagination
    """
    try:
        # Start with base queryset
        queryset = DailyWeather.objects.select_related("station").all()

        # Build comprehensive filters
        filters = FilterParams()

        # Date filtering with improved error handling
        if query_params.start_date or query_params.end_date:
            try:
                start_date = (
                    parse_date_safely(query_params.start_date, "start_date")
                    if query_params.start_date
                    else None
                )
                end_date = (
                    parse_date_safely(query_params.end_date, "end_date")
                    if query_params.end_date
                    else None
                )

                # Validate date range consistency with year/month filters
                validate_date_range_consistency(
                    start_date, end_date, query_params.year, query_params.month
                )

                filters.date_range = DateRangeFilter(
                    start_date=start_date, end_date=end_date
                )

            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                logger.error(f"Unexpected error in date filtering: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error processing date filters: {str(e)}",
                )

        # Year and month filtering with validation
        if query_params.year or query_params.month:
            # Validate consistency with date range filters (already done above if date range exists)
            if not (query_params.start_date or query_params.end_date):
                validate_date_range_consistency(
                    None, None, query_params.year, query_params.month
                )

            if query_params.year:
                filters.year = query_params.year
            if query_params.month:
                filters.month = query_params.month

        # Temperature filtering with validation
        if query_params.min_temp is not None or query_params.max_temp is not None:
            # Validate temperature ranges (reasonable for Earth's climate)
            if query_params.min_temp is not None and (
                query_params.min_temp < -100 or query_params.min_temp > 70
            ):
                logger.warning(
                    f"Extreme minimum temperature value: {query_params.min_temp}°C"
                )
                # Don't raise error but log for monitoring - could be valid research data

            if query_params.max_temp is not None and (
                query_params.max_temp < -100 or query_params.max_temp > 70
            ):
                logger.warning(
                    f"Extreme maximum temperature value: {query_params.max_temp}°C"
                )

            # Validate min <= max
            if (
                query_params.min_temp is not None
                and query_params.max_temp is not None
                and query_params.min_temp > query_params.max_temp
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Minimum temperature ({query_params.min_temp}°C) cannot be greater than maximum temperature ({query_params.max_temp}°C)",
                )

            filters.temperature_range = NumericRangeFilter(
                min_value=query_params.min_temp, max_value=query_params.max_temp
            )

        # Precipitation filtering with validation
        if (
            query_params.min_precipitation is not None
            or query_params.max_precipitation is not None
        ):
            # Validate precipitation ranges (must be non-negative)
            if (
                query_params.min_precipitation is not None
                and query_params.min_precipitation < 0
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Minimum precipitation cannot be negative: {query_params.min_precipitation}mm",
                )

            if (
                query_params.max_precipitation is not None
                and query_params.max_precipitation < 0
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum precipitation cannot be negative: {query_params.max_precipitation}mm",
                )

            # Validate min <= max
            if (
                query_params.min_precipitation is not None
                and query_params.max_precipitation is not None
                and query_params.min_precipitation > query_params.max_precipitation
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Minimum precipitation ({query_params.min_precipitation}mm) cannot be greater than maximum precipitation ({query_params.max_precipitation}mm)",
                )

            # Log extreme values for monitoring
            if (
                query_params.max_precipitation is not None
                and query_params.max_precipitation > 1000
            ):
                logger.warning(
                    f"Very high precipitation value: {query_params.max_precipitation}mm"
                )

            filters.precipitation_range = NumericRangeFilter(
                min_value=query_params.min_precipitation,
                max_value=query_params.max_precipitation,
            )

        # Location filtering
        states = query_params.states
        if states:
            filters.location = StateFilter(states=states)

        # Station filtering
        if query_params.station_ids:
            queryset = queryset.filter(station__station_id__in=query_params.station_ids)

        # Data availability filtering
        if query_params.has_temperature is not None:
            filters.has_temperature = query_params.has_temperature
        if query_params.has_precipitation is not None:
            filters.has_precipitation = query_params.has_precipitation

        # Validate filter compatibility
        validation = validate_filter_compatibility(filters)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filter combination: {validation['errors']}",
            )

        # Apply filters
        queryset = apply_filters(queryset, filters, "daily_weather")

        # Apply sorting
        sort_params = SortParams(
            sort_by=query_params.sort_by, sort_order=query_params.sort_order
        )
        queryset = apply_sorting(queryset, sort_params, "daily_weather")

        # Apply pagination
        pagination_params = PaginationParams(
            page=query_params.page, page_size=query_params.page_size
        )

        paginated_result = paginate_queryset(queryset, pagination_params, request)

        # Convert to response models
        weather_responses = [
            DailyWeatherResponse.from_orm(record) for record in paginated_result.items
        ]

        # Return paginated response with filter warnings
        result = PaginatedResponse[DailyWeatherResponse](
            items=weather_responses,
            pagination=paginated_result.pagination,
            links=paginated_result.links,
        )

        # Add filter validation warnings to response if any
        if validation.get("warnings"):
            logger.warning(f"Filter warnings: {validation['warnings']}")

        return result

    except Exception as e:
        logger.error(f"Error listing daily weather: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving daily weather: {str(e)}",
        )


@router.get(
    "/yearly-stats", response_model=PaginatedResponse[YearlyWeatherStatsResponse]
)
async def list_yearly_stats_filtered(
    request: Request,
    query_params: YearlyStatsQueryParams = Depends(create_yearly_stats_query_params),
) -> PaginatedResponse[YearlyWeatherStatsResponse]:
    """
    List yearly weather statistics with advanced filtering.

    Supports:
    - Year range filtering
    - Temperature statistics filtering
    - Precipitation statistics filtering
    - Data completeness filtering
    - Station and state filtering
    - Multi-field sorting
    """
    try:
        # Start with base queryset
        queryset = YearlyWeatherStats.objects.select_related("station").all()

        # Year filtering with validation
        if query_params.start_year or query_params.end_year or query_params.years:
            # Validate year ranges
            if query_params.start_year and (
                query_params.start_year < 1800 or query_params.start_year > 2100
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_year: {query_params.start_year}. Year must be between 1800 and 2100",
                )

            if query_params.end_year and (
                query_params.end_year < 1800 or query_params.end_year > 2100
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_year: {query_params.end_year}. Year must be between 1800 and 2100",
                )

            # Validate start_year <= end_year
            if (
                query_params.start_year
                and query_params.end_year
                and query_params.start_year > query_params.end_year
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Start year ({query_params.start_year}) cannot be greater than end year ({query_params.end_year})",
                )

            # Validate specific years
            if query_params.years:
                invalid_years = [
                    year for year in query_params.years if year < 1800 or year > 2100
                ]
                if invalid_years:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid years: {invalid_years}. All years must be between 1800 and 2100",
                    )

                # Check for conflicting year filters
                if query_params.start_year or query_params.end_year:
                    logger.warning("Both year range and specific years provided")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot use both year range (start_year/end_year) and specific years filters simultaneously",
                    )

            # Apply the filters
            if query_params.start_year:
                queryset = queryset.filter(year__gte=query_params.start_year)
            if query_params.end_year:
                queryset = queryset.filter(year__lte=query_params.end_year)
            if query_params.years:
                queryset = queryset.filter(year__in=query_params.years)

        # Temperature filtering
        if query_params.min_avg_temp is not None:
            queryset = queryset.filter(
                avg_max_temp__gte=query_params.min_avg_temp * 10
            )  # Convert to tenths
        if query_params.max_avg_temp is not None:
            queryset = queryset.filter(avg_max_temp__lte=query_params.max_avg_temp * 10)

        # Precipitation filtering
        if query_params.min_total_precipitation is not None:
            queryset = queryset.filter(
                total_precipitation__gte=query_params.min_total_precipitation * 10
            )
        if query_params.max_total_precipitation is not None:
            queryset = queryset.filter(
                total_precipitation__lte=query_params.max_total_precipitation * 10
            )

        # Data completeness filtering
        if query_params.min_data_completeness is not None:
            # Calculate minimum required temperature records for completeness percentage
            min_records = (
                query_params.min_data_completeness / 100.0 * 365
            )  # Approximate
            queryset = queryset.filter(records_with_temp__gte=min_records)

        # Station filtering
        if query_params.station_ids:
            queryset = queryset.filter(station__station_id__in=query_params.station_ids)

        # State filtering
        if query_params.states:
            queryset = queryset.filter(station__state__in=query_params.states)

        # Apply sorting
        sort_params = SortParams(
            sort_by=query_params.sort_by, sort_order=query_params.sort_order
        )
        queryset = apply_sorting(queryset, sort_params, "yearly_stats")

        # Apply pagination
        pagination_params = PaginationParams(
            page=query_params.page, page_size=query_params.page_size
        )

        paginated_result = paginate_queryset(queryset, pagination_params, request)

        # Convert to response models
        stats_responses = [
            YearlyWeatherStatsResponse.from_orm(stat) for stat in paginated_result.items
        ]

        return PaginatedResponse[YearlyWeatherStatsResponse](
            items=stats_responses,
            pagination=paginated_result.pagination,
            links=paginated_result.links,
        )

    except Exception as e:
        logger.error(f"Error listing yearly stats: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving yearly statistics: {str(e)}",
        )


@router.get("/sort-info/{model_type}")
async def get_sort_information(model_type: str) -> dict[str, Any]:
    """
    Get available sort fields and information for a model type.

    Args:
        model_type: Type of model ('weather_station', 'daily_weather', 'yearly_stats')

    Returns:
        Information about available sort fields and usage
    """
    if model_type not in [
        "weather_station",
        "daily_weather",
        "yearly_stats",
        "crop_yield",
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model type. Allowed types: weather_station, daily_weather, yearly_stats, crop_yield",
        )

    available_fields = get_available_sort_fields(model_type)

    return {
        "model_type": model_type,
        "available_fields": available_fields,
        "usage_examples": {
            "single_field": "?sort_by=date&sort_order=desc",
            "with_pagination": "?sort_by=date&sort_order=desc&page=1&page_size=50",
            "note": "Use 'asc' for ascending or 'desc' for descending order",
        },
        "field_count": len(available_fields),
    }


@router.get("/filter-info")
async def get_filter_information() -> dict[str, Any]:
    """
    Get information about available filters and usage examples.

    Returns:
        Comprehensive filter documentation and examples
    """
    return {
        "available_filters": {
            "date_range": {
                "description": "Filter by date range",
                "parameters": ["start_date", "end_date"],
                "format": "YYYY-MM-DD",
                "example": "?start_date=2023-01-01&end_date=2023-12-31",
            },
            "year_month": {
                "description": "Filter by specific year or month",
                "parameters": ["year", "month"],
                "example": "?year=2023&month=6",
            },
            "temperature_range": {
                "description": "Filter by temperature range (Celsius)",
                "parameters": ["min_temp", "max_temp"],
                "example": "?min_temp=-10&max_temp=40",
            },
            "precipitation_range": {
                "description": "Filter by precipitation range (mm)",
                "parameters": ["min_precipitation", "max_precipitation"],
                "example": "?min_precipitation=0&max_precipitation=100",
            },
            "location": {
                "description": "Filter by state or station",
                "parameters": ["states", "station_ids"],
                "example": "?states=IL&states=IA&station_ids=USC00110072",
            },
            "data_availability": {
                "description": "Filter by data availability",
                "parameters": ["has_temperature", "has_precipitation"],
                "example": "?has_temperature=true&has_precipitation=true",
            },
            "text_search": {
                "description": "Search in text fields (stations only)",
                "parameters": ["search"],
                "example": "?search=Chicago",
            },
        },
        "combination_examples": {
            "comprehensive": "?start_date=2023-01-01&end_date=2023-12-31&states=IL&states=IA&min_temp=-10&max_temp=40&has_temperature=true&sort_by=date&sort_order=desc&page=1&page_size=50",
            "simple_date": "?year=2023&sort_by=date&sort_order=desc",
            "location_focus": "?states=IL&search=Chicago&sort_by=name",
        },
        "notes": [
            "Multiple values for lists (states, station_ids) should be provided as separate parameters",
            "Date formats must be YYYY-MM-DD",
            "Temperature values are in Celsius",
            "Precipitation values are in millimeters",
            "Combine filters for more specific results",
        ],
    }
