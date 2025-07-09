"""
FastAPI Application for Weather Data Engineering API.

This application provides a RESTful API for weather data management and analysis,
integrating with Django ORM for database operations.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import django
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Add the project root to Python path for Django imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")

try:
    django.setup()
except ImproperlyConfigured as e:
    logging.error(f"Django configuration error: {e}")
    sys.exit(1)

from src.config import settings  # noqa: E402
from src.routers import (  # noqa: E402
    crops,
    docs,
    filtered_endpoints,
    health,
    simple_weather,
    stats,
    weather,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown operations.
    """
    # Startup operations
    logging.info("Starting Weather Data Engineering API...")

    # Verify Django database connection
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        logging.info("Django database connection verified")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise

    # Log application configuration
    logging.info(f"API running in {'DEBUG' if settings.debug else 'PRODUCTION'} mode")
    logging.info(f"Database: {django_settings.DATABASES['default']['NAME']}")
    logging.info(f"Allowed hosts: {django_settings.ALLOWED_HOSTS}")

    yield

    # Shutdown operations
    logging.info("Shutting down Weather Data Engineering API...")


# Import documentation configuration
from src.docs.openapi_config import get_openapi_config, get_openapi_tags  # noqa: E402
from src.docs.swagger_ui import create_custom_openapi_schema  # noqa: E402

# Get enhanced OpenAPI configuration
openapi_config = get_openapi_config()

# FastAPI application instance with enhanced documentation
app = FastAPI(
    title=openapi_config["title"],
    description=openapi_config["description"],
    version=openapi_config["version"],
    contact=openapi_config.get("contact"),
    license_info=openapi_config.get("license"),
    servers=openapi_config.get("servers", []),
    tags_metadata=get_openapi_tags(),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Apply custom OpenAPI schema with enhanced documentation
create_custom_openapi_schema(app)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log incoming requests and their processing time.
    """
    start_time = datetime.now()

    # Log request details
    logging.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = (datetime.now() - start_time).total_seconds()

    # Log response details
    logging.info(
        f"Response: {response.status_code} " f"processed in {process_time:.3f}s"
    )

    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logging.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path),
        },
    )


# Include routers
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health & Status"],
)

app.include_router(
    weather.router,
    prefix="/api/v1/weather",
    tags=["Weather Data"],
)

app.include_router(
    crops.router,
    prefix="/api/v1/crops",
    tags=["Crop Data"],
)

app.include_router(
    stats.router,
    prefix="/api/v1/stats",
    tags=["Statistics & Analytics"],
)

app.include_router(
    simple_weather.router,
    prefix="/api/weather",
    tags=["Simple Weather API"],
)

app.include_router(
    filtered_endpoints.router,
    prefix="/api/v2",
    tags=["Enhanced API with Filtering & Pagination"],
)

app.include_router(
    docs.router,
    prefix="/docs/api",
    tags=["Documentation & API Information"],
)


# Root endpoint
@app.get("/", response_model=dict[str, Any])
async def root():
    """
    Root endpoint providing comprehensive API information.

    Returns information about the Weather Data Engineering API including:
    - Basic API metadata
    - Documentation URLs
    - Available endpoints
    - Enhanced documentation features
    """
    return {
        "message": "Weather Data Engineering API",
        "version": openapi_config["version"],
        "description": "A comprehensive data engineering solution for weather data management and analysis",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
            "custom_swagger": "/docs/api/custom-swagger",
            "custom_redoc": "/docs/api/custom-redoc",
            "api_info": "/docs/api",
            "examples": "/docs/api/examples",
            "integration_guides": "/docs/api/integration-guides",
            "endpoints_info": "/docs/api/endpoints",
            "documentation_status": "/docs/api/status",
        },
        "endpoints": {
            "weather_v1": "/api/v1/weather",
            "simple_weather": "/api/weather",
            "enhanced_api_v2": "/api/v2",
            "crops": "/api/v1/crops",
            "stats": "/api/v1/stats",
            "health": "/health",
            "system_info": "/info",
        },
        "features": {
            "filtering": "Advanced filtering capabilities",
            "pagination": "Page-based and cursor-based pagination",
            "sorting": "Multi-field sorting with validation",
            "search": "Full-text search capabilities",
            "documentation": "Enhanced interactive documentation",
            "examples": "Comprehensive API examples",
            "integration_guides": "Multi-language integration guides",
        },
        "data_coverage": {
            "time_period": "1985-2014 (30 years)",
            "geographic_coverage": "Nebraska, Iowa, Illinois, Indiana, Ohio",
            "weather_stations": "200+ stations",
            "data_points": "Temperature, precipitation, weather station metadata",
        },
        "contact": openapi_config.get("contact"),
        "license": openapi_config.get("license"),
        "timestamp": datetime.now().isoformat(),
    }


# Configuration endpoint
@app.get("/info", response_model=dict[str, Any])
async def api_info():
    """
    API configuration and system information.
    """
    return {
        "api": {
            "name": "Weather Data Engineering API",
            "version": "1.0.0",
            "environment": "development" if settings.debug else "production",
            "debug": settings.debug,
        },
        "database": {
            "engine": django_settings.DATABASES["default"]["ENGINE"],
            "name": django_settings.DATABASES["default"]["NAME"],
            "host": django_settings.DATABASES["default"]["HOST"],
            "port": django_settings.DATABASES["default"]["PORT"],
        },
        "django": {
            "version": django.VERSION,
            "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE"),
            "installed_apps": len(django_settings.INSTALLED_APPS),
        },
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Start the server
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.debug,
        log_level=settings.LOG_LEVEL.lower(),
    )
