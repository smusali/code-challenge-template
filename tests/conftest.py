"""
Pytest configuration and shared fixtures for weather data engineering API tests.

This module provides common test configuration, fixtures, and utilities
used across the test suite.
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory with test weather data files."""
    data_dir = tmp_path_factory.mktemp("test_weather_data")

    # Create sample weather data files for testing
    sample_data = [
        "20230101\t289\t178\t25",
        "20230102\t295\t185\t0",
        "20230103\t-9999\t-9999\t-9999",  # Missing data
        "20230104\t310\t200\t50",
        "20230105\t280\t170\t-9999",  # Missing precipitation
    ]

    # Create a test weather station file
    test_file = data_dir / "USC00TEST001.txt"
    test_file.write_text("\n".join(sample_data))

    return data_dir


@pytest.fixture
def sample_weather_lines():
    """Provide sample weather data lines for testing."""
    return [
        "20230615\t289\t178\t25",  # Valid line
        "20230616\t-9999\t-9999\t-9999",  # All missing
        "20230617\t310\t200\t0",  # Zero precipitation
        "20230618\t285\t285\t15",  # Equal temperatures
        "20230619\t350\t250\t100",  # High values
        "20230620\t-100\t-200\t5",  # Negative temperatures
    ]


@pytest.fixture
def invalid_weather_lines():
    """Provide invalid weather data lines for testing."""
    return [
        "20230615\t289\t178",  # Too few fields
        "20230615\t289\t178\t25\textra",  # Too many fields
        "2023-06-15\t289\t178\t25",  # Wrong date format
        "20230615\tabc\t178\t25",  # Invalid temperature
        "20230615\t289\t178\tabc",  # Invalid precipitation
        "20230615\t150\t200\t25",  # Max < Min temperature
        "20230615\t289\t178\t-50",  # Negative precipitation
        "",  # Empty line
        "invalid data",  # Completely invalid
    ]


@pytest.fixture(autouse=True)
def setup_django_settings():
    """Configure Django settings for tests."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")

    try:
        import django

        if not django.conf.settings.configured:
            django.setup()
    except ImportError:
        # Django not available in test environment
        pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add slow marker to tests that might be slow
        if "integration" in item.nodeid or "test_large" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
