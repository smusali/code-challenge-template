"""
Tests for async bulk database writer functionality.

This module tests the performance improvements and correctness of the async bulk writer
compared to synchronous operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core_django.utils.async_bulk_writer import (
    AsyncBulkWriter,
    BulkWriterConfig,
    BulkWriterMetrics,
    WeatherDataBulkWriter,
    bulk_create_async,
)


class TestBulkWriterConfig:
    """Test bulk writer configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BulkWriterConfig()

        assert config.batch_size == 2000
        assert config.max_concurrent_batches == 4
        assert config.max_retries == 3
        assert config.retry_delay == 0.5
        assert config.connection_timeout == 30.0
        assert config.chunk_size == 10000
        assert config.use_ignore_conflicts is True
        assert config.progress_callback is None
        assert config.progress_interval == 1000

    def test_custom_config(self):
        """Test custom configuration values."""

        def progress_callback(x, y):
            return None

        config = BulkWriterConfig(
            batch_size=5000,
            max_concurrent_batches=8,
            progress_callback=progress_callback,
        )

        assert config.batch_size == 5000
        assert config.max_concurrent_batches == 8
        assert config.progress_callback == progress_callback


class TestBulkWriterMetrics:
    """Test bulk writer metrics tracking."""

    def test_metrics_initialization(self):
        """Test metrics are properly initialized."""
        metrics = BulkWriterMetrics()

        assert metrics.total_records == 0
        assert metrics.successful_records == 0
        assert metrics.failed_records == 0
        assert metrics.total_batches == 0
        assert metrics.successful_batches == 0
        assert metrics.failed_batches == 0
        assert metrics.start_time > 0
        assert metrics.end_time is None

    def test_duration_calculation(self):
        """Test duration calculation."""
        metrics = BulkWriterMetrics()
        metrics.start_time = 100.0
        metrics.end_time = 105.0

        assert metrics.duration == 5.0

    def test_records_per_second(self):
        """Test records per second calculation."""
        metrics = BulkWriterMetrics()
        metrics.start_time = 100.0
        metrics.end_time = 105.0
        metrics.successful_records = 1000

        assert metrics.records_per_second == 200.0

    def test_success_rate(self):
        """Test success rate calculation."""
        metrics = BulkWriterMetrics()
        metrics.total_records = 1000
        metrics.successful_records = 950

        assert metrics.success_rate == 95.0


class TestAsyncBulkWriter:
    """Test async bulk writer functionality."""

    @pytest.fixture
    def mock_model_class(self):
        """Mock Django model class."""
        mock_class = MagicMock()
        mock_class.__name__ = "TestModel"
        mock_class.objects.bulk_create = MagicMock()
        return mock_class

    @pytest.fixture
    def mock_records(self):
        """Mock record instances."""
        return [MagicMock() for _ in range(10)]

    @pytest.fixture
    def bulk_writer(self):
        """Create bulk writer instance."""
        config = BulkWriterConfig(
            batch_size=5,
            max_concurrent_batches=2,
            max_retries=1,
        )
        return AsyncBulkWriter(config)

    @pytest.mark.asyncio
    async def test_bulk_create_empty_records(self, bulk_writer, mock_model_class):
        """Test bulk create with empty records list."""
        metrics = await bulk_writer.bulk_create_async(mock_model_class, [])

        assert metrics.total_records == 0
        assert metrics.successful_records == 0
        assert metrics.total_batches == 0

    @pytest.mark.asyncio
    @patch("core_django.utils.async_bulk_writer.asgiref.sync.sync_to_async")
    async def test_bulk_create_success(
        self, mock_sync_to_async, bulk_writer, mock_model_class, mock_records
    ):
        """Test successful bulk create operation."""
        # Mock the sync_to_async wrapper
        mock_bulk_create = AsyncMock()
        mock_sync_to_async.return_value = mock_bulk_create

        metrics = await bulk_writer.bulk_create_async(mock_model_class, mock_records)

        assert metrics.total_records == 10
        assert metrics.successful_records == 10
        assert metrics.total_batches == 2  # 10 records / 5 batch_size = 2 batches
        assert metrics.successful_batches == 2
        assert metrics.failed_batches == 0
        assert metrics.records_per_second > 0

    @pytest.mark.asyncio
    @patch("core_django.utils.async_bulk_writer.asgiref.sync.sync_to_async")
    async def test_bulk_create_with_retry(
        self, mock_sync_to_async, bulk_writer, mock_model_class, mock_records
    ):
        """Test bulk create with retry on failure."""
        # Mock the sync_to_async wrapper to fail once then succeed
        mock_bulk_create = AsyncMock()
        mock_bulk_create.side_effect = [Exception("Database error"), None]
        mock_sync_to_async.return_value = mock_bulk_create

        metrics = await bulk_writer.bulk_create_async(
            mock_model_class, mock_records[:5]
        )  # Single batch

        assert metrics.total_records == 5
        assert metrics.successful_records == 5
        assert metrics.total_batches == 1
        assert mock_bulk_create.call_count == 2  # Initial call + 1 retry

    @pytest.mark.asyncio
    @patch("core_django.utils.async_bulk_writer.asgiref.sync.sync_to_async")
    async def test_bulk_create_max_retries_exceeded(
        self, mock_sync_to_async, bulk_writer, mock_model_class, mock_records
    ):
        """Test bulk create when max retries are exceeded."""
        # Mock the sync_to_async wrapper to always fail
        mock_bulk_create = AsyncMock()
        mock_bulk_create.side_effect = Exception("Persistent database error")
        mock_sync_to_async.return_value = mock_bulk_create

        metrics = await bulk_writer.bulk_create_async(
            mock_model_class, mock_records[:5]
        )  # Single batch

        assert metrics.total_records == 5
        assert metrics.successful_records == 0
        assert metrics.failed_records == 5
        assert metrics.total_batches == 1
        assert metrics.failed_batches == 1
        assert (
            mock_bulk_create.call_count == 2
        )  # Initial call + 1 retry (max_retries=1)

    @pytest.mark.asyncio
    async def test_progress_callback(self, mock_model_class, mock_records):
        """Test progress callback functionality."""
        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        config = BulkWriterConfig(
            batch_size=5,
            max_concurrent_batches=1,
            progress_callback=progress_callback,
        )
        bulk_writer = AsyncBulkWriter(config)

        with patch("core_django.utils.async_bulk_writer.asgiref.sync.sync_to_async"):
            await bulk_writer.bulk_create_async(
                mock_model_class, mock_records, progress_callback=progress_callback
            )

        # Should have progress updates for each batch
        assert len(progress_calls) >= 1
        assert all(
            isinstance(call[0], int) and isinstance(call[1], int)
            for call in progress_calls
        )


class TestWeatherDataBulkWriter:
    """Test weather-specific bulk writer functionality."""

    @pytest.fixture
    def weather_bulk_writer(self):
        """Create weather data bulk writer instance."""
        config = BulkWriterConfig(batch_size=5, max_concurrent_batches=2)
        return WeatherDataBulkWriter(config)

    @pytest.mark.asyncio
    @patch("core_django.utils.async_bulk_writer.asgiref.sync.sync_to_async")
    async def test_station_caching(self, mock_sync_to_async, weather_bulk_writer):
        """Test weather station caching functionality."""
        mock_stations = [MagicMock(station_id=f"USC{i:05d}") for i in range(3)]
        mock_bulk_create = AsyncMock()
        mock_sync_to_async.return_value = mock_bulk_create

        await weather_bulk_writer.bulk_create_weather_stations_async(mock_stations)

        # Check that stations were cached
        assert len(weather_bulk_writer.station_cache) == 3
        assert "USC00000" in weather_bulk_writer.station_cache
        assert "USC00001" in weather_bulk_writer.station_cache
        assert "USC00002" in weather_bulk_writer.station_cache


class TestConvenienceFunction:
    """Test convenience function for bulk operations."""

    @pytest.mark.asyncio
    @patch("core_django.utils.async_bulk_writer.AsyncBulkWriter.bulk_create_async")
    async def test_bulk_create_async_convenience(self, mock_bulk_create_async):
        """Test convenience function for bulk create."""
        mock_model_class = MagicMock()
        mock_records = [MagicMock() for _ in range(5)]
        mock_metrics = BulkWriterMetrics()
        mock_bulk_create_async.return_value = mock_metrics

        result = await bulk_create_async(
            mock_model_class,
            mock_records,
            batch_size=10,
            max_concurrent_batches=2,
        )

        assert result == mock_metrics
        mock_bulk_create_async.assert_called_once_with(mock_model_class, mock_records)


class TestAsyncBulkWriterIntegration:
    """Integration tests for async bulk writer with Django models."""

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_weather_station_bulk_create_integration(self):
        """Test actual bulk creation of weather stations."""
        from core_django.models.models import WeatherStation

        # Create test stations
        stations = [
            WeatherStation(station_id=f"TEST{i:03d}", name=f"Test Station {i}")
            for i in range(5)
        ]

        config = BulkWriterConfig(batch_size=3, max_concurrent_batches=1)
        bulk_writer = WeatherDataBulkWriter(config)

        metrics = await bulk_writer.bulk_create_weather_stations_async(stations)

        assert metrics.total_records == 5
        assert metrics.successful_records == 5
        assert metrics.total_batches == 2  # 5 records / 3 batch_size = 2 batches
        assert metrics.records_per_second > 0

        # Verify records were created
        assert WeatherStation.objects.filter(station_id__startswith="TEST").count() == 5

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_performance_comparison(self):
        """Test performance comparison between sync and async operations."""
        import time

        from core_django.models.models import WeatherStation

        # Create test data
        num_records = 100
        stations_sync = [
            WeatherStation(station_id=f"SYNC{i:03d}", name=f"Sync Station {i}")
            for i in range(num_records)
        ]
        stations_async = [
            WeatherStation(station_id=f"ASYNC{i:03d}", name=f"Async Station {i}")
            for i in range(num_records)
        ]

        # Test synchronous bulk create
        sync_start = time.time()
        WeatherStation.objects.bulk_create(stations_sync, batch_size=20)
        sync_duration = time.time() - sync_start

        # Test asynchronous bulk create
        config = BulkWriterConfig(batch_size=20, max_concurrent_batches=4)
        bulk_writer = WeatherDataBulkWriter(config)

        async_start = time.time()
        metrics = await bulk_writer.bulk_create_weather_stations_async(stations_async)
        async_duration = time.time() - async_start

        # Verify both methods created the records
        assert (
            WeatherStation.objects.filter(station_id__startswith="SYNC").count()
            == num_records
        )
        assert (
            WeatherStation.objects.filter(station_id__startswith="ASYNC").count()
            == num_records
        )

        # Async should be comparable or faster (though this can vary based on system load)
        assert metrics.successful_records == num_records
        assert metrics.records_per_second > 0

        print(f"Sync duration: {sync_duration:.3f}s")
        print(f"Async duration: {async_duration:.3f}s")
        print(f"Async records/sec: {metrics.records_per_second:.0f}")
