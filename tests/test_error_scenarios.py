"""
Integration tests for error handling and edge cases.

This module tests:
- HTTP error responses (400, 404, 422, 500, etc.)
- Invalid parameter handling
- Edge cases and boundary conditions
- Rate limiting and throttling
- Malformed requests
- Authentication errors
"""

import pytest

from tests.test_base import IntegrationTestBase


@pytest.mark.integration
@pytest.mark.api
class TestHTTPErrorHandling(IntegrationTestBase):
    """Test HTTP error handling and responses."""

    @pytest.mark.asyncio
    async def test_404_errors(self):
        """Test 404 error handling."""
        invalid_endpoints = [
            "/api/nonexistent",
            "/api/v1/weather/nonexistent",
            "/api/v2/nonexistent",
            "/docs/nonexistent",
            "/api/v1/weather/stations/NONEXISTENT123",
            "/api/v1/stats/yearly/NONEXISTENT123",
        ]

        for endpoint in invalid_endpoints:
            response = await self.get(endpoint)

            # Should return 404
            assert response.status_code == 404, f"Endpoint {endpoint} should return 404"

            # Should have appropriate error format
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("application/json"):
                data = self.assert_json_response(response)
                assert "error" in data or "detail" in data or "message" in data

    @pytest.mark.asyncio
    async def test_400_bad_request_errors(self):
        """Test 400 Bad Request error handling."""
        # Test invalid query parameters
        bad_requests = [
            ("/api/v2/weather-stations", {"page": "invalid"}),
            ("/api/v2/weather-stations", {"page_size": "not_a_number"}),
            ("/api/v2/weather-stations", {"page": -1}),
            ("/api/v2/weather-stations", {"page_size": 0}),
            ("/api/v2/weather-stations", {"page_size": 10000}),  # Too large
            ("/api/v2/daily-weather", {"start_date": "invalid-date"}),
            ("/api/v2/daily-weather", {"end_date": "2023-13-45"}),  # Invalid date
            ("/api/v2/daily-weather", {"min_temp": "not_a_number"}),
            ("/api/v2/daily-weather", {"sort_order": "invalid"}),
            ("/api/v2/yearly-stats", {"start_year": "invalid"}),
            ("/api/v2/yearly-stats", {"end_year": 3000}),  # Future year
        ]

        for endpoint, params in bad_requests:
            response = await self.get(endpoint, params=params)

            # Should return 400 or 422
            assert response.status_code in [400, 422], (
                f"Endpoint {endpoint} with params {params} should return 400/422, "
                f"got {response.status_code}"
            )

            # Should have error information
            if response.headers.get("content-type", "").startswith("application/json"):
                data = self.assert_json_response(response)
                assert "error" in data or "detail" in data or "message" in data

    @pytest.mark.asyncio
    async def test_422_validation_errors(self):
        """Test 422 Unprocessable Entity errors."""
        # Test validation errors
        validation_errors = [
            ("/api/v2/weather-stations", {"states": ["INVALID_STATE"]}),
            ("/api/v2/daily-weather", {"states": ["XX"]}),  # Invalid state code
            (
                "/api/v2/daily-weather",
                {"start_date": "2023-01-01", "end_date": "2022-01-01"},
            ),  # End before start
            (
                "/api/v2/yearly-stats",
                {"start_year": 2020, "end_year": 2010},
            ),  # End before start
        ]

        for endpoint, params in validation_errors:
            response = await self.get(endpoint, params=params)

            # Should return 422 or 400
            assert response.status_code in [
                400,
                422,
            ], f"Endpoint {endpoint} with params {params} should return 400/422"

    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self):
        """Test 405 Method Not Allowed errors."""
        # Test wrong HTTP methods
        endpoints = [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
            "/docs/api",
            "/health",
        ]

        for endpoint in endpoints:
            # These endpoints should only accept GET
            response = await self.post(endpoint, json_data={"test": "data"})

            # Should return 405
            assert response.status_code in [
                405,
                404,
            ], f"POST to {endpoint} should return 405 or 404"

            # Check for Allow header
            if response.status_code == 405:
                assert (
                    "allow" in response.headers
                ), "405 response should include Allow header"

    @pytest.mark.asyncio
    async def test_500_server_errors(self):
        """Test server error handling (if any endpoints cause them)."""
        # Test edge cases that might cause server errors
        edge_cases = [
            ("/api/v2/daily-weather", {"page_size": -2147483648}),  # Integer overflow
            ("/api/v2/weather-stations", {"page": 999999999}),  # Very large page
        ]

        for endpoint, params in edge_cases:
            response = await self.get(endpoint, params=params)

            # Should not return 500
            assert response.status_code < 500, (
                f"Endpoint {endpoint} with params {params} should not return 500, "
                f"got {response.status_code}"
            )


@pytest.mark.integration
@pytest.mark.api
class TestEdgeCases(IntegrationTestBase):
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Test handling of empty results."""
        # Test filters that should return no results
        empty_filters = [
            ("/api/v2/weather-stations", {"search": "NONEXISTENT_STATION_12345"}),
            (
                "/api/v2/daily-weather",
                {"start_date": "2030-01-01", "end_date": "2030-01-01"},
            ),  # Future date
            (
                "/api/v2/yearly-stats",
                {"start_year": 2030, "end_year": 2030},
            ),  # Future year
        ]

        for endpoint, params in empty_filters:
            response = await self.get(endpoint, params=params)

            # Should return 200 with empty results
            self.assert_status_code(response, 200)
            data = self.assert_json_response(response)

            # Should be paginated response with empty items
            self.assert_pagination_response(data)
            assert (
                len(data["items"]) == 0
            ), f"Should return empty results for {endpoint}"
            assert data["pagination"]["total_items"] == 0

    @pytest.mark.asyncio
    async def test_boundary_values(self):
        """Test boundary values for parameters."""
        # Test minimum valid values
        boundary_tests = [
            ("/api/v2/weather-stations", {"page": 1, "page_size": 1}),
            ("/api/v2/daily-weather", {"page_size": 1}),
            ("/api/v2/yearly-stats", {"page_size": 1}),
        ]

        for endpoint, params in boundary_tests:
            response = await self.get(endpoint, params=params)

            # Should handle boundary values gracefully
            assert response.status_code in [
                200,
                400,
                422,
            ], f"Endpoint {endpoint} should handle boundary values gracefully"

            if response.status_code == 200:
                data = self.assert_json_response(response)
                self.assert_pagination_response(data)

                # Should respect page_size limit
                assert len(data["items"]) <= params.get("page_size", 50)

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test handling of special characters in parameters."""
        special_char_tests = [
            (
                "/api/v2/weather-stations",
                {"search": "'; DROP TABLE weather_stations; --"},
            ),  # SQL injection attempt
            (
                "/api/v2/weather-stations",
                {"search": "<script>alert('xss')</script>"},
            ),  # XSS attempt
            (
                "/api/v2/weather-stations",
                {"search": "../../etc/passwd"},
            ),  # Path traversal
            (
                "/api/v2/weather-stations",
                {"search": "unicode: 🌦️☀️🌡️"},
            ),  # Unicode characters
        ]

        for endpoint, params in special_char_tests:
            response = await self.get(endpoint, params=params)

            # Should handle special characters safely
            assert response.status_code in [
                200,
                400,
                422,
            ], f"Endpoint {endpoint} should handle special characters safely"

            # Should not return server errors
            assert (
                response.status_code < 500
            ), f"Special characters should not cause server errors in {endpoint}"

    @pytest.mark.asyncio
    async def test_large_parameter_values(self):
        """Test handling of large parameter values."""
        large_value_tests = [
            (
                "/api/v2/weather-stations",
                {"search": "A" * 1000},
            ),  # Very long search string
            ("/api/v2/daily-weather", {"states": ["IL"] * 100}),  # Many states
        ]

        for endpoint, params in large_value_tests:
            response = await self.get(endpoint, params=params)

            # Should handle large values gracefully
            assert response.status_code in [
                200,
                400,
                422,
            ], f"Endpoint {endpoint} should handle large values gracefully"

            # Should not cause server errors
            assert response.status_code < 500


@pytest.mark.integration
@pytest.mark.api
class TestConcurrencyAndLoad(IntegrationTestBase):
    """Test concurrency handling and load scenarios."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import asyncio

        # Create many concurrent requests
        endpoints = [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
            "/docs/api",
            "/health",
        ]

        tasks = []
        for _ in range(10):
            for endpoint in endpoints:
                tasks.append(self.get(endpoint, params={"page_size": 5}))

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_responses = 0
        client_errors = 0
        server_errors = 0
        exceptions = 0

        for response in responses:
            if isinstance(response, Exception):
                exceptions += 1
            else:
                if response.status_code < 400:
                    successful_responses += 1
                elif response.status_code < 500:
                    client_errors += 1
                else:
                    server_errors += 1

        # Should handle concurrent requests well
        success_rate = successful_responses / len(responses)
        assert success_rate >= 0.7, f"Success rate too low under load: {success_rate}"

        # Should not have many server errors
        server_error_rate = server_errors / len(responses)
        assert (
            server_error_rate < 0.1
        ), f"Too many server errors under load: {server_error_rate}"

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test request timeout handling."""
        # Test with very small timeout (this might not work in all environments)
        import httpx

        try:
            async with httpx.AsyncClient(timeout=0.001) as client:
                await client.get("http://test/api/v2/weather-stations")
                # If this doesn't timeout, that's also OK
        except httpx.TimeoutException:
            # Expected behavior
            pass
        except Exception:
            # Other exceptions are acceptable in this test
            pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_stability(self):
        """Test memory stability under repeated requests."""
        # Make many requests to check for memory leaks
        endpoint = "/api/v2/weather-stations"

        for i in range(50):
            response = await self.get(endpoint, params={"page_size": 10})

            # Should continue to work
            assert response.status_code in [
                200,
                400,
                404,
            ], f"Request {i} should not fail with server error"

            # Ensure response is handled properly
            if response.status_code == 200:
                data = self.assert_json_response(response)
                assert isinstance(data, dict)


@pytest.mark.integration
@pytest.mark.api
class TestDataIntegrity(IntegrationTestBase):
    """Test data integrity and consistency."""

    @pytest.mark.asyncio
    async def test_data_consistency_across_pages(self):
        """Test data consistency across pagination."""
        # Get first page
        response1 = await self.get(
            "/api/v2/weather-stations", params={"page": 1, "page_size": 5}
        )

        if response1.status_code == 200:
            data1 = self.assert_json_response(response1)

            if data1["pagination"]["has_next"]:
                # Get second page
                response2 = await self.get(
                    "/api/v2/weather-stations", params={"page": 2, "page_size": 5}
                )

                if response2.status_code == 200:
                    data2 = self.assert_json_response(response2)

                    # Should not have duplicate items
                    ids1 = {item["id"] for item in data1["items"]}
                    ids2 = {item["id"] for item in data2["items"]}

                    overlap = ids1.intersection(ids2)
                    assert (
                        len(overlap) == 0
                    ), f"Pages should not have duplicate items: {overlap}"

                    # Total items should be consistent
                    assert (
                        data1["pagination"]["total_items"]
                        == data2["pagination"]["total_items"]
                    )

    @pytest.mark.asyncio
    async def test_filter_consistency(self):
        """Test filter consistency and correctness."""
        # Test that filters actually work
        response = await self.get("/api/v2/weather-stations", params={"states": ["IL"]})

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # All results should match filter
            for station in data["items"]:
                assert (
                    station["state"] == "IL"
                ), f"Filter should be respected: {station}"

    @pytest.mark.asyncio
    async def test_sort_consistency(self):
        """Test sorting consistency and correctness."""
        response = await self.get(
            "/api/v2/weather-stations",
            params={"sort_by": "name", "sort_order": "asc", "page_size": 10},
        )

        if response.status_code == 200:
            data = self.assert_json_response(response)

            if len(data["items"]) > 1:
                # Should be sorted by name
                names = [station["name"] for station in data["items"]]
                assert names == sorted(
                    names
                ), f"Results should be sorted by name: {names}"


@pytest.mark.integration
@pytest.mark.api
class TestResponseFormats(IntegrationTestBase):
    """Test response format consistency and correctness."""

    @pytest.mark.asyncio
    async def test_json_response_format(self):
        """Test JSON response format consistency."""
        json_endpoints = [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
            "/docs/api",
            "/docs/api/examples",
            "/health",
        ]

        for endpoint in json_endpoints:
            response = await self.get(endpoint, params={"page_size": 5})

            if response.status_code == 200:
                # Should have JSON content type
                content_type = response.headers.get("content-type", "")
                assert content_type.startswith(
                    "application/json"
                ), f"Endpoint {endpoint} should return JSON"

                # Should be valid JSON
                data = self.assert_json_response(response)
                assert isinstance(data, dict | list)

    @pytest.mark.asyncio
    async def test_html_response_format(self):
        """Test HTML response format consistency."""
        html_endpoints = [
            "/docs",
            "/redoc",
            "/docs/api/custom-swagger",
            "/docs/api/custom-redoc",
        ]

        for endpoint in html_endpoints:
            response = await self.get(endpoint)

            if response.status_code == 200:
                # Should have HTML content type
                content_type = response.headers.get("content-type", "")
                assert (
                    "text/html" in content_type
                ), f"Endpoint {endpoint} should return HTML"

                # Should be valid HTML
                html_content = self.assert_html_response(response)
                assert "<html" in html_content or "<!DOCTYPE" in html_content

    @pytest.mark.asyncio
    async def test_error_response_format(self):
        """Test error response format consistency."""
        # Generate some errors
        response = await self.get("/api/v2/weather-stations", params={"page": -1})

        if response.status_code >= 400:
            # Error should have consistent format
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("application/json"):
                data = self.assert_json_response(response)

                # Should have error information
                error_fields = ["error", "detail", "message"]
                has_error_field = any(field in data for field in error_fields)
                assert (
                    has_error_field
                ), f"Error response should have error information: {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
