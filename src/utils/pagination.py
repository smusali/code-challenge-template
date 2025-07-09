"""
Pagination utilities for the Weather Data Engineering API.

This module provides reusable pagination functionality including:
- Page-based pagination (traditional page numbers)
- Cursor-based pagination (for large datasets)
- Pagination metadata and response wrappers
"""

import base64
import logging
from typing import Any, Generic, TypeVar
from urllib.parse import urlencode

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import QuerySet
from fastapi import Query, Request
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard page-based pagination parameters."""

    page: int = Field(
        default=1, ge=1, le=10000, description="Page number (1-based)", example=1
    )
    page_size: int = Field(
        default=20, ge=1, le=1000, description="Number of items per page", example=20
    )

    @validator("page")
    def validate_page(cls, v):
        """Validate page number."""
        if v < 1:
            raise ValueError("Page number must be at least 1")
        if v > 10000:
            raise ValueError("Page number cannot exceed 10000")
        return v

    @validator("page_size")
    def validate_page_size(cls, v):
        """Validate page size."""
        if v < 1:
            raise ValueError("Page size must be at least 1")
        if v > 1000:
            raise ValueError("Page size cannot exceed 1000")
        return v


class PaginationMeta(BaseModel):
    """Pagination metadata for page-based pagination."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_page: int | None = Field(None, description="Next page number if available")
    previous_page: int | None = Field(
        None, description="Previous page number if available"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 2,
                "page_size": 20,
                "total_items": 156,
                "total_pages": 8,
                "has_next": True,
                "has_previous": True,
                "next_page": 3,
                "previous_page": 1,
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    links: dict[str, str | None] = Field(
        default_factory=dict, description="Navigation links"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "items": ["..."],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 156,
                    "total_pages": 8,
                    "has_next": True,
                    "has_previous": False,
                    "next_page": 2,
                    "previous_page": None,
                },
                "links": {
                    "self": "/api/endpoint?page=1&page_size=20",
                    "next": "/api/endpoint?page=2&page_size=20",
                    "previous": None,
                    "first": "/api/endpoint?page=1&page_size=20",
                    "last": "/api/endpoint?page=8&page_size=20",
                },
            }
        }


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters for large datasets."""

    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of items to return",
        example=50,
    )
    cursor: str | None = Field(
        default=None,
        description="Pagination cursor for next page",
        example="eyJpZCI6MTIzLCJkYXRlIjoiMjAyNC0wMS0xNSJ9",  # pragma: allowlist secret
    )
    order: str = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort order for cursor pagination",
        example="asc",
    )

    @validator("limit")
    def validate_limit(cls, v):
        """Validate limit."""
        if v < 1:
            raise ValueError("Limit must be at least 1")
        if v > 1000:
            raise ValueError("Limit cannot exceed 1000")
        return v


class CursorPaginationMeta(BaseModel):
    """Pagination metadata for cursor-based pagination."""

    limit: int = Field(..., description="Maximum items per page")
    has_next: bool = Field(..., description="Whether there are more items")
    has_previous: bool = Field(..., description="Whether there are previous items")
    next_cursor: str | None = Field(None, description="Cursor for next page")
    previous_cursor: str | None = Field(None, description="Cursor for previous page")
    total_items: int | None = Field(None, description="Total items (if available)")

    class Config:
        json_schema_extra = {
            "example": {
                "limit": 50,
                "has_next": True,
                "has_previous": False,
                "next_cursor": "eyJpZCI6MTIzLCJkYXRlIjoiMjAyNC0wMS0xNSJ9",  # pragma: allowlist secret
                "previous_cursor": None,
                "total_items": None,
            }
        }


def create_pagination_params(
    page: int = Query(1, ge=1, le=10000, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
) -> PaginationParams:
    """Dependency function to create pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)


def create_cursor_pagination_params(
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    cursor: str | None = Query(None, description="Pagination cursor"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
) -> CursorPaginationParams:
    """Dependency function to create cursor pagination parameters."""
    return CursorPaginationParams(limit=limit, cursor=cursor, order=order)


def paginate_queryset(
    queryset: QuerySet,
    pagination: PaginationParams,
    request: Request | None = None,
) -> PaginatedResponse[Any]:
    """
    Paginate a Django QuerySet using page-based pagination.

    Args:
        queryset: Django QuerySet to paginate
        pagination: Pagination parameters
        request: FastAPI request object (for link generation)

    Returns:
        PaginatedResponse with items and pagination metadata
    """
    try:
        paginator = Paginator(queryset, pagination.page_size)
        page_obj = paginator.get_page(pagination.page)

        # Handle invalid page numbers gracefully
        if pagination.page > paginator.num_pages and paginator.num_pages > 0:
            page_obj = paginator.get_page(paginator.num_pages)
            actual_page = paginator.num_pages
        else:
            actual_page = pagination.page

    except (PageNotAnInteger, EmptyPage):
        # Return empty result for invalid pages
        page_obj = paginator.get_page(1)
        actual_page = 1

    # Create pagination metadata
    pagination_meta = PaginationMeta(
        page=actual_page,
        page_size=pagination.page_size,
        total_items=paginator.count,
        total_pages=paginator.num_pages,
        has_next=page_obj.has_next(),
        has_previous=page_obj.has_previous(),
        next_page=page_obj.next_page_number() if page_obj.has_next() else None,
        previous_page=page_obj.previous_page_number()
        if page_obj.has_previous()
        else None,
    )

    # Generate navigation links if request is provided
    links = {}
    if request:
        base_url = str(request.url).split("?")[0]
        query_params = dict(request.query_params)

        # Self link
        query_params.update({"page": actual_page, "page_size": pagination.page_size})
        links["self"] = f"{base_url}?{urlencode(query_params)}"

        # Next link
        if pagination_meta.has_next:
            query_params.update({"page": pagination_meta.next_page})
            links["next"] = f"{base_url}?{urlencode(query_params)}"
        else:
            links["next"] = None

        # Previous link
        if pagination_meta.has_previous:
            query_params.update({"page": pagination_meta.previous_page})
            links["previous"] = f"{base_url}?{urlencode(query_params)}"
        else:
            links["previous"] = None

        # First and last links
        query_params.update({"page": 1})
        links["first"] = f"{base_url}?{urlencode(query_params)}"

        query_params.update({"page": pagination_meta.total_pages})
        links["last"] = f"{base_url}?{urlencode(query_params)}"

    return PaginatedResponse(
        items=list(page_obj.object_list),
        pagination=pagination_meta,
        links=links,
    )


def encode_cursor(data: dict) -> str:
    """Encode cursor data to base64 string."""
    import json

    json_str = json.dumps(data, default=str, sort_keys=True)
    return base64.b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode cursor from base64 string."""
    import json

    try:
        json_str = base64.b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Invalid cursor format: {e}")
        return {}


def cursor_paginate_queryset(
    queryset: QuerySet,
    pagination: CursorPaginationParams,
    cursor_field: str = "id",
    request: Request | None = None,
) -> dict[str, Any]:
    """
    Paginate a Django QuerySet using cursor-based pagination.

    Args:
        queryset: Django QuerySet to paginate
        pagination: Cursor pagination parameters
        cursor_field: Field to use for cursor (default: "id")
        request: FastAPI request object (for link generation)

    Returns:
        Dictionary with items and cursor pagination metadata
    """
    # Apply cursor filtering if provided
    if pagination.cursor:
        cursor_data = decode_cursor(pagination.cursor)
        if cursor_data and cursor_field in cursor_data:
            cursor_value = cursor_data[cursor_field]

            if pagination.order == "asc":
                queryset = queryset.filter(**{f"{cursor_field}__gt": cursor_value})
            else:
                queryset = queryset.filter(**{f"{cursor_field}__lt": cursor_value})

    # Apply ordering
    order_field = cursor_field if pagination.order == "asc" else f"-{cursor_field}"
    queryset = queryset.order_by(order_field)

    # Fetch one extra item to determine if there's a next page
    items = list(queryset[: pagination.limit + 1])
    has_next = len(items) > pagination.limit

    # Remove the extra item
    if has_next:
        items = items[: pagination.limit]

    # Generate cursors
    next_cursor = None
    if has_next and items:
        last_item = items[-1]
        cursor_value = getattr(last_item, cursor_field)
        next_cursor = encode_cursor({cursor_field: cursor_value})

    # For previous cursor, we would need to implement reverse pagination
    # This is more complex and often not needed for real-time data
    previous_cursor = None

    pagination_meta = CursorPaginationMeta(
        limit=pagination.limit,
        has_next=has_next,
        has_previous=bool(pagination.cursor),  # Simplified
        next_cursor=next_cursor,
        previous_cursor=previous_cursor,
    )

    # Generate navigation links if request is provided
    links = {}
    if request:
        base_url = str(request.url).split("?")[0]
        query_params = dict(request.query_params)

        # Self link
        links["self"] = str(request.url)

        # Next link
        if next_cursor:
            query_params.update({"cursor": next_cursor, "limit": pagination.limit})
            links["next"] = f"{base_url}?{urlencode(query_params)}"
        else:
            links["next"] = None

    return {
        "items": items,
        "pagination": pagination_meta,
        "links": links,
    }


def get_pagination_info(queryset: QuerySet, page_size: int) -> dict[str, Any]:
    """
    Get pagination information for a queryset without executing it.

    Args:
        queryset: Django QuerySet
        page_size: Items per page

    Returns:
        Dictionary with pagination information
    """
    total_items = queryset.count()
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "page_size": page_size,
    }
