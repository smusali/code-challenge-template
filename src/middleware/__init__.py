"""
Middleware package for the Weather Data Engineering API.

This package contains custom middleware for:
- ETag generation and conditional request handling
- HTTP caching headers
- Request/response processing
"""

from .etag_middleware import ETagMiddleware, create_etag_middleware

__all__ = ["ETagMiddleware", "create_etag_middleware"]
