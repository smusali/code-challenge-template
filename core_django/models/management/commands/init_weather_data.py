"""
Django management command to initialize weather database with existing data.

This command parses all weather data files in the wx_data directory and
populates the WeatherStation and DailyWeather models with the data.

Usage:
    python manage.py init_weather_data [--clear] [--batch-size=1000]
"""

import asyncio
import glob
import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from core_django.models.models import DailyWeather, WeatherStation
from core_django.utils.async_bulk_writer import BulkWriterConfig, WeatherDataBulkWriter


class Command(BaseCommand):
    help = "Initialize weather database with existing data from wx_data directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before importing",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=2000,
            help="Number of records to process in each batch (default: 2000)",
        )
        parser.add_argument(
            "--data-dir",
            type=str,
            default="wx_data",
            help="Directory containing weather data files (default: wx_data)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse files but don't save to database",
        )
        parser.add_argument(
            "--max-concurrent-batches",
            type=int,
            default=4,
            help="Maximum number of concurrent batch operations (default: 4)",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.verbosity = options["verbosity"]
        self.batch_size = options["batch_size"]
        self.data_dir = options["data_dir"]
        self.dry_run = options["dry_run"]
        self.max_concurrent_batches = options["max_concurrent_batches"]

        # Validate data directory exists
        if not os.path.exists(self.data_dir):
            raise CommandError(f"Data directory '{self.data_dir}' does not exist")

        # Clear existing data if requested
        if options["clear"] and not self.dry_run:
            self.clear_existing_data()

        # Get all weather data files
        weather_files = self.get_weather_files()
        if not weather_files:
            raise CommandError(f"No weather data files found in '{self.data_dir}'")

        self.stdout.write(
            self.style.SUCCESS("🌤️  Starting weather data initialization...")
        )
        self.stdout.write(f"📁 Data directory: {self.data_dir}")
        self.stdout.write(f"📊 Found {len(weather_files)} weather station files")
        self.stdout.write(f"📦 Batch size: {self.batch_size}")
        self.stdout.write(f"🔄 Max concurrent batches: {self.max_concurrent_batches}")

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No data will be saved")
            )

        # Run async processing
        try:
            asyncio.run(self.process_files_async(weather_files))
        except Exception as e:
            raise CommandError(f"Error during async processing: {e}")

    async def process_files_async(self, weather_files):
        """Process all weather files using async bulk operations."""
        # Configure async bulk writer
        config = BulkWriterConfig(
            batch_size=self.batch_size,
            max_concurrent_batches=self.max_concurrent_batches,
            progress_callback=self.progress_callback if self.verbosity >= 1 else None,
            progress_interval=self.batch_size,
        )

        bulk_writer = WeatherDataBulkWriter(config)

        # Collect all stations and daily records
        all_stations = []
        all_daily_records = []
        total_stations = 0
        total_records = 0

        for i, file_path in enumerate(weather_files, 1):
            self.stdout.write(
                f"\n📡 Processing file {i}/{len(weather_files)}: {os.path.basename(file_path)}"
            )

            try:
                station_id = self.extract_station_id(file_path)
                station, daily_records = await self.parse_weather_file_async(
                    file_path, station_id
                )

                if station:
                    all_stations.append(station)
                    total_stations += 1

                if daily_records:
                    all_daily_records.extend(daily_records)
                    total_records += len(daily_records)

                if self.verbosity >= 2:
                    self.stdout.write(
                        f"   ✅ Parsed {len(daily_records):,} records for station {station_id}"
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error processing {file_path}: {e}")
                )
                continue

        if not self.dry_run and (all_stations or all_daily_records):
            # Bulk create stations first
            if all_stations:
                self.stdout.write(
                    f"\n🏗️  Creating {len(all_stations):,} weather stations..."
                )
                station_metrics = await bulk_writer.bulk_create_weather_stations_async(
                    all_stations,
                    self.progress_callback if self.verbosity >= 1 else None,
                )
                self.stdout.write(
                    f"   ✅ Created {station_metrics.successful_records:,} stations "
                    f"in {station_metrics.duration:.2f}s "
                    f"({station_metrics.records_per_second:.0f} records/sec)"
                )

            # Bulk create daily records
            if all_daily_records:
                self.stdout.write(
                    f"\n🏗️  Creating {len(all_daily_records):,} daily weather records..."
                )
                daily_metrics = await bulk_writer.bulk_create_daily_weather_async(
                    all_daily_records,
                    self.progress_callback if self.verbosity >= 1 else None,
                )
                self.stdout.write(
                    f"   ✅ Created {daily_metrics.successful_records:,} daily records "
                    f"in {daily_metrics.duration:.2f}s "
                    f"({daily_metrics.records_per_second:.0f} records/sec)"
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS("\n🎉 Weather data initialization complete!")
        )
        self.stdout.write("📊 Summary:")
        self.stdout.write(f"   • Weather stations: {total_stations:,}")
        self.stdout.write(f"   • Daily weather records: {total_records:,}")

        if not self.dry_run:
            # Verify database counts
            db_stations = WeatherStation.objects.count()
            db_records = DailyWeather.objects.count()

            self.stdout.write("\n📋 Database verification:")
            self.stdout.write(f"   • Weather stations in DB: {db_stations:,}")
            self.stdout.write(f"   • Daily weather records in DB: {db_records:,}")

    def progress_callback(self, current: int, total: int):
        """Progress callback for bulk operations."""
        percentage = (current / total * 100) if total > 0 else 0
        self.stdout.write(f"   📈 Progress: {current:,}/{total:,} ({percentage:.1f}%)")

    def clear_existing_data(self):
        """Clear existing weather data from the database."""
        self.stdout.write("🗑️  Clearing existing data...")

        # Delete in correct order (child records first)
        daily_count = DailyWeather.objects.count()
        station_count = WeatherStation.objects.count()

        DailyWeather.objects.all().delete()
        WeatherStation.objects.all().delete()

        self.stdout.write(f"   • Deleted {daily_count:,} daily weather records")
        self.stdout.write(f"   • Deleted {station_count:,} weather stations")

    def get_weather_files(self) -> list[str]:
        """Get all weather data files from the data directory."""
        pattern = os.path.join(self.data_dir, "USC*.txt")
        files = glob.glob(pattern)
        return sorted(files)

    def extract_station_id(self, file_path: str) -> str:
        """Extract station ID from file path."""
        filename = os.path.basename(file_path)
        station_id = filename.replace(".txt", "")
        return station_id

    async def parse_weather_file_async(self, file_path: str, station_id: str):
        """Parse a single weather data file asynchronously."""
        # Create weather station
        station = (
            WeatherStation(
                station_id=station_id,
                name=f"Weather Station {station_id}",
            )
            if not self.dry_run
            else None
        )

        # Parse daily weather records
        daily_records = []

        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    (
                        date_obj,
                        max_temp,
                        min_temp,
                        precipitation,
                    ) = self.parse_weather_line(line)

                    if not self.dry_run:
                        daily_record = DailyWeather(
                            station=station,
                            date=date_obj,
                            max_temp=max_temp,
                            min_temp=min_temp,
                            precipitation=precipitation,
                        )
                        daily_records.append(daily_record)

                except Exception as e:
                    if self.verbosity >= 2:
                        self.stdout.write(
                            self.style.WARNING(
                                f"   ⚠️  Skipping invalid line {line_num} in {file_path}: {e}"
                            )
                        )
                    continue

        return station, daily_records

    def parse_weather_line(
        self, line: str
    ) -> tuple[datetime, int | None, int | None, int | None]:
        """Parse a single line of weather data."""
        parts = line.split("\t")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid line format: expected 4 fields, got {len(parts)}"
            )

        date_str, max_temp_str, min_temp_str, precip_str = parts

        # Parse date
        try:
            date_obj = datetime.strptime(date_str.strip(), "%Y%m%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}")

        # Parse temperatures and precipitation (handle missing values)
        max_temp = self.parse_value(max_temp_str.strip())
        min_temp = self.parse_value(min_temp_str.strip())
        precipitation = self.parse_value(precip_str.strip())

        # Validate precipitation is non-negative if present
        if precipitation is not None and precipitation < 0:
            precipitation = None

        return date_obj, max_temp, min_temp, precipitation

    def parse_value(self, value_str: str) -> int | None:
        """Parse a weather value, handling missing data (-9999)."""
        try:
            value = int(value_str)
            return None if value == -9999 else value
        except ValueError:
            return None
