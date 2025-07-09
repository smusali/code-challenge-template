"""
Async Bulk Database Writer for High-Performance Data Ingestion

This module provides optimized async bulk database operations for weather data ingestion,
significantly improving performance over synchronous operations.

Features:
- Async database operations with connection pooling
- Concurrent batch processing
- Memory-efficient streaming operations
- Progress tracking and performance metrics
- Error handling with retry logic
- Configurable batch sizes and concurrency levels
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, TypeVar

import asgiref.sync
from django.db import transaction
from django.db.models import Model

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Model)


@dataclass
class BulkWriterConfig:
    """Configuration for async bulk writer operations."""

    # Batch processing settings
    batch_size: int = 2000
    max_concurrent_batches: int = 4

    # Connection and retry settings
    max_retries: int = 3
    retry_delay: float = 0.5
    connection_timeout: float = 30.0

    # Performance settings
    chunk_size: int = 10000
    use_ignore_conflicts: bool = True

    # Progress tracking
    progress_callback: Callable[[int, int], None] | None = None
    progress_interval: int = 1000


@dataclass
class BulkWriterMetrics:
    """Performance metrics for bulk write operations."""

    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    total_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0

    @property
    def duration(self) -> float:
        """Total operation duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def records_per_second(self) -> float:
        """Records processed per second."""
        duration = self.duration
        return self.successful_records / duration if duration > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        total = self.total_records
        return (self.successful_records / total * 100) if total > 0 else 0.0


class AsyncBulkWriter:
    """High-performance async bulk database writer."""

    def __init__(self, config: BulkWriterConfig = None):
        self.config = config or BulkWriterConfig()
        self.metrics = BulkWriterMetrics()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)

    async def bulk_create_async(
        self,
        model_class: type[T],
        records: list[T],
        batch_size: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BulkWriterMetrics:
        """
        Async bulk create operation with optimized performance.

        Args:
            model_class: Django model class
            records: List of model instances to create
            batch_size: Override default batch size
            progress_callback: Progress callback function

        Returns:
            BulkWriterMetrics with operation statistics
        """
        if not records:
            return self.metrics

        effective_batch_size = batch_size or self.config.batch_size
        callback = progress_callback or self.config.progress_callback

        logger.info(
            f"Starting async bulk create for {len(records):,} {model_class.__name__} records"
        )

        self.metrics = BulkWriterMetrics()
        self.metrics.total_records = len(records)

        # Process records in batches concurrently
        batches = [
            records[i : i + effective_batch_size]
            for i in range(0, len(records), effective_batch_size)
        ]

        self.metrics.total_batches = len(batches)

        # Create async tasks for concurrent processing
        tasks = [
            self._process_batch_async(model_class, batch_idx, batch, callback)
            for batch_idx, batch in enumerate(batches)
        ]

        # Execute batches concurrently with semaphore limiting
        await asyncio.gather(*tasks, return_exceptions=True)

        self.metrics.end_time = time.time()

        logger.info(
            f"Async bulk create completed: {self.metrics.successful_records:,}/{self.metrics.total_records:,} "
            f"records in {self.metrics.duration:.2f}s "
            f"({self.metrics.records_per_second:.0f} records/sec, "
            f"{self.metrics.success_rate:.1f}% success rate)"
        )

        return self.metrics

    async def _process_batch_async(
        self,
        model_class: type[T],
        batch_idx: int,
        batch: list[T],
        progress_callback: Callable[[int, int], None] | None = None,
    ):
        """Process a single batch asynchronously with retry logic."""
        async with self._semaphore:
            for attempt in range(self.config.max_retries + 1):
                try:
                    await self._execute_batch_create(model_class, batch)
                    self.metrics.successful_batches += 1
                    self.metrics.successful_records += len(batch)

                    if progress_callback:
                        progress_callback(
                            self.metrics.successful_records, self.metrics.total_records
                        )

                    logger.debug(
                        f"Batch {batch_idx + 1} completed successfully ({len(batch)} records)"
                    )
                    return

                except Exception as e:
                    if attempt < self.config.max_retries:
                        logger.warning(
                            f"Batch {batch_idx + 1} failed (attempt {attempt + 1}), retrying: {e}"
                        )
                        await asyncio.sleep(self.config.retry_delay * (2**attempt))
                    else:
                        logger.error(
                            f"Batch {batch_idx + 1} failed after {self.config.max_retries} retries: {e}"
                        )
                        self.metrics.failed_batches += 1
                        self.metrics.failed_records += len(batch)

    async def _execute_batch_create(self, model_class: type[T], batch: list[T]):
        """Execute the actual database bulk create operation."""
        # Use sync_to_async to make Django ORM operations async-compatible
        bulk_create_sync = asgiref.sync.sync_to_async(
            lambda: model_class.objects.bulk_create(
                batch,
                batch_size=len(batch),
                ignore_conflicts=self.config.use_ignore_conflicts,
            ),
            thread_sensitive=True,
        )

        await bulk_create_sync()

    async def stream_bulk_create_async(
        self,
        model_class: type[T],
        record_iterator: AsyncIterator[T],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BulkWriterMetrics:
        """
        Stream-based async bulk create for memory-efficient processing of large datasets.

        Args:
            model_class: Django model class
            record_iterator: Async iterator yielding model instances
            progress_callback: Progress callback function

        Returns:
            BulkWriterMetrics with operation statistics
        """
        logger.info(f"Starting stream bulk create for {model_class.__name__}")

        self.metrics = BulkWriterMetrics()
        current_batch = []

        async for record in record_iterator:
            current_batch.append(record)

            if len(current_batch) >= self.config.batch_size:
                await self._process_batch_async(
                    model_class,
                    self.metrics.total_batches,
                    current_batch,
                    progress_callback,
                )
                self.metrics.total_batches += 1
                current_batch = []

        # Process remaining records
        if current_batch:
            await self._process_batch_async(
                model_class,
                self.metrics.total_batches,
                current_batch,
                progress_callback,
            )
            self.metrics.total_batches += 1

        self.metrics.end_time = time.time()

        logger.info(
            f"Stream bulk create completed: {self.metrics.successful_records:,} records "
            f"in {self.metrics.duration:.2f}s ({self.metrics.records_per_second:.0f} records/sec)"
        )

        return self.metrics

    @asynccontextmanager
    async def transaction_async(self):
        """Async context manager for database transactions."""
        # Use sync_to_async for Django transaction management
        enter_transaction = asgiref.sync.sync_to_async(
            transaction.atomic().__enter__, thread_sensitive=True
        )
        exit_transaction = asgiref.sync.sync_to_async(
            transaction.atomic().__exit__, thread_sensitive=True
        )

        trans = await enter_transaction()
        try:
            yield trans
        except Exception as e:
            await exit_transaction(type(e), e, e.__traceback__)
            raise
        else:
            await exit_transaction(None, None, None)


class WeatherDataBulkWriter(AsyncBulkWriter):
    """Specialized async bulk writer for weather data with domain-specific optimizations."""

    def __init__(self, config: BulkWriterConfig = None):
        super().__init__(config)
        self.station_cache = {}

    async def bulk_create_weather_stations_async(
        self,
        stations: list[Any],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BulkWriterMetrics:
        """Optimized bulk creation of weather stations with caching."""
        from core_django.models.models import WeatherStation

        # Remove duplicates and cache for later use
        unique_stations = {}
        for station in stations:
            if station.station_id not in unique_stations:
                unique_stations[station.station_id] = station
                self.station_cache[station.station_id] = station

        return await self.bulk_create_async(
            WeatherStation,
            list(unique_stations.values()),
            progress_callback=progress_callback,
        )

    async def bulk_create_daily_weather_async(
        self,
        daily_records: list[Any],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BulkWriterMetrics:
        """Optimized bulk creation of daily weather records."""
        from core_django.models.models import DailyWeather

        return await self.bulk_create_async(
            DailyWeather,
            daily_records,
            progress_callback=progress_callback,
        )

    async def bulk_create_yearly_stats_async(
        self,
        yearly_stats: list[Any],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BulkWriterMetrics:
        """Optimized bulk creation of yearly weather statistics."""
        from core_django.models.models import YearlyWeatherStats

        return await self.bulk_create_async(
            YearlyWeatherStats,
            yearly_stats,
            progress_callback=progress_callback,
        )


# Convenience function for simple async bulk operations
async def bulk_create_async(
    model_class: type[T],
    records: list[T],
    batch_size: int = 2000,
    max_concurrent_batches: int = 4,
    progress_callback: Callable[[int, int], None] | None = None,
) -> BulkWriterMetrics:
    """
    Convenience function for async bulk create operations.

    Args:
        model_class: Django model class
        records: List of model instances to create
        batch_size: Number of records per batch
        max_concurrent_batches: Maximum concurrent batch operations
        progress_callback: Progress callback function

    Returns:
        BulkWriterMetrics with operation statistics
    """
    config = BulkWriterConfig(
        batch_size=batch_size,
        max_concurrent_batches=max_concurrent_batches,
        progress_callback=progress_callback,
    )

    writer = AsyncBulkWriter(config)
    return await writer.bulk_create_async(model_class, records)
