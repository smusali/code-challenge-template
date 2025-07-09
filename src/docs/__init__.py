"""
Documentation utilities for the Weather Data Engineering API.

This package provides enhanced OpenAPI documentation features including:
- Custom OpenAPI schema generation
- Swagger UI customization
- Security documentation
- Comprehensive endpoint documentation
"""

from .openapi_config import get_openapi_config, get_openapi_tags
from .swagger_ui import get_swagger_ui_config

__all__ = [
    "get_openapi_config",
    "get_openapi_tags",
    "get_swagger_ui_config",
]
