"""
Weather data API endpoints.

This module provides RESTful API endpoints for weather station management,
daily weather observations, and yearly weather statistics.
"""

import logging
from datetime import date, datetime
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Max, Min, Q
from django.shortcuts import get_object_or_404
from fastapi import APIRouter, Depends, HTTPException, Query, status

from core_django.models.models import DailyWeather, WeatherStation, YearlyWeatherStats
from core_django.utils.units import (
    calculate_data_completeness,
    tenths_to_celsius,
    tenths_to_millimeters,
)
from src.models.common import (
    PaginatedResponse,
    SuccessResponse,
)
from src.models.weather import (
    DailyWeatherCreate,
    DailyWeatherResponse,
    DailyWeatherUpdate,
    WeatherDataSummary,
    WeatherStationCreate,
    WeatherStationResponse,
    WeatherStationUpdate,
    YearlyWeatherStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> dict:
    """Get pagination parameters."""
    return {"page": page, "page_size": page_size}


def paginate_queryset(queryset, page: int, page_size: int):
    """Paginate a Django queryset."""
    total_items = queryset.count()
    total_pages = (total_items + page_size - 1) // page_size

    offset = (page - 1) * page_size
    items = list(queryset[offset : offset + page_size])

    return {
        "items": items,
        "total_items": total_items,
        "total_pages": total_pages,
        "page": page,
        "page_size": page_size,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def convert_daily_weather_to_response(
    daily_weather: DailyWeather,
) -> DailyWeatherResponse:
    """Convert Django model to Pydantic response model."""
    return DailyWeatherResponse(
        id=daily_weather.id,
        station_id=daily_weather.station.station_id,
        date=daily_weather.date,
        max_temp=daily_weather.max_temp,
        min_temp=daily_weather.min_temp,
        precipitation=daily_weather.precipitation,
        max_temp_celsius=daily_weather.max_temp_celsius,
        min_temp_celsius=daily_weather.min_temp_celsius,
        precipitation_mm=daily_weather.precipitation_mm,
        created_at=daily_weather.created_at,
        updated_at=daily_weather.updated_at,
    )


def convert_yearly_stats_to_response(
    yearly_stats: YearlyWeatherStats,
) -> YearlyWeatherStatsResponse:
    """Convert Django yearly stats model to Pydantic response model."""
    return YearlyWeatherStatsResponse(
        id=yearly_stats.id,
        station_id=yearly_stats.station.station_id,
        year=yearly_stats.year,
        avg_max_temp=yearly_stats.avg_max_temp,
        avg_min_temp=yearly_stats.avg_min_temp,
        max_temp=yearly_stats.max_temp,
        min_temp=yearly_stats.min_temp,
        total_precipitation=yearly_stats.total_precipitation,
        avg_precipitation=yearly_stats.avg_precipitation,
        max_precipitation=yearly_stats.max_precipitation,
        total_records=yearly_stats.total_records,
        records_with_temp=yearly_stats.records_with_temp,
        records_with_precipitation=yearly_stats.records_with_precipitation,
        avg_max_temp_celsius=yearly_stats.avg_max_temp_celsius,
        avg_min_temp_celsius=yearly_stats.avg_min_temp_celsius,
        max_temp_celsius=yearly_stats.max_temp_celsius,
        min_temp_celsius=yearly_stats.min_temp_celsius,
        total_precipitation_mm=yearly_stats.total_precipitation_mm,
        avg_precipitation_mm=yearly_stats.avg_precipitation_mm,
        max_precipitation_mm=yearly_stats.max_precipitation_mm,
        temperature_completeness=calculate_data_completeness(
            yearly_stats.records_with_temp, yearly_stats.total_records
        ),
        precipitation_completeness=calculate_data_completeness(
            yearly_stats.records_with_precipitation, yearly_stats.total_records
        ),
        created_at=yearly_stats.created_at,
        updated_at=yearly_stats.updated_at,
    )


# Weather Stations Endpoints


@router.get("/stations", response_model=PaginatedResponse[WeatherStationResponse])
async def list_weather_stations(
    pagination: dict = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search by station ID or name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    sort_by: Optional[str] = Query("station_id", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "asc", regex="^(asc|desc)$", description="Sort order"
    ),
):
    """
    List all weather stations with pagination and filtering.
    """
    try:
        queryset = WeatherStation.objects.all()

        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(station_id__icontains=search) | Q(name__icontains=search)
            )

        # Apply state filter
        if state:
            queryset = queryset.filter(state=state.upper())

        # Apply sorting
        if sort_by:
            if sort_order == "desc":
                sort_by = f"-{sort_by}"
            queryset = queryset.order_by(sort_by)

        # Paginate results
        paginated = paginate_queryset(
            queryset, pagination["page"], pagination["page_size"]
        )

        # Convert to response models
        stations = [
            WeatherStationResponse.from_orm(station) for station in paginated["items"]
        ]

        return PaginatedResponse(
            data=stations,
            meta={
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total_items": paginated["total_items"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_previous": paginated["has_previous"],
            },
        )

    except Exception as e:
        logger.error(f"Error listing weather stations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing weather stations: {str(e)}",
        )


@router.post(
    "/stations",
    response_model=WeatherStationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_weather_station(station_data: WeatherStationCreate):
    """
    Create a new weather station.
    """
    try:
        # Check if station already exists
        if WeatherStation.objects.filter(station_id=station_data.station_id).exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Weather station {station_data.station_id} already exists",
            )

        # Create new station
        station = WeatherStation.objects.create(
            station_id=station_data.station_id,
            name=station_data.name,
            latitude=station_data.latitude,
            longitude=station_data.longitude,
            elevation=station_data.elevation,
            state=station_data.state,
        )

        logger.info(f"Created weather station: {station.station_id}")
        return WeatherStationResponse.from_orm(station)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating weather station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating weather station: {str(e)}",
        )


@router.get("/stations/{station_id}", response_model=WeatherStationResponse)
async def get_weather_station(station_id: str):
    """
    Get a specific weather station by ID.
    """
    try:
        station = get_object_or_404(WeatherStation, station_id=station_id)
        return WeatherStationResponse.from_orm(station)

    except Exception as e:
        logger.error(f"Error retrieving weather station {station_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather station {station_id} not found",
        )


@router.put("/stations/{station_id}", response_model=WeatherStationResponse)
async def update_weather_station(station_id: str, station_data: WeatherStationUpdate):
    """
    Update an existing weather station.
    """
    try:
        station = get_object_or_404(WeatherStation, station_id=station_id)

        # Update fields
        update_data = station_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(station, field, value)

        station.save()

        logger.info(f"Updated weather station: {station.station_id}")
        return WeatherStationResponse.from_orm(station)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error updating weather station {station_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating weather station: {str(e)}",
        )


@router.delete("/stations/{station_id}")
async def delete_weather_station(station_id: str):
    """
    Delete a weather station and all associated data.
    """
    try:
        station = get_object_or_404(WeatherStation, station_id=station_id)

        # Count associated records before deletion
        daily_count = station.daily_records.count()
        yearly_count = station.yearly_stats.count()

        station.delete()

        logger.info(
            f"Deleted weather station {station_id} with {daily_count} daily records and {yearly_count} yearly stats"
        )

        return SuccessResponse(
            message=f"Weather station {station_id} deleted successfully",
            data={
                "station_id": station_id,
                "deleted_daily_records": daily_count,
                "deleted_yearly_stats": yearly_count,
            },
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error deleting weather station {station_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting weather station: {str(e)}",
        )


# Daily Weather Endpoints


@router.get("/daily", response_model=PaginatedResponse[DailyWeatherResponse])
async def list_daily_weather(
    pagination: dict = Depends(get_pagination_params),
    station_id: Optional[str] = Query(None, description="Filter by station ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    has_temp: Optional[bool] = Query(
        None, description="Filter records with temperature data"
    ),
    has_precipitation: Optional[bool] = Query(
        None, description="Filter records with precipitation data"
    ),
    sort_by: Optional[str] = Query("date", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort order"
    ),
):
    """
    List daily weather records with pagination and filtering.
    """
    try:
        queryset = DailyWeather.objects.select_related("station")

        # Apply filters
        if station_id:
            queryset = queryset.filter(station__station_id=station_id)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        if has_temp is not None:
            if has_temp:
                queryset = queryset.filter(
                    max_temp__isnull=False, min_temp__isnull=False
                )
            else:
                queryset = queryset.filter(
                    Q(max_temp__isnull=True) | Q(min_temp__isnull=True)
                )

        if has_precipitation is not None:
            if has_precipitation:
                queryset = queryset.filter(precipitation__isnull=False)
            else:
                queryset = queryset.filter(precipitation__isnull=True)

        # Apply sorting
        if sort_by:
            if sort_order == "desc":
                sort_by = f"-{sort_by}"
            queryset = queryset.order_by(sort_by)

        # Paginate results
        paginated = paginate_queryset(
            queryset, pagination["page"], pagination["page_size"]
        )

        # Convert to response models
        daily_records = [
            convert_daily_weather_to_response(record) for record in paginated["items"]
        ]

        return PaginatedResponse(
            data=daily_records,
            meta={
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total_items": paginated["total_items"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_previous": paginated["has_previous"],
            },
        )

    except Exception as e:
        logger.error(f"Error listing daily weather records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing daily weather records: {str(e)}",
        )


@router.post(
    "/daily", response_model=DailyWeatherResponse, status_code=status.HTTP_201_CREATED
)
async def create_daily_weather(weather_data: DailyWeatherCreate):
    """
    Create a new daily weather record.
    """
    try:
        # Get weather station
        station = get_object_or_404(WeatherStation, station_id=weather_data.station_id)

        # Check if record already exists
        if DailyWeather.objects.filter(
            station=station, date=weather_data.date
        ).exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Daily weather record for {weather_data.station_id} on {weather_data.date} already exists",
            )

        # Create new record
        daily_weather = DailyWeather.objects.create(
            station=station,
            date=weather_data.date,
            max_temp=weather_data.max_temp,
            min_temp=weather_data.min_temp,
            precipitation=weather_data.precipitation,
        )

        logger.info(
            f"Created daily weather record for {station.station_id} on {weather_data.date}"
        )
        return convert_daily_weather_to_response(daily_weather)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating daily weather record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating daily weather record: {str(e)}",
        )


@router.get("/daily/{record_id}", response_model=DailyWeatherResponse)
async def get_daily_weather(record_id: int):
    """
    Get a specific daily weather record by ID.
    """
    try:
        daily_weather = get_object_or_404(
            DailyWeather.objects.select_related("station"), id=record_id
        )
        return convert_daily_weather_to_response(daily_weather)

    except Exception as e:
        logger.error(f"Error retrieving daily weather record {record_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily weather record {record_id} not found",
        )


@router.put("/daily/{record_id}", response_model=DailyWeatherResponse)
async def update_daily_weather(record_id: int, weather_data: DailyWeatherUpdate):
    """
    Update an existing daily weather record.
    """
    try:
        daily_weather = get_object_or_404(
            DailyWeather.objects.select_related("station"), id=record_id
        )

        # Update fields
        update_data = weather_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(daily_weather, field, value)

        daily_weather.save()

        logger.info(f"Updated daily weather record {record_id}")
        return convert_daily_weather_to_response(daily_weather)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error updating daily weather record {record_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating daily weather record: {str(e)}",
        )


@router.delete("/daily/{record_id}")
async def delete_daily_weather(record_id: int):
    """
    Delete a daily weather record.
    """
    try:
        daily_weather = get_object_or_404(DailyWeather, id=record_id)

        station_id = daily_weather.station.station_id
        date = daily_weather.date

        daily_weather.delete()

        logger.info(
            f"Deleted daily weather record {record_id} for {station_id} on {date}"
        )

        return SuccessResponse(
            message=f"Daily weather record {record_id} deleted successfully",
            data={
                "record_id": record_id,
                "station_id": station_id,
                "date": date,
            },
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error deleting daily weather record {record_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting daily weather record: {str(e)}",
        )


# Yearly Statistics Endpoints


@router.get(
    "/yearly-stats", response_model=PaginatedResponse[YearlyWeatherStatsResponse]
)
async def list_yearly_stats(
    pagination: dict = Depends(get_pagination_params),
    station_id: Optional[str] = Query(None, description="Filter by station ID"),
    year: Optional[int] = Query(None, description="Filter by year"),
    start_year: Optional[int] = Query(None, description="Start year filter"),
    end_year: Optional[int] = Query(None, description="End year filter"),
    sort_by: Optional[str] = Query("year", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort order"
    ),
):
    """
    List yearly weather statistics with pagination and filtering.
    """
    try:
        queryset = YearlyWeatherStats.objects.select_related("station")

        # Apply filters
        if station_id:
            queryset = queryset.filter(station__station_id=station_id)

        if year:
            queryset = queryset.filter(year=year)

        if start_year:
            queryset = queryset.filter(year__gte=start_year)

        if end_year:
            queryset = queryset.filter(year__lte=end_year)

        # Apply sorting
        if sort_by:
            if sort_order == "desc":
                sort_by = f"-{sort_by}"
            queryset = queryset.order_by(sort_by)

        # Paginate results
        paginated = paginate_queryset(
            queryset, pagination["page"], pagination["page_size"]
        )

        # Convert to response models
        yearly_stats = [
            convert_yearly_stats_to_response(stat) for stat in paginated["items"]
        ]

        return PaginatedResponse(
            data=yearly_stats,
            meta={
                "page": paginated["page"],
                "page_size": paginated["page_size"],
                "total_items": paginated["total_items"],
                "total_pages": paginated["total_pages"],
                "has_next": paginated["has_next"],
                "has_previous": paginated["has_previous"],
            },
        )

    except Exception as e:
        logger.error(f"Error listing yearly weather statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing yearly weather statistics: {str(e)}",
        )


@router.get("/yearly-stats/{stat_id}", response_model=YearlyWeatherStatsResponse)
async def get_yearly_stats(stat_id: int):
    """
    Get a specific yearly weather statistics record by ID.
    """
    try:
        yearly_stats = get_object_or_404(
            YearlyWeatherStats.objects.select_related("station"), id=stat_id
        )
        return convert_yearly_stats_to_response(yearly_stats)

    except Exception as e:
        logger.error(f"Error retrieving yearly weather statistics {stat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Yearly weather statistics {stat_id} not found",
        )


@router.get("/summary", response_model=WeatherDataSummary)
async def get_weather_data_summary():
    """
    Get comprehensive summary of weather data.
    """
    try:
        # Get counts
        total_stations = WeatherStation.objects.count()
        total_daily_records = DailyWeather.objects.count()
        total_yearly_stats = YearlyWeatherStats.objects.count()

        # Get date range
        date_range = DailyWeather.objects.aggregate(
            earliest=Min("date"), latest=Max("date")
        )

        # Get temperature range (convert from tenths to Celsius)
        temp_range = DailyWeather.objects.aggregate(
            min_temp=Min("min_temp"), max_temp=Max("max_temp")
        )

        # Get precipitation range (convert from tenths to mm)
        precip_range = DailyWeather.objects.aggregate(
            min_precip=Min("precipitation"), max_precip=Max("precipitation")
        )

        # Calculate data completeness
        total_records = total_daily_records
        temp_records = DailyWeather.objects.filter(
            max_temp__isnull=False, min_temp__isnull=False
        ).count()
        precip_records = DailyWeather.objects.filter(
            precipitation__isnull=False
        ).count()

        return WeatherDataSummary(
            total_stations=total_stations,
            total_daily_records=total_daily_records,
            total_yearly_stats=total_yearly_stats,
            date_range=date_range,
            temperature_range={
                "min": tenths_to_celsius(temp_range["min_temp"]),
                "max": tenths_to_celsius(temp_range["max_temp"]),
            },
            precipitation_range={
                "min": tenths_to_millimeters(precip_range["min_precip"]),
                "max": tenths_to_millimeters(precip_range["max_precip"]),
            },
            data_completeness={
                "temperature": calculate_data_completeness(temp_records, total_records),
                "precipitation": calculate_data_completeness(
                    precip_records, total_records
                ),
            },
        )

    except Exception as e:
        logger.error(f"Error getting weather data summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting weather data summary: {str(e)}",
        )
