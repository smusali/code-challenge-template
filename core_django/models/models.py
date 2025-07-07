"""
Django models for Weather Data Engineering API.

This module contains the following models:
- WeatherStation: Metadata for weather stations
- DailyWeather: Daily weather observations
- YearlyWeatherStats: Aggregated yearly statistics (to be implemented)
- CropYield: Agricultural yield data (to be implemented)
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
    """Aggregated yearly weather statistics (to be implemented)."""

    pass


class CropYield(models.Model):
    """Agricultural yield data (to be implemented)."""

    pass
