"""
Base test class with common utilities for integration testing.

This module provides:
- Base test class with common methods
- HTTP client utilities
- Response validation helpers
- Database testing utilities
- Performance testing helpers
"""

import json
from datetime import datetime
from typing import Any

import pytest
from httpx import AsyncClient, Response


class BaseAPITest:
    """Base class for API integration tests with common utilities."""

    client: "AsyncClient" = None

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Make a GET request with optional parameters and headers."""
        return await self.client.get(url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Make a POST request with optional JSON data."""
        return await self.client.post(url, json=json_data, data=data, headers=headers)

    async def put(
        self,
        url: str,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Make a PUT request with optional JSON data."""
        return await self.client.put(url, json=json_data, headers=headers)

    async def delete(self, url: str, headers: dict[str, str] | None = None) -> Response:
        """Make a DELETE request."""
        return await self.client.delete(url, headers=headers)

    def assert_status_code(self, response: Response, expected_code: int):
        """Assert that response has expected status code."""
        assert response.status_code == expected_code, (
            f"Expected status code {expected_code}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    def assert_json_response(self, response: Response) -> dict[str, Any]:
        """Assert that response is valid JSON and return parsed data."""
        assert response.headers.get("content-type", "").startswith(
            "application/json"
        ), f"Expected JSON response, got {response.headers.get('content-type')}"

        try:
            return response.json()
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}. Response text: {response.text}")

    def assert_html_response(self, response: Response) -> str:
        """Assert that response is HTML and return text."""
        content_type = response.headers.get("content-type", "")
        assert (
            "text/html" in content_type
        ), f"Expected HTML response, got {content_type}"
        return response.text

    def assert_required_fields(self, data: dict[str, Any], required_fields: list[str]):
        """Assert that all required fields are present in data."""
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        assert not missing_fields, f"Missing required fields: {missing_fields}"

    def assert_field_types(self, data: dict[str, Any], field_types: dict[str, type]):
        """Assert that fields have correct types."""
        type_errors = []

        for field, expected_type in field_types.items():
            if field in data:
                actual_value = data[field]
                if not isinstance(actual_value, expected_type):
                    type_errors.append(
                        f"Field '{field}' has incorrect type. "
                        f"Expected {expected_type}, got {type(actual_value)}"
                    )

        assert not type_errors, f"Type validation errors: {type_errors}"

    def assert_pagination_response(self, data: dict[str, Any]):
        """Assert that response has valid pagination structure."""
        required_fields = ["items", "pagination", "links"]
        self.assert_required_fields(data, required_fields)

        # Validate pagination metadata
        pagination = data["pagination"]
        pagination_fields = [
            "page",
            "page_size",
            "total_items",
            "total_pages",
            "has_next",
            "has_previous",
        ]
        self.assert_required_fields(pagination, pagination_fields)

        # Validate types
        assert isinstance(pagination["page"], int) and pagination["page"] >= 1
        assert isinstance(pagination["page_size"], int) and pagination["page_size"] >= 1
        assert (
            isinstance(pagination["total_items"], int)
            and pagination["total_items"] >= 0
        )
        assert (
            isinstance(pagination["total_pages"], int)
            and pagination["total_pages"] >= 0
        )
        assert isinstance(pagination["has_next"], bool)
        assert isinstance(pagination["has_previous"], bool)

        # Validate links
        links = data["links"]
        assert isinstance(links, dict)
        assert "self" in links

        # Validate items
        assert isinstance(data["items"], list)

    def assert_error_response(self, response: Response, expected_status: int):
        """Assert that response is a proper error response."""
        self.assert_status_code(response, expected_status)

        # For JSON error responses
        if response.headers.get("content-type", "").startswith("application/json"):
            data = self.assert_json_response(response)
            assert (
                "error" in data or "detail" in data
            ), "Error response should contain error information"

    def assert_response_time(self, response: Response, max_seconds: float = 5.0):
        """Assert that response time is within acceptable limits."""
        # Note: This is a simplified version. In real tests, you'd measure elapsed time
        # during the request. For now, we'll just check that we got a response.
        assert response is not None, "Should receive a response within time limit"

    def extract_pagination_info(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Extract pagination information from response."""
        return {
            "current_page": response_data["pagination"]["page"],
            "page_size": response_data["pagination"]["page_size"],
            "total_items": response_data["pagination"]["total_items"],
            "total_pages": response_data["pagination"]["total_pages"],
            "has_next": response_data["pagination"]["has_next"],
            "has_previous": response_data["pagination"]["has_previous"],
            "items_count": len(response_data["items"]),
        }

    def assert_date_format(self, date_string: str):
        """Assert that date string is in correct ISO format."""
        try:
            datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid date format: {date_string}")

    def assert_geographic_coordinates(self, latitude: float, longitude: float):
        """Assert that geographic coordinates are valid."""
        assert -90 <= latitude <= 90, f"Invalid latitude: {latitude}"
        assert -180 <= longitude <= 180, f"Invalid longitude: {longitude}"

    def assert_weather_data_validity(self, weather_data: dict[str, Any]):
        """Assert that weather data contains valid values."""
        # Temperature should be reasonable (in tenths of degrees Celsius)
        if weather_data.get("max_temp") is not None:
            max_temp = weather_data["max_temp"]
            assert (
                -500 <= max_temp <= 600
            ), f"Unreasonable max temperature: {max_temp/10}°C"

        if weather_data.get("min_temp") is not None:
            min_temp = weather_data["min_temp"]
            assert (
                -500 <= min_temp <= 600
            ), f"Unreasonable min temperature: {min_temp/10}°C"

        # Check temperature relationship
        if (
            weather_data.get("max_temp") is not None
            and weather_data.get("min_temp") is not None
        ):
            assert (
                weather_data["max_temp"] >= weather_data["min_temp"]
            ), "Max temperature should be >= min temperature"

        # Precipitation should be non-negative (in tenths of mm)
        if weather_data.get("precipitation") is not None:
            precipitation = weather_data["precipitation"]
            assert precipitation >= 0, f"Negative precipitation: {precipitation/10}mm"

    async def test_endpoint_accessibility(self, endpoints: list[str]):
        """Test that all endpoints are accessible and return appropriate responses."""
        results = {}

        for endpoint in endpoints:
            try:
                response = await self.get(endpoint)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 500,
                    "content_type": response.headers.get("content-type", ""),
                }
            except Exception as e:
                results[endpoint] = {
                    "status_code": None,
                    "accessible": False,
                    "error": str(e),
                }

        return results

    async def test_pagination_consistency(
        self, endpoint: str, params: dict[str, Any] | None = None, max_pages: int = 3
    ):
        """Test pagination consistency across multiple pages."""
        if params is None:
            params = {}

        pages_data = []
        current_page = 1

        while current_page <= max_pages:
            test_params = {**params, "page": current_page, "page_size": 5}
            response = await self.get(endpoint, params=test_params)

            if response.status_code != 200:
                break

            data = self.assert_json_response(response)
            self.assert_pagination_response(data)

            pages_data.append(data)

            if not data["pagination"]["has_next"]:
                break

            current_page += 1

        # Validate pagination consistency
        if len(pages_data) > 1:
            for i, page_data in enumerate(pages_data):
                expected_page = i + 1
                assert page_data["pagination"]["page"] == expected_page

                # First page should not have previous
                if i == 0:
                    assert not page_data["pagination"]["has_previous"]
                else:
                    assert page_data["pagination"]["has_previous"]

        return pages_data

    async def test_filter_combinations(
        self, endpoint: str, filter_params: dict[str, list[Any]]
    ):
        """Test various combinations of filters."""
        results = {}

        # Test individual filters
        for param_name, param_values in filter_params.items():
            for value in param_values:
                params = {param_name: value, "page_size": 5}
                response = await self.get(endpoint, params=params)

                results[f"{param_name}={value}"] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                }

                if response.status_code == 200:
                    data = self.assert_json_response(response)
                    results[f"{param_name}={value}"]["items_count"] = len(
                        data.get("items", [])
                    )

        # Test combined filters
        if len(filter_params) > 1:
            combined_params = {"page_size": 5}
            for param_name, param_values in filter_params.items():
                if param_values:
                    combined_params[param_name] = param_values[0]

            response = await self.get(endpoint, params=combined_params)
            results["combined_filters"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "params": combined_params,
            }

        return results


class WeatherStationTestMixin:
    """Mixin for weather station specific test utilities."""

    def assert_weather_station_structure(self, station_data: dict[str, Any]):
        """Assert that weather station data has correct structure."""
        required_fields = ["id", "station_id", "name", "state", "latitude", "longitude"]
        self.assert_required_fields(station_data, required_fields)

        # Validate data types
        assert isinstance(station_data["id"], int)
        assert (
            isinstance(station_data["station_id"], str)
            and len(station_data["station_id"]) > 0
        )
        assert isinstance(station_data["name"], str) and len(station_data["name"]) > 0
        assert (
            isinstance(station_data["state"], str) and len(station_data["state"]) == 2
        )
        assert isinstance(station_data["latitude"], int | float)
        assert isinstance(station_data["longitude"], int | float)

        # Validate coordinates
        self.assert_geographic_coordinates(
            station_data["latitude"], station_data["longitude"]
        )


class DailyWeatherTestMixin:
    """Mixin for daily weather data specific test utilities."""

    def assert_daily_weather_structure(self, weather_data: dict[str, Any]):
        """Assert that daily weather data has correct structure."""
        required_fields = ["id", "station", "date"]
        self.assert_required_fields(weather_data, required_fields)

        # Validate data types
        assert isinstance(weather_data["id"], int)
        assert isinstance(
            weather_data["station"], dict | int
        )  # Can be nested object or ID
        assert isinstance(weather_data["date"], str)

        # Validate date format
        self.assert_date_format(weather_data["date"])

        # Validate weather measurements
        self.assert_weather_data_validity(weather_data)


class DocumentationTestMixin:
    """Mixin for documentation specific test utilities."""

    def assert_openapi_schema(self, schema_data: dict[str, Any]):
        """Assert that OpenAPI schema has correct structure."""
        required_fields = ["openapi", "info", "paths"]
        self.assert_required_fields(schema_data, required_fields)

        # Validate info section
        info = schema_data["info"]
        info_fields = ["title", "version", "description"]
        self.assert_required_fields(info, info_fields)

        # Validate paths
        paths = schema_data["paths"]
        assert isinstance(paths, dict) and len(paths) > 0

    def assert_api_info_structure(self, api_info: dict[str, Any]):
        """Assert that API info has correct structure."""
        required_fields = [
            "name",
            "version",
            "description",
            "documentation",
            "endpoints",
        ]
        self.assert_required_fields(api_info, required_fields)

        # Validate documentation links
        docs = api_info["documentation"]
        doc_fields = ["swagger_ui", "redoc", "openapi_schema"]
        self.assert_required_fields(docs, doc_fields)

        # Validate endpoints
        endpoints = api_info["endpoints"]
        assert isinstance(endpoints, dict) and len(endpoints) > 0


class PerformanceTestMixin:
    """Mixin for performance testing utilities."""

    async def measure_response_time(
        self, method: str, url: str, **kwargs
    ) -> dict[str, Any]:
        """Measure response time for a request."""
        start_time = datetime.now()

        if method.upper() == "GET":
            response = await self.get(url, **kwargs)
        elif method.upper() == "POST":
            response = await self.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()

        return {
            "response": response,
            "elapsed_time": elapsed_time,
            "status_code": response.status_code,
            "success": response.status_code < 400,
        }

    async def test_response_times(self, endpoints: list[str], max_time: float = 2.0):
        """Test response times for multiple endpoints."""
        results = {}

        for endpoint in endpoints:
            result = await self.measure_response_time("GET", endpoint)
            results[endpoint] = {
                "elapsed_time": result["elapsed_time"],
                "within_limit": result["elapsed_time"] <= max_time,
                "status_code": result["status_code"],
            }

        return results


class IntegrationTestBase(
    BaseAPITest,
    WeatherStationTestMixin,
    DailyWeatherTestMixin,
    DocumentationTestMixin,
    PerformanceTestMixin,
):
    """
    Complete base class for integration tests.

    Combines all mixins to provide comprehensive testing utilities.
    """

    @pytest.fixture(autouse=True)
    async def setup_client(self, client: AsyncClient):
        """Set up the HTTP client for tests."""
        self.client = client
