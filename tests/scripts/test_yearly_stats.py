#!/usr/bin/env python3
"""
Unit tests for yearly weather statistics computation script.

This test suite covers all classes and methods in the compute_yearly_stats.py script
with comprehensive validation of computation logic, error handling, and Django integration.
"""

import logging
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

# ruff: noqa: E402
# Django setup must happen before importing models
import django
from django.conf import settings
from django.test import TestCase, TransactionTestCase

if not settings.configured:
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")
    django.setup()


from core_django.models.models import DailyWeather, WeatherStation, YearlyWeatherStats

# Import the module we're testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.compute_yearly_stats import (
    YearlyStatsComputer,
    YearlyStatsConfig,
    YearlyStatsLogger,
    YearlyStatsMetrics,
    create_argument_parser,
    main,
)


class TestYearlyStatsConfig(unittest.TestCase):
    """Test YearlyStatsConfig configuration class."""

    def test_config_defaults(self):
        """Test that configuration has correct default values."""
        config = YearlyStatsConfig()

        self.assertEqual(config.log_level, "INFO")
        self.assertIsNone(config.log_file)
        self.assertEqual(config.batch_size, 100)
        self.assertFalse(config.clear_existing)
        self.assertFalse(config.dry_run)
        self.assertEqual(config.progress_interval, 10)
        self.assertTrue(config.enable_metrics)
        self.assertEqual(config.log_format, "structured")
        self.assertIsNone(config.target_year)
        self.assertIsNone(config.target_station)
        self.assertIsNone(config.start_year)
        self.assertIsNone(config.end_year)
        self.assertFalse(config.force_recompute)

    def test_config_assignment(self):
        """Test that configuration values can be assigned."""
        config = YearlyStatsConfig()

        config.log_level = "DEBUG"
        config.log_file = "/tmp/test.log"
        config.batch_size = 50
        config.clear_existing = True
        config.dry_run = True
        config.target_year = 2023
        config.target_station = "USC00110072"
        config.start_year = 2020
        config.end_year = 2023
        config.force_recompute = True

        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.log_file, "/tmp/test.log")
        self.assertEqual(config.batch_size, 50)
        self.assertTrue(config.clear_existing)
        self.assertTrue(config.dry_run)
        self.assertEqual(config.target_year, 2023)
        self.assertEqual(config.target_station, "USC00110072")
        self.assertEqual(config.start_year, 2020)
        self.assertEqual(config.end_year, 2023)
        self.assertTrue(config.force_recompute)


class TestYearlyStatsLogger(unittest.TestCase):
    """Test YearlyStatsLogger logging configuration."""

    def setUp(self):
        """Set up test configuration."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "INFO"
        self.config.log_format = "structured"

    def test_logger_creation(self):
        """Test logger creation and configuration."""
        logger_manager = YearlyStatsLogger(self.config)
        logger = logger_manager.get_logger()

        self.assertEqual(logger.name, "yearly_stats")
        self.assertEqual(logger.level, logging.INFO)
        self.assertTrue(len(logger.handlers) > 0)

    def test_structured_format(self):
        """Test structured log format."""
        self.config.log_format = "structured"
        logger_manager = YearlyStatsLogger(self.config)

        # Check that handlers are configured correctly
        handlers = logger_manager.logger.handlers
        self.assertTrue(len(handlers) > 0)

        # Check console handler formatter
        console_handler = handlers[0]
        self.assertIsInstance(console_handler, logging.StreamHandler)

    def test_json_format(self):
        """Test JSON log format."""
        self.config.log_format = "json"
        logger_manager = YearlyStatsLogger(self.config)

        handlers = logger_manager.logger.handlers
        self.assertTrue(len(handlers) > 0)

        # Check that JSON formatter is used
        formatter = handlers[0].formatter
        self.assertIsInstance(formatter, logging.Formatter)

    def test_simple_format(self):
        """Test simple log format."""
        self.config.log_format = "simple"
        logger_manager = YearlyStatsLogger(self.config)

        handlers = logger_manager.logger.handlers
        self.assertTrue(len(handlers) > 0)

    def test_file_logging(self):
        """Test file logging configuration."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.config.log_file = temp_file.name
            logger_manager = YearlyStatsLogger(self.config)

            handlers = logger_manager.logger.handlers
            self.assertEqual(len(handlers), 2)  # Console + file

            # Check file handler
            file_handler = handlers[1]
            self.assertIsInstance(file_handler, logging.handlers.RotatingFileHandler)

    def test_log_level_setting(self):
        """Test different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            self.config.log_level = level
            logger_manager = YearlyStatsLogger(self.config)
            logger = logger_manager.get_logger()

            expected_level = getattr(logging, level)
            self.assertEqual(logger.level, expected_level)


class TestYearlyStatsMetrics(unittest.TestCase):
    """Test YearlyStatsMetrics performance tracking."""

    def setUp(self):
        """Set up test metrics."""
        self.metrics = YearlyStatsMetrics()

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        self.assertEqual(self.metrics.start_time, 0.0)
        self.assertEqual(self.metrics.end_time, 0.0)
        self.assertEqual(self.metrics.total_combinations, 0)
        self.assertEqual(self.metrics.processed_combinations, 0)
        self.assertEqual(self.metrics.successful_computations, 0)
        self.assertEqual(self.metrics.failed_computations, 0)
        self.assertEqual(self.metrics.skipped_existing, 0)
        self.assertEqual(self.metrics.error_count, 0)
        self.assertEqual(self.metrics.batch_processing_times, [])
        self.assertEqual(self.metrics.errors_by_type, {})

    def test_timing_methods(self):
        """Test timing functionality."""
        import time

        self.metrics.start_timing()
        start_time = self.metrics.start_time
        self.assertGreater(start_time, 0)

        time.sleep(0.01)  # Small delay

        self.metrics.end_timing()
        end_time = self.metrics.end_time
        self.assertGreater(end_time, start_time)

    def test_error_tracking(self):
        """Test error tracking functionality."""
        self.metrics.add_error("computation_error")
        self.metrics.add_error("save_error")
        self.metrics.add_error("computation_error")

        self.assertEqual(self.metrics.error_count, 3)
        self.assertEqual(self.metrics.errors_by_type["computation_error"], 2)
        self.assertEqual(self.metrics.errors_by_type["save_error"], 1)

    def test_processing_rate(self):
        """Test processing rate calculation."""
        # Test with no processing
        self.assertEqual(self.metrics.get_processing_rate(), 0.0)

        # Test with processing - simulate timing
        import time

        self.metrics.start_timing()
        time.sleep(0.01)  # Small delay to ensure timing difference
        self.metrics.processed_combinations = 100
        self.metrics.end_timing()

        rate = self.metrics.get_processing_rate()
        self.assertGreater(rate, 0)

    def test_summary_generation(self):
        """Test metrics summary generation."""
        # Set up some test data
        self.metrics.start_timing()
        self.metrics.total_combinations = 150
        self.metrics.processed_combinations = 140
        self.metrics.successful_computations = 135
        self.metrics.failed_computations = 5
        self.metrics.skipped_existing = 10
        self.metrics.add_error("test_error")
        self.metrics.end_timing()

        summary = self.metrics.get_summary()

        # Check summary structure
        required_keys = [
            "duration_seconds",
            "total_combinations",
            "processed_combinations",
            "successful_computations",
            "failed_computations",
            "skipped_existing",
            "error_count",
            "processing_rate_per_second",
            "errors_by_type",
            "success_rate",
        ]

        for key in required_keys:
            self.assertIn(key, summary)

        # Check specific values
        self.assertEqual(summary["total_combinations"], 150)
        self.assertEqual(summary["processed_combinations"], 140)
        self.assertEqual(summary["successful_computations"], 135)
        self.assertEqual(summary["failed_computations"], 5)
        self.assertEqual(summary["skipped_existing"], 10)
        self.assertEqual(summary["error_count"], 1)
        self.assertAlmostEqual(summary["success_rate"], 96.43, places=2)


class TestYearlyStatsComputerInit(TestCase):
    """Test YearlyStatsComputer initialization."""

    def setUp(self):
        """Set up test configuration."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "ERROR"  # Reduce log noise in tests

    def test_computer_initialization(self):
        """Test computer initialization."""
        computer = YearlyStatsComputer(self.config)

        self.assertEqual(computer.config, self.config)
        self.assertIsInstance(computer.logger_manager, YearlyStatsLogger)
        self.assertIsInstance(computer.metrics, YearlyStatsMetrics)
        self.assertIsNotNone(computer.logger)

    def test_django_availability_check(self):
        """Test Django availability validation."""
        # Should work with Django available
        computer = YearlyStatsComputer(self.config)
        self.assertIsNotNone(computer)

        # Should fail without Django in non-dry-run mode
        self.config.dry_run = False
        with patch("scripts.compute_yearly_stats.DJANGO_AVAILABLE", False):
            with self.assertRaises(RuntimeError):
                YearlyStatsComputer(self.config)

    def test_dry_run_without_django(self):
        """Test dry run mode without Django."""
        self.config.dry_run = True

        with patch("scripts.compute_yearly_stats.DJANGO_AVAILABLE", False):
            computer = YearlyStatsComputer(self.config)
            self.assertIsNotNone(computer)


class TestYearlyStatsComputerValidation(TestCase):
    """Test YearlyStatsComputer validation methods."""

    def setUp(self):
        """Set up test configuration and computer."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "ERROR"
        self.computer = YearlyStatsComputer(self.config)

    def test_year_validation(self):
        """Test year filter validation."""
        # Valid year
        self.config.target_year = 2023
        self.assertTrue(self.computer._validate_filters())

        # Invalid year - too low
        self.config.target_year = 1799
        self.assertFalse(self.computer._validate_filters())

        # Invalid year - too high
        self.config.target_year = 2101
        self.assertFalse(self.computer._validate_filters())

    def test_year_range_validation(self):
        """Test year range validation."""
        # Valid range
        self.config.start_year = 2020
        self.config.end_year = 2023
        self.assertTrue(self.computer._validate_filters())

        # Invalid range - start after end
        self.config.start_year = 2023
        self.config.end_year = 2020
        self.assertFalse(self.computer._validate_filters())

    def test_station_validation_dry_run(self):
        """Test station validation in dry run mode."""
        self.config.dry_run = True
        self.config.target_station = "USC00110072"

        # Should pass validation in dry run mode
        self.assertTrue(self.computer._validate_filters())

    def test_station_validation_with_django(self):
        """Test station validation with Django."""
        self.config.dry_run = False
        self.config.target_station = "USC00110072"

        # Create a test station
        _station = WeatherStation.objects.create(
            station_id="USC00110072", name="Test Station", state="IL"
        )

        # Should pass validation
        self.assertTrue(self.computer._validate_filters())

        # Test with non-existent station
        self.config.target_station = "USC00999999"
        self.assertFalse(self.computer._validate_filters())


class TestYearlyStatsComputerStatistics(TransactionTestCase):
    """Test YearlyStatsComputer statistics computation."""

    def setUp(self):
        """Set up test data."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "ERROR"
        self.computer = YearlyStatsComputer(self.config)

        # Create test weather station
        self.station = WeatherStation.objects.create(
            station_id="USC00110072", name="Test Station", state="IL"
        )

        # Create test daily weather data
        self.daily_records = [
            DailyWeather.objects.create(
                station=self.station,
                date=date(2023, 1, 1),
                max_temp=100,  # 10.0°C
                min_temp=50,  # 5.0°C
                precipitation=25,  # 2.5mm
            ),
            DailyWeather.objects.create(
                station=self.station,
                date=date(2023, 1, 2),
                max_temp=150,  # 15.0°C
                min_temp=75,  # 7.5°C
                precipitation=50,  # 5.0mm
            ),
            DailyWeather.objects.create(
                station=self.station,
                date=date(2023, 1, 3),
                max_temp=200,  # 20.0°C
                min_temp=100,  # 10.0°C
                precipitation=None,  # Missing
            ),
        ]

    def test_compute_yearly_stats(self):
        """Test yearly statistics computation."""
        stats = self.computer._compute_yearly_stats("USC00110072", 2023)

        self.assertIsNotNone(stats)
        self.assertEqual(stats.station, self.station)
        self.assertEqual(stats.year, 2023)
        self.assertEqual(stats.total_records, 3)
        self.assertEqual(stats.records_with_temp, 3)
        self.assertEqual(stats.records_with_precipitation, 2)

        # Check temperature statistics
        self.assertEqual(stats.avg_max_temp, Decimal("150.0"))  # (100+150+200)/3
        self.assertEqual(stats.avg_min_temp, Decimal("75.0"))  # (50+75+100)/3
        self.assertEqual(stats.max_temp, 200)
        self.assertEqual(stats.min_temp, 50)

        # Check precipitation statistics
        self.assertEqual(stats.total_precipitation, 75)  # 25+50
        self.assertEqual(stats.avg_precipitation, Decimal("37.5"))  # 75/2
        self.assertEqual(stats.max_precipitation, 50)

    def test_compute_yearly_stats_nonexistent_station(self):
        """Test computation with non-existent station."""
        stats = self.computer._compute_yearly_stats("USC00999999", 2023)
        self.assertIsNone(stats)

    def test_compute_yearly_stats_no_data(self):
        """Test computation with no data for the year."""
        stats = self.computer._compute_yearly_stats("USC00110072", 2022)
        self.assertIsNone(stats)

    def test_compute_yearly_stats_missing_values(self):
        """Test computation with missing temperature values."""
        # Create record with missing temperatures
        DailyWeather.objects.create(
            station=self.station,
            date=date(2023, 1, 4),
            max_temp=None,
            min_temp=None,
            precipitation=100,
        )

        stats = self.computer._compute_yearly_stats("USC00110072", 2023)

        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_records, 4)
        self.assertEqual(stats.records_with_temp, 3)  # Only 3 have both max and min
        self.assertEqual(stats.records_with_precipitation, 3)

    def test_compute_yearly_stats_all_missing_temps(self):
        """Test computation with all missing temperatures."""
        # Clear existing data
        DailyWeather.objects.filter(station=self.station).delete()

        # Create records with no temperature data
        DailyWeather.objects.create(
            station=self.station,
            date=date(2023, 1, 1),
            max_temp=None,
            min_temp=None,
            precipitation=25,
        )

        stats = self.computer._compute_yearly_stats("USC00110072", 2023)

        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_records, 1)
        self.assertEqual(stats.records_with_temp, 0)
        self.assertEqual(stats.records_with_precipitation, 1)
        self.assertIsNone(stats.avg_max_temp)
        self.assertIsNone(stats.avg_min_temp)
        self.assertIsNone(stats.max_temp)
        self.assertIsNone(stats.min_temp)

    def test_save_yearly_stats_batch(self):
        """Test saving yearly statistics in batch."""
        # Compute stats
        stats = self.computer._compute_yearly_stats("USC00110072", 2023)

        # Save batch
        self.computer._save_yearly_stats_batch([stats])

        # Verify saved
        saved_stats = YearlyWeatherStats.objects.get(station=self.station, year=2023)
        self.assertEqual(saved_stats.total_records, 3)
        self.assertEqual(saved_stats.avg_max_temp, Decimal("150.0"))

    def test_save_yearly_stats_batch_conflict(self):
        """Test saving batch with duplicate entries."""
        stats = self.computer._compute_yearly_stats("USC00110072", 2023)

        # Save twice - should handle conflict gracefully
        self.computer._save_yearly_stats_batch([stats])
        self.computer._save_yearly_stats_batch([stats])

        # Should still have only one record
        count = YearlyWeatherStats.objects.filter(
            station=self.station, year=2023
        ).count()
        self.assertEqual(count, 1)


class TestYearlyStatsComputerCombinations(TransactionTestCase):
    """Test YearlyStatsComputer station-year combinations."""

    def setUp(self):
        """Set up test data."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "ERROR"
        self.computer = YearlyStatsComputer(self.config)

        # Create test stations
        self.station1 = WeatherStation.objects.create(
            station_id="USC00110072", name="Station 1", state="IL"
        )
        self.station2 = WeatherStation.objects.create(
            station_id="USC00110073", name="Station 2", state="IL"
        )

        # Create daily weather data
        DailyWeather.objects.create(
            station=self.station1,
            date=date(2022, 1, 1),
            max_temp=100,
            min_temp=50,
            precipitation=25,
        )
        DailyWeather.objects.create(
            station=self.station1,
            date=date(2023, 1, 1),
            max_temp=150,
            min_temp=75,
            precipitation=50,
        )
        DailyWeather.objects.create(
            station=self.station2,
            date=date(2023, 1, 1),
            max_temp=200,
            min_temp=100,
            precipitation=75,
        )

    def test_get_station_year_combinations_all(self):
        """Test getting all station-year combinations."""
        combinations = self.computer._get_station_year_combinations()

        expected = [
            ("USC00110072", 2022),
            ("USC00110072", 2023),
            ("USC00110073", 2023),
        ]

        self.assertEqual(sorted(combinations), sorted(expected))

    def test_get_station_year_combinations_target_year(self):
        """Test filtering by target year."""
        self.config.target_year = 2023
        combinations = self.computer._get_station_year_combinations()

        expected = [
            ("USC00110072", 2023),
            ("USC00110073", 2023),
        ]

        self.assertEqual(sorted(combinations), sorted(expected))

    def test_get_station_year_combinations_target_station(self):
        """Test filtering by target station."""
        self.config.target_station = "USC00110072"
        combinations = self.computer._get_station_year_combinations()

        expected = [
            ("USC00110072", 2022),
            ("USC00110072", 2023),
        ]

        self.assertEqual(sorted(combinations), sorted(expected))

    def test_get_station_year_combinations_year_range(self):
        """Test filtering by year range."""
        self.config.start_year = 2023
        self.config.end_year = 2023
        combinations = self.computer._get_station_year_combinations()

        expected = [
            ("USC00110072", 2023),
            ("USC00110073", 2023),
        ]

        self.assertEqual(sorted(combinations), sorted(expected))

    def test_get_station_year_combinations_exclude_existing(self):
        """Test excluding existing statistics."""
        # Create existing yearly stats
        YearlyWeatherStats.objects.create(
            station=self.station1,
            year=2023,
            total_records=1,
            records_with_temp=1,
            records_with_precipitation=1,
        )

        combinations = self.computer._get_station_year_combinations()

        # Should exclude the existing combination
        expected = [
            ("USC00110072", 2022),
            ("USC00110073", 2023),
        ]

        self.assertEqual(sorted(combinations), sorted(expected))
        self.assertEqual(self.computer.metrics.skipped_existing, 1)

    def test_get_station_year_combinations_force_recompute(self):
        """Test force recompute option."""
        # Create existing yearly stats
        YearlyWeatherStats.objects.create(
            station=self.station1,
            year=2023,
            total_records=1,
            records_with_temp=1,
            records_with_precipitation=1,
        )

        self.config.force_recompute = True
        combinations = self.computer._get_station_year_combinations()

        # Should include all combinations
        expected = [
            ("USC00110072", 2022),
            ("USC00110072", 2023),
            ("USC00110073", 2023),
        ]

        self.assertEqual(sorted(combinations), sorted(expected))


class TestYearlyStatsComputerClearData(TransactionTestCase):
    """Test YearlyStatsComputer data clearing functionality."""

    def setUp(self):
        """Set up test data."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "ERROR"
        self.computer = YearlyStatsComputer(self.config)

        # Create test stations
        self.station1 = WeatherStation.objects.create(
            station_id="USC00110072", name="Station 1", state="IL"
        )
        self.station2 = WeatherStation.objects.create(
            station_id="USC00110073", name="Station 2", state="CA"
        )

        # Create yearly statistics
        YearlyWeatherStats.objects.create(
            station=self.station1,
            year=2022,
            total_records=365,
            records_with_temp=365,
            records_with_precipitation=300,
        )
        YearlyWeatherStats.objects.create(
            station=self.station1,
            year=2023,
            total_records=365,
            records_with_temp=365,
            records_with_precipitation=310,
        )
        YearlyWeatherStats.objects.create(
            station=self.station2,
            year=2023,
            total_records=365,
            records_with_temp=365,
            records_with_precipitation=290,
        )

    def test_clear_all_data(self):
        """Test clearing all existing data."""
        # Verify we have data
        self.assertEqual(YearlyWeatherStats.objects.count(), 3)

        # Clear all data
        self.computer._clear_existing_data()

        # Verify all data is cleared
        self.assertEqual(YearlyWeatherStats.objects.count(), 0)

    def test_clear_data_by_year(self):
        """Test clearing data by specific year."""
        self.config.target_year = 2023

        # Clear data for 2023
        self.computer._clear_existing_data()

        # Verify only 2023 data is cleared
        remaining = YearlyWeatherStats.objects.all()
        self.assertEqual(remaining.count(), 1)
        self.assertEqual(remaining.first().year, 2022)

    def test_clear_data_by_station(self):
        """Test clearing data by specific station."""
        self.config.target_station = "USC00110072"

        # Clear data for station 1
        self.computer._clear_existing_data()

        # Verify only station 1 data is cleared
        remaining = YearlyWeatherStats.objects.all()
        self.assertEqual(remaining.count(), 1)
        self.assertEqual(remaining.first().station.station_id, "USC00110073")

    def test_clear_data_by_year_range(self):
        """Test clearing data by year range."""
        self.config.start_year = 2023
        self.config.end_year = 2023

        # Clear data for 2023
        self.computer._clear_existing_data()

        # Verify only 2023 data is cleared
        remaining = YearlyWeatherStats.objects.all()
        self.assertEqual(remaining.count(), 1)
        self.assertEqual(remaining.first().year, 2022)

    def test_clear_data_combined_filters(self):
        """Test clearing data with combined filters."""
        self.config.target_year = 2023
        self.config.target_station = "USC00110072"

        # Clear data for station 1 in 2023
        self.computer._clear_existing_data()

        # Verify only that specific combination is cleared
        remaining = YearlyWeatherStats.objects.all()
        self.assertEqual(remaining.count(), 2)

        # Check remaining records
        years = [stats.year for stats in remaining]
        stations = [stats.station.station_id for stats in remaining]

        self.assertIn(2022, years)
        self.assertIn("USC00110073", stations)


class TestYearlyStatsComputerIntegration(TransactionTestCase):
    """Test YearlyStatsComputer integration scenarios."""

    def setUp(self):
        """Set up test data."""
        self.config = YearlyStatsConfig()
        self.config.log_level = "ERROR"
        self.config.batch_size = 2

        # Create test stations
        self.station1 = WeatherStation.objects.create(
            station_id="USC00110072", name="Station 1", state="IL"
        )
        self.station2 = WeatherStation.objects.create(
            station_id="USC00110073", name="Station 2", state="IL"
        )

        # Create daily weather data
        for i in range(3):
            DailyWeather.objects.create(
                station=self.station1,
                date=date(2023, 1, i + 1),
                max_temp=100 + i * 10,
                min_temp=50 + i * 5,
                precipitation=25 + i * 5,
            )
            DailyWeather.objects.create(
                station=self.station2,
                date=date(2023, 1, i + 1),
                max_temp=200 + i * 10,
                min_temp=150 + i * 5,
                precipitation=50 + i * 10,
            )

    def test_full_computation_process(self):
        """Test the full computation process."""
        computer = YearlyStatsComputer(self.config)
        success = computer.run()

        self.assertTrue(success)
        self.assertEqual(computer.metrics.total_combinations, 2)
        self.assertEqual(computer.metrics.successful_computations, 2)
        self.assertEqual(computer.metrics.failed_computations, 0)

        # Verify statistics were created
        stats = YearlyWeatherStats.objects.all()
        self.assertEqual(stats.count(), 2)

    def test_dry_run_mode(self):
        """Test dry run mode."""
        self.config.dry_run = True
        computer = YearlyStatsComputer(self.config)
        success = computer.run()

        self.assertTrue(success)
        self.assertEqual(computer.metrics.successful_computations, 2)

        # Verify no statistics were saved
        stats = YearlyWeatherStats.objects.all()
        self.assertEqual(stats.count(), 0)

    def test_batch_processing(self):
        """Test batch processing functionality."""
        self.config.batch_size = 1  # Process one at a time
        computer = YearlyStatsComputer(self.config)
        success = computer.run()

        self.assertTrue(success)
        self.assertEqual(computer.metrics.successful_computations, 2)
        self.assertEqual(len(computer.metrics.batch_processing_times), 2)

    def test_error_handling(self):
        """Test error handling during computation."""
        computer = YearlyStatsComputer(self.config)

        # Mock a computation error
        with patch.object(computer, "_compute_yearly_stats") as mock_compute:
            mock_compute.side_effect = Exception("Test error")

            success = computer.run()

            self.assertFalse(success)
            self.assertEqual(computer.metrics.failed_computations, 2)
            self.assertEqual(computer.metrics.error_count, 2)
            self.assertIn("computation_error", computer.metrics.errors_by_type)


class TestArgumentParser(unittest.TestCase):
    """Test command line argument parsing."""

    def setUp(self):
        """Set up argument parser."""
        self.parser = create_argument_parser()

    def test_default_arguments(self):
        """Test default argument values."""
        args = self.parser.parse_args([])

        self.assertIsNone(args.year)
        self.assertIsNone(args.station)
        self.assertIsNone(args.start_year)
        self.assertIsNone(args.end_year)
        self.assertEqual(args.batch_size, 100)
        self.assertFalse(args.clear)
        self.assertFalse(args.force_recompute)
        self.assertFalse(args.dry_run)
        self.assertEqual(args.log_level, "INFO")
        self.assertIsNone(args.log_file)
        self.assertEqual(args.log_format, "structured")
        self.assertEqual(args.progress_interval, 10)

    def test_year_argument(self):
        """Test year argument parsing."""
        args = self.parser.parse_args(["--year", "2023"])
        self.assertEqual(args.year, 2023)

    def test_station_argument(self):
        """Test station argument parsing."""
        args = self.parser.parse_args(["--station", "USC00110072"])
        self.assertEqual(args.station, "USC00110072")

    def test_year_range_arguments(self):
        """Test year range argument parsing."""
        args = self.parser.parse_args(["--start-year", "2020", "--end-year", "2023"])
        self.assertEqual(args.start_year, 2020)
        self.assertEqual(args.end_year, 2023)

    def test_processing_arguments(self):
        """Test processing argument parsing."""
        args = self.parser.parse_args(
            ["--batch-size", "50", "--clear", "--force-recompute", "--dry-run"]
        )

        self.assertEqual(args.batch_size, 50)
        self.assertTrue(args.clear)
        self.assertTrue(args.force_recompute)
        self.assertTrue(args.dry_run)

    def test_logging_arguments(self):
        """Test logging argument parsing."""
        args = self.parser.parse_args(
            [
                "--log-level",
                "DEBUG",
                "--log-file",
                "/tmp/test.log",
                "--log-format",
                "json",
                "--progress-interval",
                "5",
            ]
        )

        self.assertEqual(args.log_level, "DEBUG")
        self.assertEqual(args.log_file, "/tmp/test.log")
        self.assertEqual(args.log_format, "json")
        self.assertEqual(args.progress_interval, 5)

    def test_invalid_log_level(self):
        """Test invalid log level argument."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--log-level", "INVALID"])

    def test_invalid_log_format(self):
        """Test invalid log format argument."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--log-format", "invalid"])


class TestMainFunction(unittest.TestCase):
    """Test main function execution."""

    def test_main_success(self):
        """Test successful main execution."""
        test_args = ["--dry-run", "--log-level", "ERROR"]

        with patch("sys.argv", ["compute_yearly_stats.py"] + test_args):
            with patch(
                "scripts.compute_yearly_stats.YearlyStatsComputer"
            ) as mock_computer_class:
                mock_computer = Mock()
                mock_computer.run.return_value = True
                mock_computer_class.return_value = mock_computer

                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 0)
                mock_computer.run.assert_called_once()

    def test_main_failure(self):
        """Test main execution with failure."""
        test_args = ["--dry-run", "--log-level", "ERROR"]

        with patch("sys.argv", ["compute_yearly_stats.py"] + test_args):
            with patch(
                "scripts.compute_yearly_stats.YearlyStatsComputer"
            ) as mock_computer_class:
                mock_computer = Mock()
                mock_computer.run.return_value = False
                mock_computer_class.return_value = mock_computer

                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 1)

    def test_main_keyboard_interrupt(self):
        """Test main execution with keyboard interrupt."""
        test_args = ["--dry-run", "--log-level", "ERROR"]

        with patch("sys.argv", ["compute_yearly_stats.py"] + test_args):
            with patch(
                "scripts.compute_yearly_stats.YearlyStatsComputer"
            ) as mock_computer_class:
                mock_computer = Mock()
                mock_computer.run.side_effect = KeyboardInterrupt()
                mock_computer_class.return_value = mock_computer

                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 1)

    def test_main_exception(self):
        """Test main execution with exception."""
        test_args = ["--dry-run", "--log-level", "ERROR"]

        with patch("sys.argv", ["compute_yearly_stats.py"] + test_args):
            with patch(
                "scripts.compute_yearly_stats.YearlyStatsComputer"
            ) as mock_computer_class:
                mock_computer_class.side_effect = Exception("Test error")

                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
