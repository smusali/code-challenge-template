"""
Integration tests for enhanced API v2 endpoints with filtering, pagination, and sorting.

This module tests:
- Weather stations endpoint with filtering and search
- Daily weather endpoint with comprehensive filtering
- Yearly statistics endpoint with advanced queries
- Pagination functionality (page-based)
- Sorting capabilities
- Filter combinations and edge cases
- Performance and response validation
"""

import pytest

from tests.test_base import IntegrationTestBase


@pytest.mark.integration
@pytest.mark.api
class TestEnhancedWeatherStations(IntegrationTestBase):
    """Test enhanced weather stations endpoint (/api/v2/weather-stations)."""

    @pytest.mark.asyncio
    async def test_weather_stations_basic(self):
        """Test basic weather stations retrieval."""
        response = await self.get("/api/v2/weather-stations")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate pagination response structure
        self.assert_pagination_response(data)

        # Validate weather station items
        for station in data["items"]:
            self.assert_weather_station_structure(station)

    @pytest.mark.asyncio
    async def test_weather_stations_pagination(self):
        """Test weather stations pagination."""
        # Test first page
        response = await self.get(
            "/api/v2/weather-stations", params={"page": 1, "page_size": 2}
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)
        pagination_info = self.extract_pagination_info(data)

        assert pagination_info["current_page"] == 1
        assert pagination_info["page_size"] == 2
        assert pagination_info["items_count"] <= 2

        # If there are more pages, test second page
        if pagination_info["has_next"]:
            response = await self.get(
                "/api/v2/weather-stations", params={"page": 2, "page_size": 2}
            )
            data = self.assert_json_response(response)

            pagination_info = self.extract_pagination_info(data)
            assert pagination_info["current_page"] == 2
            assert pagination_info["has_previous"]

    @pytest.mark.asyncio
    async def test_weather_stations_search(self):
        """Test weather stations text search functionality."""
        # Search for Chicago
        response = await self.get(
            "/api/v2/weather-stations", params={"search": "Chicago"}
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # All results should contain "Chicago" in name or station_id
        for station in data["items"]:
            station_text = f"{station['name']} {station['station_id']}".lower()
            assert (
                "chicago" in station_text
            ), f"Search result should contain 'Chicago': {station['name']}"

    @pytest.mark.asyncio
    async def test_weather_stations_state_filter(self):
        """Test weather stations state filtering."""
        # Filter by Illinois
        response = await self.get("/api/v2/weather-stations", params={"states": ["IL"]})
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # All results should be in Illinois
        for station in data["items"]:
            assert station["state"] == "IL", f"Station should be in IL: {station}"

    @pytest.mark.asyncio
    async def test_weather_stations_multiple_states(self):
        """Test weather stations filtering with multiple states."""
        response = await self.get(
            "/api/v2/weather-stations", params={"states": ["IL", "IA"]}
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # All results should be in IL or IA
        for station in data["items"]:
            assert station["state"] in [
                "IL",
                "IA",
            ], f"Station should be in IL or IA: {station}"

    @pytest.mark.asyncio
    async def test_weather_stations_sorting(self):
        """Test weather stations sorting."""
        # Sort by name ascending
        response = await self.get(
            "/api/v2/weather-stations",
            params={"sort_by": "name", "sort_order": "asc", "page_size": 10},
        )
        data = self.assert_json_response(response)

        # Verify sorting
        names = [station["name"] for station in data["items"]]
        assert names == sorted(names), "Stations should be sorted by name ascending"

        # Sort by name descending
        response = await self.get(
            "/api/v2/weather-stations",
            params={"sort_by": "name", "sort_order": "desc", "page_size": 10},
        )
        data = self.assert_json_response(response)

        names = [station["name"] for station in data["items"]]
        assert names == sorted(
            names, reverse=True
        ), "Stations should be sorted by name descending"

    @pytest.mark.asyncio
    async def test_weather_stations_combined_filters(self):
        """Test weather stations with combined filters."""
        response = await self.get(
            "/api/v2/weather-stations",
            params={
                "search": "Test",
                "states": ["IL"],
                "sort_by": "name",
                "sort_order": "asc",
                "page": 1,
                "page_size": 5,
            },
        )

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)
        self.assert_pagination_response(data)

        # Validate that filters are applied
        for station in data["items"]:
            assert station["state"] == "IL"
            assert (
                "test" in station["name"].lower()
                or "test" in station["station_id"].lower()
            )

    @pytest.mark.asyncio
    async def test_weather_stations_invalid_params(self):
        """Test weather stations with invalid parameters."""
        # Invalid page number
        response = await self.get("/api/v2/weather-stations", params={"page": 0})
        assert response.status_code in [400, 422], "Invalid page should return error"

        # Invalid page size
        response = await self.get("/api/v2/weather-stations", params={"page_size": -1})
        assert response.status_code in [
            400,
            422,
        ], "Invalid page_size should return error"

        # Invalid sort order
        response = await self.get(
            "/api/v2/weather-stations", params={"sort_order": "invalid"}
        )
        assert response.status_code in [
            400,
            422,
        ], "Invalid sort_order should return error"


@pytest.mark.integration
@pytest.mark.api
class TestEnhancedDailyWeather(IntegrationTestBase):
    """Test enhanced daily weather endpoint (/api/v2/daily-weather)."""

    @pytest.mark.asyncio
    async def test_daily_weather_basic(self):
        """Test basic daily weather retrieval."""
        response = await self.get("/api/v2/daily-weather")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate pagination response structure
        self.assert_pagination_response(data)

        # Validate daily weather items
        for weather in data["items"]:
            self.assert_daily_weather_structure(weather)

    @pytest.mark.asyncio
    async def test_daily_weather_date_filtering(self):
        """Test daily weather date range filtering."""
        response = await self.get(
            "/api/v2/daily-weather",
            params={
                "start_date": "2010-01-01",
                "end_date": "2010-01-31",
                "page_size": 20,
            },
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # All records should be within date range
        for weather in data["items"]:
            weather_date = weather["date"]
            assert (
                "2010-01" in weather_date
            ), f"Date should be in January 2010: {weather_date}"

    @pytest.mark.asyncio
    async def test_daily_weather_temperature_filtering(self):
        """Test daily weather temperature filtering."""
        response = await self.get(
            "/api/v2/daily-weather",
            params={"min_temp": 0, "max_temp": 30, "page_size": 10},  # 0°C  # 30°C
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # Validate temperature ranges
        for weather in data["items"]:
            if weather.get("max_temp") is not None:
                max_temp_celsius = weather["max_temp"] / 10.0
                assert (
                    0 <= max_temp_celsius <= 30
                ), f"Max temp should be 0-30°C: {max_temp_celsius}"

    @pytest.mark.asyncio
    async def test_daily_weather_precipitation_filtering(self):
        """Test daily weather precipitation filtering."""
        response = await self.get(
            "/api/v2/daily-weather",
            params={
                "min_precipitation": 0,  # 0mm
                "max_precipitation": 50,  # 50mm
                "page_size": 10,
            },
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # Validate precipitation ranges
        for weather in data["items"]:
            if weather.get("precipitation") is not None:
                precip_mm = weather["precipitation"] / 10.0
                assert (
                    0 <= precip_mm <= 50
                ), f"Precipitation should be 0-50mm: {precip_mm}"

    @pytest.mark.asyncio
    async def test_daily_weather_state_filtering(self):
        """Test daily weather state filtering."""
        response = await self.get(
            "/api/v2/daily-weather", params={"states": ["IL"], "page_size": 10}
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # All records should be from Illinois stations
        for weather in data["items"]:
            if isinstance(weather["station"], dict):
                assert weather["station"]["state"] == "IL"

    @pytest.mark.asyncio
    async def test_daily_weather_sorting(self):
        """Test daily weather sorting."""
        response = await self.get(
            "/api/v2/daily-weather",
            params={"sort_by": "date", "sort_order": "desc", "page_size": 5},
        )
        data = self.assert_json_response(response)

        # Verify date sorting (descending)
        dates = [weather["date"] for weather in data["items"]]
        assert dates == sorted(
            dates, reverse=True
        ), "Weather should be sorted by date descending"

    @pytest.mark.asyncio
    async def test_daily_weather_data_availability_filtering(self):
        """Test filtering by data availability."""
        response = await self.get(
            "/api/v2/daily-weather", params={"has_temperature": True, "page_size": 10}
        )
        data = self.assert_json_response(response)

        # All records should have temperature data
        for weather in data["items"]:
            assert (
                weather.get("max_temp") is not None
                or weather.get("min_temp") is not None
            )

    @pytest.mark.asyncio
    async def test_daily_weather_comprehensive_filtering(self):
        """Test daily weather with comprehensive filtering."""
        response = await self.get(
            "/api/v2/daily-weather",
            params={
                "start_date": "2010-01-01",
                "end_date": "2010-01-31",
                "states": ["IL", "IA"],
                "min_temp": -10,
                "max_temp": 40,
                "has_temperature": True,
                "sort_by": "date",
                "sort_order": "asc",
                "page": 1,
                "page_size": 20,
            },
        )

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)
        self.assert_pagination_response(data)

        # Validate all filters are applied
        for weather in data["items"]:
            # Date range
            assert "2010-01" in weather["date"]

            # Temperature data availability
            assert (
                weather.get("max_temp") is not None
                or weather.get("min_temp") is not None
            )

            # State filter (if station data is included)
            if isinstance(weather["station"], dict):
                assert weather["station"]["state"] in ["IL", "IA"]


@pytest.mark.integration
@pytest.mark.api
class TestEnhancedYearlyStats(IntegrationTestBase):
    """Test enhanced yearly statistics endpoint (/api/v2/yearly-stats)."""

    @pytest.mark.asyncio
    async def test_yearly_stats_basic(self):
        """Test basic yearly statistics retrieval."""
        response = await self.get("/api/v2/yearly-stats")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate pagination response structure
        self.assert_pagination_response(data)

        # Validate yearly stats items
        for stats in data["items"]:
            required_fields = [
                "id",
                "station",
                "year",
                "avg_max_temp",
                "avg_min_temp",
                "total_precipitation",
            ]
            self.assert_required_fields(stats, required_fields)

            # Validate data types
            assert isinstance(stats["id"], int)
            assert isinstance(stats["year"], int)
            assert (
                stats["year"] >= 1980 and stats["year"] <= 2030
            )  # Reasonable year range

    @pytest.mark.asyncio
    async def test_yearly_stats_year_filtering(self):
        """Test yearly statistics year filtering."""
        response = await self.get(
            "/api/v2/yearly-stats", params={"start_year": 2005, "end_year": 2015}
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # All records should be within year range
        for stats in data["items"]:
            assert (
                2005 <= stats["year"] <= 2015
            ), f"Year should be 2005-2015: {stats['year']}"

    @pytest.mark.asyncio
    async def test_yearly_stats_temperature_filtering(self):
        """Test yearly statistics temperature filtering."""
        response = await self.get(
            "/api/v2/yearly-stats",
            params={
                "min_avg_temp": 10,  # 10°C
                "max_avg_temp": 25,  # 25°C
            },
        )
        data = self.assert_json_response(response)

        self.assert_pagination_response(data)

        # Validate temperature ranges
        for stats in data["items"]:
            if stats.get("avg_max_temp") is not None:
                avg_temp_celsius = stats["avg_max_temp"] / 10.0
                assert (
                    10 <= avg_temp_celsius <= 25
                ), f"Avg temp should be 10-25°C: {avg_temp_celsius}"

    @pytest.mark.asyncio
    async def test_yearly_stats_sorting(self):
        """Test yearly statistics sorting."""
        response = await self.get(
            "/api/v2/yearly-stats",
            params={"sort_by": "year", "sort_order": "desc", "page_size": 10},
        )
        data = self.assert_json_response(response)

        # Verify year sorting (descending)
        years = [stats["year"] for stats in data["items"]]
        assert years == sorted(
            years, reverse=True
        ), "Stats should be sorted by year descending"

    @pytest.mark.asyncio
    async def test_yearly_stats_data_completeness(self):
        """Test yearly statistics data completeness filtering."""
        response = await self.get(
            "/api/v2/yearly-stats",
            params={"min_data_completeness": 80, "page_size": 10},  # 80% completeness
        )
        data = self.assert_json_response(response)

        # Validate data completeness
        for stats in data["items"]:
            if stats.get("records_with_temp") is not None:
                # Approximate completeness check (365 days in a year)
                completeness = (stats["records_with_temp"] / 365.0) * 100
                assert (
                    completeness >= 75
                ), f"Data completeness should be high: {completeness}%"


@pytest.mark.integration
@pytest.mark.api
class TestEnhancedUtilityEndpoints(IntegrationTestBase):
    """Test enhanced utility endpoints (sort-info, filter-info)."""

    @pytest.mark.asyncio
    async def test_sort_info_endpoint(self):
        """Test sort information endpoint."""
        model_types = ["weather_station", "daily_weather", "yearly_stats"]

        for model_type in model_types:
            response = await self.get(f"/api/v2/sort-info/{model_type}")

            self.assert_status_code(response, 200)
            data = self.assert_json_response(response)

            # Validate response structure
            required_fields = ["model_type", "available_fields", "usage_examples"]
            self.assert_required_fields(data, required_fields)

            assert data["model_type"] == model_type
            assert isinstance(data["available_fields"], list)
            assert len(data["available_fields"]) > 0
            assert isinstance(data["usage_examples"], dict)

    @pytest.mark.asyncio
    async def test_sort_info_invalid_model(self):
        """Test sort info with invalid model type."""
        response = await self.get("/api/v2/sort-info/invalid_model")

        self.assert_status_code(response, 400)
        data = self.assert_json_response(response)
        assert "error" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_filter_info_endpoint(self):
        """Test filter information endpoint."""
        response = await self.get("/api/v2/filter-info")

        self.assert_status_code(response, 200)
        data = self.assert_json_response(response)

        # Validate response structure
        required_fields = ["available_filters", "combination_examples"]
        self.assert_required_fields(data, required_fields)

        # Validate available filters
        filters = data["available_filters"]
        expected_filters = [
            "date_range",
            "temperature_range",
            "precipitation_range",
            "location",
        ]

        for filter_type in expected_filters:
            assert filter_type in filters, f"Should have {filter_type} filter info"
            filter_info = filters[filter_type]
            assert "description" in filter_info
            assert "parameters" in filter_info
            assert isinstance(filter_info["parameters"], list)


@pytest.mark.integration
@pytest.mark.performance
class TestEnhancedEndpointsPerformance(IntegrationTestBase):
    """Test performance of enhanced endpoints."""

    @pytest.mark.asyncio
    async def test_pagination_performance(self):
        """Test pagination performance across endpoints."""
        endpoints = [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
        ]

        for endpoint in endpoints:
            # Test multiple page sizes
            for page_size in [10, 50, 100]:
                result = await self.measure_response_time(
                    "GET", endpoint, params={"page": 1, "page_size": page_size}
                )

                assert result["success"], f"Request to {endpoint} should succeed"
                assert result["elapsed_time"] < 3.0, (
                    f"Response time for {endpoint} (page_size={page_size}) too slow: "
                    f"{result['elapsed_time']}s"
                )

    @pytest.mark.asyncio
    async def test_filtering_performance(self):
        """Test filtering performance."""
        # Test complex filtering
        result = await self.measure_response_time(
            "GET",
            "/api/v2/daily-weather",
            params={
                "start_date": "2010-01-01",
                "end_date": "2010-12-31",
                "states": ["IL", "IA"],
                "min_temp": -10,
                "max_temp": 40,
                "has_temperature": True,
                "page_size": 50,
            },
        )

        assert result["success"], "Complex filtering should succeed"
        assert (
            result["elapsed_time"] < 5.0
        ), f"Complex filtering too slow: {result['elapsed_time']}s"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_enhanced_requests(self):
        """Test concurrent requests to enhanced endpoints."""
        import asyncio

        # Create multiple concurrent requests
        tasks = []
        endpoints = [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
        ]

        for endpoint in endpoints:
            for _ in range(3):
                tasks.append(self.get(endpoint, params={"page_size": 10}))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful_responses = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                successful_responses += 1

        success_rate = successful_responses / len(responses)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
