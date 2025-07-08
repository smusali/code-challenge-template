"""
Pydantic models for crop yield data.

This module contains Pydantic models for crop yield data that correspond
to the Django CropYield model.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class CropYieldBase(BaseModel):
    """Base model for crop yield data."""

    year: int = Field(..., ge=1800, le=2100, description="Year for the crop yield data")
    crop_type: str = Field(
        default="corn_grain",
        max_length=50,
        description="Type of crop (e.g., corn_grain, soybeans, wheat)",
    )
    country: str = Field(
        default="US", max_length=3, description="Country code (e.g., US, CA, MX)"
    )
    state: Optional[str] = Field(
        None, max_length=2, description="State code for regional data (optional)"
    )
    yield_value: int = Field(
        ..., ge=0, description="Crop yield value in appropriate units"
    )
    yield_unit: str = Field(
        default="thousand_metric_tons",
        max_length=30,
        description="Unit of measurement for yield value",
    )
    source: Optional[str] = Field(
        None, max_length=100, description="Data source or reference"
    )

    @validator("country")
    def validate_country(cls, v):
        """Validate country code format."""
        if v and len(v) != 2 and len(v) != 3:
            raise ValueError("Country code must be 2 or 3 characters")
        return v.upper() if v else v

    @validator("state")
    def validate_state(cls, v):
        """Validate state code format."""
        if v and len(v) != 2:
            raise ValueError("State code must be 2 characters")
        return v.upper() if v else v

    @validator("crop_type")
    def validate_crop_type(cls, v):
        """Validate crop type."""
        allowed_types = [
            "corn_grain",
            "corn_silage",
            "soybeans",
            "wheat",
            "cotton",
            "rice",
            "barley",
            "oats",
            "sorghum",
            "rye",
            "peanuts",
            "sunflower",
            "canola",
            "sugar_beets",
            "potatoes",
            "tomatoes",
        ]
        if v and v not in allowed_types:
            # Allow custom crop types but warn about validation
            pass
        return v.lower() if v else v


class CropYieldCreate(CropYieldBase):
    """Model for creating a new crop yield record."""

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2024,
                "crop_type": "corn_grain",
                "country": "US",
                "state": "IL",
                "yield_value": 14500,
                "yield_unit": "thousand_metric_tons",
                "source": "USDA NASS",
            }
        }


class CropYieldUpdate(CropYieldBase):
    """Model for updating an existing crop yield record."""

    year: Optional[int] = Field(
        None, ge=1800, le=2100, description="Year for the crop yield data"
    )
    yield_value: Optional[int] = Field(
        None, ge=0, description="Crop yield value in appropriate units"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "yield_value": 15000,
                "yield_unit": "thousand_metric_tons",
                "source": "USDA NASS - Updated",
            }
        }


class CropYieldResponse(CropYieldBase):
    """Model for crop yield responses."""

    id: int = Field(..., description="Record ID")
    created_at: datetime = Field(..., description="When the record was created")
    updated_at: datetime = Field(..., description="When the record was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "year": 2024,
                "crop_type": "corn_grain",
                "country": "US",
                "state": "IL",
                "yield_value": 14500,
                "yield_unit": "thousand_metric_tons",
                "source": "USDA NASS",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class CropYieldSummary(BaseModel):
    """Summary statistics for crop yield data."""

    total_records: int = Field(..., description="Total number of crop yield records")
    year_range: dict[str, Optional[int]] = Field(
        ..., description="Range of years with crop data"
    )
    crop_types: list[str] = Field(..., description="List of available crop types")
    countries: list[str] = Field(..., description="List of countries with crop data")
    states: list[str] = Field(..., description="List of states with crop data")
    yield_statistics: dict[str, dict[str, float]] = Field(
        ..., description="Yield statistics by crop type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_records": 1500,
                "year_range": {"earliest": 1990, "latest": 2024},
                "crop_types": ["corn_grain", "soybeans", "wheat", "cotton"],
                "countries": ["US", "CA", "MX"],
                "states": ["IL", "IA", "NE", "MN", "IN"],
                "yield_statistics": {
                    "corn_grain": {
                        "min": 8500.0,
                        "max": 16000.0,
                        "mean": 12250.0,
                        "median": 12100.0,
                    }
                },
            }
        }


class CropYieldTrend(BaseModel):
    """Crop yield trend data for a specific crop and location."""

    crop_type: str = Field(..., description="Type of crop")
    country: str = Field(..., description="Country code")
    state: Optional[str] = Field(None, description="State code (optional)")
    years: list[int] = Field(..., description="Years with data")
    yields: list[int] = Field(..., description="Yield values for each year")
    yield_unit: str = Field(..., description="Unit of measurement")
    trend_direction: str = Field(
        ..., description="Overall trend direction (up/down/stable)"
    )
    correlation_coefficient: Optional[float] = Field(
        None, description="Correlation coefficient with year"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "crop_type": "corn_grain",
                "country": "US",
                "state": "IL",
                "years": [2020, 2021, 2022, 2023, 2024],
                "yields": [13500, 14000, 13800, 14200, 14500],
                "yield_unit": "thousand_metric_tons",
                "trend_direction": "up",
                "correlation_coefficient": 0.85,
            }
        }


class CropYieldComparison(BaseModel):
    """Comparison of crop yields between different locations or time periods."""

    crop_type: str = Field(..., description="Type of crop being compared")
    yield_unit: str = Field(..., description="Unit of measurement")
    comparisons: list[dict[str, any]] = Field(
        ..., description="List of yield comparisons"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "crop_type": "corn_grain",
                "yield_unit": "thousand_metric_tons",
                "comparisons": [
                    {
                        "location": {"country": "US", "state": "IL"},
                        "year": 2024,
                        "yield": 14500,
                        "rank": 1,
                    },
                    {
                        "location": {"country": "US", "state": "IA"},
                        "year": 2024,
                        "yield": 13800,
                        "rank": 2,
                    },
                ],
            }
        }


class CropYieldFilter(BaseModel):
    """Filter parameters for crop yield queries."""

    year_start: Optional[int] = Field(None, ge=1800, le=2100, description="Start year")
    year_end: Optional[int] = Field(None, ge=1800, le=2100, description="End year")
    crop_types: Optional[list[str]] = Field(
        None, description="List of crop types to include"
    )
    countries: Optional[list[str]] = Field(
        None, description="List of countries to include"
    )
    states: Optional[list[str]] = Field(None, description="List of states to include")
    min_yield: Optional[int] = Field(None, ge=0, description="Minimum yield value")
    max_yield: Optional[int] = Field(None, ge=0, description="Maximum yield value")

    @validator("year_end")
    def validate_year_range(cls, v, values):
        """Validate that end year is not before start year."""
        if (
            v
            and "year_start" in values
            and values["year_start"]
            and v < values["year_start"]
        ):
            raise ValueError("End year must be greater than or equal to start year")
        return v

    @validator("max_yield")
    def validate_yield_range(cls, v, values):
        """Validate that max yield is not less than min yield."""
        if (
            v
            and "min_yield" in values
            and values["min_yield"]
            and v < values["min_yield"]
        ):
            raise ValueError("Max yield must be greater than or equal to min yield")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "year_start": 2020,
                "year_end": 2024,
                "crop_types": ["corn_grain", "soybeans"],
                "countries": ["US"],
                "states": ["IL", "IA", "NE"],
                "min_yield": 10000,
                "max_yield": 20000,
            }
        }
