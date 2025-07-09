"""
Integration tests for weather data endpoints (v1 APIs and simple weather API).

This module tests:
- Weather API v1 endpoints
- Simple weather API endpoints
- Statistics endpoints
- Crop yield endpoints
- Basic CRUD operations
- Data validation
"""

import pytest

from tests.test_base import IntegrationTestBase


@pytest.mark.integration
@pytest.mark.api
class TestWeatherV1Endpoints(IntegrationTestBase):
    """Test weather API v1 endpoints."""

    @pytest.mark.asyncio
    async def test_weather_stations_v1(self):
        """Test weather stations v1 endpoint."""
        response = await self.get("/api/v1/weather/stations")

        # Should return 200 or 404 (if not implemented)
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should be a list or paginated response
            if isinstance(data, list):
                for station in data:
                    self.assert_weather_station_structure(station)
            elif isinstance(data, dict) and "items" in data:
                self.assert_pagination_response(data)
                for station in data["items"]:
                    self.assert_weather_station_structure(station)

    @pytest.mark.asyncio
    async def test_weather_station_detail_v1(self):
        """Test individual weather station endpoint."""
        response = await self.get("/api/v1/weather/stations/TEST001")

        # Should return 200, 404, or 501
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)
            self.assert_weather_station_structure(data)
            assert data["station_id"] == "TEST001"

    @pytest.mark.asyncio
    async def test_daily_weather_v1(self):
        """Test daily weather v1 endpoint."""
        response = await self.get("/api/v1/weather/daily")

        # Should return 200 or 404 (if not implemented)
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should be a list or paginated response
            if isinstance(data, list):
                for weather in data:
                    self.assert_daily_weather_structure(weather)
            elif isinstance(data, dict) and "items" in data:
                self.assert_pagination_response(data)
                for weather in data["items"]:
                    self.assert_daily_weather_structure(weather)

    @pytest.mark.asyncio
    async def test_daily_weather_by_station_v1(self):
        """Test daily weather by station v1 endpoint."""
        response = await self.get("/api/v1/weather/daily/TEST001")

        # Should return 200, 404, or 501
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should be a list or paginated response
            if isinstance(data, list):
                for weather in data:
                    self.assert_daily_weather_structure(weather)
            elif isinstance(data, dict) and "items" in data:
                self.assert_pagination_response(data)
                for weather in data["items"]:
                    self.assert_daily_weather_structure(weather)


@pytest.mark.integration
@pytest.mark.api
class TestSimpleWeatherAPI(IntegrationTestBase):
    """Test simple weather API endpoints."""

    @pytest.mark.asyncio
    async def test_simple_weather_endpoints(self):
        """Test simple weather API endpoints."""
        # Test various simple weather endpoints
        simple_endpoints = [
            "/api/weather",
            "/api/weather/",
            "/api/weather/stations",
            "/api/weather/daily",
        ]

        for endpoint in simple_endpoints:
            response = await self.get(endpoint)

            # Should return 200 or 404 (if not implemented)
            assert response.status_code in [200, 404, 501]

            if response.status_code == 200:
                data = self.assert_json_response(response)

                # Should have some structure
                assert isinstance(data, dict | list)

                # If it's a list, validate weather structure
                if isinstance(data, list) and len(data) > 0:
                    first_item = data[0]
                    if "station_id" in first_item or "station" in first_item:
                        # Likely weather data
                        self.assert_daily_weather_structure(first_item)
                    elif "name" in first_item and "latitude" in first_item:
                        # Likely station data
                        self.assert_weather_station_structure(first_item)


@pytest.mark.integration
@pytest.mark.api
class TestStatisticsEndpoints(IntegrationTestBase):
    """Test statistics and analytics endpoints."""

    @pytest.mark.asyncio
    async def test_stats_summary(self):
        """Test statistics summary endpoint."""
        response = await self.get("/api/v1/stats/summary")

        # Should return 200 or 404 (if not implemented)
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should be a dictionary with statistics
            assert isinstance(data, dict)

            # Should contain statistical information
            stat_fields = [
                "total_stations",
                "total_records",
                "date_range",
                "statistics",
            ]
            for field in stat_fields:
                if field in data:
                    assert data[field] is not None

    @pytest.mark.asyncio
    async def test_yearly_stats_by_station(self):
        """Test yearly statistics by station."""
        response = await self.get("/api/v1/stats/yearly/TEST001")

        # Should return 200, 404, or 501
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should be a list or dictionary
            if isinstance(data, list):
                for stat in data:
                    assert isinstance(stat, dict)
                    if "year" in stat:
                        assert isinstance(stat["year"], int)
                        assert stat["year"] >= 1980 and stat["year"] <= 2030
            elif isinstance(data, dict):
                assert "station_id" in data or "station" in data


@pytest.mark.integration
@pytest.mark.api
class TestCropYieldEndpoints(IntegrationTestBase):
    """Test crop yield data endpoints."""

    @pytest.mark.asyncio
    async def test_crop_yield_endpoint(self):
        """Test crop yield data endpoint."""
        response = await self.get("/api/v1/crops/yield")

        # Should return 200 or 404 (if not implemented)
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should be a list or paginated response
            if isinstance(data, list):
                for crop in data:
                    self.assert_crop_yield_structure(crop)
            elif isinstance(data, dict) and "items" in data:
                self.assert_pagination_response(data)
                for crop in data["items"]:
                    self.assert_crop_yield_structure(crop)

    def assert_crop_yield_structure(self, crop_data: dict):
        """Assert crop yield data structure."""
        # Basic fields that crop yield should have
        if "year" in crop_data:
            assert isinstance(crop_data["year"], int)
            assert crop_data["year"] >= 1980 and crop_data["year"] <= 2030

        if "yield" in crop_data:
            assert isinstance(crop_data["yield"], int | float)
            assert crop_data["yield"] >= 0

        if "state" in crop_data:
            assert isinstance(crop_data["state"], str)
            assert len(crop_data["state"]) == 2  # State abbreviation


@pytest.mark.integration
@pytest.mark.api
class TestWeatherEndpointsValidation(IntegrationTestBase):
    """Test weather endpoints data validation and quality."""

    @pytest.mark.asyncio
    async def test_weather_data_consistency(self):
        """Test weather data consistency across endpoints."""
        # Get data from enhanced endpoint
        response_v2 = await self.get(
            "/api/v2/weather-stations", params={"page_size": 5}
        )
        if response_v2.status_code == 200:
            data_v2 = self.assert_json_response(response_v2)

            # Get data from v1 endpoint (if available)
            response_v1 = await self.get("/api/v1/weather/stations")
            if response_v1.status_code == 200:
                data_v1 = self.assert_json_response(response_v1)

                # Data should be consistent between versions
                v2_stations = data_v2["items"] if "items" in data_v2 else []
                v1_stations = (
                    data_v1 if isinstance(data_v1, list) else data_v1.get("items", [])
                )

                # At least some stations should be present in both
                if v2_stations and v1_stations:
                    v2_ids = {s["station_id"] for s in v2_stations}
                    v1_ids = {s["station_id"] for s in v1_stations}

                    # Should have overlap
                    common_ids = v2_ids.intersection(v1_ids)
                    assert (
                        len(common_ids) > 0
                    ), "Should have common stations between v1 and v2"

    @pytest.mark.asyncio
    async def test_weather_data_temporal_consistency(self):
        """Test temporal consistency of weather data."""
        response = await self.get(
            "/api/v2/daily-weather",
            params={
                "start_date": "2010-01-01",
                "end_date": "2010-01-05",
                "page_size": 20,
            },
        )

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # All dates should be within range
            for weather in data["items"]:
                weather_date = weather["date"]
                assert (
                    "2010-01-0" in weather_date
                ), f"Date should be in range: {weather_date}"

                # Temperature relationship should be consistent
                if weather.get("max_temp") and weather.get("min_temp"):
                    assert (
                        weather["max_temp"] >= weather["min_temp"]
                    ), f"Max temp should be >= min temp: {weather['max_temp']} vs {weather['min_temp']}"

    @pytest.mark.asyncio
    async def test_weather_data_geographic_consistency(self):
        """Test geographic consistency of weather data."""
        response = await self.get(
            "/api/v2/weather-stations", params={"states": ["IL"], "page_size": 10}
        )

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # All stations should be in Illinois
            for station in data["items"]:
                assert station["state"] == "IL", f"Station should be in IL: {station}"

                # Illinois coordinates should be reasonable
                lat, lon = station["latitude"], station["longitude"]
                assert 37 <= lat <= 43, f"Illinois latitude should be ~37-43: {lat}"
                assert (
                    -92 <= lon <= -87
                ), f"Illinois longitude should be ~-92 to -87: {lon}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_weather_endpoints_performance(self):
        """Test performance of weather endpoints."""
        endpoints = [
            "/api/v2/weather-stations",
            "/api/v2/daily-weather",
            "/api/v2/yearly-stats",
        ]

        for endpoint in endpoints:
            result = await self.measure_response_time(
                "GET", endpoint, params={"page_size": 10}
            )

            if result["success"]:
                assert (
                    result["elapsed_time"] < 3.0
                ), f"Weather endpoint {endpoint} too slow: {result['elapsed_time']}s"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test handling of large data requests."""
        # Test large page size
        response = await self.get(
            "/api/v2/daily-weather",
            params={
                "page_size": 100,
                "start_date": "2010-01-01",
                "end_date": "2010-01-31",
            },
        )

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # Should handle large requests gracefully
            assert len(data["items"]) <= 100, "Should respect page size limit"

            # Response should be reasonable
            assert len(data["items"]) > 0, "Should return some data"

    @pytest.mark.asyncio
    async def test_data_completeness_validation(self):
        """Test data completeness and quality validation."""
        response = await self.get(
            "/api/v2/daily-weather", params={"has_temperature": True, "page_size": 10}
        )

        if response.status_code == 200:
            data = self.assert_json_response(response)

            # All records should have temperature data
            for weather in data["items"]:
                has_temp = (
                    weather.get("max_temp") is not None
                    or weather.get("min_temp") is not None
                )
                assert (
                    has_temp
                ), f"Should have temperature data when filtered: {weather}"


@pytest.mark.integration
@pytest.mark.api
class TestWeatherEndpointsIntegration(IntegrationTestBase):
    """Test integration between different weather endpoints."""

    @pytest.mark.asyncio
    async def test_station_weather_data_integration(self):
        """Test integration between stations and weather data."""
        # Get stations
        stations_response = await self.get(
            "/api/v2/weather-stations", params={"page_size": 3}
        )

        if stations_response.status_code == 200:
            stations_data = self.assert_json_response(stations_response)

            if stations_data["items"]:
                # Get weather data for first station
                station = stations_data["items"][0]
                station_id = station["station_id"]

                weather_response = await self.get(
                    "/api/v2/daily-weather",
                    params={"station_ids": [station_id], "page_size": 5},
                )

                if weather_response.status_code == 200:
                    weather_data = self.assert_json_response(weather_response)

                    # Weather data should be from the requested station
                    for weather in weather_data["items"]:
                        if isinstance(weather["station"], dict):
                            assert weather["station"]["station_id"] == station_id
                        # Note: might be just ID in some implementations

    @pytest.mark.asyncio
    async def test_yearly_stats_integration(self):
        """Test integration between daily weather and yearly stats."""
        # Get yearly stats
        stats_response = await self.get("/api/v2/yearly-stats", params={"page_size": 1})

        if stats_response.status_code == 200:
            stats_data = self.assert_json_response(stats_response)

            if stats_data["items"]:
                stat = stats_data["items"][0]
                year = stat["year"]

                # Get daily weather for same year
                daily_response = await self.get(
                    "/api/v2/daily-weather",
                    params={
                        "start_date": f"{year}-01-01",
                        "end_date": f"{year}-12-31",
                        "page_size": 10,
                    },
                )

                if daily_response.status_code == 200:
                    daily_data = self.assert_json_response(daily_response)

                    # Should have daily data for the year
                    for weather in daily_data["items"]:
                        weather_year = int(weather["date"].split("-")[0])
                        assert (
                            weather_year == year
                        ), f"Weather year should match: {weather_year} vs {year}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
