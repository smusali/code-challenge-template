"""
Unit conversion utilities for weather data.

This module contains functions to convert between different units used in weather data:
- Temperature: tenths of degrees Celsius to degrees Celsius
- Precipitation: tenths of millimeters to millimeters
- Data quality calculations and rounding utilities
"""

from decimal import Decimal


def tenths_to_celsius(tenths_value: int | float | None) -> float | None:
    """
    Convert temperature from tenths of degrees Celsius to degrees Celsius.

    Args:
        tenths_value: Temperature in tenths of degrees Celsius, or None

    Returns:
        Temperature in degrees Celsius, or None if input is None

    Examples:
        >>> tenths_to_celsius(250)
        25.0
        >>> tenths_to_celsius(-50)
        -5.0
        >>> tenths_to_celsius(None)
        None
    """
    return tenths_value / 10.0 if tenths_value is not None else None


def tenths_to_millimeters(tenths_value: int | float | None) -> float | None:
    """
    Convert precipitation from tenths of millimeters to millimeters.

    Args:
        tenths_value: Precipitation in tenths of millimeters, or None

    Returns:
        Precipitation in millimeters, or None if input is None

    Examples:
        >>> tenths_to_millimeters(125)
        12.5
        >>> tenths_to_millimeters(0)
        0.0
        >>> tenths_to_millimeters(None)
        None
    """
    return tenths_value / 10.0 if tenths_value is not None else None


def decimal_tenths_to_celsius(tenths_value: Decimal | None) -> float | None:
    """
    Convert temperature from Decimal tenths of degrees Celsius to degrees Celsius.

    Args:
        tenths_value: Temperature in tenths of degrees Celsius as Decimal, or None

    Returns:
        Temperature in degrees Celsius as float, or None if input is None

    Examples:
        >>> decimal_tenths_to_celsius(Decimal('250.5'))
        25.05
        >>> decimal_tenths_to_celsius(None)
        None
    """
    return float(tenths_value) / 10.0 if tenths_value is not None else None


def decimal_tenths_to_millimeters(tenths_value: Decimal | None) -> float | None:
    """
    Convert precipitation from Decimal tenths of millimeters to millimeters.

    Args:
        tenths_value: Precipitation in tenths of millimeters as Decimal, or None

    Returns:
        Precipitation in millimeters as float, or None if input is None

    Examples:
        >>> decimal_tenths_to_millimeters(Decimal('125.5'))
        12.55
        >>> decimal_tenths_to_millimeters(None)
        None
    """
    return float(tenths_value) / 10.0 if tenths_value is not None else None


def calculate_data_completeness(records_with_data: int, total_records: int) -> float:
    """
    Calculate data completeness as a percentage.

    Args:
        records_with_data: Number of records containing valid data
        total_records: Total number of records

    Returns:
        Completeness percentage (0.0 to 100.0)

    Examples:
        >>> calculate_data_completeness(80, 100)
        80.0
        >>> calculate_data_completeness(0, 100)
        0.0
        >>> calculate_data_completeness(50, 0)
        0.0
    """
    if total_records == 0:
        return 0.0
    return (records_with_data / total_records) * 100.0


def round_to_decimal(value: float | None, decimal_places: int = 1) -> Decimal | None:
    """
    Round a float value to specified decimal places and return as Decimal.

    Args:
        value: Float value to round, or None
        decimal_places: Number of decimal places to round to (default: 1)

    Returns:
        Rounded value as Decimal, or None if input is None

    Examples:
        >>> round_to_decimal(25.456)
        Decimal('25.5')
        >>> round_to_decimal(25.456, 2)
        Decimal('25.46')
        >>> round_to_decimal(None)
        None
    """
    if value is None:
        return None
    return Decimal(str(round(value, decimal_places)))


def celsius_to_tenths(celsius_value: float | None) -> int | None:
    """
    Convert temperature from degrees Celsius to tenths of degrees Celsius.

    Args:
        celsius_value: Temperature in degrees Celsius, or None

    Returns:
        Temperature in tenths of degrees Celsius, or None if input is None

    Examples:
        >>> celsius_to_tenths(25.0)
        250
        >>> celsius_to_tenths(-5.5)
        -55
        >>> celsius_to_tenths(None)
        None
    """
    return int(celsius_value * 10) if celsius_value is not None else None


def millimeters_to_tenths(mm_value: float | None) -> int | None:
    """
    Convert precipitation from millimeters to tenths of millimeters.

    Args:
        mm_value: Precipitation in millimeters, or None

    Returns:
        Precipitation in tenths of millimeters, or None if input is None

    Examples:
        >>> millimeters_to_tenths(12.5)
        125
        >>> millimeters_to_tenths(0.0)
        0
        >>> millimeters_to_tenths(None)
        None
    """
    return int(mm_value * 10) if mm_value is not None else None
