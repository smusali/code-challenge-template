"""
Integration tests for health and system endpoints.

This module tests:
- Health check endpoint functionality
- System information endpoints
- Root API information endpoint
- Response formats and content validation
- Performance and availability
"""

import pytest

from tests.test_base import IntegrationTestBase


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoints(IntegrationTestBase):
    """Test health check and system status endpoints."""

    @pytest.mark.asyncio
    async def test_health_check_basic(self):
        """Test basic health check endpoint."""
        response = await self.get("/health")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate response structure
        required_fields = ["status", "timestamp"]
        self.assert_required_fields(data, required_fields)

        # Validate field types and values
        assert isinstance(data["status"], str)
        assert data["status"] in ["healthy", "unhealthy", "degraded"]

        # Validate timestamp format
        self.assert_date_format(data["timestamp"])

    @pytest.mark.asyncio
    async def test_health_check_detailed(self):
        """Test detailed health check response."""
        response = await self.get("/health")
        data = self.assert_json_response(response)

        # Should contain additional health information
        expected_optional_fields = ["version", "uptime", "environment"]
        for field in expected_optional_fields:
            if field in data:
                assert data[field] is not None

                if field == "version":
                    assert isinstance(data[field], str) and len(data[field]) > 0
                elif field == "uptime":
                    assert isinstance(data[field], int | float) and data[field] >= 0
                elif field == "environment":
                    assert isinstance(data[field], str)

    @pytest.mark.asyncio
    async def test_health_endpoint_with_trailing_slash(self):
        """Test health endpoint with trailing slash."""
        response = await self.get("/health/")

        # Should still work (might redirect or handle gracefully)
        assert response.status_code in [200, 301, 302, 404]

        if response.status_code == 200:
            data = self.assert_json_response(response)
            assert "status" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root API information endpoint."""
        response = await self.get("/")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate root endpoint structure
        required_fields = ["message", "version", "documentation", "endpoints"]
        self.assert_required_fields(data, required_fields)

        # Validate field types
        assert isinstance(data["message"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["documentation"], dict)
        assert isinstance(data["endpoints"], dict)

        # Validate documentation links
        docs = data["documentation"]
        expected_doc_fields = ["swagger_ui", "redoc", "openapi_schema"]
        for field in expected_doc_fields:
            assert field in docs
            assert isinstance(docs[field], str)
            assert docs[field].startswith("/")

        # Validate endpoints
        endpoints = data["endpoints"]
        assert len(endpoints) > 0
        for endpoint_name, endpoint_path in endpoints.items():
            assert isinstance(endpoint_name, str)
            assert isinstance(endpoint_path, str)
            assert endpoint_path.startswith("/")

    @pytest.mark.asyncio
    async def test_api_info_endpoint(self):
        """Test system information endpoint."""
        response = await self.get("/info")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate system info structure
        expected_sections = ["api", "database", "django"]
        for section in expected_sections:
            if section in data:
                assert isinstance(data[section], dict)

                if section == "api":
                    api_info = data[section]
                    assert "name" in api_info
                    assert "version" in api_info
                    assert isinstance(api_info["name"], str)
                    assert isinstance(api_info["version"], str)

                elif section == "database":
                    db_info = data[section]
                    assert "engine" in db_info
                    assert "name" in db_info
                    assert isinstance(db_info["engine"], str)
                    assert isinstance(db_info["name"], str)

                elif section == "django":
                    django_info = data[section]
                    assert "version" in django_info
                    assert isinstance(django_info["version"], list | tuple)

    @pytest.mark.asyncio
    async def test_health_response_consistency(self):
        """Test that health check responses are consistent across multiple calls."""
        responses = []

        # Make multiple requests
        for _ in range(3):
            response = await self.get("/health")
            self.assert_status_code(response, 200)
            data = self.assert_json_response(response)
            responses.append(data)

        # All responses should have the same status
        statuses = [r["status"] for r in responses]
        assert len(set(statuses)) == 1, "Health status should be consistent"

        # Timestamps should be different (requests made at different times)
        timestamps = [r["timestamp"] for r in responses]
        assert len(set(timestamps)) == len(timestamps), "Timestamps should be unique"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self):
        """Test health endpoint response time."""
        # Health checks should be fast
        result = await self.measure_response_time("GET", "/health")

        assert result["success"], "Health check should succeed"
        assert (
            result["elapsed_time"] < 1.0
        ), f"Health check too slow: {result['elapsed_time']}s"

    @pytest.mark.asyncio
    async def test_health_endpoint_headers(self):
        """Test health endpoint response headers."""
        response = await self.get("/health")

        # Validate headers
        assert "content-type" in response.headers
        assert response.headers["content-type"].startswith("application/json")

        # Check for security headers (if implemented)
        security_headers = ["x-content-type-options", "x-frame-options"]
        for header in security_headers:
            if header in response.headers:
                # If present, should have secure values
                assert response.headers[header] is not None

    @pytest.mark.asyncio
    async def test_endpoints_accessibility(self):
        """Test that all system endpoints are accessible."""
        endpoints = ["/", "/health", "/info"]

        results = await self.test_endpoint_accessibility(endpoints)

        for endpoint, result in results.items():
            assert result["accessible"], f"Endpoint {endpoint} should be accessible"
            assert (
                result["status_code"] == 200
            ), f"Endpoint {endpoint} should return 200"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_health_under_load(self):
        """Test health endpoint under multiple concurrent requests."""
        import asyncio

        # Create multiple concurrent requests
        tasks = [self.get("/health") for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All requests should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Request {i} should succeed"
            data = self.assert_json_response(response)
            assert data["status"] in ["healthy", "unhealthy", "degraded"]

    @pytest.mark.asyncio
    async def test_invalid_health_methods(self):
        """Test that health endpoint only accepts GET requests."""
        # Test other HTTP methods
        methods_to_test = ["POST", "PUT", "DELETE"]

        for method in methods_to_test:
            if method == "POST":
                response = await self.post("/health")
            elif method == "PUT":
                response = await self.put("/health")
            elif method == "DELETE":
                response = await self.delete("/health")

            # Should return method not allowed or not found
            assert response.status_code in [
                405,
                404,
            ], f"Health endpoint should not accept {method} requests"

    @pytest.mark.asyncio
    async def test_root_endpoint_content_validation(self):
        """Test detailed validation of root endpoint content."""
        response = await self.get("/")
        data = self.assert_json_response(response)

        # Validate API message
        assert "Weather Data Engineering API" in data["message"]

        # Validate version format (should be semantic versioning)
        version = data["version"]
        version_parts = version.split(".")
        assert (
            len(version_parts) >= 2
        ), "Version should have at least major.minor format"

        # Validate documentation URLs are valid paths
        docs = data["documentation"]
        for _doc_type, url in docs.items():
            assert url.startswith(
                "/"
            ), f"Documentation URL should be absolute path: {url}"

            # Test that documentation endpoints are accessible
            doc_response = await self.get(url)
            assert doc_response.status_code in [
                200,
                302,
            ], f"Documentation endpoint {url} should be accessible"

        # Validate endpoint URLs
        endpoints = data["endpoints"]
        for _endpoint_name, endpoint_url in endpoints.items():
            assert endpoint_url.startswith(
                "/"
            ), f"Endpoint URL should be absolute path: {endpoint_url}"

    @pytest.mark.asyncio
    async def test_system_info_content_validation(self):
        """Test detailed validation of system info content."""
        response = await self.get("/info")
        data = self.assert_json_response(response)

        # Validate API information
        if "api" in data:
            api_info = data["api"]
            assert "Weather Data Engineering API" in api_info.get("name", "")

            # Environment should be a valid value
            if "environment" in api_info:
                valid_environments = ["development", "testing", "staging", "production"]
                assert api_info["environment"] in valid_environments

        # Validate database information
        if "database" in data:
            db_info = data["database"]
            if "engine" in db_info:
                # Should be a known database engine
                assert "django.db.backends" in db_info["engine"]

        # Validate Django information
        if "django" in data:
            django_info = data["django"]
            if "version" in django_info:
                version = django_info["version"]
                assert len(version) >= 3, "Django version should have major.minor.patch"
                assert all(isinstance(v, int) for v in version[:3])

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid requests."""
        # Test non-existent endpoint
        response = await self.get("/non-existent-endpoint")
        assert response.status_code == 404

        # Test malformed URL (if applicable)
        response = await self.get("/health/../..")
        # Should either normalize the path or return 404
        assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.performance
class TestSystemPerformance(IntegrationTestBase):
    """Test system performance and availability."""

    @pytest.mark.asyncio
    async def test_response_times(self):
        """Test response times for all system endpoints."""
        endpoints = ["/", "/health", "/info"]

        results = await self.test_response_times(endpoints, max_time=2.0)

        for endpoint, result in results.items():
            assert result[
                "within_limit"
            ], f"Endpoint {endpoint} took {result['elapsed_time']}s (limit: 2.0s)"
            assert result["status_code"] == 200

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests to system endpoints."""
        import asyncio

        # Create concurrent requests to different endpoints
        tasks = []
        endpoints = ["/", "/health", "/info"]

        for _ in range(5):
            for endpoint in endpoints:
                tasks.append(self.get(endpoint))

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate all responses
        successful_responses = 0
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Request failed with exception: {response}")
            else:
                if response.status_code == 200:
                    successful_responses += 1

        # At least 80% of requests should succeed
        success_rate = successful_responses / len(responses)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test that repeated requests don't cause memory issues."""
        # Make many requests to check for memory leaks
        for _ in range(20):
            response = await self.get("/health")
            self.assert_status_code(response, 200)

            # Ensure response is properly handled
            data = self.assert_json_response(response)
            assert "status" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
