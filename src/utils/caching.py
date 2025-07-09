"""
Caching utilities for ETag generation and cache control headers.

This module provides utilities for HTTP caching including:
- ETag generation based on response content
- Cache control headers for different endpoint types
- Conditional request handling
- Cache policy configuration
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import Request, Response


class CachePolicy(Enum):
    """Cache policy types for different endpoint categories."""

    NO_CACHE = "no_cache"  # Don't cache at all
    SHORT_CACHE = "short_cache"  # Cache for 5 minutes
    MEDIUM_CACHE = "medium_cache"  # Cache for 1 hour
    LONG_CACHE = "long_cache"  # Cache for 24 hours
    STATIC_CACHE = "static_cache"  # Cache for 30 days


class CacheConfig:
    """Configuration for cache policies."""

    CACHE_DURATIONS = {
        CachePolicy.NO_CACHE: 0,
        CachePolicy.SHORT_CACHE: 300,  # 5 minutes
        CachePolicy.MEDIUM_CACHE: 3600,  # 1 hour
        CachePolicy.LONG_CACHE: 86400,  # 24 hours
        CachePolicy.STATIC_CACHE: 2592000,  # 30 days
    }

    # Endpoint-specific cache policies
    ENDPOINT_POLICIES = {
        "/health": CachePolicy.NO_CACHE,
        "/info": CachePolicy.SHORT_CACHE,
        "/": CachePolicy.MEDIUM_CACHE,
        "/docs": CachePolicy.STATIC_CACHE,
        "/redoc": CachePolicy.STATIC_CACHE,
        "/openapi.json": CachePolicy.MEDIUM_CACHE,
        "/api/v1/weather/stations": CachePolicy.MEDIUM_CACHE,
        "/api/v1/weather/daily": CachePolicy.MEDIUM_CACHE,
        "/api/v1/crops": CachePolicy.MEDIUM_CACHE,
        "/api/v1/stats": CachePolicy.MEDIUM_CACHE,
        "/api/v2": CachePolicy.MEDIUM_CACHE,
        "/api/weather": CachePolicy.MEDIUM_CACHE,
        "/docs/api": CachePolicy.LONG_CACHE,
    }


def generate_etag(content: str | bytes | dict[str, Any]) -> str:
    """
    Generate ETag for response content.

    Args:
        content: Response content (string, bytes, or dict)

    Returns:
        ETag value as hex string
    """
    if isinstance(content, dict):
        # Convert dict to JSON string for consistent hashing
        content_str = json.dumps(content, sort_keys=True, default=str)
    elif isinstance(content, str):
        content_str = content
    elif isinstance(content, bytes):
        content_str = content.decode("utf-8")
    else:
        content_str = str(content)

    # Generate MD5 hash
    hash_object = hashlib.md5(content_str.encode("utf-8"), usedforsecurity=False)
    return f'"{hash_object.hexdigest()}"'


def get_cache_policy(path: str) -> CachePolicy:
    """
    Get cache policy for a given endpoint path.

    Args:
        path: Request path

    Returns:
        Cache policy enum value
    """
    # Check exact matches first
    if path in CacheConfig.ENDPOINT_POLICIES:
        return CacheConfig.ENDPOINT_POLICIES[path]

    # Check prefix matches
    for pattern, policy in CacheConfig.ENDPOINT_POLICIES.items():
        if path.startswith(pattern):
            return policy

    # Default policy for API endpoints
    if path.startswith("/api/"):
        return CachePolicy.MEDIUM_CACHE

    # Default policy for documentation
    if path.startswith("/docs/"):
        return CachePolicy.LONG_CACHE

    # Default policy
    return CachePolicy.SHORT_CACHE


def get_cache_control_header(policy: CachePolicy) -> str:
    """
    Get Cache-Control header value for a cache policy.

    Args:
        policy: Cache policy enum value

    Returns:
        Cache-Control header value
    """
    duration = CacheConfig.CACHE_DURATIONS[policy]

    if policy == CachePolicy.NO_CACHE:
        return "no-cache, no-store, must-revalidate"
    elif policy == CachePolicy.SHORT_CACHE:
        return f"public, max-age={duration}, must-revalidate"
    elif policy == CachePolicy.MEDIUM_CACHE:
        return f"public, max-age={duration}"
    elif policy == CachePolicy.LONG_CACHE:
        return f"public, max-age={duration}, immutable"
    elif policy == CachePolicy.STATIC_CACHE:
        return f"public, max-age={duration}, immutable"

    return "public, max-age=300"


def should_return_304(request: Request, etag: str) -> bool:
    """
    Check if we should return 304 Not Modified based on request headers.

    Args:
        request: FastAPI request object
        etag: Generated ETag value

    Returns:
        True if should return 304, False otherwise
    """
    # Check If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match:
        # Handle multiple ETags (comma-separated)
        etags = [tag.strip() for tag in if_none_match.split(",")]
        if "*" in etags or etag in etags:
            return True

    return False


def add_caching_headers(response: Response, content: Any, path: str) -> Response:
    """
    Add caching headers to response.

    Args:
        response: FastAPI response object
        content: Response content for ETag generation
        path: Request path

    Returns:
        Response with added caching headers
    """
    # Get cache policy
    policy = get_cache_policy(path)

    # Generate ETag
    etag = generate_etag(content)

    # Add headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = get_cache_control_header(policy)

    # Add Last-Modified header
    response.headers["Last-Modified"] = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    # Add Vary header for content negotiation
    response.headers["Vary"] = "Accept-Encoding, Accept"

    return response


def create_304_response(etag: str) -> Response:
    """
    Create 304 Not Modified response.

    Args:
        etag: ETag value

    Returns:
        304 response with appropriate headers
    """
    response = Response(status_code=304)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["Last-Modified"] = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    return response


def is_cacheable_method(method: str) -> bool:
    """
    Check if HTTP method is cacheable.

    Args:
        method: HTTP method

    Returns:
        True if method is cacheable, False otherwise
    """
    return method.upper() in ["GET", "HEAD"]


def is_cacheable_status(status_code: int) -> bool:
    """
    Check if HTTP status code is cacheable.

    Args:
        status_code: HTTP status code

    Returns:
        True if status code is cacheable, False otherwise
    """
    return status_code in [200, 203, 300, 301, 410]


def get_cache_key(request: Request) -> str:
    """
    Generate cache key for request.

    Args:
        request: FastAPI request object

    Returns:
        Cache key string
    """
    # Create cache key from path and query parameters
    key_parts = [request.url.path, str(sorted(request.query_params.items()))]

    # Add relevant headers that affect caching
    accept_encoding = request.headers.get("Accept-Encoding", "")
    if accept_encoding:
        key_parts.append(f"accept-encoding:{accept_encoding}")

    cache_key = "|".join(key_parts)
    return hashlib.md5(cache_key.encode(), usedforsecurity=False).hexdigest()
