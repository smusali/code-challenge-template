"""
Integration tests for date filter edge cases and validation.

This module tests the improved date filtering logic to ensure edge cases
are handled properly with appropriate error messages.
"""

from datetime import date
from unittest.mock import patch

import pytest

from src.utils.filtering import parse_date_safely, validate_date_range_consistency
from tests.test_base import BaseAPITest


class TestDateFilterEdgeCases(BaseAPITest):
    """Test date filter edge cases and validation."""

    def test_parse_date_safely_valid_dates(self):
        """Test safe date parsing with valid dates."""
        # Standard date
        result = parse_date_safely("2023-06-15", "test_date")
        assert result == date(2023, 6, 15)

        # Leap year date
        result = parse_date_safely("2024-02-29", "test_date")
        assert result == date(2024, 2, 29)

        # New Year's Day
        result = parse_date_safely("2023-01-01", "test_date")
        assert result == date(2023, 1, 1)

    def test_parse_date_safely_invalid_formats(self):
        """Test safe date parsing with invalid formats."""
        from fastapi import HTTPException

        # Wrong format
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("2023/06/15", "test_date")
        assert "Invalid test_date format" in str(exc_info.value.detail)

        # Incomplete date
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("2023-06", "test_date")
        assert "Invalid test_date format" in str(exc_info.value.detail)

        # Invalid characters
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("2023-ab-15", "test_date")
        assert "Invalid test_date format" in str(exc_info.value.detail)

    def test_parse_date_safely_invalid_dates(self):
        """Test safe date parsing with invalid dates."""
        from fastapi import HTTPException

        # February 29 in non-leap year
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("2023-02-29", "test_date")
        assert "Day does not exist" in str(exc_info.value.detail)

        # Invalid month
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("2023-13-15", "test_date")
        assert "Month must be between 1 and 12" in str(exc_info.value.detail)

        # Invalid day
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("2023-11-31", "test_date")
        assert "Day does not exist" in str(exc_info.value.detail)

        # Year out of range
        with pytest.raises(HTTPException) as exc_info:
            parse_date_safely("1799-06-15", "test_date")
        assert "Year must be between 1800 and 2100" in str(exc_info.value.detail)

    def test_validate_date_range_consistency(self):
        """Test date range consistency validation."""
        from fastapi import HTTPException

        # Conflicting date range and year filters
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range_consistency(
                date(2023, 1, 1), date(2023, 12, 31), 2023, None
            )
        assert "Cannot use both date range filters" in str(exc_info.value.detail)

        # Month without year
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range_consistency(None, None, None, 6)
        assert "must also specify a year" in str(exc_info.value.detail)

        # Invalid month
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range_consistency(None, None, 2023, 13)
        assert "Month must be between 1 and 12" in str(exc_info.value.detail)

    def test_api_invalid_date_formats(self):
        """Test API endpoints with invalid date formats."""
        # Test daily weather endpoint with invalid start_date
        response = self.client.get("/api/v2/daily-weather?start_date=2023/06/15")
        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]

        # Test with invalid end_date
        response = self.client.get("/api/v2/daily-weather?end_date=2023-13-01")
        assert response.status_code == 400
        assert "Month must be between 1 and 12" in response.json()["detail"]

    def test_api_conflicting_date_filters(self):
        """Test API endpoints with conflicting date filters."""
        # Date range + year filter
        response = self.client.get(
            "/api/v2/daily-weather?start_date=2023-01-01&end_date=2023-12-31&year=2023"
        )
        assert response.status_code == 400
        assert "Cannot use both date range filters" in response.json()["detail"]

        # Month without year
        response = self.client.get("/api/v2/daily-weather?month=6")
        assert response.status_code == 400
        assert "must also specify a year" in response.json()["detail"]

    def test_api_invalid_temperature_ranges(self):
        """Test API endpoints with invalid temperature ranges."""
        # Min > Max temperature
        response = self.client.get("/api/v2/daily-weather?min_temp=30&max_temp=20")
        assert response.status_code == 400
        assert "Minimum temperature" in response.json()["detail"]
        assert "cannot be greater than maximum temperature" in response.json()["detail"]

    def test_api_invalid_precipitation_ranges(self):
        """Test API endpoints with invalid precipitation ranges."""
        # Negative precipitation
        response = self.client.get("/api/v2/daily-weather?min_precipitation=-10")
        assert response.status_code == 400
        assert "cannot be negative" in response.json()["detail"]

        # Min > Max precipitation
        response = self.client.get(
            "/api/v2/daily-weather?min_precipitation=100&max_precipitation=50"
        )
        assert response.status_code == 400
        assert "Minimum precipitation" in response.json()["detail"]
        assert (
            "cannot be greater than maximum precipitation" in response.json()["detail"]
        )

    def test_api_invalid_yearly_stats_filters(self):
        """Test yearly stats endpoint with invalid filters."""
        # Start year > End year
        response = self.client.get("/api/v2/yearly-stats?start_year=2023&end_year=2020")
        assert response.status_code == 400
        assert "cannot be greater than end year" in response.json()["detail"]

        # Conflicting year filters
        response = self.client.get(
            "/api/v2/yearly-stats?start_year=2020&years=2021,2022,2023"
        )
        assert response.status_code == 400
        assert "Cannot use both year range" in response.json()["detail"]

        # Invalid specific years
        response = self.client.get("/api/v2/yearly-stats?years=1799,2023,2101")
        assert response.status_code == 400
        assert "Invalid years" in response.json()["detail"]

    def test_api_valid_edge_case_dates(self):
        """Test API endpoints with valid edge case dates."""
        # Leap year February 29
        response = self.client.get(
            "/api/v2/daily-weather?start_date=2024-02-29&end_date=2024-02-29"
        )
        assert response.status_code == 200

        # Year boundaries
        response = self.client.get(
            "/api/v2/daily-weather?start_date=1985-01-01&end_date=1985-01-01"
        )
        assert response.status_code == 200

        # Valid year and month combination
        response = self.client.get("/api/v2/daily-weather?year=2023&month=2")
        assert response.status_code == 200

    def test_api_extreme_temperature_logging(self):
        """Test that extreme temperature values are logged but not rejected."""
        with patch("src.routers.filtered_endpoints.logger") as mock_logger:
            # Extreme but possibly valid temperature
            response = self.client.get("/api/v2/daily-weather?min_temp=-80")
            assert response.status_code == 200
            mock_logger.warning.assert_called()
            assert "Extreme minimum temperature" in str(mock_logger.warning.call_args)

    def test_api_extreme_precipitation_logging(self):
        """Test that extreme precipitation values are logged."""
        with patch("src.routers.filtered_endpoints.logger") as mock_logger:
            # Very high precipitation value
            response = self.client.get("/api/v2/daily-weather?max_precipitation=1500")
            assert response.status_code == 200
            mock_logger.warning.assert_called()
            assert "Very high precipitation value" in str(mock_logger.warning.call_args)
