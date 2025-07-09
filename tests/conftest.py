"""
Test configuration and fixtures for integration tests.

This module provides:
- Django test configuration
- Test database setup
- Common test fixtures
- Test utilities and helpers
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Any

import django
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure Django settings for testing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")
os.environ.setdefault(
    "DATABASE_URL", "sqlite:///:memory:"
)  # Use in-memory SQLite for tests
os.environ.setdefault("DJANGO_DEBUG", "False")

# Setup Django
django.setup()

# Import after Django setup
from core_django.models.models import (  # noqa: E402
    DailyWeather,
    WeatherStation,
    YearlyWeatherStats,
)
from src.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Set up the test database with sample data."""
    with django_db_blocker.unblock():
        # Create test weather stations
        stations_data = [
            {
                "station_id": "TEST001",
                "name": "Chicago Test Station",
                "state": "IL",
                "latitude": 41.8781,
                "longitude": -87.6298,
            },
            {
                "station_id": "TEST002",
                "name": "Des Moines Test Station",
                "state": "IA",
                "latitude": 41.5868,
                "longitude": -93.6250,
            },
            {
                "station_id": "TEST003",
                "name": "Indianapolis Test Station",
                "state": "IN",
                "latitude": 39.7684,
                "longitude": -86.1581,
            },
        ]

        test_stations = []
        for station_data in stations_data:
            station, created = WeatherStation.objects.get_or_create(
                station_id=station_data["station_id"], defaults=station_data
            )
            test_stations.append(station)

        # Create test daily weather data
        base_date = datetime(2010, 1, 1).date()
        for i, station in enumerate(test_stations):
            for day_offset in range(30):  # 30 days of test data per station
                test_date = base_date + timedelta(days=day_offset)

                # Create varying weather data
                max_temp = 200 + (i * 50) + (day_offset * 10)  # In tenths of degrees
                min_temp = max_temp - 100
                precipitation = (day_offset % 5) * 25  # Varying precipitation

                DailyWeather.objects.get_or_create(
                    station=station,
                    date=test_date,
                    defaults={
                        "max_temp": max_temp,
                        "min_temp": min_temp,
                        "precipitation": precipitation,
                    },
                )

        # Create test yearly statistics
        for station in test_stations:
            YearlyWeatherStats.objects.get_or_create(
                station=station,
                year=2010,
                defaults={
                    "avg_max_temp": 250,  # 25.0°C
                    "avg_min_temp": 150,  # 15.0°C
                    "total_precipitation": 1000,  # 100.0mm
                    "records_with_temp": 365,
                    "records_with_precipitation": 300,
                },
            )


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Create an async HTTP client for testing."""
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def sample_station_data() -> dict[str, Any]:
    """Provide sample weather station data for tests."""
    return {
        "station_id": "SAMPLE001",
        "name": "Sample Weather Station",
        "state": "IL",
        "latitude": 42.0,
        "longitude": -88.0,
    }


@pytest.fixture
def sample_weather_data() -> dict[str, Any]:
    """Provide sample daily weather data for tests."""
    return {
        "date": "2010-01-15",
        "max_temp": 250,  # 25.0°C in tenths
        "min_temp": 150,  # 15.0°C in tenths
        "precipitation": 50,  # 5.0mm in tenths
    }


@pytest.fixture
def invalid_data_samples() -> dict[str, dict[str, Any]]:
    """Provide various invalid data samples for testing error handling."""
    return {
        "invalid_station": {
            "station_id": "",  # Empty station ID
            "name": "Test Station",
            "state": "XX",  # Invalid state
            "latitude": 200.0,  # Invalid latitude
            "longitude": -200.0,  # Invalid longitude
        },
        "invalid_weather": {
            "date": "invalid-date",
            "max_temp": "not-a-number",
            "min_temp": None,
            "precipitation": -100,  # Negative precipitation
        },
        "missing_required": {
            # Missing required fields
        },
    }


@pytest.fixture
def api_endpoints() -> dict[str, list[str]]:
    """Provide a comprehensive list of API endpoints for testing."""
    return {
        "health": [
            "/health",
            "/health/",
        ],
        "system": [
            "/",
            "/info",
        ],
        "weather_v1": [
            "/api/v1/weather/stations",
            "/api/v1/weather/stations/TEST001",
            "/api/v1/weather/daily",
            "/api/v1/weather/daily/TEST001",
        ],
        "enhanced_v2": [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
            "/api/v2/sort-info/daily_weather",
            "/api/v2/filter-info",
        ],
        "documentation": [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/docs/api",
            "/docs/api/endpoints",
            "/docs/api/examples",
            "/docs/api/integration-guides",
            "/docs/api/status",
            "/docs/api/custom-swagger",
            "/docs/api/custom-redoc",
        ],
        "statistics": [
            "/api/v1/stats/summary",
            "/api/v1/stats/yearly/TEST001",
        ],
        "crops": [
            "/api/v1/crops/yield",
        ],
    }


@pytest.fixture
def test_query_params() -> dict[str, dict[str, Any]]:
    """Provide various query parameter combinations for testing."""
    return {
        "pagination": {
            "page": 1,
            "page_size": 10,
        },
        "filtering": {
            "start_date": "2010-01-01",
            "end_date": "2010-01-31",
            "states": ["IL", "IA"],
            "min_temp": -10,
            "max_temp": 40,
        },
        "sorting": {
            "sort_by": "date",
            "sort_order": "desc",
        },
        "search": {
            "search": "Chicago",
            "has_recent_data": True,
        },
        "invalid": {
            "page": -1,
            "page_size": 0,
            "start_date": "invalid-date",
            "sort_order": "invalid",
        },
    }


@pytest.fixture
def expected_response_schemas() -> dict[str, dict[str, Any]]:
    """Provide expected response schemas for validation."""
    return {
        "weather_station": {
            "required_fields": [
                "id",
                "station_id",
                "name",
                "state",
                "latitude",
                "longitude",
            ],
            "field_types": {
                "id": int,
                "station_id": str,
                "name": str,
                "state": str,
                "latitude": float,
                "longitude": float,
            },
        },
        "daily_weather": {
            "required_fields": [
                "id",
                "station",
                "date",
                "max_temp",
                "min_temp",
                "precipitation",
            ],
            "field_types": {
                "id": int,
                "date": str,
                "max_temp": (int, type(None)),
                "min_temp": (int, type(None)),
                "precipitation": (int, type(None)),
            },
        },
        "paginated_response": {
            "required_fields": ["items", "pagination", "links"],
            "field_types": {
                "items": list,
                "pagination": dict,
                "links": dict,
            },
        },
        "health_response": {
            "required_fields": ["status", "timestamp"],
            "field_types": {
                "status": str,
                "timestamp": str,
            },
        },
        "api_info": {
            "required_fields": [
                "name",
                "version",
                "description",
                "documentation",
                "endpoints",
            ],
            "field_types": {
                "name": str,
                "version": str,
                "description": str,
                "documentation": dict,
                "endpoints": dict,
            },
        },
    }


class TestDataHelper:
    """Helper class for creating and managing test data."""

    @staticmethod
    def create_test_station(station_data: dict[str, Any] = None) -> WeatherStation:
        """Create a test weather station."""
        default_data = {
            "station_id": f"TEST{datetime.now().microsecond}",
            "name": "Test Station",
            "state": "IL",
            "latitude": 41.8781,
            "longitude": -87.6298,
        }

        if station_data:
            default_data.update(station_data)

        return WeatherStation.objects.create(**default_data)

    @staticmethod
    def create_test_weather_record(
        station: WeatherStation, date_offset: int = 0
    ) -> DailyWeather:
        """Create a test daily weather record."""
        test_date = datetime(2010, 1, 1).date() + timedelta(days=date_offset)

        return DailyWeather.objects.create(
            station=station,
            date=test_date,
            max_temp=250,  # 25.0°C
            min_temp=150,  # 15.0°C
            precipitation=25,  # 2.5mm
        )

    @staticmethod
    def create_test_yearly_stats(
        station: WeatherStation, year: int = 2010
    ) -> YearlyWeatherStats:
        """Create test yearly weather statistics."""
        return YearlyWeatherStats.objects.create(
            station=station,
            year=year,
            avg_max_temp=250,
            avg_min_temp=150,
            total_precipitation=1000,
            records_with_temp=365,
            records_with_precipitation=300,
        )


@pytest.fixture
def test_data_helper() -> TestDataHelper:
    """Provide the test data helper."""
    return TestDataHelper()


def validate_response_schema(
    response_data: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
    """Validate response data against expected schema."""
    errors = []

    # Check required fields
    for field in schema.get("required_fields", []):
        if field not in response_data:
            errors.append(f"Missing required field: {field}")

    # Check field types
    for field, expected_type in schema.get("field_types", {}).items():
        if field in response_data:
            actual_value = response_data[field]
            if not isinstance(actual_value, expected_type):
                errors.append(
                    f"Field {field} has incorrect type. Expected {expected_type}, got {type(actual_value)}"
                )

    return errors


@pytest.fixture
def schema_validator():
    """Provide the schema validation function."""
    return validate_response_schema


# Performance testing utilities
class PerformanceTimer:
    """Simple performance timer for testing response times."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start the timer."""
        self.start_time = datetime.now()

    def stop(self):
        """Stop the timer."""
        self.end_time = datetime.now()

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@pytest.fixture
def performance_timer() -> PerformanceTimer:
    """Provide a performance timer for response time testing."""
    return PerformanceTimer()


# Test environment configuration
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("TESTING", "True")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")  # Reduce log noise during tests
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line(
        "markers", "documentation: marks tests as documentation tests"
    )
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
