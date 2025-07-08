"""
Health check and system status endpoints.

This module provides health check endpoints for monitoring system status,
database connectivity, and service availability.
"""

import logging
import os
from datetime import datetime
from typing import Any

import psutil
from django.db import connection
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    uptime: float
    environment: str


class SystemStatusResponse(BaseModel):
    """System status response model."""

    status: str
    timestamp: datetime
    services: dict[str, Any]
    system: dict[str, Any]
    database: dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns basic service status information for load balancer health checks.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Get process information
        process = psutil.Process()
        uptime = datetime.now().timestamp() - process.create_time()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            uptime=uptime,
            environment=os.getenv("ENVIRONMENT", "development"),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}",
        )


@router.get("/status", response_model=SystemStatusResponse)
async def system_status():
    """
    Detailed system status endpoint.

    Returns comprehensive system status including database, memory, disk, and service health.
    """
    try:
        # Check database connection and get stats
        db_status = await _check_database_health()

        # Get system metrics
        system_metrics = await _get_system_metrics()

        # Check external services
        services_status = await _check_services_health()

        return SystemStatusResponse(
            status="healthy"
            if all(
                [
                    db_status["status"] == "healthy",
                    system_metrics["status"] == "healthy",
                    services_status["status"] == "healthy",
                ]
            )
            else "unhealthy",
            timestamp=datetime.now(),
            services=services_status,
            system=system_metrics,
            database=db_status,
        )

    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System status check failed: {str(e)}",
        )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.

    Checks if the service is ready to receive traffic.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return {"status": "ready", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        )


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Checks if the service is alive and responsive.
    """
    try:
        # Basic process check
        process = psutil.Process()

        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "pid": process.pid,
            "memory_percent": process.memory_percent(),
        }

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not alive",
        )


async def _check_database_health() -> dict[str, Any]:
    """
    Check database connectivity and performance.

    Returns database health status with connection metrics.
    """
    try:
        start_time = datetime.now()

        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        # Check database version
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]

        # Get database size
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_database_size(current_database()) as db_size
            """
            )
            db_size = cursor.fetchone()[0]

        # Get connection count
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*) as connection_count
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            )
            connection_count = cursor.fetchone()[0]

        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "version": db_version,
            "database_size_bytes": db_size,
            "active_connections": connection_count,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


async def _get_system_metrics() -> dict[str, Any]:
    """
    Get system resource metrics.

    Returns CPU, memory, and disk usage information.
    """
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Get memory usage
        memory = psutil.virtual_memory()

        # Get disk usage
        disk = psutil.disk_usage("/")

        # Get process information
        process = psutil.Process()

        return {
            "status": "healthy",
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "percent": memory.percent,
            },
            "disk": {
                "total_bytes": disk.total,
                "free_bytes": disk.free,
                "percent": (disk.used / disk.total) * 100,
            },
            "process": {
                "pid": process.pid,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "uptime_seconds": datetime.now().timestamp() - process.create_time(),
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"System metrics check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


async def _check_services_health() -> dict[str, Any]:
    """
    Check health of external services.

    Returns status of Redis, external APIs, and other dependencies.
    """
    try:
        services = {}

        # Check Redis if configured
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis

                redis_client = redis.from_url(redis_url)
                redis_client.ping()
                services["redis"] = {
                    "status": "healthy",
                    "url": redis_url,
                }
            except Exception as e:
                services["redis"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        # Add more service checks as needed

        return {
            "status": "healthy"
            if all(service.get("status") == "healthy" for service in services.values())
            else "unhealthy",
            "services": services,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
