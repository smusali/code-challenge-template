"""
Pydantic models for weather data.

This module contains Pydantic models for weather stations, daily weather observations,
and yearly weather statistics that correspond to the Django ORM models.
"""

from datetime import date as DateType
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class WeatherStationBase(BaseModel):
    """Base model for weather station data."""

    name: str | None = Field(
        None, max_length=255, description="Human-readable station name"
    )
    latitude: Decimal | None = Field(
        None, ge=-90.0, le=90.0, description="Station latitude in decimal degrees"
    )
    longitude: Decimal | None = Field(
        None, ge=-180.0, le=180.0, description="Station longitude in decimal degrees"
    )
    elevation: Decimal | None = Field(None, description="Station elevation in meters")
    state: str | None = Field(None, max_length=2, description="US state abbreviation")


class WeatherStationCreate(WeatherStationBase):
    """Model for creating a new weather station."""

    station_id: str = Field(
        ..., max_length=20, description="Weather station identifier (e.g., USC00110072)"
    )

    @validator("station_id")
    def validate_station_id(cls, v):
        """Validate station ID format."""
        if not v.startswith("USC00") or len(v) != 11:
            raise ValueError("Station ID must be in format USC00XXXXXX")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "USC00110072",
                "name": "Weather Station Name",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "elevation": 10.0,
                "state": "NY",
            }
        }


class WeatherStationUpdate(WeatherStationBase):
    """Model for updating an existing weather station."""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Weather Station Name",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "elevation": 15.0,
                "state": "NY",
            }
        }


class WeatherStationResponse(WeatherStationBase):
    """Model for weather station responses."""

    station_id: str = Field(..., description="Weather station identifier")
    created_at: datetime = Field(..., description="When the station was created")
    updated_at: datetime = Field(..., description="When the station was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "station_id": "USC00110072",
                "name": "Weather Station Name",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "elevation": 10.0,
                "state": "NY",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class DailyWeatherBase(BaseModel):
    """Base model for daily weather data."""

    date: DateType = Field(..., description="Date of the weather observation")
    max_temp: int | None = Field(
        None, description="Maximum temperature in tenths of degrees Celsius"
    )
    min_temp: int | None = Field(
        None, description="Minimum temperature in tenths of degrees Celsius"
    )
    precipitation: int | None = Field(
        None, ge=0, description="Precipitation in tenths of millimeters"
    )

    @validator("max_temp", "min_temp")
    def validate_temperatures(cls, v):
        """Validate temperature values."""
        if v is not None and (v < -1000 or v > 600):
            raise ValueError("Temperature value seems unrealistic")
        return v

    @validator("precipitation")
    def validate_precipitation(cls, v):
        """Validate precipitation values."""
        if v is not None and v < 0:
            raise ValueError("Precipitation cannot be negative")
        return v


class DailyWeatherCreate(DailyWeatherBase):
    """Model for creating a new daily weather record."""

    station_id: str = Field(..., description="Weather station identifier")

    @validator("station_id")
    def validate_station_id(cls, v):
        """Validate station ID format."""
        if not v.startswith("USC00") or len(v) != 11:
            raise ValueError("Station ID must be in format USC00XXXXXX")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "USC00110072",
                "date": "2024-01-01",
                "max_temp": 250,
                "min_temp": 100,
                "precipitation": 25,
            }
        }


class DailyWeatherUpdate(DailyWeatherBase):
    """Model for updating an existing daily weather record."""

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-01",
                "max_temp": 250,
                "min_temp": 100,
                "precipitation": 25,
            }
        }


class DailyWeatherResponse(DailyWeatherBase):
    """Model for daily weather responses."""

    id: int = Field(..., description="Record ID")
    station_id: str = Field(..., description="Weather station identifier")
    max_temp_celsius: float | None = Field(
        None, description="Maximum temperature in degrees Celsius"
    )
    min_temp_celsius: float | None = Field(
        None, description="Minimum temperature in degrees Celsius"
    )
    precipitation_mm: float | None = Field(
        None, description="Precipitation in millimeters"
    )
    created_at: datetime = Field(..., description="When the record was created")
    updated_at: datetime = Field(..., description="When the record was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "station_id": "USC00110072",
                "date": "2024-01-01",
                "max_temp": 250,
                "min_temp": 100,
                "precipitation": 25,
                "max_temp_celsius": 25.0,
                "min_temp_celsius": 10.0,
                "precipitation_mm": 2.5,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class YearlyWeatherStatsResponse(BaseModel):
    """Model for yearly weather statistics responses."""

    id: int = Field(..., description="Record ID")
    station_id: str = Field(..., description="Weather station identifier")
    year: int = Field(..., description="Year for these statistics")

    # Temperature statistics
    avg_max_temp: Decimal | None = Field(
        None, description="Average maximum temperature in tenths of degrees Celsius"
    )
    avg_min_temp: Decimal | None = Field(
        None, description="Average minimum temperature in tenths of degrees Celsius"
    )
    max_temp: int | None = Field(
        None, description="Highest maximum temperature in tenths of degrees Celsius"
    )
    min_temp: int | None = Field(
        None, description="Lowest minimum temperature in tenths of degrees Celsius"
    )

    # Precipitation statistics
    total_precipitation: int | None = Field(
        None, description="Total precipitation in tenths of millimeters"
    )
    avg_precipitation: Decimal | None = Field(
        None, description="Average daily precipitation in tenths of millimeters"
    )
    max_precipitation: int | None = Field(
        None, description="Highest daily precipitation in tenths of millimeters"
    )

    # Data quality metrics
    total_records: int = Field(..., description="Total number of daily records")
    records_with_temp: int = Field(
        ..., description="Records with valid temperature data"
    )
    records_with_precipitation: int = Field(
        ..., description="Records with valid precipitation data"
    )

    # Converted values for convenience
    avg_max_temp_celsius: float | None = Field(
        None, description="Average maximum temperature in degrees Celsius"
    )
    avg_min_temp_celsius: float | None = Field(
        None, description="Average minimum temperature in degrees Celsius"
    )
    max_temp_celsius: float | None = Field(
        None, description="Highest maximum temperature in degrees Celsius"
    )
    min_temp_celsius: float | None = Field(
        None, description="Lowest minimum temperature in degrees Celsius"
    )
    total_precipitation_mm: float | None = Field(
        None, description="Total precipitation in millimeters"
    )
    avg_precipitation_mm: float | None = Field(
        None, description="Average daily precipitation in millimeters"
    )
    max_precipitation_mm: float | None = Field(
        None, description="Highest daily precipitation in millimeters"
    )

    # Data completeness percentages
    temperature_completeness: float | None = Field(
        None, description="Temperature data completeness percentage"
    )
    precipitation_completeness: float | None = Field(
        None, description="Precipitation data completeness percentage"
    )

    created_at: datetime = Field(..., description="When the record was created")
    updated_at: datetime = Field(..., description="When the record was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "station_id": "USC00110072",
                "year": 2024,
                "avg_max_temp": 200.5,
                "avg_min_temp": 50.2,
                "max_temp": 350,
                "min_temp": -100,
                "total_precipitation": 1200,
                "avg_precipitation": 3.3,
                "max_precipitation": 150,
                "total_records": 365,
                "records_with_temp": 350,
                "records_with_precipitation": 300,
                "avg_max_temp_celsius": 20.05,
                "avg_min_temp_celsius": 5.02,
                "max_temp_celsius": 35.0,
                "min_temp_celsius": -10.0,
                "total_precipitation_mm": 120.0,
                "avg_precipitation_mm": 0.33,
                "max_precipitation_mm": 15.0,
                "temperature_completeness": 95.89,
                "precipitation_completeness": 82.19,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class WeatherStationWithStats(WeatherStationResponse):
    """Extended weather station model with statistics."""

    yearly_stats: list[YearlyWeatherStatsResponse] = Field(
        default_factory=list, description="Yearly statistics for this station"
    )
    total_records: int = Field(0, description="Total daily weather records")
    first_record_date: DateType | None = Field(None, description="Date of first record")
    last_record_date: DateType | None = Field(None, description="Date of last record")

    class Config:
        from_attributes = True


class WeatherDataSummary(BaseModel):
    """Summary statistics for weather data."""

    total_stations: int = Field(..., description="Total number of weather stations")
    total_daily_records: int = Field(..., description="Total daily weather records")
    total_yearly_stats: int = Field(..., description="Total yearly statistics records")
    date_range: dict[str, DateType | None] = Field(
        ..., description="Date range of available data"
    )
    temperature_range: dict[str, float | None] = Field(
        ..., description="Temperature range in degrees Celsius"
    )
    precipitation_range: dict[str, float | None] = Field(
        ..., description="Precipitation range in millimeters"
    )
    data_completeness: dict[str, float] = Field(
        ..., description="Data completeness percentages"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_stations": 150,
                "total_daily_records": 500000,
                "total_yearly_stats": 1500,
                "date_range": {"earliest": "1950-01-01", "latest": "2024-12-31"},
                "temperature_range": {"min": -45.0, "max": 50.0},
                "precipitation_range": {"min": 0.0, "max": 500.0},
                "data_completeness": {"temperature": 95.5, "precipitation": 87.3},
            }
        }
