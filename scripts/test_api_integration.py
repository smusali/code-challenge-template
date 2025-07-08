#!/usr/bin/env python3
"""
Integration test script for the Weather Data Engineering API.

This script tests the basic functionality of the FastAPI application
with Django ORM integration.
"""

import os
import sys
from datetime import datetime

import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")

import django

django.setup()

from core_django.models.models import CropYield, DailyWeather, WeatherStation


def test_django_integration():
    """Test Django ORM integration."""
    print("Testing Django ORM integration...")

    # Test database connection
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

    # Test model access
    try:
        station_count = WeatherStation.objects.count()
        daily_count = DailyWeather.objects.count()
        crop_count = CropYield.objects.count()

        print(f"✓ Weather stations: {station_count}")
        print(f"✓ Daily weather records: {daily_count}")
        print(f"✓ Crop yield records: {crop_count}")
    except Exception as e:
        print(f"✗ Model access failed: {e}")
        return False

    return True


def test_api_endpoints(base_url="http://localhost:8000"):
    """Test API endpoints."""
    print(f"\nTesting API endpoints at {base_url}...")

    # Test health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health check endpoint working")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✓ Root endpoint working")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False

    # Test API info endpoint
    try:
        response = requests.get(f"{base_url}/info", timeout=5)
        if response.status_code == 200:
            print("✓ API info endpoint working")
        else:
            print(f"✗ API info endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API info endpoint failed: {e}")
        return False

    # Test weather endpoints
    try:
        response = requests.get(f"{base_url}/api/v1/weather/stations", timeout=5)
        if response.status_code == 200:
            print("✓ Weather stations endpoint working")
        else:
            print(f"✗ Weather stations endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Weather stations endpoint failed: {e}")
        return False

    # Test crops endpoints
    try:
        response = requests.get(f"{base_url}/api/v1/crops/", timeout=5)
        if response.status_code == 200:
            print("✓ Crops endpoint working")
        else:
            print(f"✗ Crops endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Crops endpoint failed: {e}")
        return False

    return True


def test_api_documentation(base_url="http://localhost:8000"):
    """Test API documentation endpoints."""
    print(f"\nTesting API documentation at {base_url}...")

    # Test OpenAPI schema
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            print("✓ OpenAPI schema available")
        else:
            print(f"✗ OpenAPI schema failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ OpenAPI schema failed: {e}")
        return False

    # Test Swagger UI
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ Swagger UI available")
        else:
            print(f"✗ Swagger UI failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Swagger UI failed: {e}")
        return False

    # Test ReDoc
    try:
        response = requests.get(f"{base_url}/redoc", timeout=5)
        if response.status_code == 200:
            print("✓ ReDoc documentation available")
        else:
            print(f"✗ ReDoc documentation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ ReDoc documentation failed: {e}")
        return False

    return True


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Weather Data Engineering API - Integration Tests")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")

    success = True

    # Test Django integration
    if not test_django_integration():
        success = False

    # Test API endpoints (optional - only if server is running)
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    try:
        if test_api_endpoints(api_base_url):
            test_api_documentation(api_base_url)
        else:
            success = False
    except Exception as e:
        print(f"\nNote: API server tests skipped (server not running): {e}")
        print("To test API endpoints, start the server with:")
        print("  cd /path/to/project && python -m uvicorn src.main:app --reload")

    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✓ All integration tests passed!")
        print("\nNext steps:")
        print("1. Start the API server: python -m uvicorn src.main:app --reload")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Test endpoints manually or with automated tests")
        return 0
    else:
        print("✗ Some integration tests failed!")
        print("\nPlease check the error messages above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
