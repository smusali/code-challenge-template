"""
Django management command to calculate and initialize yearly weather statistics.

This command aggregates daily weather data to create yearly statistics
for efficient querying and analysis.

Usage:
    python manage.py init_yearly_stats [--clear] [--batch-size=100]
"""

import asyncio

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.db.models import Avg, Count, Max, Min, Sum

from core_django.models.models import DailyWeather, WeatherStation, YearlyWeatherStats
from core_django.utils.async_bulk_writer import BulkWriterConfig, WeatherDataBulkWriter
from core_django.utils.units import round_to_decimal


class Command(BaseCommand):
    help = "Calculate and initialize yearly weather statistics from daily data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing yearly statistics before calculating",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of station-year combinations to process in each batch (default: 500)",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Calculate statistics for specific year only",
        )
        parser.add_argument(
            "--station",
            type=str,
            help="Calculate statistics for specific station only",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Calculate statistics but don't save to database",
        )
        parser.add_argument(
            "--max-concurrent-batches",
            type=int,
            default=6,
            help="Maximum number of concurrent batch operations (default: 6)",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.verbosity = options["verbosity"]
        self.batch_size = options["batch_size"]
        self.target_year = options["year"]
        self.target_station = options["station"]
        self.dry_run = options["dry_run"]
        self.max_concurrent_batches = options["max_concurrent_batches"]

        # Clear existing data if requested
        if options["clear"] and not self.dry_run:
            self.clear_existing_data()

        self.stdout.write(
            self.style.SUCCESS("📊 Starting yearly weather statistics calculation...")
        )

        if self.target_year:
            self.stdout.write(f"🎯 Target year: {self.target_year}")
        if self.target_station:
            self.stdout.write(f"🎯 Target station: {self.target_station}")
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No data will be saved")
            )

        # Run async processing
        try:
            asyncio.run(self.process_statistics_async())
        except Exception as e:
            raise CommandError(f"Error during async processing: {e}")

    async def process_statistics_async(self):
        """Process yearly statistics using async bulk operations."""
        # Get station-year combinations that need processing
        combinations = self.get_station_year_combinations()

        if not combinations:
            self.stdout.write(
                self.style.WARNING("⚠️  No station-year combinations found to process")
            )
            return

        self.stdout.write(
            f"📋 Found {len(combinations):,} station-year combinations to process"
        )
        self.stdout.write(f"📦 Batch size: {self.batch_size}")
        self.stdout.write(f"🔄 Max concurrent batches: {self.max_concurrent_batches}")

        # Configure async bulk writer
        config = BulkWriterConfig(
            batch_size=self.batch_size,
            max_concurrent_batches=self.max_concurrent_batches,
            progress_callback=self.progress_callback if self.verbosity >= 1 else None,
            progress_interval=self.batch_size,
        )

        bulk_writer = WeatherDataBulkWriter(config)

        # Process combinations in chunks and calculate statistics
        all_yearly_stats = []
        chunk_size = self.batch_size * self.max_concurrent_batches

        for i in range(0, len(combinations), chunk_size):
            chunk = combinations[i : i + chunk_size]

            if self.verbosity >= 1:
                chunk_num = (i // chunk_size) + 1
                total_chunks = (len(combinations) + chunk_size - 1) // chunk_size
                self.stdout.write(
                    f"\n📊 Processing chunk {chunk_num}/{total_chunks}..."
                )

            # Calculate statistics for this chunk concurrently
            chunk_stats = await self.calculate_chunk_statistics_async(chunk)
            all_yearly_stats.extend(chunk_stats)

            if self.verbosity >= 2:
                self.stdout.write(f"   ✅ Calculated {len(chunk_stats)} statistics")

        # Bulk create all statistics
        if not self.dry_run and all_yearly_stats:
            self.stdout.write(
                f"\n🏗️  Creating {len(all_yearly_stats):,} yearly statistics..."
            )
            stats_metrics = await bulk_writer.bulk_create_yearly_stats_async(
                all_yearly_stats,
                self.progress_callback if self.verbosity >= 1 else None,
            )
            self.stdout.write(
                f"   ✅ Created {stats_metrics.successful_records:,} statistics "
                f"in {stats_metrics.duration:.2f}s "
                f"({stats_metrics.records_per_second:.0f} records/sec)"
            )

        # Summary
        self.stdout.write(
            self.style.SUCCESS("\n🎉 Yearly statistics calculation complete!")
        )
        self.stdout.write("📊 Summary:")
        self.stdout.write(
            f"   • Station-year combinations processed: {len(combinations):,}"
        )
        self.stdout.write(f"   • Yearly statistics created: {len(all_yearly_stats):,}")

        if not self.dry_run:
            # Verify database counts
            db_stats = YearlyWeatherStats.objects.count()
            self.stdout.write("\n📋 Database verification:")
            self.stdout.write(f"   • Yearly statistics in DB: {db_stats:,}")

    async def calculate_chunk_statistics_async(self, combinations):
        """Calculate statistics for a chunk of station-year combinations concurrently."""
        tasks = [
            self.calculate_yearly_stats_async(station_id, year)
            for station_id, year in combinations
        ]

        # Execute calculations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        stats = []
        for result in results:
            if result and not isinstance(result, Exception):
                stats.append(result)
            elif isinstance(result, Exception) and self.verbosity >= 2:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Error calculating statistics: {result}")
                )

        return stats

    async def calculate_yearly_stats_async(
        self, station_id: str, year: int
    ) -> YearlyWeatherStats | None:
        """Calculate yearly statistics for a specific station and year asynchronously."""
        # Get the weather station
        try:
            station = await asyncio.to_thread(
                WeatherStation.objects.get, station_id=station_id
            )
        except WeatherStation.DoesNotExist:
            if self.verbosity >= 2:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Station {station_id} not found")
                )
            return None

        # Get daily records for this station and year
        daily_records = DailyWeather.objects.filter(station=station, date__year=year)

        # Check if records exist
        records_exist = await asyncio.to_thread(daily_records.exists)
        if not records_exist:
            return None

        # Calculate basic aggregate statistics
        aggregates = await asyncio.to_thread(
            daily_records.aggregate,
            # Temperature statistics
            avg_max_temp=Avg("max_temp"),
            avg_min_temp=Avg("min_temp"),
            max_temp=Max("max_temp"),
            min_temp=Min("min_temp"),
            # Precipitation statistics
            total_precipitation=Sum("precipitation"),
            avg_precipitation=Avg("precipitation"),
            max_precipitation=Max("precipitation"),
            # Data quality metrics
            total_records=Count("id"),
        )

        # Calculate data quality metrics separately to avoid aggregation conflicts
        records_with_temp = await asyncio.to_thread(
            daily_records.filter(max_temp__isnull=False).count
        )
        records_with_precipitation = await asyncio.to_thread(
            daily_records.filter(precipitation__isnull=False).count
        )

        aggregates["records_with_temp"] = records_with_temp
        aggregates["records_with_precipitation"] = records_with_precipitation

        # Create YearlyWeatherStats object
        yearly_stats = YearlyWeatherStats(
            station=station,
            year=year,
            avg_max_temp=round_to_decimal(aggregates["avg_max_temp"]),
            avg_min_temp=round_to_decimal(aggregates["avg_min_temp"]),
            max_temp=aggregates["max_temp"],
            min_temp=aggregates["min_temp"],
            total_precipitation=aggregates["total_precipitation"],
            avg_precipitation=round_to_decimal(aggregates["avg_precipitation"]),
            max_precipitation=aggregates["max_precipitation"],
            total_records=aggregates["total_records"],
            records_with_temp=aggregates["records_with_temp"],
            records_with_precipitation=aggregates["records_with_precipitation"],
        )

        if self.verbosity >= 3:
            self.stdout.write(
                f"   📊 {station_id}-{year}: "
                f"Records={aggregates['total_records']}, "
                f"AvgMaxTemp={yearly_stats.avg_max_temp_celsius}°C, "
                f"TotalPrecip={yearly_stats.total_precipitation_mm}mm"
            )

        return yearly_stats

    def progress_callback(self, current: int, total: int):
        """Progress callback for bulk operations."""
        percentage = (current / total * 100) if total > 0 else 0
        self.stdout.write(f"   📈 Progress: {current:,}/{total:,} ({percentage:.1f}%)")

    def clear_existing_data(self):
        """Clear existing yearly statistics from the database."""
        self.stdout.write("🗑️  Clearing existing yearly statistics...")

        stats_count = YearlyWeatherStats.objects.count()
        YearlyWeatherStats.objects.all().delete()

        self.stdout.write(f"   • Deleted {stats_count:,} yearly statistics")

    def get_station_year_combinations(self) -> list[tuple[str, int]]:
        """Get all station-year combinations that have daily data."""
        query = DailyWeather.objects.values("station_id", "date__year").distinct()

        # Apply filters if specified
        if self.target_station:
            query = query.filter(station_id=self.target_station)
        if self.target_year:
            query = query.filter(date__year=self.target_year)

        # If not in dry run mode, exclude combinations that already have statistics
        if not self.dry_run:
            existing_stats = YearlyWeatherStats.objects.values_list(
                "station_id", "year"
            )
            if existing_stats:
                query = query.exclude(
                    models.Q(station_id__in=[s[0] for s in existing_stats])
                    & models.Q(date__year__in=[s[1] for s in existing_stats])
                )

        combinations = [
            (item["station_id"], item["date__year"])
            for item in query.order_by("station_id", "date__year")
        ]

        return combinations
