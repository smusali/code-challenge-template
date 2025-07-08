"""
API routers package for the Weather Data Engineering API.

This package contains all FastAPI router modules for different API endpoints:
- health: Health check and system status endpoints
- weather: Weather data management endpoints
- crops: Crop yield data endpoints
- stats: Statistics and analytics endpoints
"""

from . import crops, health, stats, weather

__all__ = ["health", "weather", "crops", "stats"]
