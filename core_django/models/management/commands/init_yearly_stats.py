"""
Django management command to calculate and initialize yearly weather statistics.

This command aggregates daily weather data to create yearly statistics
for efficient querying and analysis.

Usage:
    python manage.py init_yearly_stats [--clear] [--batch-size=100]
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.db.models import Avg, Count, Max, Min, Sum

from core_django.models.models import DailyWeather, WeatherStation, YearlyWeatherStats


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
            default=100,
            help="Number of station-year combinations to process in each batch (default: 100)",
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

    def handle(self, *args, **options):
        """Main command handler."""
        self.verbosity = options["verbosity"]
        self.batch_size = options["batch_size"]
        self.target_year = options["year"]
        self.target_station = options["station"]
        self.dry_run = options["dry_run"]

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

        # Process combinations in batches
        total_processed = 0
        total_created = 0

        for i in range(0, len(combinations), self.batch_size):
            batch = combinations[i : i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(combinations) + self.batch_size - 1) // self.batch_size

            if self.verbosity >= 1:
                self.stdout.write(
                    f"\n📦 Processing batch {batch_num}/{total_batches}..."
                )

            try:
                batch_created = self.process_batch(batch)
                total_processed += len(batch)
                total_created += batch_created

                if self.verbosity >= 2:
                    self.stdout.write(
                        f"   ✅ Processed {len(batch)} combinations, created {batch_created} statistics"
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error processing batch {batch_num}: {e}")
                )
                continue

        # Summary
        self.stdout.write(
            self.style.SUCCESS("\n🎉 Yearly statistics calculation complete!")
        )
        self.stdout.write("📊 Summary:")
        self.stdout.write(
            f"   • Station-year combinations processed: {total_processed:,}"
        )
        self.stdout.write(f"   • Yearly statistics created: {total_created:,}")

        if not self.dry_run:
            # Verify database counts
            db_stats = YearlyWeatherStats.objects.count()
            self.stdout.write("\n📋 Database verification:")
            self.stdout.write(f"   • Yearly statistics in DB: {db_stats:,}")

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

    def process_batch(self, batch: list[tuple[str, int]]) -> int:
        """Process a batch of station-year combinations."""
        stats_to_create = []

        for station_id, year in batch:
            try:
                stats = self.calculate_yearly_stats(station_id, year)
                if stats and not self.dry_run:
                    stats_to_create.append(stats)

            except Exception as e:
                if self.verbosity >= 2:
                    self.stdout.write(
                        self.style.WARNING(
                            f"   ⚠️  Error calculating stats for {station_id}-{year}: {e}"
                        )
                    )
                continue

        # Save all statistics in this batch
        if not self.dry_run and stats_to_create:
            self.save_yearly_stats_batch(stats_to_create)

        return len(stats_to_create)

    def calculate_yearly_stats(
        self, station_id: str, year: int
    ) -> YearlyWeatherStats | None:
        """Calculate yearly statistics for a specific station and year."""
        # Get the weather station
        try:
            station = WeatherStation.objects.get(station_id=station_id)
        except WeatherStation.DoesNotExist:
            if self.verbosity >= 2:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Station {station_id} not found")
                )
            return None

        # Get daily records for this station and year
        daily_records = DailyWeather.objects.filter(station=station, date__year=year)

        if not daily_records.exists():
            return None

        # Calculate aggregate statistics
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
            # Data quality metrics
            total_records=Count("id"),
            records_with_temp=Count(
                "max_temp", filter=models.Q(max_temp__isnull=False)
            ),
            records_with_precipitation=Count(
                "precipitation", filter=models.Q(precipitation__isnull=False)
            ),
        )

        # Create YearlyWeatherStats object
        yearly_stats = YearlyWeatherStats(
            station=station,
            year=year,
            avg_max_temp=self.round_decimal(aggregates["avg_max_temp"]),
            avg_min_temp=self.round_decimal(aggregates["avg_min_temp"]),
            max_temp=aggregates["max_temp"],
            min_temp=aggregates["min_temp"],
            total_precipitation=aggregates["total_precipitation"],
            avg_precipitation=self.round_decimal(aggregates["avg_precipitation"]),
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

    def round_decimal(self, value: float | None) -> Decimal | None:
        """Round a float value to 1 decimal place for storage."""
        if value is None:
            return None
        return Decimal(str(round(value, 1)))

    def save_yearly_stats_batch(self, yearly_stats: list[YearlyWeatherStats]):
        """Save a batch of yearly statistics to the database."""
        try:
            with transaction.atomic():
                YearlyWeatherStats.objects.bulk_create(
                    yearly_stats,
                    ignore_conflicts=True,  # Skip duplicates
                    batch_size=self.batch_size,
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error saving batch: {e}"))
            raise
