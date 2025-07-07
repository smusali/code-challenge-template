# Generated manually for implementing YearlyWeatherStats and CropYield models

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("models", "0001_initial"),
    ]

    operations = [
        # Remove the placeholder YearlyWeatherStats model
        migrations.DeleteModel(
            name="YearlyWeatherStats",
        ),
        # Remove the placeholder CropYield model
        migrations.DeleteModel(
            name="CropYield",
        ),
        # Create the full YearlyWeatherStats model
        migrations.CreateModel(
            name="YearlyWeatherStats",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "year",
                    models.IntegerField(
                        help_text="Year for these statistics",
                        validators=[
                            django.core.validators.MinValueValidator(1800),
                            django.core.validators.MaxValueValidator(2100),
                        ],
                    ),
                ),
                (
                    "avg_max_temp",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="Average maximum temperature in tenths of degrees Celsius",
                        max_digits=6,
                        null=True,
                    ),
                ),
                (
                    "avg_min_temp",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="Average minimum temperature in tenths of degrees Celsius",
                        max_digits=6,
                        null=True,
                    ),
                ),
                (
                    "max_temp",
                    models.IntegerField(
                        blank=True,
                        help_text="Highest maximum temperature in tenths of degrees Celsius",
                        null=True,
                    ),
                ),
                (
                    "min_temp",
                    models.IntegerField(
                        blank=True,
                        help_text="Lowest minimum temperature in tenths of degrees Celsius",
                        null=True,
                    ),
                ),
                (
                    "total_precipitation",
                    models.IntegerField(
                        blank=True,
                        help_text="Total precipitation in tenths of millimeters",
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "avg_precipitation",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="Average daily precipitation in tenths of millimeters",
                        max_digits=8,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "max_precipitation",
                    models.IntegerField(
                        blank=True,
                        help_text="Highest daily precipitation in tenths of millimeters",
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "total_records",
                    models.IntegerField(
                        default=0,
                        help_text="Total number of daily records for this year",
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "records_with_temp",
                    models.IntegerField(
                        default=0,
                        help_text="Number of records with valid temperature data",
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "records_with_precipitation",
                    models.IntegerField(
                        default=0,
                        help_text="Number of records with valid precipitation data",
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "station",
                    models.ForeignKey(
                        help_text="Weather station for these statistics",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="yearly_stats",
                        to="models.weatherstation",
                    ),
                ),
            ],
            options={
                "verbose_name": "Yearly Weather Statistics",
                "verbose_name_plural": "Yearly Weather Statistics",
                "db_table": "yearly_weather_stats",
                "indexes": [
                    models.Index(fields=["station", "year"], name="yearly_weat_station_65e3b3_idx"),
                    models.Index(fields=["year"], name="yearly_weat_year_18a8f7_idx"),
                    models.Index(fields=["year", "avg_max_temp"], name="yearly_weat_year_5d0c5a_idx"),
                    models.Index(fields=["year", "avg_min_temp"], name="yearly_weat_year_c0b93c_idx"),
                    models.Index(fields=["year", "total_precipitation"], name="yearly_weat_year_4e7c67_idx"),
                ],
                "unique_together": {("station", "year")},
            },
        ),
        # Create the full CropYield model
        migrations.CreateModel(
            name="CropYield",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "year",
                    models.IntegerField(
                        help_text="Year for the crop yield data",
                        validators=[
                            django.core.validators.MinValueValidator(1800),
                            django.core.validators.MaxValueValidator(2100),
                        ],
                    ),
                ),
                (
                    "crop_type",
                    models.CharField(
                        default="corn_grain",
                        help_text="Type of crop (e.g., corn_grain, soybeans, wheat)",
                        max_length=50,
                    ),
                ),
                (
                    "country",
                    models.CharField(
                        default="US",
                        help_text="Country code (e.g., US, CA, MX)",
                        max_length=3,
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        blank=True,
                        help_text="State code for regional data (optional)",
                        max_length=2,
                    ),
                ),
                (
                    "yield_value",
                    models.IntegerField(
                        help_text="Crop yield value in appropriate units (e.g., thousand metric tons)",
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "yield_unit",
                    models.CharField(
                        default="thousand_metric_tons",
                        help_text="Unit of measurement for yield value",
                        max_length=30,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        help_text="Data source or reference",
                        max_length=100,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Crop Yield",
                "verbose_name_plural": "Crop Yields",
                "db_table": "crop_yields",
                "indexes": [
                    models.Index(fields=["year"], name="crop_yields_year_2fd844_idx"),
                    models.Index(fields=["crop_type", "year"], name="crop_yields_crop_ty_f4bf74_idx"),
                    models.Index(fields=["country", "year"], name="crop_yields_country_a47e8a_idx"),
                    models.Index(fields=["year", "yield_value"], name="crop_yields_year_6b02d0_idx"),
                ],
                "unique_together": {("year", "crop_type", "country", "state")},
            },
        ),
    ] 