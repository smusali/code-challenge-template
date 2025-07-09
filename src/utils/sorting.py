"""
Sorting utilities for the Weather Data Engineering API.

This module provides reusable sorting functionality including:
- Field validation for safe sorting
- Multi-field sorting support
- Context-aware field mapping
"""

import logging
from typing import Any

from django.db.models import QuerySet
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class SortField(BaseModel):
    """Single sort field specification."""

    field: str = Field(..., description="Field name to sort by", example="date")
    order: str = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort order (asc/desc)",
        example="asc",
    )

    @validator("field")
    def validate_field_name(cls, v):
        """Validate field name contains only safe characters."""
        if not v.replace("_", "").replace("__", "").isalnum():
            raise ValueError("Field name contains invalid characters")
        return v

    def to_django_order(self) -> str:
        """Convert to Django order_by format."""
        return self.field if self.order == "asc" else f"-{self.field}"

    class Config:
        json_schema_extra = {"example": {"field": "date", "order": "desc"}}


class SortParams(BaseModel):
    """Multi-field sorting parameters."""

    sort_by: str = Field(
        default="id", description="Primary field to sort by", example="date"
    )
    sort_order: str = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Primary sort order",
        example="desc",
    )
    secondary_sort: list[SortField] = Field(
        default_factory=list, description="Additional sort fields", max_items=5
    )

    @validator("sort_by")
    def validate_primary_field(cls, v):
        """Validate primary sort field."""
        if not v.replace("_", "").replace("__", "").isalnum():
            raise ValueError("Sort field contains invalid characters")
        return v

    def to_django_order_list(self) -> list[str]:
        """Convert to Django order_by list."""
        # Primary sort field
        primary = self.sort_by if self.sort_order == "asc" else f"-{self.sort_by}"
        order_list = [primary]

        # Secondary sort fields
        for field in self.secondary_sort:
            order_list.append(field.to_django_order())

        return order_list

    class Config:
        json_schema_extra = {
            "example": {
                "sort_by": "date",
                "sort_order": "desc",
                "secondary_sort": [{"field": "station_id", "order": "asc"}],
            }
        }


# Define allowed sort fields for each model context
ALLOWED_SORT_FIELDS = {
    "weather_station": {
        "id": "station_id",
        "station_id": "station_id",
        "name": "name",
        "state": "state",
        "latitude": "latitude",
        "longitude": "longitude",
        "elevation": "elevation",
        "created_at": "created_at",
        "updated_at": "updated_at",
    },
    "daily_weather": {
        "id": "id",
        "date": "date",
        "station": "station__station_id",
        "station_id": "station__station_id",
        "station_name": "station__name",
        "state": "station__state",
        "max_temp": "max_temp",
        "min_temp": "min_temp",
        "temperature": "max_temp",  # alias
        "precipitation": "precipitation",
        "created_at": "created_at",
        "updated_at": "updated_at",
    },
    "yearly_stats": {
        "id": "id",
        "year": "year",
        "station": "station__station_id",
        "station_id": "station__station_id",
        "station_name": "station__name",
        "state": "station__state",
        "avg_max_temp": "avg_max_temp",
        "avg_min_temp": "avg_min_temp",
        "max_temp": "max_temp",
        "min_temp": "min_temp",
        "total_precipitation": "total_precipitation",
        "avg_precipitation": "avg_precipitation",
        "max_precipitation": "max_precipitation",
        "total_records": "total_records",
        "completeness": "records_with_temp",  # alias for data completeness
        "created_at": "created_at",
        "updated_at": "updated_at",
    },
    "crop_yield": {
        "id": "id",
        "year": "year",
        "crop_type": "crop_type",
        "country": "country",
        "state": "state",
        "yield_value": "yield_value",
        "yield_unit": "yield_unit",
        "created_at": "created_at",
        "updated_at": "updated_at",
    },
}

# Default sort fields for each context
DEFAULT_SORT_FIELDS = {
    "weather_station": "station_id",
    "daily_weather": "date",
    "yearly_stats": "year",
    "crop_yield": "year",
}


def create_sort_params(
    sort_by: str = Query("id", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
) -> SortParams:
    """Dependency function to create sort parameters."""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


def validate_sort_fields(sort_params: SortParams, model_context: str) -> list[str]:
    """
    Validate and map sort fields for a specific model context.

    Args:
        sort_params: SortParams object with sort configuration
        model_context: Context for field validation ('daily_weather', 'weather_station', etc.)

    Returns:
        List of validated Django field names for order_by()

    Raises:
        HTTPException: If any sort field is invalid for the context
    """
    allowed_fields = ALLOWED_SORT_FIELDS.get(model_context, {})

    if not allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Sorting not supported for context: {model_context}",
        )

    validated_fields = []

    # Validate primary sort field
    if sort_params.sort_by not in allowed_fields:
        # Try to use default field if primary is invalid
        default_field = DEFAULT_SORT_FIELDS.get(model_context, "id")
        if default_field in allowed_fields:
            logger.warning(
                f"Invalid sort field '{sort_params.sort_by}' for {model_context}, "
                f"using default '{default_field}'"
            )
            mapped_field = allowed_fields[default_field]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort field '{sort_params.sort_by}' for {model_context}. "
                f"Allowed fields: {list(allowed_fields.keys())}",
            )
    else:
        mapped_field = allowed_fields[sort_params.sort_by]

    # Add primary field with order
    primary_field = (
        mapped_field if sort_params.sort_order == "asc" else f"-{mapped_field}"
    )
    validated_fields.append(primary_field)

    # Validate secondary sort fields
    for secondary in sort_params.secondary_sort:
        if secondary.field not in allowed_fields:
            logger.warning(
                f"Skipping invalid secondary sort field '{secondary.field}' for {model_context}"
            )
            continue

        mapped_secondary = allowed_fields[secondary.field]
        secondary_field = (
            mapped_secondary if secondary.order == "asc" else f"-{mapped_secondary}"
        )

        # Avoid duplicate sort fields
        if secondary_field not in validated_fields and mapped_secondary != mapped_field:
            validated_fields.append(secondary_field)

    return validated_fields


def apply_sorting(
    queryset: QuerySet,
    sort_params: SortParams,
    model_context: str,
    default_fallback: bool = True,
) -> QuerySet:
    """
    Apply sorting to a Django QuerySet with validation.

    Args:
        queryset: Django QuerySet to sort
        sort_params: SortParams object with sort configuration
        model_context: Context for field validation
        default_fallback: Whether to apply default sorting if validation fails

    Returns:
        Sorted QuerySet
    """
    try:
        validated_fields = validate_sort_fields(sort_params, model_context)
        return queryset.order_by(*validated_fields)

    except HTTPException:
        if default_fallback:
            # Apply default sorting on validation failure
            default_field = DEFAULT_SORT_FIELDS.get(model_context, "id")
            allowed_fields = ALLOWED_SORT_FIELDS.get(model_context, {})

            if default_field in allowed_fields:
                mapped_default = allowed_fields[default_field]
                logger.warning(
                    f"Applying default sort '{default_field}' for {model_context}"
                )
                return queryset.order_by(mapped_default)

        # Re-raise if no fallback or fallback fails
        raise


def get_available_sort_fields(model_context: str) -> dict[str, str]:
    """
    Get available sort fields for a model context.

    Args:
        model_context: Context to get fields for

    Returns:
        Dictionary mapping user-friendly field names to descriptions
    """
    field_descriptions = {
        "weather_station": {
            "id": "Station identifier",
            "station_id": "Station identifier",
            "name": "Station name",
            "state": "State code",
            "latitude": "Latitude coordinate",
            "longitude": "Longitude coordinate",
            "elevation": "Elevation in meters",
            "created_at": "Record creation date",
            "updated_at": "Record update date",
        },
        "daily_weather": {
            "id": "Record identifier",
            "date": "Observation date",
            "station": "Station identifier",
            "station_id": "Station identifier",
            "station_name": "Station name",
            "state": "State code",
            "max_temp": "Maximum temperature",
            "min_temp": "Minimum temperature",
            "temperature": "Maximum temperature (alias)",
            "precipitation": "Precipitation amount",
            "created_at": "Record creation date",
            "updated_at": "Record update date",
        },
        "yearly_stats": {
            "id": "Record identifier",
            "year": "Statistics year",
            "station": "Station identifier",
            "station_id": "Station identifier",
            "station_name": "Station name",
            "state": "State code",
            "avg_max_temp": "Average maximum temperature",
            "avg_min_temp": "Average minimum temperature",
            "max_temp": "Highest temperature recorded",
            "min_temp": "Lowest temperature recorded",
            "total_precipitation": "Total precipitation",
            "avg_precipitation": "Average daily precipitation",
            "max_precipitation": "Highest daily precipitation",
            "total_records": "Number of observations",
            "completeness": "Data completeness percentage",
            "created_at": "Record creation date",
            "updated_at": "Record update date",
        },
        "crop_yield": {
            "id": "Record identifier",
            "year": "Crop year",
            "crop_type": "Type of crop",
            "country": "Country code",
            "state": "State code",
            "yield_value": "Yield amount",
            "yield_unit": "Yield measurement unit",
            "created_at": "Record creation date",
            "updated_at": "Record update date",
        },
    }

    return field_descriptions.get(model_context, {})


def build_sort_response_metadata(
    sort_params: SortParams, model_context: str
) -> dict[str, Any]:
    """
    Build metadata about applied sorting for API responses.

    Args:
        sort_params: Applied sort parameters
        model_context: Model context used

    Returns:
        Dictionary with sort metadata
    """
    try:
        validated_fields = validate_sort_fields(sort_params, model_context)
        available_fields = list(ALLOWED_SORT_FIELDS.get(model_context, {}).keys())

        return {
            "applied_sort": {
                "primary_field": sort_params.sort_by,
                "primary_order": sort_params.sort_order,
                "secondary_fields": [
                    {"field": sf.field, "order": sf.order}
                    for sf in sort_params.secondary_sort
                ],
                "django_order_by": validated_fields,
            },
            "available_fields": available_fields,
            "default_field": DEFAULT_SORT_FIELDS.get(model_context, "id"),
        }

    except HTTPException as e:
        return {
            "error": str(e.detail),
            "available_fields": list(ALLOWED_SORT_FIELDS.get(model_context, {}).keys()),
            "default_field": DEFAULT_SORT_FIELDS.get(model_context, "id"),
        }


def create_multi_field_sort(field_configs: list[dict[str, str]]) -> SortParams:
    """
    Create SortParams with multiple fields from configuration.

    Args:
        field_configs: List of dicts with 'field' and 'order' keys

    Returns:
        SortParams object with configured fields

    Example:
        >>> configs = [
        ...     {"field": "date", "order": "desc"},
        ...     {"field": "station_id", "order": "asc"}
        ... ]
        >>> sort_params = create_multi_field_sort(configs)
    """
    if not field_configs:
        return SortParams()

    primary = field_configs[0]
    secondary_fields = []

    for config in field_configs[1:]:
        secondary_fields.append(
            SortField(field=config.get("field", "id"), order=config.get("order", "asc"))
        )

    return SortParams(
        sort_by=primary.get("field", "id"),
        sort_order=primary.get("order", "asc"),
        secondary_sort=secondary_fields,
    )
