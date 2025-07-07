"""
Django management command to initialize crop yield database with existing data.

This command parses the crop yield data file and populates the CropYield model.

Usage:
    python manage.py init_crop_yield [--clear] [--data-file=path]
"""

import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core_django.models.models import CropYield


class Command(BaseCommand):
    help = "Initialize crop yield database with existing data from yld_data directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing crop yield data before importing",
        )
        parser.add_argument(
            "--data-file",
            type=str,
            default="yld_data/US_corn_grain_yield.txt",
            help="Path to crop yield data file (default: yld_data/US_corn_grain_yield.txt)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse file but don't save to database",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.verbosity = options["verbosity"]
        self.data_file = options["data_file"]
        self.dry_run = options["dry_run"]

        # Validate data file exists
        if not os.path.exists(self.data_file):
            raise CommandError(f"Data file '{self.data_file}' does not exist")

        # Clear existing data if requested
        if options["clear"] and not self.dry_run:
            self.clear_existing_data()

        self.stdout.write(
            self.style.SUCCESS("🌽 Starting crop yield data initialization...")
        )
        self.stdout.write(f"📁 Data file: {self.data_file}")

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No data will be saved")
            )

        # Process the crop yield file
        try:
            records_count = self.process_crop_yield_file()

            # Summary
            self.stdout.write(
                self.style.SUCCESS("\n🎉 Crop yield data initialization complete!")
            )
            self.stdout.write("📊 Summary:")
            self.stdout.write(f"   • Crop yield records: {records_count:,}")

            if not self.dry_run:
                # Verify database counts
                db_records = CropYield.objects.count()
                self.stdout.write("\n📋 Database verification:")
                self.stdout.write(f"   • Crop yield records in DB: {db_records:,}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            raise

    def clear_existing_data(self):
        """Clear existing crop yield data from the database."""
        self.stdout.write("🗑️  Clearing existing crop yield data...")

        record_count = CropYield.objects.count()
        CropYield.objects.all().delete()

        self.stdout.write(f"   • Deleted {record_count:,} crop yield records")

    def process_crop_yield_file(self) -> int:
        """Process the crop yield data file."""
        crop_records = []
        processed_count = 0

        with open(self.data_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    year, yield_value = self.parse_yield_line(line)

                    if not self.dry_run:
                        crop_record = CropYield(
                            year=year,
                            crop_type="corn_grain",
                            country="US",
                            state="",  # National data
                            yield_value=yield_value,
                            yield_unit="thousand_metric_tons",
                            source="US_corn_grain_yield.txt",
                        )
                        crop_records.append(crop_record)

                    processed_count += 1

                    if self.verbosity >= 2:
                        self.stdout.write(
                            f"   📅 {year}: {yield_value:,} thousand metric tons"
                        )

                except Exception as e:
                    if self.verbosity >= 1:
                        self.stdout.write(
                            self.style.WARNING(
                                f"   ⚠️  Skipping invalid line {line_num}: {e}"
                            )
                        )
                    continue

        # Save all records
        if not self.dry_run and crop_records:
            self.save_crop_records(crop_records)

        return processed_count

    def parse_yield_line(self, line: str) -> tuple[int, int]:
        """Parse a single line of crop yield data."""
        parts = line.split("\t")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid line format: expected 2 fields, got {len(parts)}"
            )

        year_str, yield_str = parts

        # Parse year
        try:
            year = int(year_str.strip())
            if year < 1800 or year > 2100:
                raise ValueError(f"Year out of range: {year}")
        except ValueError:
            raise ValueError(f"Invalid year format: {year_str}")

        # Parse yield value
        try:
            yield_value = int(yield_str.strip())
            if yield_value < 0:
                raise ValueError(f"Negative yield value: {yield_value}")
        except ValueError:
            raise ValueError(f"Invalid yield value format: {yield_str}")

        return year, yield_value

    def save_crop_records(self, crop_records: list[CropYield]):
        """Save crop yield records to the database."""
        try:
            with transaction.atomic():
                CropYield.objects.bulk_create(
                    crop_records,
                    ignore_conflicts=True,  # Skip duplicates
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error saving records: {e}"))
            raise
