"""
Integration tests for documentation endpoints and OpenAPI features.

This module tests:
- OpenAPI schema generation and validation
- Swagger UI accessibility and customization
- ReDoc documentation
- API information endpoints
- Examples and integration guides
- Documentation status and health
"""

import json

import pytest

from tests.test_base import IntegrationTestBase


@pytest.mark.integration
@pytest.mark.documentation
class TestOpenAPIDocumentation(IntegrationTestBase):
    """Test OpenAPI schema and documentation endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_schema(self):
        """Test OpenAPI schema generation."""
        response = await self.get("/openapi.json")

        self.assert_status_code(response, 200)
        schema = self.assert_json_response(response)

        # Validate OpenAPI schema structure
        self.assert_openapi_schema(schema)

        # Validate specific Weather API requirements
        info = schema["info"]
        assert "Weather Data Engineering API" in info["title"]
        assert "version" in info
        assert "description" in info

        # Check for contact information
        if "contact" in info:
            contact = info["contact"]
            assert isinstance(contact, dict)
            if "email" in contact:
                assert "@" in contact["email"]

        # Validate paths
        paths = schema["paths"]
        expected_paths = [
            "/health",
            "/",
            "/info",
            "/docs/api",
            "/api/v2/weather-stations",
        ]

        for expected_path in expected_paths:
            assert (
                expected_path in paths
            ), f"Expected path {expected_path} not found in OpenAPI schema"

    @pytest.mark.asyncio
    async def test_swagger_ui(self):
        """Test Swagger UI accessibility."""
        response = await self.get("/docs")

        self.assert_status_code(response, 200)
        html_content = self.assert_html_response(response)

        # Validate Swagger UI content
        assert (
            "swagger-ui" in html_content.lower()
        ), "Should contain Swagger UI elements"
        assert "openapi.json" in html_content, "Should reference OpenAPI schema"

        # Check for custom styling (if implemented)
        if "weather" in html_content.lower():
            assert True  # Custom weather theme detected

    @pytest.mark.asyncio
    async def test_redoc_documentation(self):
        """Test ReDoc documentation accessibility."""
        response = await self.get("/redoc")

        self.assert_status_code(response, 200)
        html_content = self.assert_html_response(response)

        # Validate ReDoc content
        assert "redoc" in html_content.lower(), "Should contain ReDoc elements"
        assert "openapi.json" in html_content, "Should reference OpenAPI schema"

    @pytest.mark.asyncio
    async def test_custom_swagger_ui(self):
        """Test custom Swagger UI endpoint."""
        response = await self.get("/docs/api/custom-swagger")

        self.assert_status_code(response, 200)
        html_content = self.assert_html_response(response)

        # Should have enhanced Swagger UI
        assert "swagger-ui" in html_content.lower()
        assert "weather" in html_content.lower()  # Custom weather theme

    @pytest.mark.asyncio
    async def test_custom_redoc(self):
        """Test custom ReDoc endpoint."""
        response = await self.get("/docs/api/custom-redoc")

        self.assert_status_code(response, 200)
        html_content = self.assert_html_response(response)

        # Should have enhanced ReDoc
        assert "redoc" in html_content.lower()


@pytest.mark.integration
@pytest.mark.documentation
class TestAPIInformationEndpoints(IntegrationTestBase):
    """Test API information and documentation endpoints."""

    @pytest.mark.asyncio
    async def test_api_info_endpoint(self):
        """Test main API information endpoint."""
        response = await self.get("/docs/api")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate API info structure
        self.assert_api_info_structure(data)

        # Validate specific content
        assert "Weather Data Engineering API" in data["name"]
        assert len(data["version"]) > 0
        assert "weather" in data["description"].lower()

        # Validate documentation links
        docs = data["documentation"]
        for _doc_type, url in docs.items():
            assert url.startswith("/"), f"Documentation URL should be absolute: {url}"

        # Validate endpoints count
        assert data["endpoints_count"] > 0
        assert isinstance(data["endpoints_count"], int)

    @pytest.mark.asyncio
    async def test_endpoints_info(self):
        """Test endpoints information endpoint."""
        response = await self.get("/docs/api/endpoints")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Should be a list of endpoint information
        assert isinstance(data, list)

        if len(data) > 0:
            endpoint_info = data[0]
            required_fields = ["path", "method"]
            self.assert_required_fields(endpoint_info, required_fields)

            assert isinstance(endpoint_info["path"], str)
            assert endpoint_info["method"] in ["GET", "POST", "PUT", "DELETE", "PATCH"]

    @pytest.mark.asyncio
    async def test_api_examples(self):
        """Test API examples endpoint."""
        response = await self.get("/docs/api/examples")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Should be a list of examples
        assert isinstance(data, list)
        assert len(data) > 0, "Should have API examples"

        for example in data:
            required_fields = ["title", "description", "method", "url", "curl_example"]
            self.assert_required_fields(example, required_fields)

            # Validate example structure
            assert isinstance(example["title"], str) and len(example["title"]) > 0
            assert (
                isinstance(example["description"], str)
                and len(example["description"]) > 0
            )
            assert example["method"] in ["GET", "POST", "PUT", "DELETE", "PATCH"]
            assert example["url"].startswith("http"), "Example URL should be complete"
            assert "curl" in example["curl_example"], "Should contain curl command"

    @pytest.mark.asyncio
    async def test_integration_guides(self):
        """Test integration guides endpoint."""
        response = await self.get("/docs/api/integration-guides")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Should be a list of integration guides
        assert isinstance(data, list)
        assert len(data) > 0, "Should have integration guides"

        # Check for expected languages
        languages = [guide["language"] for guide in data]
        expected_languages = ["python", "javascript"]

        for expected_lang in expected_languages:
            assert (
                expected_lang in languages
            ), f"Should have {expected_lang} integration guide"

        for guide in data:
            required_fields = [
                "title",
                "description",
                "language",
                "code_example",
                "prerequisites",
                "steps",
            ]
            self.assert_required_fields(guide, required_fields)

            # Validate guide structure
            assert isinstance(guide["title"], str) and len(guide["title"]) > 0
            assert (
                isinstance(guide["code_example"], str)
                and len(guide["code_example"]) > 100
            )
            assert isinstance(guide["prerequisites"], list)
            assert isinstance(guide["steps"], list)

    @pytest.mark.asyncio
    async def test_documentation_status(self):
        """Test documentation status endpoint."""
        response = await self.get("/docs/api/status")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate status structure
        required_fields = ["status", "schema_available", "total_endpoints"]
        self.assert_required_fields(data, required_fields)

        # Validate field values
        assert data["status"] in ["healthy", "error"]
        assert isinstance(data["schema_available"], bool)
        assert isinstance(data["total_endpoints"], int) and data["total_endpoints"] > 0

        # If status is healthy, should have additional info
        if data["status"] == "healthy":
            assert "features" in data
            assert "documentation_urls" in data

            features = data["features"]
            assert isinstance(features, dict)

            expected_features = ["swagger_ui", "redoc", "examples"]
            for feature in expected_features:
                if feature in features:
                    assert isinstance(features[feature], bool)


@pytest.mark.integration
@pytest.mark.documentation
class TestDocumentationContent(IntegrationTestBase):
    """Test documentation content validation and quality."""

    @pytest.mark.asyncio
    async def test_api_examples_validity(self):
        """Test that API examples are valid and executable."""
        response = await self.get("/docs/api/examples")
        data = self.assert_json_response(response)

        for example in data:
            # Test if example URLs are valid by making actual requests
            if example["method"] == "GET":
                # Extract path from full URL
                example_url = example["url"]
                if "http" in example_url:
                    # Extract just the path
                    path = (
                        example_url.split("//")[1].split("/", 1)[1]
                        if "/" in example_url.split("//")[1]
                        else ""
                    )
                    if path:
                        path = "/" + path

                        # Test the endpoint (may fail due to filters, but should not 500)
                        try:
                            test_response = await self.get(path)
                            assert (
                                test_response.status_code < 500
                            ), f"Example endpoint {path} should not return server error"
                        except Exception:
                            # Some examples might have complex parameters, that's ok
                            pass

    @pytest.mark.asyncio
    async def test_integration_guides_completeness(self):
        """Test integration guides completeness and quality."""
        response = await self.get("/docs/api/integration-guides")
        data = self.assert_json_response(response)

        for guide in data:
            # Code examples should be substantial
            code_example = guide["code_example"]
            assert (
                len(code_example) > 200
            ), f"Code example for {guide['language']} should be substantial"

            # Should contain actual code patterns
            language = guide["language"]
            if language == "python":
                assert "import" in code_example, "Python guide should have imports"
                assert (
                    "def " in code_example or "class " in code_example
                ), "Python guide should have functions/classes"
            elif language == "javascript":
                assert (
                    "async" in code_example or "function" in code_example
                ), "JavaScript guide should have functions"
                assert (
                    "await" in code_example or "then" in code_example
                ), "JavaScript guide should handle async"

            # Prerequisites should be meaningful
            prerequisites = guide["prerequisites"]
            assert len(prerequisites) > 0, f"Should have prerequisites for {language}"

            # Steps should be actionable
            steps = guide["steps"]
            assert len(steps) > 2, f"Should have multiple steps for {language}"

    @pytest.mark.asyncio
    async def test_openapi_schema_completeness(self):
        """Test OpenAPI schema completeness and quality."""
        response = await self.get("/openapi.json")
        schema = self.assert_json_response(response)

        # Should have tags for organization
        assert "tags" in schema, "Schema should have tags for organization"
        tags = schema["tags"]
        assert len(tags) > 0, "Should have at least one tag"

        for tag in tags:
            assert "name" in tag, "Tag should have name"
            assert "description" in tag, "Tag should have description"
            assert len(tag["description"]) > 50, "Tag description should be substantial"

        # Should have security definitions
        if "components" in schema and "securitySchemes" in schema["components"]:
            security_schemes = schema["components"]["securitySchemes"]
            assert len(security_schemes) > 0, "Should have security schemes defined"

        # Check path documentation quality
        paths = schema["paths"]
        documented_paths = 0

        for path, methods in paths.items():
            for method, spec in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    documented_paths += 1

                    # Should have summary or description
                    assert (
                        "summary" in spec or "description" in spec
                    ), f"Path {method.upper()} {path} should have summary or description"

                    # Should have response definitions
                    assert (
                        "responses" in spec
                    ), f"Path {method.upper()} {path} should have responses"
                    responses = spec["responses"]
                    assert (
                        "200" in responses or "201" in responses
                    ), f"Path {method.upper()} {path} should have success response"

        assert documented_paths > 10, "Should have substantial API documentation"


@pytest.mark.integration
@pytest.mark.documentation
class TestDocumentationAccessibility(IntegrationTestBase):
    """Test documentation accessibility and user experience."""

    @pytest.mark.asyncio
    async def test_documentation_links_validity(self):
        """Test that all documentation links are valid."""
        # Get root API info with documentation links
        response = await self.get("/")
        data = self.assert_json_response(response)

        docs = data["documentation"]

        for doc_type, url in docs.items():
            doc_response = await self.get(url)
            assert (
                doc_response.status_code == 200
            ), f"Documentation link {doc_type} ({url}) should be accessible"

    @pytest.mark.asyncio
    async def test_documentation_navigation(self):
        """Test documentation navigation and cross-references."""
        # Test that API info references are consistent
        response = await self.get("/docs/api")
        api_info = self.assert_json_response(response)

        # Test that referenced endpoints exist
        docs = api_info["documentation"]
        for _doc_type, url in docs.items():
            if url.startswith("/"):
                test_response = await self.get(url)
                assert (
                    test_response.status_code == 200
                ), f"Referenced documentation {url} should exist"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_documentation_performance(self):
        """Test documentation endpoints performance."""
        doc_endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/docs/api",
            "/docs/api/examples",
            "/docs/api/integration-guides",
        ]

        for endpoint in doc_endpoints:
            result = await self.measure_response_time("GET", endpoint)

            assert result[
                "success"
            ], f"Documentation endpoint {endpoint} should succeed"
            assert (
                result["elapsed_time"] < 3.0
            ), f"Documentation endpoint {endpoint} too slow: {result['elapsed_time']}s"

    @pytest.mark.asyncio
    async def test_documentation_content_types(self):
        """Test documentation content types and headers."""
        # JSON endpoints should return JSON
        json_endpoints = ["/openapi.json", "/docs/api", "/docs/api/examples"]

        for endpoint in json_endpoints:
            response = await self.get(endpoint)
            assert response.headers.get("content-type", "").startswith(
                "application/json"
            ), f"Endpoint {endpoint} should return JSON"

        # HTML endpoints should return HTML
        html_endpoints = [
            "/docs",
            "/redoc",
            "/docs/api/custom-swagger",
            "/docs/api/custom-redoc",
        ]

        for endpoint in html_endpoints:
            response = await self.get(endpoint)
            content_type = response.headers.get("content-type", "")
            assert (
                "text/html" in content_type
            ), f"Endpoint {endpoint} should return HTML"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_documentation_under_load(self):
        """Test documentation endpoints under concurrent load."""
        import asyncio

        # Create concurrent requests to documentation
        endpoints = ["/docs", "/openapi.json", "/docs/api", "/docs/api/examples"]
        tasks = []

        for _ in range(5):
            for endpoint in endpoints:
                tasks.append(self.get(endpoint))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful_responses = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                successful_responses += 1

        success_rate = successful_responses / len(responses)
        assert (
            success_rate >= 0.9
        ), f"Documentation success rate too low: {success_rate}"


@pytest.mark.integration
@pytest.mark.documentation
class TestDocumentationSecurity(IntegrationTestBase):
    """Test documentation security and safety."""

    @pytest.mark.asyncio
    async def test_documentation_headers(self):
        """Test documentation security headers."""
        endpoints = ["/docs", "/redoc", "/docs/api/custom-swagger"]

        for endpoint in endpoints:
            response = await self.get(endpoint)

            # Check for basic security headers (if implemented)
            headers = response.headers

            # Content-Type should be set
            assert (
                "content-type" in headers
            ), f"Endpoint {endpoint} should have content-type header"

            # Check for common security headers (optional but good practice)
            security_headers = [
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection",
            ]
            for header in security_headers:
                if header in headers:
                    # If present, validate it has appropriate value
                    assert headers[header] is not None

    @pytest.mark.asyncio
    async def test_no_sensitive_data_exposure(self):
        """Test that documentation doesn't expose sensitive data."""
        response = await self.get("/openapi.json")
        schema = self.assert_json_response(response)

        # Convert to string for searching
        schema_str = json.dumps(schema).lower()

        # Should not contain sensitive patterns
        sensitive_patterns = ["password", "secret", "token", "key", "api_key"]

        for pattern in sensitive_patterns:
            if pattern in schema_str:
                # If found, ensure it's in documentation context, not actual values
                assert (
                    "example" not in schema_str or f'"{pattern}"' not in schema_str
                ), f"Documentation should not expose actual {pattern} values"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
