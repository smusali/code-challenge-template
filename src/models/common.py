"""
Common Pydantic models for shared response structures.

This module contains reusable Pydantic models for pagination,
error handling, and common response patterns.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Type variable for generic pagination
T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    detail: str | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="When the error occurred")
    path: str | None = Field(None, description="API path where error occurred")
    request_id: str | None = Field(None, description="Request ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Invalid input data",
                "detail": "Field 'station_id' is required",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/api/v1/weather/stations",
                "request_id": "req_123456789",
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata model."""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_previous": False,
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""

    data: list[T] = Field(..., description="List of items for current page")
    meta: PaginationMeta = Field(..., description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "data": ["List of items based on endpoint"],
                "meta": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_previous": False,
                },
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(..., description="Timestamp of health check")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Service uptime in seconds")
    environment: str = Field(..., description="Environment (development/production)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0",
                "uptime": 3600.0,
                "environment": "development",
            }
        }


class SystemStatusResponse(BaseModel):
    """System status response model."""

    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Status check timestamp")
    services: dict[str, Any] = Field(..., description="External services status")
    system: dict[str, Any] = Field(..., description="System metrics")
    database: dict[str, Any] = Field(..., description="Database status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "services": {
                    "redis": {"status": "healthy"},
                },
                "system": {
                    "cpu": {"percent": 25.5},
                    "memory": {"percent": 60.2},
                },
                "database": {
                    "status": "healthy",
                    "response_time_ms": 15.2,
                },
            }
        }


class BulkOperationResponse(BaseModel):
    """Bulk operation response model."""

    success: bool = Field(..., description="Whether the operation was successful")
    processed: int = Field(..., description="Number of items processed")
    created: int = Field(..., description="Number of items created")
    updated: int = Field(..., description="Number of items updated")
    skipped: int = Field(..., description="Number of items skipped")
    errors: list[str] = Field(..., description="List of errors encountered")
    timestamp: datetime = Field(..., description="Operation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "processed": 100,
                "created": 80,
                "updated": 20,
                "skipped": 0,
                "errors": [],
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class FilterParams(BaseModel):
    """Common filter parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: str | None = Field(None, description="Search term")
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_order: str | None = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order (asc/desc)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "search": "USC00",
                "sort_by": "created_at",
                "sort_order": "desc",
            }
        }


class DateRangeFilter(BaseModel):
    """Date range filter for time-based queries."""

    start_date: datetime | None = Field(None, description="Start date (inclusive)")
    end_date: datetime | None = Field(None, description="End date (inclusive)")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response model."""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Any | None = Field(None, description="Optional response data")
    timestamp: datetime = Field(..., description="Operation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": 123},
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class ValidationError(BaseModel):
    """Validation error detail model."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any | None = Field(None, description="Value that failed validation")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "station_id",
                "message": "Station ID must be in format USC00XXXXXX",
                "value": "INVALID123",
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""

    error: str = Field("validation_error", description="Error type")
    message: str = Field(..., description="Main error message")
    errors: list[ValidationError] = Field(..., description="List of validation errors")
    timestamp: datetime = Field(..., description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Request validation failed",
                "errors": [
                    {
                        "field": "station_id",
                        "message": "Station ID is required",
                        "value": None,
                    }
                ],
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
