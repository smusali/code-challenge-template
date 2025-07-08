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
from src.routers import crops, health, simple_weather, stats, weather  # noqa: E402


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


# FastAPI application instance
app = FastAPI(
    title="Weather Data Engineering API",
    description="""
    A comprehensive API for weather data management and analysis.

    This API provides endpoints for:
    - Weather station management
    - Daily weather observations
    - Yearly weather statistics
    - Crop yield data
    - Data ingestion and processing
    - Analytics and reporting

    Built with FastAPI and Django ORM integration.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

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


# Root endpoint
@app.get("/", response_model=dict[str, Any])
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "Weather Data Engineering API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health",
        "endpoints": {
            "weather": "/api/v1/weather",
            "simple_weather": "/api/weather",
            "crops": "/api/v1/crops",
            "stats": "/api/v1/stats",
        },
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
