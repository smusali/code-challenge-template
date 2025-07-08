#!/usr/bin/env python3
"""
Weather Data Ingestion Script with Structured Logging

This script provides a robust CLI tool for ingesting weather station data
with comprehensive logging, error handling, and progress tracking.

Features:
- Structured logging with configurable levels
- File and console output with rotating log files
- Batch processing with progress tracking
- Data validation and error recovery
- Performance metrics and statistics
- Django integration support
- Standalone execution capability

Usage:
    python scripts/ingest_weather_data.py --data-dir wx_data --log-level INFO
    python scripts/ingest_weather_data.py --clear --batch-size 2000 --dry-run
"""

import argparse
import glob
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
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

    from core_django.models.models import DailyWeather, WeatherStation

    DJANGO_AVAILABLE = True
except ImportError as e:
    print(f"Django not available: {e}")
    DJANGO_AVAILABLE = False


class WeatherDataIngestorConfig:
    """Configuration class for weather data ingestion."""

    def __init__(self):
        self.data_dir: str = "wx_data"
        self.log_level: str = "INFO"
        self.log_file: str | None = None
        self.batch_size: int = 1000
        self.clear_existing: bool = False
        self.dry_run: bool = False
        self.max_workers: int = 1
        self.progress_interval: int = 100
        self.enable_metrics: bool = True
        self.log_format: str = "structured"  # structured, simple, json


class WeatherDataLogger:
    """Enhanced logging configuration with structured output."""

    def __init__(self, config: WeatherDataIngestorConfig):
        self.config = config
        self.logger = logging.getLogger("weather_ingestion")
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
                "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s:%(lineno)-4d | %(message)s"
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
                backupCount=5,  # 10MB
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Suppress some verbose Django logs
        logging.getLogger("django.db.backends").setLevel(logging.WARNING)
        logging.getLogger("django.db.backends.schema").setLevel(logging.WARNING)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger


class WeatherDataMetrics:
    """Performance and processing metrics tracking."""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.total_files: int = 0
        self.processed_files: int = 0
        self.total_records: int = 0
        self.processed_records: int = 0
        self.error_count: int = 0
        self.skipped_records: int = 0
        self.duplicate_records: int = 0
        self.stations_created: int = 0
        self.stations_updated: int = 0
        self.file_processing_times: list[float] = []
        self.batch_processing_times: list[float] = []
        self.errors_by_type: dict[str, int] = {}

    def start_timing(self):
        """Start timing the ingestion process."""
        self.start_time = time.time()

    def end_timing(self):
        """End timing the ingestion process."""
        self.end_time = time.time()

    def add_error(self, error_type: str):
        """Add an error to the metrics."""
        self.error_count += 1
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

    def get_processing_rate(self) -> float:
        """Calculate records per second processing rate."""
        if self.end_time > self.start_time and self.processed_records > 0:
            return self.processed_records / (self.end_time - self.start_time)
        return 0.0

    def get_summary(self) -> dict:
        """Get a summary of metrics."""
        duration = (
            self.end_time - self.start_time if self.end_time > self.start_time else 0
        )

        return {
            "duration_seconds": duration,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "error_count": self.error_count,
            "skipped_records": self.skipped_records,
            "duplicate_records": self.duplicate_records,
            "stations_created": self.stations_created,
            "stations_updated": self.stations_updated,
            "processing_rate_per_second": self.get_processing_rate(),
            "errors_by_type": self.errors_by_type,
            "success_rate": (self.processed_records / max(self.total_records, 1)) * 100,
        }


class WeatherDataParser:
    """Weather data file parser with validation."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def parse_weather_line(
        self, line: str, line_number: int
    ) -> tuple[datetime, int | None, int | None, int | None] | None:
        """Parse a single line of weather data with validation."""
        try:
            parts = line.strip().split("\t")
            if len(parts) != 4:
                self.logger.warning(
                    f"Line {line_number}: Invalid format - expected 4 fields, got {len(parts)}"
                )
                return None

            date_str, max_temp_str, min_temp_str, precip_str = parts

            # Parse date
            try:
                date_obj = datetime.strptime(date_str.strip(), "%Y%m%d").date()
            except ValueError as e:
                self.logger.warning(
                    f"Line {line_number}: Invalid date format '{date_str}': {e}"
                )
                return None

            # Parse temperatures and precipitation
            max_temp = self._parse_value(max_temp_str.strip(), "max_temp", line_number)
            min_temp = self._parse_value(min_temp_str.strip(), "min_temp", line_number)
            precipitation = self._parse_value(
                precip_str.strip(), "precipitation", line_number
            )

            # Validate temperature relationship
            if max_temp is not None and min_temp is not None and max_temp < min_temp:
                self.logger.warning(
                    f"Line {line_number}: Max temp ({max_temp}) < Min temp ({min_temp})"
                )
                return None

            # Validate precipitation is non-negative
            if precipitation is not None and precipitation < 0:
                self.logger.warning(
                    f"Line {line_number}: Negative precipitation ({precipitation})"
                )
                precipitation = None

            return date_obj, max_temp, min_temp, precipitation

        except Exception as e:
            self.logger.error(f"Line {line_number}: Unexpected error parsing line: {e}")
            return None

    def _parse_value(
        self, value_str: str, field_name: str, line_number: int
    ) -> int | None:
        """Parse a weather value, handling missing data (-9999)."""
        try:
            value = int(value_str)
            if value == -9999:
                return None
            return value
        except ValueError:
            self.logger.warning(
                f"Line {line_number}: Invalid {field_name} value '{value_str}'"
            )
            return None


class WeatherDataIngestor:
    """Main weather data ingestion class with comprehensive logging."""

    def __init__(self, config: WeatherDataIngestorConfig):
        self.config = config
        self.logger_manager = WeatherDataLogger(config)
        self.logger = self.logger_manager.get_logger()
        self.parser = WeatherDataParser(self.logger)
        self.metrics = WeatherDataMetrics()

        # Validate dependencies
        if not DJANGO_AVAILABLE and not config.dry_run:
            raise RuntimeError(
                "Django is required for database operations. Use --dry-run for testing without Django."
            )

    def run(self) -> bool:
        """Main ingestion process."""
        self.logger.info("🌤️  Starting weather data ingestion process")
        self.logger.info(f"Configuration: {self._log_config()}")

        self.metrics.start_timing()

        try:
            # Validate data directory
            if not self._validate_data_directory():
                return False

            # Get weather data files
            weather_files = self._get_weather_files()
            if not weather_files:
                self.logger.error(
                    f"No weather data files found in '{self.config.data_dir}'"
                )
                return False

            self.metrics.total_files = len(weather_files)
            self.logger.info(f"📊 Found {len(weather_files)} weather station files")

            # Clear existing data if requested
            if self.config.clear_existing and not self.config.dry_run:
                self._clear_existing_data()

            # Process files
            success = self._process_files(weather_files)

            self.metrics.end_timing()
            self._log_final_summary()

            return success

        except Exception as e:
            self.logger.error(f"❌ Fatal error during ingestion: {e}", exc_info=True)
            self.metrics.end_timing()
            return False

    def _validate_data_directory(self) -> bool:
        """Validate that the data directory exists and is accessible."""
        if not os.path.exists(self.config.data_dir):
            self.logger.error(f"Data directory '{self.config.data_dir}' does not exist")
            return False

        if not os.path.isdir(self.config.data_dir):
            self.logger.error(
                f"Data directory '{self.config.data_dir}' is not a directory"
            )
            return False

        if not os.access(self.config.data_dir, os.R_OK):
            self.logger.error(
                f"Data directory '{self.config.data_dir}' is not readable"
            )
            return False

        self.logger.info(f"📁 Data directory validated: {self.config.data_dir}")
        return True

    def _get_weather_files(self) -> list[str]:
        """Get all weather data files from the data directory."""
        pattern = os.path.join(self.config.data_dir, "USC*.txt")
        files = glob.glob(pattern)
        return sorted(files)

    def _clear_existing_data(self):
        """Clear existing weather data from the database."""
        if not DJANGO_AVAILABLE:
            return

        self.logger.info("🗑️  Clearing existing weather data...")

        try:
            daily_count = DailyWeather.objects.count()
            station_count = WeatherStation.objects.count()

            DailyWeather.objects.all().delete()
            WeatherStation.objects.all().delete()

            self.logger.info(f"   • Deleted {daily_count:,} daily weather records")
            self.logger.info(f"   • Deleted {station_count:,} weather stations")

        except Exception as e:
            self.logger.error(f"Error clearing existing data: {e}")
            raise

    def _process_files(self, weather_files: list[str]) -> bool:
        """Process all weather data files."""
        success_count = 0

        for i, file_path in enumerate(weather_files, 1):
            self.logger.info(
                f"📡 Processing file {i}/{len(weather_files)}: {os.path.basename(file_path)}"
            )

            file_start_time = time.time()

            try:
                station_id = self._extract_station_id(file_path)
                records_processed = self._process_weather_file(file_path, station_id)

                file_end_time = time.time()
                file_duration = file_end_time - file_start_time

                self.metrics.file_processing_times.append(file_duration)
                self.metrics.processed_files += 1
                success_count += 1

                self.logger.info(
                    f"   ✅ Processed {records_processed:,} records in {file_duration:.2f}s"
                )

            except Exception as e:
                self.logger.error(f"   ❌ Error processing {file_path}: {e}")
                self.metrics.add_error("file_processing_error")
                continue

        return success_count == len(weather_files)

    def _extract_station_id(self, file_path: str) -> str:
        """Extract station ID from file path."""
        filename = os.path.basename(file_path)
        station_id = filename.replace(".txt", "")
        return station_id

    def _process_weather_file(self, file_path: str, station_id: str) -> int:
        """Process a single weather data file."""
        # Create or get weather station
        station = None
        if not self.config.dry_run and DJANGO_AVAILABLE:
            station, created = WeatherStation.objects.get_or_create(
                station_id=station_id,
                defaults={"name": f"Weather Station {station_id}"},
            )
            if created:
                self.metrics.stations_created += 1
            else:
                self.metrics.stations_updated += 1

        # Process daily records
        daily_records = []
        processed_count = 0
        line_number = 0

        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line_number += 1

                    if not line.strip():
                        continue

                    self.metrics.total_records += 1

                    # Parse the line
                    parsed_data = self.parser.parse_weather_line(line, line_number)
                    if parsed_data is None:
                        self.metrics.skipped_records += 1
                        continue

                    date_obj, max_temp, min_temp, precipitation = parsed_data

                    # Create record
                    if not self.config.dry_run and DJANGO_AVAILABLE:
                        daily_record = DailyWeather(
                            station=station,
                            date=date_obj,
                            max_temp=max_temp,
                            min_temp=min_temp,
                            precipitation=precipitation,
                        )
                        daily_records.append(daily_record)

                    processed_count += 1
                    self.metrics.processed_records += 1

                    # Process in batches
                    if (
                        not self.config.dry_run
                        and DJANGO_AVAILABLE
                        and len(daily_records) >= self.config.batch_size
                    ):
                        self._save_daily_records_batch(daily_records)
                        daily_records = []

                    # Log progress
                    if processed_count % self.config.progress_interval == 0:
                        self.logger.debug(
                            f"   📊 Processed {processed_count:,} records from {station_id}"
                        )

        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            self.metrics.add_error("file_read_error")
            raise

        # Save remaining records
        if not self.config.dry_run and DJANGO_AVAILABLE and daily_records:
            self._save_daily_records_batch(daily_records)

        return processed_count

    def _save_daily_records_batch(self, daily_records: list):
        """Save a batch of daily weather records to the database."""
        if not DJANGO_AVAILABLE:
            return

        batch_start_time = time.time()

        try:
            with transaction.atomic():
                created_records = DailyWeather.objects.bulk_create(
                    daily_records,
                    ignore_conflicts=True,
                    batch_size=self.config.batch_size,
                )

                duplicate_count = len(daily_records) - len(created_records)
                self.metrics.duplicate_records += duplicate_count

                if duplicate_count > 0:
                    self.logger.debug(
                        f"   ⚠️  Skipped {duplicate_count} duplicate records"
                    )

        except Exception as e:
            self.logger.error(f"Error saving batch: {e}")
            self.metrics.add_error("batch_save_error")
            raise

        finally:
            batch_end_time = time.time()
            self.metrics.batch_processing_times.append(
                batch_end_time - batch_start_time
            )

    def _log_config(self) -> str:
        """Log the current configuration."""
        return (
            f"data_dir={self.config.data_dir}, "
            f"batch_size={self.config.batch_size}, "
            f"dry_run={self.config.dry_run}, "
            f"clear_existing={self.config.clear_existing}"
        )

    def _log_final_summary(self):
        """Log final processing summary with metrics."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎉 Weather data ingestion complete!")
        self.logger.info("=" * 80)

        summary = self.metrics.get_summary()

        self.logger.info("📊 Processing Summary:")
        self.logger.info(f"   • Duration: {summary['duration_seconds']:.2f} seconds")
        self.logger.info(
            f"   • Files processed: {summary['processed_files']}/{summary['total_files']}"
        )
        self.logger.info(
            f"   • Records processed: {summary['processed_records']:,}/{summary['total_records']:,}"
        )
        self.logger.info(
            f"   • Processing rate: {summary['processing_rate_per_second']:.2f} records/second"
        )
        self.logger.info(f"   • Success rate: {summary['success_rate']:.2f}%")

        if summary["error_count"] > 0:
            self.logger.warning("⚠️  Issues encountered:")
            self.logger.warning(f"   • Total errors: {summary['error_count']}")
            self.logger.warning(f"   • Skipped records: {summary['skipped_records']}")
            self.logger.warning(
                f"   • Duplicate records: {summary['duplicate_records']}"
            )

            if summary["errors_by_type"]:
                self.logger.warning("   • Error breakdown:")
                for error_type, count in summary["errors_by_type"].items():
                    self.logger.warning(f"     - {error_type}: {count}")

        if not self.config.dry_run and DJANGO_AVAILABLE:
            self.logger.info("🏗️  Database changes:")
            self.logger.info(
                f"   • Weather stations created: {summary['stations_created']}"
            )
            self.logger.info(
                f"   • Weather stations updated: {summary['stations_updated']}"
            )

            # Verify database counts
            try:
                db_stations = WeatherStation.objects.count()
                db_records = DailyWeather.objects.count()
                self.logger.info(f"   • Total stations in DB: {db_stations:,}")
                self.logger.info(f"   • Total records in DB: {db_records:,}")
            except Exception as e:
                self.logger.warning(f"Could not verify database counts: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Weather Data Ingestion Script with Structured Logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic ingestion
    python scripts/ingest_weather_data.py

    # Custom data directory with logging
    python scripts/ingest_weather_data.py --data-dir custom_wx_data --log-level DEBUG

    # Dry run with file logging
    python scripts/ingest_weather_data.py --dry-run --log-file logs/ingestion.log

    # Clear existing data with larger batch size
    python scripts/ingest_weather_data.py --clear --batch-size 2000

    # JSON logging format
    python scripts/ingest_weather_data.py --log-format json --log-file logs/ingestion.json
        """,
    )

    parser.add_argument(
        "--data-dir",
        default="wx_data",
        help="Directory containing weather data files (default: wx_data)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument("--log-file", help="Log file path (default: console only)")

    parser.add_argument(
        "--log-format",
        choices=["simple", "structured", "json"],
        default="structured",
        help="Log format (default: structured)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of records to process in each batch (default: 1000)",
    )

    parser.add_argument(
        "--clear", action="store_true", help="Clear existing data before importing"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Parse files but don't save to database"
    )

    parser.add_argument(
        "--progress-interval",
        type=int,
        default=1000,
        help="Progress reporting interval (default: 1000)",
    )

    return parser


def main():
    """Main entry point for the script."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Create configuration
    config = WeatherDataIngestorConfig()
    config.data_dir = args.data_dir
    config.log_level = args.log_level
    config.log_file = args.log_file
    config.log_format = args.log_format
    config.batch_size = args.batch_size
    config.clear_existing = args.clear
    config.dry_run = args.dry_run
    config.progress_interval = args.progress_interval

    # Run ingestion
    try:
        ingestor = WeatherDataIngestor(config)
        success = ingestor.run()

        if success:
            print("\n✅ Weather data ingestion completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Weather data ingestion failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Ingestion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
