"""
Unit tests for WeatherDataParser

Tests the weather data parsing and validation functionality including:
- Valid data parsing
- Invalid format handling
- Missing value processing
- Temperature validation
- Date parsing
- Error handling and logging
"""

import logging
from datetime import date
from unittest.mock import Mock

import pytest

from scripts.ingest_weather_data import WeatherDataParser


class TestWeatherDataParser:
    """Test suite for WeatherDataParser class."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=logging.Logger)

    @pytest.fixture
    def parser(self, mock_logger):
        """Create a WeatherDataParser instance with mock logger."""
        return WeatherDataParser(mock_logger)

    def test_parse_valid_weather_line(self, parser):
        """Test parsing a valid weather data line."""
        # Valid line: date, max_temp, min_temp, precipitation
        line = "20230615\t289\t178\t25"
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert date_obj == date(2023, 6, 15)
        assert max_temp == 289
        assert min_temp == 178
        assert precipitation == 25

    def test_parse_line_with_missing_values(self, parser):
        """Test parsing a line with missing values (-9999)."""
        line = "20230615\t-9999\t178\t-9999"
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert date_obj == date(2023, 6, 15)
        assert max_temp is None  # -9999 converted to None
        assert min_temp == 178
        assert precipitation is None  # -9999 converted to None

    def test_parse_line_with_all_missing_values(self, parser):
        """Test parsing a line where all weather values are missing."""
        line = "20230615\t-9999\t-9999\t-9999"
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert date_obj == date(2023, 6, 15)
        assert max_temp is None
        assert min_temp is None
        assert precipitation is None

    def test_parse_line_invalid_field_count(self, parser, mock_logger):
        """Test handling of lines with incorrect number of fields."""
        # Too few fields
        line = "20230615\t289\t178"
        result = parser.parse_weather_line(line, 1)

        assert result is None
        mock_logger.warning.assert_called_with(
            "Line 1: Invalid format - expected 4 fields, got 3"
        )

        # Too many fields
        mock_logger.reset_mock()
        line = "20230615\t289\t178\t25\textra"
        result = parser.parse_weather_line(line, 2)

        assert result is None
        mock_logger.warning.assert_called_with(
            "Line 2: Invalid format - expected 4 fields, got 5"
        )

    def test_parse_line_invalid_date_format(self, parser, mock_logger):
        """Test handling of invalid date formats."""
        # Invalid date format
        line = "2023-06-15\t289\t178\t25"
        result = parser.parse_weather_line(line, 1)

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Line 1: Invalid date format" in call_args

    def test_parse_line_invalid_date_values(self, parser, mock_logger):
        """Test handling of invalid date values."""
        # Invalid month
        line = "20231315\t289\t178\t25"
        result = parser.parse_weather_line(line, 1)

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Line 1: Invalid date format" in call_args

    def test_parse_line_temperature_validation_fails(self, parser, mock_logger):
        """Test temperature validation when max < min."""
        line = "20230615\t150\t200\t25"  # max_temp < min_temp
        result = parser.parse_weather_line(line, 1)

        assert result is None
        mock_logger.warning.assert_called_with(
            "Line 1: Max temp (150) < Min temp (200)"
        )

    def test_parse_line_temperature_validation_edge_case(self, parser):
        """Test temperature validation when max == min."""
        line = "20230615\t175\t175\t25"  # max_temp == min_temp
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert max_temp == 175
        assert min_temp == 175

    def test_parse_line_negative_precipitation_handled(self, parser, mock_logger):
        """Test handling of negative precipitation values."""
        line = "20230615\t289\t178\t-50"
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert precipitation is None  # Negative precipitation set to None
        mock_logger.warning.assert_called_with("Line 1: Negative precipitation (-50)")

    def test_parse_line_zero_precipitation(self, parser):
        """Test handling of zero precipitation (valid case)."""
        line = "20230615\t289\t178\t0"
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert precipitation == 0

    def test_parse_line_with_whitespace(self, parser):
        """Test parsing lines with extra whitespace."""
        line = "  20230615  \t  289  \t  178  \t  25  "
        result = parser.parse_weather_line(line, 1)

        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert date_obj == date(2023, 6, 15)
        assert max_temp == 289
        assert min_temp == 178
        assert precipitation == 25

    def test_parse_line_unexpected_exception(self, parser, mock_logger):
        """Test handling of unexpected exceptions during parsing."""
        # This should trigger an exception in the parsing logic
        line = None  # This will cause an AttributeError
        result = parser.parse_weather_line(line, 1)

        assert result is None
        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args[0][0]
        assert "Line 1: Unexpected error parsing line" in call_args

    def test_parse_value_valid_integer(self, parser):
        """Test _parse_value with valid integer."""
        result = parser._parse_value("289", "max_temp", 1)
        assert result == 289

    def test_parse_value_missing_sentinel(self, parser):
        """Test _parse_value with -9999 sentinel value."""
        result = parser._parse_value("-9999", "max_temp", 1)
        assert result is None

    def test_parse_value_invalid_format(self, parser, mock_logger):
        """Test _parse_value with invalid format."""
        result = parser._parse_value("abc", "max_temp", 1)
        assert result is None
        mock_logger.warning.assert_called_with("Line 1: Invalid max_temp value 'abc'")

    def test_parse_value_empty_string(self, parser, mock_logger):
        """Test _parse_value with empty string."""
        result = parser._parse_value("", "precipitation", 5)
        assert result is None
        mock_logger.warning.assert_called_with("Line 5: Invalid precipitation value ''")

    def test_parse_value_float_string(self, parser, mock_logger):
        """Test _parse_value with float string (invalid for int parsing)."""
        result = parser._parse_value("123.45", "min_temp", 3)
        assert result is None
        mock_logger.warning.assert_called_with(
            "Line 3: Invalid min_temp value '123.45'"
        )

    def test_parse_multiple_valid_lines(self, parser):
        """Test parsing multiple different valid lines."""
        test_cases = [
            ("20230101\t-50\t-100\t0", date(2023, 1, 1), -50, -100, 0),
            ("20230701\t350\t200\t150", date(2023, 7, 1), 350, 200, 150),
            ("20231231\t0\t-200\t-9999", date(2023, 12, 31), 0, -200, None),
        ]

        for (
            line,
            expected_date,
            expected_max,
            expected_min,
            expected_precip,
        ) in test_cases:
            result = parser.parse_weather_line(line, 1)
            assert result is not None
            date_obj, max_temp, min_temp, precipitation = result
            assert date_obj == expected_date
            assert max_temp == expected_max
            assert min_temp == expected_min
            assert precipitation == expected_precip

    def test_temperature_validation_with_missing_values(self, parser):
        """Test temperature validation when one or both temps are missing."""
        # Only max temp present
        line = "20230615\t289\t-9999\t25"
        result = parser.parse_weather_line(line, 1)
        assert result is not None

        # Only min temp present
        line = "20230615\t-9999\t178\t25"
        result = parser.parse_weather_line(line, 1)
        assert result is not None

        # Both temps missing
        line = "20230615\t-9999\t-9999\t25"
        result = parser.parse_weather_line(line, 1)
        assert result is not None

    @pytest.mark.parametrize("line_number", [1, 42, 1000, 999999])
    def test_line_number_reporting(self, parser, mock_logger, line_number):
        """Test that line numbers are correctly reported in error messages."""
        invalid_line = "invalid\tdata"
        parser.parse_weather_line(invalid_line, line_number)

        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert f"Line {line_number}:" in call_args

    def test_extreme_temperature_values(self, parser):
        """Test parsing with extreme but valid temperature values."""
        # Very high temperatures
        line = "20230615\t500\t400\t1000"
        result = parser.parse_weather_line(line, 1)
        assert result is not None

        # Very low temperatures
        line = "20230615\t-300\t-400\t0"
        result = parser.parse_weather_line(line, 1)
        assert result is not None

    def test_leap_year_date_parsing(self, parser):
        """Test parsing dates in leap years."""
        # Valid leap year date
        line = "20200229\t289\t178\t25"
        result = parser.parse_weather_line(line, 1)
        assert result is not None
        date_obj, _, _, _ = result
        assert date_obj == date(2020, 2, 29)

    def test_non_leap_year_invalid_date(self, parser, mock_logger):
        """Test invalid date in non-leap year."""
        # Invalid date (Feb 29 in non-leap year)
        line = "20210229\t289\t178\t25"
        result = parser.parse_weather_line(line, 1)
        assert result is None
        mock_logger.warning.assert_called()
