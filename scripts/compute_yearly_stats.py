#!/usr/bin/env python3
"""
Yearly Weather Statistics Computation Script

This script computes yearly weather statistics from daily weather data
with comprehensive logging, error handling, and progress tracking.

Features:
- Aggregates daily weather data into yearly statistics
- Comprehensive validation and error recovery
- Batch processing with progress tracking
- Django integration support
- Standalone execution capability
- Data quality metrics and reporting

Usage:
    python scripts/compute_yearly_stats.py --year 2023 --log-level INFO
    python scripts/compute_yearly_stats.py --station USC00110072 --clear
    python scripts/compute_yearly_stats.py --dry-run --batch-size 50
"""

import argparse
import logging
import logging.handlers
import os
import sys
import time
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# Add project root to path for Django imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    # Try to import Django components
    import django
    from django.conf import settings

    # Configure Django settings if not already configured
    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")
        django.setup()

    from django.db import transaction
    from django.db.models import Avg, Count, Max, Min, Sum

    from core_django.models.models import (
        DailyWeather,
        WeatherStation,
        YearlyWeatherStats,
    )

    DJANGO_AVAILABLE = True
except ImportError as e:
    print(f"Django not available: {e}")
    DJANGO_AVAILABLE = False


class YearlyStatsConfig:
    """Configuration class for yearly stats computation."""

    def __init__(self):
        self.log_level: str = "INFO"
        self.log_file: str | None = None
        self.batch_size: int = 100
        self.clear_existing: bool = False
        self.dry_run: bool = False
        self.progress_interval: int = 10
        self.enable_metrics: bool = True
        self.log_format: str = "structured"  # structured, simple, json
        self.target_year: int | None = None
        self.target_station: str | None = None
        self.start_year: int | None = None
        self.end_year: int | None = None
        self.force_recompute: bool = False


class YearlyStatsLogger:
    """Enhanced logging configuration for yearly stats computation."""

    def __init__(self, config: YearlyStatsConfig):
        self.config = config
        self.logger = logging.getLogger("yearly_stats")
        self.setup_logging()

    def setup_logging(self):
        """Configure structured logging with file and console handlers."""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Set log level
        log_level = getattr(logging, self.config.log_level.upper())
        self.logger.setLevel(log_level)

        # Create formatters
        if self.config.log_format == "json":
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"module": "%(name)s", "message": "%(message)s", '
                '"function": "%(funcName)s", "line": %(lineno)d}'
            )
        elif self.config.log_format == "structured":
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)-15s | %(funcName)-20s:%(lineno)-4d | %(message)s"
            )
        else:  # simple
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        if self.config.log_file:
            # Ensure logs directory exists
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Rotating file handler (10MB max, 5 backups)
            file_handler = logging.handlers.RotatingFileHandler(
                self.config.log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Suppress some verbose Django logs
        logging.getLogger("django.db.backends").setLevel(logging.WARNING)
        logging.getLogger("django.db.backends.schema").setLevel(logging.WARNING)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger


class YearlyStatsMetrics:
    """Performance and processing metrics tracking."""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.total_combinations: int = 0
        self.processed_combinations: int = 0
        self.successful_computations: int = 0
        self.failed_computations: int = 0
        self.skipped_existing: int = 0
        self.error_count: int = 0
        self.batch_processing_times: list[float] = []
        self.errors_by_type: dict[str, int] = {}

    def start_timing(self):
        """Start timing the computation process."""
        self.start_time = time.time()

    def end_timing(self):
        """End timing the computation process."""
        self.end_time = time.time()

    def add_error(self, error_type: str):
        """Add an error to the metrics."""
        self.error_count += 1
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

    def get_processing_rate(self) -> float:
        """Calculate combinations per second processing rate."""
        if self.end_time > self.start_time and self.processed_combinations > 0:
            return self.processed_combinations / (self.end_time - self.start_time)
        return 0.0

    def get_summary(self) -> dict:
        """Get a summary of metrics."""
        duration = (
            self.end_time - self.start_time if self.end_time > self.start_time else 0
        )

        return {
            "duration_seconds": duration,
            "total_combinations": self.total_combinations,
            "processed_combinations": self.processed_combinations,
            "successful_computations": self.successful_computations,
            "failed_computations": self.failed_computations,
            "skipped_existing": self.skipped_existing,
            "error_count": self.error_count,
            "processing_rate_per_second": self.get_processing_rate(),
            "errors_by_type": self.errors_by_type,
            "success_rate": (
                (self.successful_computations / max(self.processed_combinations, 1))
                * 100
            ),
        }


class YearlyStatsComputer:
    """Main yearly weather statistics computation class."""

    def __init__(self, config: YearlyStatsConfig):
        self.config = config
        self.logger_manager = YearlyStatsLogger(config)
        self.logger = self.logger_manager.get_logger()
        self.metrics = YearlyStatsMetrics()

        # Validate dependencies
        if not DJANGO_AVAILABLE and not config.dry_run:
            raise RuntimeError(
                "Django is required for database operations. Use --dry-run for testing without Django."
            )

    def run(self) -> bool:
        """Main computation process."""
        self.logger.info("📊 Starting yearly weather statistics computation")
        self.logger.info(f"Configuration: {self._log_config()}")

        self.metrics.start_timing()

        try:
            # Validate filters
            if not self._validate_filters():
                return False

            # Clear existing data if requested
            if self.config.clear_existing and not self.config.dry_run:
                self._clear_existing_data()

            # Get station-year combinations to process
            combinations = self._get_station_year_combinations()
            if not combinations:
                self.logger.warning("No station-year combinations found to process")
                return True

            self.metrics.total_combinations = len(combinations)
            self.logger.info(
                f"📋 Found {len(combinations):,} station-year combinations to process"
            )

            # Process combinations in batches
            success = self._process_combinations(combinations)

            self.metrics.end_timing()
            self._log_final_summary()

            return success

        except Exception as e:
            self.logger.error(f"❌ Fatal error during computation: {e}", exc_info=True)
            self.metrics.end_timing()
            return False

    def _validate_filters(self) -> bool:
        """Validate year and station filters."""
        if self.config.target_year:
            if not (1800 <= self.config.target_year <= 2100):
                self.logger.error(f"Invalid target year: {self.config.target_year}")
                return False

        if self.config.start_year and self.config.end_year:
            if self.config.start_year > self.config.end_year:
                self.logger.error(
                    f"Start year ({self.config.start_year}) cannot be after end year ({self.config.end_year})"
                )
                return False

        if self.config.target_station and not self.config.dry_run:
            if DJANGO_AVAILABLE:
                try:
                    WeatherStation.objects.get(station_id=self.config.target_station)
                except WeatherStation.DoesNotExist:
                    self.logger.error(f"Station {self.config.target_station} not found")
                    return False

        self.logger.info("✅ Filters validated successfully")
        return True

    def _clear_existing_data(self):
        """Clear existing yearly statistics from the database."""
        if not DJANGO_AVAILABLE:
            return

        self.logger.info("🗑️  Clearing existing yearly statistics...")

        try:
            filters = {}
            if self.config.target_year:
                filters["year"] = self.config.target_year
            elif self.config.start_year or self.config.end_year:
                if self.config.start_year:
                    filters["year__gte"] = self.config.start_year
                if self.config.end_year:
                    filters["year__lte"] = self.config.end_year

            if self.config.target_station:
                filters["station__station_id"] = self.config.target_station

            if filters:
                stats_count = YearlyWeatherStats.objects.filter(**filters).count()
                YearlyWeatherStats.objects.filter(**filters).delete()
                self.logger.info(
                    f"   • Deleted {stats_count:,} yearly statistics matching filters"
                )
            else:
                stats_count = YearlyWeatherStats.objects.count()
                YearlyWeatherStats.objects.all().delete()
                self.logger.info(f"   • Deleted {stats_count:,} yearly statistics")

        except Exception as e:
            self.logger.error(f"Error clearing existing data: {e}")
            raise

    def _get_station_year_combinations(self) -> list[tuple[str, int]]:
        """Get all station-year combinations that have daily data."""
        if not DJANGO_AVAILABLE:
            return []

        query = DailyWeather.objects.values(
            "station__station_id", "date__year"
        ).distinct()

        # Apply filters
        if self.config.target_station:
            query = query.filter(station__station_id=self.config.target_station)

        if self.config.target_year:
            query = query.filter(date__year=self.config.target_year)
        elif self.config.start_year or self.config.end_year:
            if self.config.start_year:
                query = query.filter(date__year__gte=self.config.start_year)
            if self.config.end_year:
                query = query.filter(date__year__lte=self.config.end_year)

        # Exclude existing combinations unless force recompute
        if not self.config.force_recompute and not self.config.clear_existing:
            existing_combinations = set(
                YearlyWeatherStats.objects.values_list("station__station_id", "year")
            )

            if existing_combinations:
                self.logger.info(
                    f"Found {len(existing_combinations):,} existing yearly statistics"
                )

        combinations = []
        for item in query.order_by("station__station_id", "date__year"):
            station_id = item["station__station_id"]
            year = item["date__year"]

            # Skip existing unless force recompute
            if not self.config.force_recompute and not self.config.clear_existing:
                if (station_id, year) in existing_combinations:
                    self.metrics.skipped_existing += 1
                    continue

            combinations.append((station_id, year))

        return combinations

    def _process_combinations(self, combinations: list[tuple[str, int]]) -> bool:
        """Process all station-year combinations in batches."""
        total_batches = (
            len(combinations) + self.config.batch_size - 1
        ) // self.config.batch_size

        for i in range(0, len(combinations), self.config.batch_size):
            batch = combinations[i : i + self.config.batch_size]
            batch_num = (i // self.config.batch_size) + 1

            self.logger.info(
                f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} combinations)"
            )

            batch_start_time = time.time()

            try:
                batch_success = self._process_batch(batch)
                self.metrics.processed_combinations += len(batch)

                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                self.metrics.batch_processing_times.append(batch_duration)

                self.logger.info(
                    f"   ✅ Batch {batch_num} completed in {batch_duration:.2f}s"
                )

                if not batch_success:
                    self.logger.warning(f"   ⚠️  Batch {batch_num} had some failures")

            except Exception as e:
                self.logger.error(f"   ❌ Error processing batch {batch_num}: {e}")
                self.metrics.add_error("batch_processing_error")
                continue

        return self.metrics.successful_computations > 0

    def _process_batch(self, batch: list[tuple[str, int]]) -> bool:
        """Process a batch of station-year combinations."""
        stats_to_create = []
        batch_success = True

        for station_id, year in batch:
            try:
                yearly_stats = self._compute_yearly_stats(station_id, year)
                if yearly_stats:
                    if not self.config.dry_run:
                        stats_to_create.append(yearly_stats)
                    self.metrics.successful_computations += 1
                else:
                    self.metrics.failed_computations += 1
                    batch_success = False

            except Exception as e:
                self.logger.warning(
                    f"   Error computing stats for {station_id}-{year}: {e}"
                )
                self.metrics.add_error("computation_error")
                self.metrics.failed_computations += 1
                batch_success = False
                continue

        # Save all statistics in this batch
        if not self.config.dry_run and stats_to_create:
            try:
                self._save_yearly_stats_batch(stats_to_create)
            except Exception as e:
                self.logger.error(f"Error saving batch: {e}")
                self.metrics.add_error("save_error")
                batch_success = False

        return batch_success

    def _compute_yearly_stats(
        self, station_id: str, year: int
    ) -> YearlyWeatherStats | None:
        """Compute yearly statistics for a specific station and year."""
        if not DJANGO_AVAILABLE:
            return None

        try:
            # Get the weather station
            station = WeatherStation.objects.get(station_id=station_id)
        except WeatherStation.DoesNotExist:
            self.logger.warning(f"Station {station_id} not found")
            return None

        # Get daily records for this station and year
        daily_records = DailyWeather.objects.filter(station=station, date__year=year)

        if not daily_records.exists():
            self.logger.debug(f"No daily records found for {station_id}-{year}")
            return None

        # Calculate aggregate statistics
        try:
            aggregates = daily_records.aggregate(
                # Temperature statistics
                avg_max_temp=Avg("max_temp"),
                avg_min_temp=Avg("min_temp"),
                max_temp=Max("max_temp"),
                min_temp=Min("min_temp"),
                # Precipitation statistics
                total_precipitation=Sum("precipitation"),
                avg_precipitation=Avg("precipitation"),
                max_precipitation=Max("precipitation"),
                # Total records
                total_records=Count("id"),
            )

            # Calculate data completeness metrics
            records_with_temp = daily_records.filter(
                max_temp__isnull=False, min_temp__isnull=False
            ).count()
            records_with_precipitation = daily_records.filter(
                precipitation__isnull=False
            ).count()

        except Exception as e:
            self.logger.error(
                f"Error calculating aggregates for {station_id}-{year}: {e}"
            )
            return None

        # Round decimal values properly
        def round_decimal(value):
            if value is None:
                return None
            return Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        # Create YearlyWeatherStats object
        yearly_stats = YearlyWeatherStats(
            station=station,
            year=year,
            avg_max_temp=round_decimal(aggregates["avg_max_temp"]),
            avg_min_temp=round_decimal(aggregates["avg_min_temp"]),
            max_temp=aggregates["max_temp"],
            min_temp=aggregates["min_temp"],
            total_precipitation=aggregates["total_precipitation"],
            avg_precipitation=round_decimal(aggregates["avg_precipitation"]),
            max_precipitation=aggregates["max_precipitation"],
            total_records=aggregates["total_records"],
            records_with_temp=records_with_temp,
            records_with_precipitation=records_with_precipitation,
        )

        self.logger.debug(
            f"📊 {station_id}-{year}: Records={aggregates['total_records']}, "
            f"AvgMax={yearly_stats.avg_max_temp_celsius}°C, "
            f"TotalPrecip={yearly_stats.total_precipitation_mm}mm"
        )

        return yearly_stats

    def _save_yearly_stats_batch(self, yearly_stats: list[YearlyWeatherStats]):
        """Save a batch of yearly statistics to the database."""
        if not DJANGO_AVAILABLE:
            return

        try:
            with transaction.atomic():
                YearlyWeatherStats.objects.bulk_create(
                    yearly_stats,
                    ignore_conflicts=True,
                    batch_size=self.config.batch_size,
                )
        except Exception as e:
            self.logger.error(f"Error saving yearly stats batch: {e}")
            raise

    def _log_config(self) -> str:
        """Log the current configuration."""
        config_parts = [
            f"batch_size={self.config.batch_size}",
            f"dry_run={self.config.dry_run}",
            f"clear_existing={self.config.clear_existing}",
        ]

        if self.config.target_year:
            config_parts.append(f"target_year={self.config.target_year}")
        if self.config.target_station:
            config_parts.append(f"target_station={self.config.target_station}")
        if self.config.start_year:
            config_parts.append(f"start_year={self.config.start_year}")
        if self.config.end_year:
            config_parts.append(f"end_year={self.config.end_year}")

        return ", ".join(config_parts)

    def _log_final_summary(self):
        """Log final processing summary with metrics."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎉 Yearly statistics computation complete!")
        self.logger.info("=" * 80)

        summary = self.metrics.get_summary()

        self.logger.info("📊 Processing Summary:")
        self.logger.info(f"   • Duration: {summary['duration_seconds']:.2f} seconds")
        self.logger.info(
            f"   • Combinations processed: {summary['processed_combinations']}/{summary['total_combinations']}"
        )
        self.logger.info(
            f"   • Successful computations: {summary['successful_computations']:,}"
        )
        self.logger.info(
            f"   • Failed computations: {summary['failed_computations']:,}"
        )
        self.logger.info(f"   • Skipped existing: {summary['skipped_existing']:,}")
        self.logger.info(
            f"   • Processing rate: {summary['processing_rate_per_second']:.2f} combinations/second"
        )
        self.logger.info(f"   • Success rate: {summary['success_rate']:.2f}%")

        if summary["error_count"] > 0:
            self.logger.warning("⚠️  Issues encountered:")
            self.logger.warning(f"   • Total errors: {summary['error_count']}")

            if summary["errors_by_type"]:
                self.logger.warning("   • Error breakdown:")
                for error_type, count in summary["errors_by_type"].items():
                    self.logger.warning(f"     - {error_type}: {count}")

        if not self.config.dry_run and DJANGO_AVAILABLE:
            try:
                db_stats = YearlyWeatherStats.objects.count()
                self.logger.info("\n📋 Database verification:")
                self.logger.info(f"   • Total yearly statistics in DB: {db_stats:,}")

                if self.config.target_year:
                    year_stats = YearlyWeatherStats.objects.filter(
                        year=self.config.target_year
                    ).count()
                    self.logger.info(
                        f"   • Statistics for {self.config.target_year}: {year_stats:,}"
                    )

                if self.config.target_station:
                    station_stats = YearlyWeatherStats.objects.filter(
                        station__station_id=self.config.target_station
                    ).count()
                    self.logger.info(
                        f"   • Statistics for {self.config.target_station}: {station_stats:,}"
                    )

            except Exception as e:
                self.logger.warning(f"Could not verify database counts: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Yearly Weather Statistics Computation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Compute all yearly statistics
    python scripts/compute_yearly_stats.py

    # Compute for specific year
    python scripts/compute_yearly_stats.py --year 2023

    # Compute for specific station
    python scripts/compute_yearly_stats.py --station USC00110072

    # Compute for year range
    python scripts/compute_yearly_stats.py --start-year 2020 --end-year 2023

    # Clear existing and recompute
    python scripts/compute_yearly_stats.py --clear --year 2023

    # Dry run with detailed logging
    python scripts/compute_yearly_stats.py --dry-run --log-level DEBUG

    # JSON logging for automation
    python scripts/compute_yearly_stats.py --log-format json --log-file logs/yearly_stats.json

    # Force recompute existing statistics
    python scripts/compute_yearly_stats.py --force-recompute --year 2023
        """,
    )

    # Input filters
    parser.add_argument(
        "--year",
        type=int,
        help="Compute statistics for specific year only",
    )

    parser.add_argument(
        "--station",
        help="Compute statistics for specific station only (e.g., USC00110072)",
    )

    parser.add_argument(
        "--start-year",
        type=int,
        help="Compute statistics starting from this year (inclusive)",
    )

    parser.add_argument(
        "--end-year",
        type=int,
        help="Compute statistics up to this year (inclusive)",
    )

    # Processing options
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of station-year combinations to process in each batch (default: 100)",
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing yearly statistics before computing",
    )

    parser.add_argument(
        "--force-recompute",
        action="store_true",
        help="Force recomputation of existing statistics",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute statistics but don't save to database",
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-file",
        help="Log file path (default: console only)",
    )

    parser.add_argument(
        "--log-format",
        choices=["simple", "structured", "json"],
        default="structured",
        help="Log format (default: structured)",
    )

    parser.add_argument(
        "--progress-interval",
        type=int,
        default=10,
        help="Progress reporting interval for batches (default: 10)",
    )

    return parser


def main():
    """Main entry point for the script."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Create configuration
    config = YearlyStatsConfig()
    config.log_level = args.log_level
    config.log_file = args.log_file
    config.log_format = args.log_format
    config.batch_size = args.batch_size
    config.clear_existing = args.clear
    config.force_recompute = args.force_recompute
    config.dry_run = args.dry_run
    config.progress_interval = args.progress_interval
    config.target_year = args.year
    config.target_station = args.station
    config.start_year = args.start_year
    config.end_year = args.end_year

    # Run computation
    try:
        computer = YearlyStatsComputer(config)
        success = computer.run()

        if success:
            print("\n✅ Yearly statistics computation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Yearly statistics computation failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Computation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
