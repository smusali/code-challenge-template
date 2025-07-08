"""
Django models for Weather Data Engineering API.

This module contains the following models:
- WeatherStation: Metadata for weather stations
- DailyWeather: Daily weather observations
- YearlyWeatherStats: Aggregated yearly statistics with temperature and precipitation metrics
- CropYield: Historical agricultural yield data for correlation analysis
- FileProcessingLog: Track file-level processing with checksums and metadata
- RecordChecksum: Track record-level checksums for duplicate detection
"""


import hashlib

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core_django.utils.units import (
    calculate_data_completeness,
    decimal_tenths_to_celsius,
    decimal_tenths_to_millimeters,
    tenths_to_celsius,
    tenths_to_millimeters,
)


class WeatherStation(models.Model):
    """
    Weather station metadata.

    Station IDs follow the format USC00XXXXXX where XXXXXX is a 6-digit identifier.
    """

    station_id = models.CharField(
        max_length=20,
        unique=True,
        primary_key=True,
        help_text="Weather station identifier (e.g., USC00110072)",
    )
    name = models.CharField(
        max_length=255, blank=True, help_text="Human-readable station name"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Station latitude in decimal degrees",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Station longitude in decimal degrees",
    )
    elevation = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Station elevation in meters",
    )
    state = models.CharField(
        max_length=2, blank=True, help_text="US state abbreviation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "models"
        db_table = "weather_stations"
        verbose_name = "Weather Station"
        verbose_name_plural = "Weather Stations"
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.station_id} - {self.name or 'Unknown Station'}"


class DailyWeather(models.Model):
    """
    Daily weather observations from weather stations.

    Temperature values are stored in tenths of degrees Celsius.
    Precipitation values are stored in tenths of millimeters.
    Missing values are represented as NULL in the database.
    """

    station = models.ForeignKey(
        WeatherStation,
        on_delete=models.CASCADE,
        related_name="daily_records",
        help_text="Weather station that recorded this observation",
    )
    date = models.DateField(help_text="Date of the weather observation")
    max_temp = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum temperature in tenths of degrees Celsius. NULL if missing (-9999 in source)",
    )
    min_temp = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum temperature in tenths of degrees Celsius. NULL if missing (-9999 in source)",
    )
    precipitation = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Precipitation in tenths of millimeters. NULL if missing (-9999 in source)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "models"
        db_table = "daily_weather"
        verbose_name = "Daily Weather Record"
        verbose_name_plural = "Daily Weather Records"
        unique_together = [["station", "date"]]
        indexes = [
            models.Index(fields=["station", "date"]),
            models.Index(fields=["date"]),
            models.Index(fields=["station", "date", "max_temp"]),
            models.Index(fields=["station", "date", "min_temp"]),
            models.Index(fields=["station", "date", "precipitation"]),
        ]

    def __str__(self):
        return f"{self.station.station_id} - {self.date}"

    @property
    def max_temp_celsius(self):
        """Convert max temperature from tenths of degrees to degrees Celsius."""
        return tenths_to_celsius(self.max_temp)

    @property
    def min_temp_celsius(self):
        """Convert min temperature from tenths of degrees to degrees Celsius."""
        return tenths_to_celsius(self.min_temp)

    @property
    def precipitation_mm(self):
        """Convert precipitation from tenths of millimeters to millimeters."""
        return tenths_to_millimeters(self.precipitation)

    def clean(self):
        """Validate that max_temp >= min_temp when both are present."""
        from django.core.exceptions import ValidationError

        if (
            self.max_temp is not None
            and self.min_temp is not None
            and self.max_temp < self.min_temp
        ):
            raise ValidationError(
                "Maximum temperature cannot be less than minimum temperature"
            )

    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)


# TODO: Implement in future commits
class YearlyWeatherStats(models.Model):
    """
    Aggregated yearly weather statistics by station.

    Provides pre-calculated statistics for efficient querying of weather trends.
    All temperature values are stored in tenths of degrees Celsius.
    All precipitation values are stored in tenths of millimeters.
    """

    station = models.ForeignKey(
        WeatherStation,
        on_delete=models.CASCADE,
        related_name="yearly_stats",
        help_text="Weather station for these statistics",
    )
    year = models.IntegerField(
        validators=[MinValueValidator(1800), MaxValueValidator(2100)],
        help_text="Year for these statistics",
    )

    # Temperature statistics (in tenths of degrees Celsius)
    avg_max_temp = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Average maximum temperature in tenths of degrees Celsius",
    )
    avg_min_temp = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Average minimum temperature in tenths of degrees Celsius",
    )
    max_temp = models.IntegerField(
        null=True,
        blank=True,
        help_text="Highest maximum temperature in tenths of degrees Celsius",
    )
    min_temp = models.IntegerField(
        null=True,
        blank=True,
        help_text="Lowest minimum temperature in tenths of degrees Celsius",
    )

    # Precipitation statistics (in tenths of millimeters)
    total_precipitation = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Total precipitation in tenths of millimeters",
    )
    avg_precipitation = models.DecimalField(
        max_digits=8,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Average daily precipitation in tenths of millimeters",
    )
    max_precipitation = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Highest daily precipitation in tenths of millimeters",
    )

    # Data quality metrics
    total_records = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of daily records for this year",
    )
    records_with_temp = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of records with valid temperature data",
    )
    records_with_precipitation = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of records with valid precipitation data",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "models"
        db_table = "yearly_weather_stats"
        verbose_name = "Yearly Weather Statistics"
        verbose_name_plural = "Yearly Weather Statistics"
        unique_together = [["station", "year"]]
        indexes = [
            models.Index(fields=["station", "year"]),
            models.Index(fields=["year"]),
            models.Index(fields=["year", "avg_max_temp"]),
            models.Index(fields=["year", "avg_min_temp"]),
            models.Index(fields=["year", "total_precipitation"]),
        ]

    def __str__(self):
        return f"{self.station.station_id} - {self.year}"

    @property
    def avg_max_temp_celsius(self):
        """Convert average max temperature to degrees Celsius."""
        return decimal_tenths_to_celsius(self.avg_max_temp)

    @property
    def avg_min_temp_celsius(self):
        """Convert average min temperature to degrees Celsius."""
        return decimal_tenths_to_celsius(self.avg_min_temp)

    @property
    def max_temp_celsius(self):
        """Convert max temperature to degrees Celsius."""
        return tenths_to_celsius(self.max_temp)

    @property
    def min_temp_celsius(self):
        """Convert min temperature to degrees Celsius."""
        return tenths_to_celsius(self.min_temp)

    @property
    def total_precipitation_mm(self):
        """Convert total precipitation to millimeters."""
        return tenths_to_millimeters(self.total_precipitation)

    @property
    def avg_precipitation_mm(self):
        """Convert average precipitation to millimeters."""
        return decimal_tenths_to_millimeters(self.avg_precipitation)

    @property
    def max_precipitation_mm(self):
        """Convert max precipitation to millimeters."""
        return tenths_to_millimeters(self.max_precipitation)

    @property
    def data_completeness_temp(self):
        """Calculate temperature data completeness as a percentage."""
        return calculate_data_completeness(self.records_with_temp, self.total_records)

    @property
    def data_completeness_precipitation(self):
        """Calculate precipitation data completeness as a percentage."""
        return calculate_data_completeness(
            self.records_with_precipitation, self.total_records
        )


class CropYield(models.Model):
    """
    Agricultural crop yield data.

    Stores annual crop yield statistics for correlation analysis with weather data.
    """

    year = models.IntegerField(
        validators=[MinValueValidator(1800), MaxValueValidator(2100)],
        help_text="Year for the crop yield data",
    )
    crop_type = models.CharField(
        max_length=50,
        default="corn_grain",
        help_text="Type of crop (e.g., corn_grain, soybeans, wheat)",
    )
    country = models.CharField(
        max_length=3,
        default="US",
        help_text="Country code (e.g., US, CA, MX)",
    )
    state = models.CharField(
        max_length=2,
        blank=True,
        help_text="State code for regional data (optional)",
    )
    yield_value = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Crop yield value in appropriate units (e.g., thousand metric tons)",
    )
    yield_unit = models.CharField(
        max_length=30,
        default="thousand_metric_tons",
        help_text="Unit of measurement for yield value",
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Data source or reference",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "models"
        db_table = "crop_yields"
        verbose_name = "Crop Yield"
        verbose_name_plural = "Crop Yields"
        unique_together = [["year", "crop_type", "country", "state"]]
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["crop_type", "year"]),
            models.Index(fields=["country", "year"]),
            models.Index(fields=["year", "yield_value"]),
        ]

    def __str__(self):
        location = f"{self.state}, {self.country}" if self.state else self.country
        return f"{self.crop_type} {self.year} - {location}: {self.yield_value:,} {self.yield_unit}"

    @property
    def yield_per_hectare(self):
        """
        Calculate approximate yield per hectare if possible.
        This is a simplified calculation and may need adjustment based on actual crop type and units.
        """
        # This would need to be customized based on actual agricultural data
        # For now, return None as we don't have area information
        return None


class FileProcessingLog(models.Model):
    """
    Track file-level processing with checksums and metadata.

    This model provides duplicate detection and processing history tracking
    for weather data files to prevent reprocessing unchanged files.
    """

    file_path = models.CharField(
        max_length=500, help_text="Relative path to the processed file"
    )
    file_name = models.CharField(max_length=255, help_text="Name of the processed file")
    file_size = models.BigIntegerField(help_text="Size of the file in bytes")
    file_checksum = models.CharField(
        max_length=64, help_text="SHA-256 checksum of the file contents"
    )
    station_id = models.CharField(
        max_length=20, help_text="Weather station ID extracted from filename"
    )

    # Processing metadata
    processing_started_at = models.DateTimeField(
        help_text="When file processing started"
    )
    processing_completed_at = models.DateTimeField(
        null=True, blank=True, help_text="When file processing completed successfully"
    )
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ("started", "Processing Started"),
            ("completed", "Processing Completed"),
            ("failed", "Processing Failed"),
            ("skipped", "Processing Skipped"),
        ],
        default="started",
        help_text="Current processing status",
    )

    # Processing results
    total_lines = models.IntegerField(
        default=0, help_text="Total number of lines in the file"
    )
    processed_records = models.IntegerField(
        default=0, help_text="Number of records successfully processed"
    )
    skipped_records = models.IntegerField(
        default=0, help_text="Number of records skipped due to errors"
    )
    duplicate_records = models.IntegerField(
        default=0, help_text="Number of duplicate records found"
    )

    # Error tracking
    error_message = models.TextField(
        blank=True, help_text="Error message if processing failed"
    )
    error_count = models.IntegerField(
        default=0, help_text="Number of errors encountered during processing"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "models"
        db_table = "file_processing_logs"
        verbose_name = "File Processing Log"
        verbose_name_plural = "File Processing Logs"
        unique_together = [["file_path", "file_checksum"]]
        indexes = [
            models.Index(fields=["file_path"]),
            models.Index(fields=["file_checksum"]),
            models.Index(fields=["station_id"]),
            models.Index(fields=["processing_status"]),
            models.Index(fields=["processing_started_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.file_name} - {self.processing_status}"

    @classmethod
    def calculate_file_checksum(cls, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    @classmethod
    def is_file_processed(cls, file_path: str) -> bool:
        """Check if a file has been successfully processed."""
        try:
            current_checksum = cls.calculate_file_checksum(file_path)
            return cls.objects.filter(
                file_path=file_path,
                file_checksum=current_checksum,
                processing_status="completed",
            ).exists()
        except Exception:
            return False

    @classmethod
    def get_processing_history(cls, file_path: str):
        """Get processing history for a file."""
        return cls.objects.filter(file_path=file_path).order_by("-created_at")


class RecordChecksum(models.Model):
    """
    Track record-level checksums for duplicate detection.

    This model provides record-level duplicate detection using content hashing
    to prevent duplicate weather observations even across different files.
    """

    station_id = models.CharField(max_length=20, help_text="Weather station ID")
    date = models.DateField(help_text="Date of the weather observation")
    content_hash = models.CharField(
        max_length=64, help_text="SHA-256 hash of the record content"
    )

    # Reference to the actual weather record
    daily_weather = models.OneToOneField(
        DailyWeather,
        on_delete=models.CASCADE,
        related_name="record_checksum",
        help_text="Associated daily weather record",
    )

    # Processing metadata
    source_file = models.CharField(
        max_length=255, help_text="Source file where this record was first processed"
    )
    processing_batch = models.CharField(
        max_length=100, blank=True, help_text="Processing batch identifier"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "models"
        db_table = "record_checksums"
        verbose_name = "Record Checksum"
        verbose_name_plural = "Record Checksums"
        unique_together = [["station_id", "date", "content_hash"]]
        indexes = [
            models.Index(fields=["station_id", "date"]),
            models.Index(fields=["content_hash"]),
            models.Index(fields=["source_file"]),
            models.Index(fields=["processing_batch"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.station_id} - {self.date} - {self.content_hash[:8]}"

    @classmethod
    def calculate_record_hash(
        cls, station_id: str, date, max_temp, min_temp, precipitation
    ) -> str:
        """Calculate SHA-256 hash of a weather record's content."""
        content = f"{station_id}|{date}|{max_temp}|{min_temp}|{precipitation}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def is_record_duplicate(
        cls, station_id: str, date, max_temp, min_temp, precipitation
    ) -> bool:
        """Check if a record with this content already exists."""
        content_hash = cls.calculate_record_hash(
            station_id, date, max_temp, min_temp, precipitation
        )
        return cls.objects.filter(
            station_id=station_id, date=date, content_hash=content_hash
        ).exists()

    @classmethod
    def create_for_record(
        cls, daily_weather: DailyWeather, source_file: str, processing_batch: str = ""
    ):
        """Create a checksum record for a DailyWeather instance."""
        content_hash = cls.calculate_record_hash(
            daily_weather.station.station_id,
            daily_weather.date,
            daily_weather.max_temp,
            daily_weather.min_temp,
            daily_weather.precipitation,
        )

        return cls.objects.create(
            station_id=daily_weather.station.station_id,
            date=daily_weather.date,
            content_hash=content_hash,
            daily_weather=daily_weather,
            source_file=source_file,
            processing_batch=processing_batch,
        )
