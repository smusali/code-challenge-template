"""
ETag middleware for handling conditional requests and caching headers.

This middleware provides:
- Automatic ETag generation for cacheable responses
- Conditional request handling (If-None-Match, If-Modified-Since)
- Cache control headers based on endpoint policies
- 304 Not Modified responses when appropriate
"""

import json
import logging
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.caching import (
    add_caching_headers,
    create_304_response,
    generate_etag,
    is_cacheable_method,
    is_cacheable_status,
    should_return_304,
)

logger = logging.getLogger(__name__)


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling ETags and conditional requests.

    This middleware:
    - Generates ETags for cacheable responses
    - Handles conditional requests (If-None-Match)
    - Adds appropriate cache control headers
    - Returns 304 Not Modified when content hasn't changed
    """

    def __init__(self, app, enable_caching: bool = True):
        """
        Initialize ETag middleware.

        Args:
            app: FastAPI application
            enable_caching: Whether to enable caching functionality
        """
        super().__init__(app)
        self.enable_caching = enable_caching

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add ETag/caching headers to response.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response with ETag and caching headers
        """
        # Skip processing if caching is disabled
        if not self.enable_caching:
            return await call_next(request)

        # Skip non-cacheable methods
        if not is_cacheable_method(request.method):
            return await call_next(request)

        # Process the request
        response = await call_next(request)

        # Skip non-cacheable status codes
        if not is_cacheable_status(response.status_code):
            return response

        # Get response content for ETag generation
        content = await self._get_response_content(response)

        if content is None:
            return response

        # Generate ETag
        etag = generate_etag(content)

        # Check if client has matching ETag
        if should_return_304(request, etag):
            logger.info(f"Returning 304 Not Modified for {request.url.path}")
            return create_304_response(etag)

        # Add caching headers to response
        response = add_caching_headers(response, content, request.url.path)

        logger.debug(f"Added ETag {etag} to response for {request.url.path}")

        return response

    async def _get_response_content(self, response: Response) -> dict | str | None:
        """
        Extract content from response for ETag generation.

        Args:
            response: FastAPI response object

        Returns:
            Response content as dict, string, or None if extraction fails
        """
        try:
            # Handle JSONResponse
            if isinstance(response, JSONResponse):
                # Access the body directly for JSONResponse
                if hasattr(response, "body") and response.body:
                    return json.loads(response.body.decode("utf-8"))
                return None

            # Handle regular Response with body
            if hasattr(response, "body") and response.body:
                body = response.body
                if isinstance(body, bytes):
                    body_str = body.decode("utf-8")
                    try:
                        # Try to parse as JSON
                        return json.loads(body_str)
                    except json.JSONDecodeError:
                        # Return as string if not JSON
                        return body_str
                return str(body)

            # Handle streaming responses (skip ETag for these)
            if hasattr(response, "media_type") and response.media_type:
                if (
                    response.media_type.startswith("text/")
                    or response.media_type == "application/json"
                ):
                    # For text responses, we could theoretically read the stream,
                    # but for simplicity, we'll skip ETag for streaming responses
                    return None

            return None

        except Exception as e:
            logger.warning(f"Failed to extract response content for ETag: {e}")
            return None

    def is_conditional_request(self, request: Request) -> bool:
        """
        Check if request is a conditional request.

        Args:
            request: FastAPI request object

        Returns:
            True if request has conditional headers, False otherwise
        """
        conditional_headers = [
            "If-None-Match",
            "If-Modified-Since",
            "If-Match",
            "If-Unmodified-Since",
        ]

        return any(header in request.headers for header in conditional_headers)


def create_etag_middleware(enable_caching: bool = True) -> ETagMiddleware:
    """
    Create ETag middleware instance.

    Args:
        enable_caching: Whether to enable caching functionality

    Returns:
        ETag middleware instance
    """
    return ETagMiddleware(enable_caching=enable_caching)
