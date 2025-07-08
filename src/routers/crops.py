"""
Crop yield data API endpoints.

This module provides RESTful API endpoints for crop yield data management,
including CRUD operations, filtering, and analytics.
"""

import logging
from datetime import datetime
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Max, Min, Q
from django.shortcuts import get_object_or_404
from fastapi import APIRouter, Depends, HTTPException, Query, status

from core_django.models.models import CropYield
from src.models.common import PaginatedResponse, SuccessResponse
from src.models.crops import (
    CropYieldComparison,
    CropYieldCreate,
    CropYieldFilter,
    CropYieldResponse,
    CropYieldSummary,
    CropYieldTrend,
    CropYieldUpdate,
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


@router.get("/", response_model=PaginatedResponse[CropYieldResponse])
async def list_crop_yields(
    pagination: dict = Depends(get_pagination_params),
    year: Optional[int] = Query(None, description="Filter by year"),
    crop_type: Optional[str] = Query(None, description="Filter by crop type"),
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state"),
    search: Optional[str] = Query(None, description="Search in crop type or source"),
    sort_by: Optional[str] = Query("year", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort order"
    ),
):
    """
    List crop yield records with pagination and filtering.
    """
    try:
        queryset = CropYield.objects.all()

        # Apply filters
        if year:
            queryset = queryset.filter(year=year)

        if crop_type:
            queryset = queryset.filter(crop_type=crop_type.lower())

        if country:
            queryset = queryset.filter(country=country.upper())

        if state:
            queryset = queryset.filter(state=state.upper())

        if search:
            queryset = queryset.filter(
                Q(crop_type__icontains=search) | Q(source__icontains=search)
            )

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
        crop_yields = [
            CropYieldResponse.from_orm(crop_yield) for crop_yield in paginated["items"]
        ]

        return PaginatedResponse(
            data=crop_yields,
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
        logger.error(f"Error listing crop yields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing crop yields: {str(e)}",
        )


@router.post("/", response_model=CropYieldResponse, status_code=status.HTTP_201_CREATED)
async def create_crop_yield(crop_data: CropYieldCreate):
    """
    Create a new crop yield record.
    """
    try:
        # Check if record already exists
        if CropYield.objects.filter(
            year=crop_data.year,
            crop_type=crop_data.crop_type,
            country=crop_data.country,
            state=crop_data.state or "",
        ).exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Crop yield record for {crop_data.crop_type} in {crop_data.country}:{crop_data.state} for {crop_data.year} already exists",
            )

        # Create new record
        crop_yield = CropYield.objects.create(
            year=crop_data.year,
            crop_type=crop_data.crop_type,
            country=crop_data.country,
            state=crop_data.state,
            yield_value=crop_data.yield_value,
            yield_unit=crop_data.yield_unit,
            source=crop_data.source,
        )

        logger.info(
            f"Created crop yield record for {crop_data.crop_type} in {crop_data.year}"
        )
        return CropYieldResponse.from_orm(crop_yield)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating crop yield record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating crop yield record: {str(e)}",
        )


@router.get("/{crop_id}", response_model=CropYieldResponse)
async def get_crop_yield(crop_id: int):
    """
    Get a specific crop yield record by ID.
    """
    try:
        crop_yield = get_object_or_404(CropYield, id=crop_id)
        return CropYieldResponse.from_orm(crop_yield)

    except Exception as e:
        logger.error(f"Error retrieving crop yield record {crop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop yield record {crop_id} not found",
        )


@router.put("/{crop_id}", response_model=CropYieldResponse)
async def update_crop_yield(crop_id: int, crop_data: CropYieldUpdate):
    """
    Update an existing crop yield record.
    """
    try:
        crop_yield = get_object_or_404(CropYield, id=crop_id)

        # Update fields
        update_data = crop_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(crop_yield, field, value)

        crop_yield.save()

        logger.info(f"Updated crop yield record {crop_id}")
        return CropYieldResponse.from_orm(crop_yield)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error updating crop yield record {crop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating crop yield record: {str(e)}",
        )


@router.delete("/{crop_id}")
async def delete_crop_yield(crop_id: int):
    """
    Delete a crop yield record.
    """
    try:
        crop_yield = get_object_or_404(CropYield, id=crop_id)

        crop_info = {
            "crop_id": crop_id,
            "year": crop_yield.year,
            "crop_type": crop_yield.crop_type,
            "country": crop_yield.country,
            "state": crop_yield.state,
        }

        crop_yield.delete()

        logger.info(f"Deleted crop yield record {crop_id}")

        return SuccessResponse(
            message=f"Crop yield record {crop_id} deleted successfully",
            data=crop_info,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error deleting crop yield record {crop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting crop yield record: {str(e)}",
        )


@router.get("/summary/overview", response_model=CropYieldSummary)
async def get_crop_yield_summary():
    """
    Get comprehensive summary of crop yield data.
    """
    try:
        # Get total records
        total_records = CropYield.objects.count()

        # Get year range
        year_range = CropYield.objects.aggregate(
            earliest=Min("year"), latest=Max("year")
        )

        # Get unique values
        crop_types = list(
            CropYield.objects.values_list("crop_type", flat=True).distinct()
        )
        countries = list(CropYield.objects.values_list("country", flat=True).distinct())
        states = list(CropYield.objects.values_list("state", flat=True).distinct())

        # Calculate yield statistics by crop type
        yield_statistics = {}
        for crop_type in crop_types:
            stats = CropYield.objects.filter(crop_type=crop_type).aggregate(
                min_yield=Min("yield_value"),
                max_yield=Max("yield_value"),
                avg_yield=Avg("yield_value"),
                count=Count("id"),
            )

            if stats["count"] > 0:
                yield_statistics[crop_type] = {
                    "min": float(stats["min_yield"]),
                    "max": float(stats["max_yield"]),
                    "mean": float(stats["avg_yield"]),
                    "count": stats["count"],
                }

        return CropYieldSummary(
            total_records=total_records,
            year_range=year_range,
            crop_types=crop_types,
            countries=countries,
            states=[state for state in states if state],  # Filter out empty states
            yield_statistics=yield_statistics,
        )

    except Exception as e:
        logger.error(f"Error getting crop yield summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting crop yield summary: {str(e)}",
        )


@router.get("/trends/{crop_type}", response_model=CropYieldTrend)
async def get_crop_yield_trend(
    crop_type: str,
    country: str = Query(..., description="Country code"),
    state: Optional[str] = Query(None, description="State code (optional)"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get yield trend data for a specific crop and location.
    """
    try:
        # Build query filters
        filters = {
            "crop_type": crop_type.lower(),
            "country": country.upper(),
        }

        if state:
            filters["state"] = state.upper()

        if start_year:
            filters["year__gte"] = start_year

        if end_year:
            filters["year__lte"] = end_year

        # Get trend data
        queryset = CropYield.objects.filter(**filters).order_by("year")

        if not queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {crop_type} in {country}:{state}",
            )

        years = []
        yields = []
        yield_unit = None

        for record in queryset:
            years.append(record.year)
            yields.append(record.yield_value)
            yield_unit = record.yield_unit

        # Calculate trend direction (simple correlation)
        if len(years) > 1:
            n = len(years)
            sum_x = sum(years)
            sum_y = sum(yields)
            sum_xy = sum(x * y for x, y in zip(years, yields, strict=True))
            sum_xx = sum(x * x for x in years)
            sum_yy = sum(y * y for y in yields)

            correlation = (n * sum_xy - sum_x * sum_y) / (
                ((n * sum_xx - sum_x * sum_x) * (n * sum_yy - sum_y * sum_y)) ** 0.5
            )

            if correlation > 0.1:
                trend_direction = "up"
            elif correlation < -0.1:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            correlation = None
            trend_direction = "stable"

        return CropYieldTrend(
            crop_type=crop_type,
            country=country,
            state=state,
            years=years,
            yields=yields,
            yield_unit=yield_unit,
            trend_direction=trend_direction,
            correlation_coefficient=correlation,
        )

    except Exception as e:
        logger.error(f"Error getting crop yield trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting crop yield trend: {str(e)}",
        )


@router.get("/comparison/{crop_type}", response_model=CropYieldComparison)
async def compare_crop_yields(
    crop_type: str,
    year: int = Query(..., description="Year to compare"),
    country: Optional[str] = Query(None, description="Filter by country"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
):
    """
    Compare crop yields across different locations for a specific year.
    """
    try:
        # Build query filters
        filters = {
            "crop_type": crop_type.lower(),
            "year": year,
        }

        if country:
            filters["country"] = country.upper()

        # Get comparison data
        queryset = CropYield.objects.filter(**filters).order_by("-yield_value")[:limit]

        if not queryset.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {crop_type} in {year}",
            )

        comparisons = []
        yield_unit = None

        for rank, record in enumerate(queryset, 1):
            comparisons.append(
                {
                    "location": {
                        "country": record.country,
                        "state": record.state,
                    },
                    "year": record.year,
                    "yield": record.yield_value,
                    "rank": rank,
                    "source": record.source,
                }
            )
            yield_unit = record.yield_unit

        return CropYieldComparison(
            crop_type=crop_type, yield_unit=yield_unit, comparisons=comparisons
        )

    except Exception as e:
        logger.error(f"Error comparing crop yields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing crop yields: {str(e)}",
        )


@router.post("/filter", response_model=PaginatedResponse[CropYieldResponse])
async def filter_crop_yields(
    filter_params: CropYieldFilter,
    pagination: dict = Depends(get_pagination_params),
):
    """
    Filter crop yields with advanced filtering options.
    """
    try:
        queryset = CropYield.objects.all()

        # Apply filters
        if filter_params.year_start:
            queryset = queryset.filter(year__gte=filter_params.year_start)

        if filter_params.year_end:
            queryset = queryset.filter(year__lte=filter_params.year_end)

        if filter_params.crop_types:
            queryset = queryset.filter(
                crop_type__in=[ct.lower() for ct in filter_params.crop_types]
            )

        if filter_params.countries:
            queryset = queryset.filter(
                country__in=[c.upper() for c in filter_params.countries]
            )

        if filter_params.states:
            queryset = queryset.filter(
                state__in=[s.upper() for s in filter_params.states]
            )

        if filter_params.min_yield:
            queryset = queryset.filter(yield_value__gte=filter_params.min_yield)

        if filter_params.max_yield:
            queryset = queryset.filter(yield_value__lte=filter_params.max_yield)

        # Order by year (descending)
        queryset = queryset.order_by("-year")

        # Paginate results
        paginated = paginate_queryset(
            queryset, pagination["page"], pagination["page_size"]
        )

        # Convert to response models
        crop_yields = [
            CropYieldResponse.from_orm(crop_yield) for crop_yield in paginated["items"]
        ]

        return PaginatedResponse(
            data=crop_yields,
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
        logger.error(f"Error filtering crop yields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error filtering crop yields: {str(e)}",
        )
