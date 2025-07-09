"""
Filtering utilities for the Weather Data Engineering API.

This module provides reusable filtering functionality including:
- Date range filtering
- Numeric range filtering
- Text search filtering
- Advanced query building with Q objects
"""

import logging
from datetime import date
from typing import Any

from django.db.models import Q, QuerySet
from fastapi import Query
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class DateRangeFilter(BaseModel):
    """Date range filter parameters."""

    start_date: date | None = Field(
        None, description="Start date (inclusive)", example="2020-01-01"
    )
    end_date: date | None = Field(
        None, description="End date (inclusive)", example="2024-12-31"
    )

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date."""
        if v and values.get("start_date") and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    def apply_to_queryset(
        self, queryset: QuerySet, field_name: str = "date"
    ) -> QuerySet:
        """Apply date range filter to queryset."""
        if self.start_date:
            queryset = queryset.filter(**{f"{field_name}__gte": self.start_date})
        if self.end_date:
            queryset = queryset.filter(**{f"{field_name}__lte": self.end_date})
        return queryset

    def to_q_object(self, field_name: str = "date") -> Q:
        """Convert to Django Q object."""
        q = Q()
        if self.start_date:
            q &= Q(**{f"{field_name}__gte": self.start_date})
        if self.end_date:
            q &= Q(**{f"{field_name}__lte": self.end_date})
        return q

    class Config:
        json_schema_extra = {
            "example": {"start_date": "2020-01-01", "end_date": "2024-12-31"}
        }


class NumericRangeFilter(BaseModel):
    """Numeric range filter parameters."""

    min_value: float | None = Field(
        None, description="Minimum value (inclusive)", example=0.0
    )
    max_value: float | None = Field(
        None, description="Maximum value (inclusive)", example=100.0
    )

    @validator("max_value")
    def validate_range(cls, v, values):
        """Validate that max_value is greater than min_value."""
        if (
            v is not None
            and values.get("min_value") is not None
            and v < values["min_value"]
        ):
            raise ValueError("Maximum value must be greater than minimum value")
        return v

    def apply_to_queryset(self, queryset: QuerySet, field_name: str) -> QuerySet:
        """Apply numeric range filter to queryset."""
        if self.min_value is not None:
            queryset = queryset.filter(**{f"{field_name}__gte": self.min_value})
        if self.max_value is not None:
            queryset = queryset.filter(**{f"{field_name}__lte": self.max_value})
        return queryset

    def to_q_object(self, field_name: str) -> Q:
        """Convert to Django Q object."""
        q = Q()
        if self.min_value is not None:
            q &= Q(**{f"{field_name}__gte": self.min_value})
        if self.max_value is not None:
            q &= Q(**{f"{field_name}__lte": self.max_value})
        return q

    class Config:
        json_schema_extra = {"example": {"min_value": 0.0, "max_value": 100.0}}


class TextSearchFilter(BaseModel):
    """Text search filter parameters."""

    search: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Search term for text fields",
        example="Chicago",
    )
    search_fields: list[str] = Field(
        default_factory=list,
        description="Fields to search in (if not specified, uses default fields)",
        example=["name", "station_id"],
    )
    case_sensitive: bool = Field(
        False, description="Whether search should be case sensitive", example=False
    )
    exact_match: bool = Field(
        False,
        description="Whether to use exact match instead of contains",
        example=False,
    )

    def apply_to_queryset(
        self, queryset: QuerySet, default_fields: list[str] | None = None
    ) -> QuerySet:
        """Apply text search filter to queryset."""
        if not self.search:
            return queryset

        search_fields = self.search_fields or default_fields or []
        if not search_fields:
            return queryset

        # Build Q object for search across multiple fields
        search_q = Q()

        for field in search_fields:
            if self.exact_match:
                if self.case_sensitive:
                    search_q |= Q(**{field: self.search})
                else:
                    search_q |= Q(**{f"{field}__iexact": self.search})
            else:
                if self.case_sensitive:
                    search_q |= Q(**{f"{field}__contains": self.search})
                else:
                    search_q |= Q(**{f"{field}__icontains": self.search})

        return queryset.filter(search_q)

    def to_q_object(self, default_fields: list[str] | None = None) -> Q:
        """Convert to Django Q object."""
        if not self.search:
            return Q()

        search_fields = self.search_fields or default_fields or []
        if not search_fields:
            return Q()

        search_q = Q()
        for field in search_fields:
            if self.exact_match:
                if self.case_sensitive:
                    search_q |= Q(**{field: self.search})
                else:
                    search_q |= Q(**{f"{field}__iexact": self.search})
            else:
                if self.case_sensitive:
                    search_q |= Q(**{f"{field}__contains": self.search})
                else:
                    search_q |= Q(**{f"{field}__icontains": self.search})

        return search_q

    class Config:
        json_schema_extra = {
            "example": {
                "search": "Chicago",
                "search_fields": ["name", "station_id"],
                "case_sensitive": False,
                "exact_match": False,
            }
        }


class StateFilter(BaseModel):
    """State/location filter parameters."""

    states: list[str] = Field(
        default_factory=list,
        description="List of state codes to filter by",
        example=["IL", "IA", "WI"],
    )
    exclude_states: list[str] = Field(
        default_factory=list,
        description="List of state codes to exclude",
        example=["AK", "HI"],
    )

    @validator("states", "exclude_states")
    def validate_state_codes(cls, v):
        """Validate state codes are 2-character uppercase."""
        for state in v:
            if not isinstance(state, str) or len(state) != 2:
                raise ValueError("State codes must be 2-character strings")
            if not state.isupper():
                raise ValueError("State codes must be uppercase")
        return v

    def apply_to_queryset(
        self, queryset: QuerySet, field_name: str = "state"
    ) -> QuerySet:
        """Apply state filter to queryset."""
        if self.states:
            queryset = queryset.filter(**{f"{field_name}__in": self.states})
        if self.exclude_states:
            queryset = queryset.exclude(**{f"{field_name}__in": self.exclude_states})
        return queryset

    def to_q_object(self, field_name: str = "state") -> Q:
        """Convert to Django Q object."""
        q = Q()
        if self.states:
            q &= Q(**{f"{field_name}__in": self.states})
        if self.exclude_states:
            q &= ~Q(**{f"{field_name}__in": self.exclude_states})
        return q

    class Config:
        json_schema_extra = {
            "example": {"states": ["IL", "IA", "WI"], "exclude_states": ["AK", "HI"]}
        }


class FilterParams(BaseModel):
    """Combined filter parameters for weather data."""

    date_range: DateRangeFilter | None = None
    temperature_range: NumericRangeFilter | None = None
    precipitation_range: NumericRangeFilter | None = None
    search: TextSearchFilter | None = None
    location: StateFilter | None = None

    # Additional filters
    has_temperature: bool | None = Field(
        None, description="Filter records that have temperature data", example=True
    )
    has_precipitation: bool | None = Field(
        None, description="Filter records that have precipitation data", example=True
    )
    year: int | None = Field(
        None, ge=1800, le=2100, description="Filter by specific year", example=2023
    )
    month: int | None = Field(
        None, ge=1, le=12, description="Filter by specific month (1-12)", example=6
    )

    class Config:
        json_schema_extra = {
            "example": {
                "date_range": {"start_date": "2020-01-01", "end_date": "2024-12-31"},
                "temperature_range": {"min_value": -10.0, "max_value": 40.0},
                "precipitation_range": {"min_value": 0.0, "max_value": 100.0},
                "search": {
                    "search": "Chicago",
                    "search_fields": ["name", "station_id"],
                },
                "location": {"states": ["IL", "IA"]},
                "has_temperature": True,
                "year": 2023,
            }
        }


def create_date_range_filter(
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
) -> DateRangeFilter:
    """Dependency function to create date range filter."""
    return DateRangeFilter(start_date=start_date, end_date=end_date)


def create_numeric_range_filter(
    min_value: float | None = Query(None, description="Minimum value"),
    max_value: float | None = Query(None, description="Maximum value"),
) -> NumericRangeFilter:
    """Dependency function to create numeric range filter."""
    return NumericRangeFilter(min_value=min_value, max_value=max_value)


def create_text_search_filter(
    search: str | None = Query(
        None, min_length=1, max_length=200, description="Search term"
    ),
    case_sensitive: bool = Query(False, description="Case sensitive search"),
    exact_match: bool = Query(False, description="Exact match search"),
) -> TextSearchFilter:
    """Dependency function to create text search filter."""
    return TextSearchFilter(
        search=search, case_sensitive=case_sensitive, exact_match=exact_match
    )


def create_state_filter(
    states: list[str] = Query(
        default_factory=list, description="State codes to include"
    ),
    exclude_states: list[str] = Query(
        default_factory=list, description="State codes to exclude"
    ),
) -> StateFilter:
    """Dependency function to create state filter."""
    return StateFilter(states=states, exclude_states=exclude_states)


def apply_filters(
    queryset: QuerySet, filters: FilterParams, model_context: str = "daily_weather"
) -> QuerySet:
    """
    Apply all filters to a queryset based on model context.

    Args:
        queryset: Django QuerySet to filter
        filters: FilterParams object with all filter criteria
        model_context: Context for field mapping ('daily_weather', 'weather_station', etc.)

    Returns:
        Filtered QuerySet
    """
    # Define field mappings for different model contexts
    field_mappings = {
        "daily_weather": {
            "date": "date",
            "temperature": "max_temp",  # Can be customized
            "precipitation": "precipitation",
            "state": "station__state",
        },
        "weather_station": {
            "state": "state",
            "search_fields": ["name", "station_id"],
        },
        "yearly_stats": {
            "temperature": "avg_max_temp",
            "precipitation": "total_precipitation",
            "state": "station__state",
            "year": "year",
        },
    }

    context_fields = field_mappings.get(model_context, {})

    # Apply date range filter
    if filters.date_range:
        date_field = context_fields.get("date", "date")
        queryset = filters.date_range.apply_to_queryset(queryset, date_field)

    # Apply temperature range filter
    if filters.temperature_range:
        temp_field = context_fields.get("temperature", "max_temp")
        queryset = filters.temperature_range.apply_to_queryset(queryset, temp_field)

    # Apply precipitation range filter
    if filters.precipitation_range:
        precip_field = context_fields.get("precipitation", "precipitation")
        queryset = filters.precipitation_range.apply_to_queryset(queryset, precip_field)

    # Apply text search filter
    if filters.search:
        default_search_fields = context_fields.get("search_fields", ["name"])
        queryset = filters.search.apply_to_queryset(queryset, default_search_fields)

    # Apply location filter
    if filters.location:
        state_field = context_fields.get("state", "state")
        queryset = filters.location.apply_to_queryset(queryset, state_field)

    # Apply additional filters
    if filters.has_temperature is not None:
        temp_field = context_fields.get("temperature", "max_temp")
        if filters.has_temperature:
            queryset = queryset.filter(**{f"{temp_field}__isnull": False})
        else:
            queryset = queryset.filter(**{f"{temp_field}__isnull": True})

    if filters.has_precipitation is not None:
        precip_field = context_fields.get("precipitation", "precipitation")
        if filters.has_precipitation:
            queryset = queryset.filter(**{f"{precip_field}__isnull": False})
        else:
            queryset = queryset.filter(**{f"{precip_field}__isnull": True})

    if filters.year is not None:
        if "year" in context_fields:
            # For yearly stats model
            queryset = queryset.filter(**{context_fields["year"]: filters.year})
        else:
            # For date-based models
            date_field = context_fields.get("date", "date")
            queryset = queryset.filter(**{f"{date_field}__year": filters.year})

    if filters.month is not None:
        date_field = context_fields.get("date", "date")
        queryset = queryset.filter(**{f"{date_field}__month": filters.month})

    return queryset


def build_filter_q(filters: FilterParams, model_context: str = "daily_weather") -> Q:
    """
    Build a Django Q object from filter parameters.

    Args:
        filters: FilterParams object with all filter criteria
        model_context: Context for field mapping

    Returns:
        Django Q object representing all filters
    """
    # This is similar to apply_filters but returns a Q object
    # Useful for more complex query building

    field_mappings = {
        "daily_weather": {
            "date": "date",
            "temperature": "max_temp",
            "precipitation": "precipitation",
            "state": "station__state",
        },
        "weather_station": {
            "state": "state",
            "search_fields": ["name", "station_id"],
        },
        "yearly_stats": {
            "temperature": "avg_max_temp",
            "precipitation": "total_precipitation",
            "state": "station__state",
            "year": "year",
        },
    }

    context_fields = field_mappings.get(model_context, {})
    combined_q = Q()

    # Build Q objects for each filter
    if filters.date_range:
        date_field = context_fields.get("date", "date")
        combined_q &= filters.date_range.to_q_object(date_field)

    if filters.temperature_range:
        temp_field = context_fields.get("temperature", "max_temp")
        combined_q &= filters.temperature_range.to_q_object(temp_field)

    if filters.precipitation_range:
        precip_field = context_fields.get("precipitation", "precipitation")
        combined_q &= filters.precipitation_range.to_q_object(precip_field)

    if filters.search:
        default_search_fields = context_fields.get("search_fields", ["name"])
        combined_q &= filters.search.to_q_object(default_search_fields)

    if filters.location:
        state_field = context_fields.get("state", "state")
        combined_q &= filters.location.to_q_object(state_field)

    # Add additional Q filters
    if filters.has_temperature is not None:
        temp_field = context_fields.get("temperature", "max_temp")
        if filters.has_temperature:
            combined_q &= Q(**{f"{temp_field}__isnull": False})
        else:
            combined_q &= Q(**{f"{temp_field}__isnull": True})

    if filters.has_precipitation is not None:
        precip_field = context_fields.get("precipitation", "precipitation")
        if filters.has_precipitation:
            combined_q &= Q(**{f"{precip_field}__isnull": False})
        else:
            combined_q &= Q(**{f"{precip_field}__isnull": True})

    if filters.year is not None:
        if "year" in context_fields:
            combined_q &= Q(**{context_fields["year"]: filters.year})
        else:
            date_field = context_fields.get("date", "date")
            combined_q &= Q(**{f"{date_field}__year": filters.year})

    if filters.month is not None:
        date_field = context_fields.get("date", "date")
        combined_q &= Q(**{f"{date_field}__month": filters.month})

    return combined_q


def validate_filter_compatibility(filters: FilterParams) -> dict[str, Any]:
    """
    Validate filter parameter combinations and return any warnings or errors.

    Args:
        filters: FilterParams object to validate

    Returns:
        Dictionary with validation results
    """
    warnings = []
    errors = []

    # Check for conflicting date filters
    if filters.date_range and (filters.year or filters.month):
        warnings.append(
            "Using both date_range and year/month filters may produce unexpected results"
        )

    # Check for overly restrictive filters
    if (
        filters.temperature_range
        and filters.temperature_range.min_value is not None
        and filters.temperature_range.max_value is not None
    ):
        temp_range = (
            filters.temperature_range.max_value - filters.temperature_range.min_value
        )
        if temp_range < 1:
            warnings.append("Very narrow temperature range may return few results")

    # Check for logical impossibilities
    if filters.has_temperature is False and filters.temperature_range:
        errors.append(
            "Cannot filter by temperature range when has_temperature is False"
        )

    if filters.has_precipitation is False and filters.precipitation_range:
        errors.append(
            "Cannot filter by precipitation range when has_precipitation is False"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
