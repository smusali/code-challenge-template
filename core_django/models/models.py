"""
Django models for Weather Data Engineering API.

This module contains the following models:
- WeatherStation: Metadata for weather stations
- DailyWeather: Daily weather observations
- YearlyWeatherStats: Aggregated yearly statistics with temperature and precipitation metrics
- CropYield: Historical agricultural yield data for correlation analysis
"""


from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
        app_label = "core_django.models"
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
        app_label = "core_django.models"
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
        return self.max_temp / 10.0 if self.max_temp is not None else None

    @property
    def min_temp_celsius(self):
        """Convert min temperature from tenths of degrees to degrees Celsius."""
        return self.min_temp / 10.0 if self.min_temp is not None else None

    @property
    def precipitation_mm(self):
        """Convert precipitation from tenths of millimeters to millimeters."""
        return self.precipitation / 10.0 if self.precipitation is not None else None

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
        app_label = "core_django.models"
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
        return (
            float(self.avg_max_temp) / 10.0 if self.avg_max_temp is not None else None
        )

    @property
    def avg_min_temp_celsius(self):
        """Convert average min temperature to degrees Celsius."""
        return (
            float(self.avg_min_temp) / 10.0 if self.avg_min_temp is not None else None
        )

    @property
    def max_temp_celsius(self):
        """Convert max temperature to degrees Celsius."""
        return self.max_temp / 10.0 if self.max_temp is not None else None

    @property
    def min_temp_celsius(self):
        """Convert min temperature to degrees Celsius."""
        return self.min_temp / 10.0 if self.min_temp is not None else None

    @property
    def total_precipitation_mm(self):
        """Convert total precipitation to millimeters."""
        return (
            self.total_precipitation / 10.0
            if self.total_precipitation is not None
            else None
        )

    @property
    def avg_precipitation_mm(self):
        """Convert average precipitation to millimeters."""
        return (
            float(self.avg_precipitation) / 10.0
            if self.avg_precipitation is not None
            else None
        )

    @property
    def max_precipitation_mm(self):
        """Convert max precipitation to millimeters."""
        return (
            self.max_precipitation / 10.0
            if self.max_precipitation is not None
            else None
        )

    @property
    def data_completeness_temp(self):
        """Calculate temperature data completeness as a percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.records_with_temp / self.total_records) * 100.0

    @property
    def data_completeness_precipitation(self):
        """Calculate precipitation data completeness as a percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.records_with_precipitation / self.total_records) * 100.0


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
        app_label = "core_django.models"
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
