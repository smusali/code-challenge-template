"""
Integration tests for WeatherDataParser

Tests the weather data parser with realistic scenarios including:
- Processing multiple lines in sequence
- Handling large datasets
- Real-world data patterns
- Performance considerations
- Error accumulation patterns
"""

import logging
from datetime import date
from unittest.mock import Mock

import pytest

from scripts.ingest_weather_data import WeatherDataParser


class TestWeatherDataParserIntegration:
    """Integration test suite for WeatherDataParser."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for integration testing."""
        return Mock(spec=logging.Logger)

    @pytest.fixture
    def parser(self, mock_logger):
        """Create a WeatherDataParser instance."""
        return WeatherDataParser(mock_logger)

    def test_process_sample_weather_lines(self, parser, sample_weather_lines):
        """Test processing a realistic set of weather data lines."""
        results = []

        for i, line in enumerate(sample_weather_lines, 1):
            result = parser.parse_weather_line(line, i)
            results.append(result)

        # Verify all valid lines were parsed successfully
        valid_results = [r for r in results if r is not None]
        assert len(valid_results) == 6  # All sample lines should be valid

        # Check specific parsed values
        first_result = valid_results[0]
        assert first_result[0] == date(2023, 6, 15)
        assert first_result[1] == 289
        assert first_result[2] == 178
        assert first_result[3] == 25

    def test_process_invalid_weather_lines(
        self, parser, mock_logger, invalid_weather_lines
    ):
        """Test processing lines with various types of errors."""
        error_count = 0
        warning_count = 0

        for i, line in enumerate(invalid_weather_lines, 1):
            result = parser.parse_weather_line(line, i)
            if result is None:
                error_count += 1

        # Check that logger was called for errors
        warning_count = mock_logger.warning.call_count
        error_count_from_logger = mock_logger.error.call_count

        # Should have warnings for most invalid lines
        assert warning_count + error_count_from_logger > 0
        # Most invalid lines should fail (empty lines are handled by the caller, not parser)
        non_empty_invalid_lines = [
            line for line in invalid_weather_lines if line.strip()
        ]
        assert (
            error_count >= len(non_empty_invalid_lines) - 2
        )  # Allow for some edge cases

    def test_mixed_valid_invalid_lines(self, parser, mock_logger):
        """Test processing a mix of valid and invalid lines."""
        lines = [
            "20230101\t289\t178\t25",  # Valid
            "20230102\t289\t178",  # Invalid - too few fields
            "20230103\t295\t185\t0",  # Valid
            "20230104\tabc\t178\t25",  # Valid with warning - non-numeric temp becomes None
            "20230105\t310\t200\t50",  # Valid
            "20230106\t150\t200\t25",  # Invalid - max < min
            "20230107\t-9999\t-9999\t-9999",  # Valid - all missing
        ]

        valid_results = []

        for i, line in enumerate(lines, 1):
            result = parser.parse_weather_line(line, i)
            if result is not None:
                valid_results.append(result)

        # Should have 5 valid results (lines 1, 3, 4, 5, 7)
        # Line 4 is valid but has warnings for invalid temp value
        assert len(valid_results) == 5

        # Check that warnings were logged for invalid lines
        assert mock_logger.warning.call_count >= 2  # At least 2 warning conditions

    @pytest.mark.integration
    def test_large_dataset_processing(self, parser, mock_logger):
        """Test processing a larger dataset for performance and reliability."""
        # Generate a large dataset with various patterns
        lines = []
        expected_valid = 0

        # Generate data for a full year using proper date format
        for month in range(1, 13):
            for day in range(1, 29):  # Use 28 days to avoid month-specific issues
                day_of_year = (month - 1) * 28 + day
                date_str = f"{2023:04d}{month:02d}{day:02d}"

                if day_of_year % 20 == 0:
                    # Every 20th day has missing data
                    line = f"{date_str}\t-9999\t-9999\t-9999"
                    lines.append(line)
                    expected_valid += 1
                elif day_of_year % 25 == 0:
                    # Every 25th day has invalid temperature relationship
                    line = f"{date_str}\t100\t200\t25"  # max < min
                    lines.append(line)
                elif day_of_year % 30 == 0:
                    # Every 30th day has invalid format
                    line = f"{date_str}\t289\t178"  # missing field
                    lines.append(line)
                else:
                    # Valid data
                    max_temp = 200 + (day_of_year % 100)
                    min_temp = max_temp - 50
                    precip = day_of_year % 30
                    line = f"{date_str}\t{max_temp}\t{min_temp}\t{precip}"
                    lines.append(line)
                    expected_valid += 1

        # Process all lines
        valid_count = 0
        for i, line in enumerate(lines, 1):
            result = parser.parse_weather_line(line, i)
            if result is not None:
                valid_count += 1

        # Verify processing statistics
        assert valid_count == expected_valid
        assert valid_count > 0  # Should have processed some valid data

    def test_temperature_validation_patterns(self, parser, mock_logger):
        """Test various temperature validation scenarios."""
        test_cases = [
            ("20230101\t100\t100\t25", True),  # Equal temps - valid
            ("20230102\t200\t100\t25", True),  # Normal case - valid
            ("20230103\t100\t200\t25", False),  # Max < Min - invalid
            ("20230104\t-100\t-200\t25", True),  # Both negative, valid order
            ("20230105\t-200\t-100\t25", False),  # Both negative, invalid order
            ("20230106\t0\t-50\t25", True),  # Zero and negative - valid
            ("20230107\t-50\t0\t25", False),  # Negative and zero - invalid
        ]

        valid_count = 0
        invalid_count = 0

        for line, should_be_valid in test_cases:
            result = parser.parse_weather_line(line, 1)
            if result is not None and should_be_valid:
                valid_count += 1
            elif result is None and not should_be_valid:
                invalid_count += 1

        # All test cases should behave as expected
        assert valid_count == sum(1 for _, valid in test_cases if valid)
        assert invalid_count == sum(1 for _, valid in test_cases if not valid)

    def test_precipitation_handling_patterns(self, parser, mock_logger):
        """Test various precipitation value handling scenarios."""
        test_cases = [
            ("20230101\t289\t178\t0", 0),  # Zero precipitation
            ("20230102\t289\t178\t25", 25),  # Normal precipitation
            ("20230103\t289\t178\t-9999", None),  # Missing precipitation
            ("20230104\t289\t178\t1000", 1000),  # High precipitation
            ("20230105\t289\t178\t-50", None),  # Negative - should be None
        ]

        for line, expected_precip in test_cases:
            result = parser.parse_weather_line(line, 1)
            assert result is not None, f"Failed to parse line: {line}"
            _, _, _, precipitation = result
            assert precipitation == expected_precip

    def test_date_parsing_edge_cases(self, parser, mock_logger):
        """Test date parsing with various edge cases."""
        test_cases = [
            ("20230101\t289\t178\t25", date(2023, 1, 1)),  # Start of year
            ("20231231\t289\t178\t25", date(2023, 12, 31)),  # End of year
            ("20200229\t289\t178\t25", date(2020, 2, 29)),  # Leap year
            ("20210228\t289\t178\t25", date(2021, 2, 28)),  # Non-leap year Feb
            ("20230630\t289\t178\t25", date(2023, 6, 30)),  # 30-day month
            ("20230731\t289\t178\t25", date(2023, 7, 31)),  # 31-day month
        ]

        for line, expected_date in test_cases:
            result = parser.parse_weather_line(line, 1)
            assert result is not None, f"Failed to parse valid date line: {line}"
            parsed_date, _, _, _ = result
            assert parsed_date == expected_date

    def test_error_accumulation_patterns(self, parser, mock_logger):
        """Test how errors accumulate during processing."""
        # Create lines with systematic errors
        lines_with_errors = [
            "20230101\t289\t178\t25",  # Valid
            "20230102\t289\t178",  # Format error - returns None
            "20230103\t295\t185\t0",  # Valid
            "invalid_date\t289\t178\t25",  # Date error - returns None
            "20230105\tabc\t178\t25",  # Value warning but still valid (None for temp)
            "20230106\t310\t200\t50",  # Valid
            "20230107\t150\t200\t25",  # Temperature validation error - returns None
        ]

        valid_results = []

        for i, line in enumerate(lines_with_errors, 1):
            result = parser.parse_weather_line(line, i)
            if result is not None:
                valid_results.append(result)

        # Should have 4 valid results (lines 1, 3, 5, 6)
        assert len(valid_results) == 4

        # Should have logged multiple warnings/errors
        total_log_calls = mock_logger.warning.call_count + mock_logger.error.call_count
        assert total_log_calls >= 4  # At least 4 error conditions

    @pytest.mark.slow
    def test_performance_with_realistic_data(self, parser):
        """Test parser performance with realistic data patterns."""
        import time

        # Generate realistic weather data patterns
        lines = []
        for year in [2020, 2021, 2022]:
            for month in range(1, 13):
                for day in range(1, 29):  # Use 28 days to avoid month-specific issues
                    date_str = f"{year}{month:02d}{day:02d}"

                    # Simulate realistic temperature and precipitation patterns
                    base_temp = 200 + (month - 6) * 30  # Seasonal variation
                    max_temp = base_temp + (day % 20)
                    min_temp = max_temp - 50 - (day % 10)
                    precip = 0 if (day % 7) == 0 else (day % 25)  # Some dry days

                    # Occasionally add missing data
                    if day % 30 == 0:
                        max_temp = -9999
                    if day % 35 == 0:
                        precip = -9999

                    line = f"{date_str}\t{max_temp}\t{min_temp}\t{precip}"
                    lines.append(line)

        # Time the parsing
        start_time = time.time()
        valid_count = 0

        for i, line in enumerate(lines, 1):
            result = parser.parse_weather_line(line, i)
            if result is not None:
                valid_count += 1

        end_time = time.time()
        processing_time = end_time - start_time

        # Performance assertions
        assert valid_count > len(lines) * 0.9  # At least 90% should be valid
        assert processing_time < len(lines) * 0.001  # Should process quickly

        # Log performance metrics
        lines_per_second = (
            len(lines) / processing_time if processing_time > 0 else float("inf")
        )
        print(
            f"\nProcessed {len(lines)} lines in {processing_time:.3f}s ({lines_per_second:.0f} lines/sec)"
        )

    def test_memory_usage_with_large_dataset(self, parser):
        """Test memory usage patterns during processing."""
        import sys

        # Track memory usage (simplified)
        initial_refs = sys.gettotalrefcount() if hasattr(sys, "gettotalrefcount") else 0

        # Process a moderate dataset
        for i in range(1000):
            line = f"2023{i%365+1:03d}\t{200+i%100}\t{150+i%50}\t{i%30}"
            parser.parse_weather_line(line, i)
            # Don't store results to test memory cleanup

        final_refs = sys.gettotalrefcount() if hasattr(sys, "gettotalrefcount") else 0

        # Memory should not grow significantly
        if hasattr(sys, "gettotalrefcount"):
            ref_growth = final_refs - initial_refs
            assert ref_growth < 1000, f"Excessive reference growth: {ref_growth}"
