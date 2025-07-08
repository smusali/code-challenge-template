"""
Unit tests for checksum functionality in weather data ingestion.

Tests the checksum and duplicate detection functionality including:
- File checksum calculation and tracking
- Record-level duplicate detection
- Processing log management
- Error handling and edge cases
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import django

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_django.core.settings")
django.setup()

# ruff: noqa: E402
from django.test import TestCase
from django.utils import timezone

from core_django.models.models import (
    DailyWeather,
    FileProcessingLog,
    RecordChecksum,
    WeatherStation,
)
from scripts.ingest_weather_data import (
    WeatherDataChecksumHandler,
    WeatherDataIngestorConfig,
)


class TestFileProcessingLog(TestCase):
    """Test suite for FileProcessingLog model."""

    def setUp(self):
        """Set up test fixtures."""
        self.station = WeatherStation.objects.create(
            station_id="USC00123456", name="Test Station"
        )

    def test_calculate_file_checksum(self):
        """Test file checksum calculation."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.write("20230102\t295\t185\t0\n")
            f.flush()
            temp_file = f.name

        try:
            # Calculate checksum
            checksum = FileProcessingLog.calculate_file_checksum(temp_file)

            # Verify checksum is consistent
            checksum2 = FileProcessingLog.calculate_file_checksum(temp_file)
            assert checksum == checksum2

            # Verify checksum is SHA-256 (64 hex characters)
            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)

        finally:
            os.unlink(temp_file)

    def test_is_file_processed_new_file(self):
        """Test file processing status for new file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # New file should not be processed
            assert not FileProcessingLog.is_file_processed(temp_file)

        finally:
            os.unlink(temp_file)

    def test_is_file_processed_existing_file(self):
        """Test file processing status for existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Create processing log
            checksum = FileProcessingLog.calculate_file_checksum(temp_file)
            FileProcessingLog.objects.create(
                file_path=temp_file,
                file_name=os.path.basename(temp_file),
                file_size=os.path.getsize(temp_file),
                file_checksum=checksum,
                station_id="USC00123456",
                processing_started_at=timezone.now(),
                processing_status="completed",
            )

            # File should now be processed
            assert FileProcessingLog.is_file_processed(temp_file)

        finally:
            os.unlink(temp_file)

    def test_is_file_processed_modified_file(self):
        """Test file processing status for modified file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Create processing log for original file
            checksum = FileProcessingLog.calculate_file_checksum(temp_file)
            FileProcessingLog.objects.create(
                file_path=temp_file,
                file_name=os.path.basename(temp_file),
                file_size=os.path.getsize(temp_file),
                file_checksum=checksum,
                station_id="USC00123456",
                processing_started_at=timezone.now(),
                processing_status="completed",
            )

            # Modify the file
            with open(temp_file, "a") as f:
                f.write("20230103\t300\t200\t15\n")

            # Modified file should not be processed
            assert not FileProcessingLog.is_file_processed(temp_file)

        finally:
            os.unlink(temp_file)

    def test_get_processing_history(self):
        """Test getting processing history for a file."""
        file_path = "test_file.txt"

        # Create multiple processing logs
        log1 = FileProcessingLog.objects.create(
            file_path=file_path,
            file_name="test_file.txt",
            file_size=1000,
            file_checksum="abc123",
            station_id="USC00123456",
            processing_started_at=timezone.now(),
            processing_status="completed",
        )

        log2 = FileProcessingLog.objects.create(
            file_path=file_path,
            file_name="test_file.txt",
            file_size=1100,
            file_checksum="def456",
            station_id="USC00123456",
            processing_started_at=timezone.now(),
            processing_status="completed",
        )

        # Get history
        history = FileProcessingLog.get_processing_history(file_path)

        # Should return both logs in reverse chronological order
        assert len(history) == 2
        assert history[0].id == log2.id  # Most recent first
        assert history[1].id == log1.id


class TestRecordChecksum(TestCase):
    """Test suite for RecordChecksum model."""

    def setUp(self):
        """Set up test fixtures."""
        self.station = WeatherStation.objects.create(
            station_id="USC00123456", name="Test Station"
        )

    def test_calculate_record_hash(self):
        """Test record content hash calculation."""
        # Test with normal values
        hash1 = RecordChecksum.calculate_record_hash(
            "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
        )

        # Same data should produce same hash
        hash2 = RecordChecksum.calculate_record_hash(
            "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
        )
        assert hash1 == hash2

        # Different data should produce different hash
        hash3 = RecordChecksum.calculate_record_hash(
            "USC00123456", datetime(2023, 1, 1).date(), 290, 178, 25
        )
        assert hash1 != hash3

        # Test with None values
        hash4 = RecordChecksum.calculate_record_hash(
            "USC00123456", datetime(2023, 1, 1).date(), None, None, None
        )
        assert hash4 != hash1

        # Verify hash is SHA-256
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_is_record_duplicate_new_record(self):
        """Test duplicate detection for new record."""
        # New record should not be duplicate
        assert not RecordChecksum.is_record_duplicate(
            "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
        )

    def test_is_record_duplicate_existing_record(self):
        """Test duplicate detection for existing record."""
        # Create a daily weather record
        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )

        # Create checksum record
        RecordChecksum.create_for_record(daily_weather, "test_file.txt", "batch_123")

        # Same record should be duplicate
        assert RecordChecksum.is_record_duplicate(
            "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
        )

        # Different record should not be duplicate
        assert not RecordChecksum.is_record_duplicate(
            "USC00123456", datetime(2023, 1, 1).date(), 290, 178, 25
        )

    def test_create_for_record(self):
        """Test creating checksum record for daily weather."""
        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )

        # Create checksum record
        checksum_record = RecordChecksum.create_for_record(
            daily_weather, "test_file.txt", "batch_123"
        )

        # Verify checksum record
        assert checksum_record.station_id == "USC00123456"
        assert checksum_record.date == datetime(2023, 1, 1).date()
        assert checksum_record.daily_weather == daily_weather
        assert checksum_record.source_file == "test_file.txt"
        assert checksum_record.processing_batch == "batch_123"
        assert len(checksum_record.content_hash) == 64


class TestWeatherDataChecksumHandler(TestCase):
    """Test suite for WeatherDataChecksumHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = WeatherDataIngestorConfig()
        self.config.enable_checksum = True
        self.config.enable_record_checksum = True
        self.mock_logger = Mock()
        self.handler = WeatherDataChecksumHandler(self.config, self.mock_logger)

        self.station = WeatherStation.objects.create(
            station_id="USC00123456", name="Test Station"
        )

    def test_init(self):
        """Test handler initialization."""
        assert self.handler.config == self.config
        assert self.handler.logger == self.mock_logger
        assert self.handler.processing_batch.startswith("batch_")

    def test_calculate_file_checksum(self):
        """Test file checksum calculation through handler."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            checksum = self.handler.calculate_file_checksum(temp_file)
            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)

        finally:
            os.unlink(temp_file)

    def test_calculate_file_checksum_error(self):
        """Test file checksum calculation error handling."""
        # Non-existent file
        checksum = self.handler.calculate_file_checksum("/nonexistent/file.txt")
        assert checksum == ""

        # Verify error was logged
        self.mock_logger.error.assert_called()

    def test_is_file_processed_disabled(self):
        """Test file processing check when checksum is disabled."""
        self.config.enable_checksum = False

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Should return False when checksum is disabled
            assert not self.handler.is_file_processed(temp_file)

        finally:
            os.unlink(temp_file)

    def test_start_file_processing(self):
        """Test starting file processing tracking."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Start processing
            log_entry = self.handler.start_file_processing(temp_file, "USC00123456")

            # Verify log entry
            assert log_entry is not None
            assert log_entry.file_path == temp_file
            assert log_entry.station_id == "USC00123456"
            assert log_entry.processing_status == "started"
            assert log_entry.file_size == os.path.getsize(temp_file)
            assert len(log_entry.file_checksum) == 64

            # Verify info was logged
            self.mock_logger.info.assert_called()

        finally:
            os.unlink(temp_file)

    def test_start_file_processing_disabled(self):
        """Test starting file processing when checksum is disabled."""
        self.config.enable_checksum = False

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Should return None when checksum is disabled
            log_entry = self.handler.start_file_processing(temp_file, "USC00123456")
            assert log_entry is None

        finally:
            os.unlink(temp_file)

    def test_complete_file_processing(self):
        """Test completing file processing tracking."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Start processing
            log_entry = self.handler.start_file_processing(temp_file, "USC00123456")

            # Complete processing
            self.handler.complete_file_processing(log_entry, 100, 5, 2, 0, 1000, "")

            # Verify log entry was updated
            log_entry.refresh_from_db()
            assert log_entry.processing_status == "completed"
            assert log_entry.processed_records == 100
            assert log_entry.skipped_records == 5
            assert log_entry.duplicate_records == 2
            assert log_entry.error_count == 0
            assert log_entry.total_lines == 1000
            assert log_entry.processing_completed_at is not None

        finally:
            os.unlink(temp_file)

    def test_complete_file_processing_with_errors(self):
        """Test completing file processing with errors."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Start processing
            log_entry = self.handler.start_file_processing(temp_file, "USC00123456")

            # Complete processing with errors
            self.handler.complete_file_processing(
                log_entry, 95, 5, 2, 3, 1000, "Some errors occurred"
            )

            # Verify log entry was updated
            log_entry.refresh_from_db()
            assert log_entry.processing_status == "failed"
            assert log_entry.error_count == 3
            assert log_entry.error_message == "Some errors occurred"

        finally:
            os.unlink(temp_file)

    def test_is_record_duplicate_disabled(self):
        """Test record duplicate check when disabled."""
        self.config.enable_record_checksum = False

        # Should return False when disabled
        assert not self.handler.is_record_duplicate(
            "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
        )

    def test_is_record_duplicate_enabled(self):
        """Test record duplicate check when enabled."""
        # Create a daily weather record
        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )

        # Create checksum record
        RecordChecksum.create_for_record(daily_weather, "test_file.txt", "batch_123")

        # Should detect duplicate
        assert self.handler.is_record_duplicate(
            "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
        )

    def test_create_record_checksum_disabled(self):
        """Test creating record checksum when disabled."""
        self.config.enable_record_checksum = False

        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )

        # Should not create checksum when disabled
        self.handler.create_record_checksum(daily_weather, "test_file.txt")

        # Verify no checksum was created
        assert RecordChecksum.objects.count() == 0

    def test_create_record_checksum_enabled(self):
        """Test creating record checksum when enabled."""
        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )

        # Should create checksum when enabled
        self.handler.create_record_checksum(daily_weather, "test_file.txt")

        # Verify checksum was created
        assert RecordChecksum.objects.count() == 1
        checksum = RecordChecksum.objects.first()
        assert checksum.station_id == "USC00123456"
        assert checksum.source_file == "test_file.txt"
        assert checksum.processing_batch == self.handler.processing_batch

    def test_reset_checksums(self):
        """Test resetting all checksum data."""
        # Create some test data
        FileProcessingLog.objects.create(
            file_path="test1.txt",
            file_name="test1.txt",
            file_size=1000,
            file_checksum="abc123",
            station_id="USC00123456",
            processing_started_at=timezone.now(),
            processing_status="completed",
        )

        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )
        RecordChecksum.create_for_record(daily_weather, "test1.txt", "batch_123")

        # Verify data exists
        assert FileProcessingLog.objects.count() == 1
        assert RecordChecksum.objects.count() == 1

        # Reset checksums
        self.config.reset_checksums = True
        self.handler.reset_checksums()

        # Verify data was deleted
        assert FileProcessingLog.objects.count() == 0
        assert RecordChecksum.objects.count() == 0

        # Verify info was logged
        self.mock_logger.info.assert_called()

    def test_reset_checksums_disabled(self):
        """Test reset checksums when disabled."""
        self.config.reset_checksums = False

        # Create some test data
        FileProcessingLog.objects.create(
            file_path="test1.txt",
            file_name="test1.txt",
            file_size=1000,
            file_checksum="abc123",
            station_id="USC00123456",
            processing_started_at=timezone.now(),
            processing_status="completed",
        )

        # Reset should not do anything
        self.handler.reset_checksums()

        # Verify data still exists
        assert FileProcessingLog.objects.count() == 1

    def test_get_checksum_stats(self):
        """Test getting checksum statistics."""
        # Create test data
        FileProcessingLog.objects.create(
            file_path="test1.txt",
            file_name="test1.txt",
            file_size=1000,
            file_checksum="abc123",
            station_id="USC00123456",
            processing_started_at=timezone.now(),
            processing_status="completed",
        )

        FileProcessingLog.objects.create(
            file_path="test2.txt",
            file_name="test2.txt",
            file_size=1000,
            file_checksum="def456",
            station_id="USC00123456",
            processing_started_at=timezone.now(),
            processing_status="failed",
        )

        daily_weather = DailyWeather.objects.create(
            station=self.station,
            date=datetime(2023, 1, 1).date(),
            max_temp=289,
            min_temp=178,
            precipitation=25,
        )
        RecordChecksum.create_for_record(daily_weather, "test1.txt", "batch_123")

        # Get stats
        stats = self.handler.get_checksum_stats()

        # Verify stats
        assert stats["total_files_processed"] == 1
        assert stats["total_files_failed"] == 1
        assert stats["total_record_checksums"] == 1
        assert stats["processing_batch"] == self.handler.processing_batch

    def test_get_checksum_stats_error(self):
        """Test getting checksum statistics with error."""
        # Mock an error
        with patch(
            "core_django.models.models.FileProcessingLog.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            stats = self.handler.get_checksum_stats()

            # Should return empty dict on error
            assert stats == {}

            # Verify error was logged
            self.mock_logger.error.assert_called()


class TestChecksumIntegration(TestCase):
    """Integration tests for checksum functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.station = WeatherStation.objects.create(
            station_id="USC00123456", name="Test Station"
        )

    def test_end_to_end_file_processing(self):
        """Test end-to-end file processing workflow."""
        config = WeatherDataIngestorConfig()
        config.enable_checksum = True
        config.enable_record_checksum = True

        mock_logger = Mock()
        handler = WeatherDataChecksumHandler(config, mock_logger)

        # Create test file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.write("20230102\t295\t185\t0\n")
            f.flush()
            temp_file = f.name

        try:
            # 1. Check if file is processed (should be False)
            assert not handler.is_file_processed(temp_file)

            # 2. Start file processing
            log_entry = handler.start_file_processing(temp_file, "USC00123456")
            assert log_entry is not None
            assert log_entry.processing_status == "started"

            # 3. Process records (simulate)
            daily_weather1 = DailyWeather.objects.create(
                station=self.station,
                date=datetime(2023, 1, 1).date(),
                max_temp=289,
                min_temp=178,
                precipitation=25,
            )

            daily_weather2 = DailyWeather.objects.create(
                station=self.station,
                date=datetime(2023, 1, 2).date(),
                max_temp=295,
                min_temp=185,
                precipitation=0,
            )

            # Create checksums
            handler.create_record_checksum(daily_weather1, temp_file)
            handler.create_record_checksum(daily_weather2, temp_file)

            # 4. Complete file processing
            handler.complete_file_processing(log_entry, 2, 0, 0, 0, 2, "")

            # 5. Verify file is now processed
            assert handler.is_file_processed(temp_file)

            # 6. Check record duplicates
            assert handler.is_record_duplicate(
                "USC00123456", datetime(2023, 1, 1).date(), 289, 178, 25
            )
            assert handler.is_record_duplicate(
                "USC00123456", datetime(2023, 1, 2).date(), 295, 185, 0
            )

            # 7. Verify processing log
            log_entry.refresh_from_db()
            assert log_entry.processing_status == "completed"
            assert log_entry.processed_records == 2
            assert log_entry.error_count == 0

            # 8. Verify record checksums
            assert RecordChecksum.objects.count() == 2

        finally:
            os.unlink(temp_file)

    def test_file_modification_detection(self):
        """Test that file modification is detected."""
        config = WeatherDataIngestorConfig()
        config.enable_checksum = True

        mock_logger = Mock()
        handler = WeatherDataChecksumHandler(config, mock_logger)

        # Create test file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("20230101\t289\t178\t25\n")
            f.flush()
            temp_file = f.name

        try:
            # Process file first time
            log_entry = handler.start_file_processing(temp_file, "USC00123456")
            handler.complete_file_processing(log_entry, 1, 0, 0, 0, 1, "")

            # Verify file is processed
            assert handler.is_file_processed(temp_file)

            # Modify file
            with open(temp_file, "a") as f:
                f.write("20230102\t295\t185\t0\n")

            # File should no longer be considered processed
            assert not handler.is_file_processed(temp_file)

        finally:
            os.unlink(temp_file)
