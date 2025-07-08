# Weather Data Engineering API - Test Suite

Comprehensive test suite for the weather data engineering CLI tools and API components.

## Overview

This test suite provides comprehensive coverage for the weather data ingestion parser, including unit tests and integration tests that validate data parsing, error handling, and performance characteristics.

## Test Structure

```
tests/
├── conftest.py                              # Shared fixtures and configuration
├── scripts/                                 # CLI tool tests
│   ├── test_weather_parser.py              # Unit tests for WeatherDataParser
│   └── test_weather_parser_integration.py  # Integration tests
└── README.md                               # This file
```

## Test Categories

### Unit Tests (`test_weather_parser.py`)
- **26 unit tests** covering core parsing functionality
- Tests individual methods in isolation
- Validates edge cases and error conditions
- Fast execution (< 1 second)

### Integration Tests (`test_weather_parser_integration.py`)
- **10 integration tests** covering realistic scenarios
- Tests with larger datasets and real-world patterns
- Performance and memory usage validation
- Moderate execution time (< 1 second)

## Running Tests

### All Tests
```bash
# Run complete test suite
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=scripts --cov-report=term-missing
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/scripts/test_weather_parser.py -v

# Integration tests only
pytest tests/scripts/test_weather_parser_integration.py -v

# Tests marked as slow (performance tests)
pytest tests/ -m slow -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

### Test Markers
- **`unit`**: Unit tests
- **`integration`**: Integration tests
- **`slow`**: Performance/long-running tests

## Test Coverage

### WeatherDataParser Class Coverage

#### Core Methods
- ✅ `parse_weather_line()` - Main parsing method
- ✅ `_parse_value()` - Value parsing helper

#### Data Validation Coverage
- ✅ **Date Parsing**: Valid dates, invalid formats, leap years
- ✅ **Temperature Validation**: Max >= Min relationships, missing values
- ✅ **Precipitation Validation**: Non-negative values, missing data handling
- ✅ **Field Validation**: Correct number of fields, data types
- ✅ **Missing Value Handling**: -9999 sentinel value processing

#### Error Handling Coverage
- ✅ **Format Errors**: Wrong number of fields, invalid formats
- ✅ **Data Type Errors**: Non-numeric values, invalid dates
- ✅ **Validation Errors**: Temperature relationships, negative precipitation
- ✅ **Exception Handling**: Unexpected errors, logging verification

#### Performance Coverage
- ✅ **Large Dataset Processing**: 300+ records with mixed patterns
- ✅ **Memory Usage**: Validation of memory cleanup
- ✅ **Processing Speed**: Performance benchmarks and timing

## Test Data Patterns

### Valid Data Examples
```
20230615\t289\t178\t25     # Normal weather data
20230616\t-9999\t-9999\t-9999  # All missing values
20230617\t310\t200\t0      # Zero precipitation
20230618\t285\t285\t15     # Equal temperatures
```

### Invalid Data Examples
```
20230615\t289\t178         # Too few fields
2023-06-15\t289\t178\t25   # Wrong date format
20230615\tabc\t178\t25     # Invalid temperature
20230615\t150\t200\t25     # Max < Min temperature
20230615\t289\t178\t-50    # Negative precipitation
```

## Test Fixtures

### Shared Fixtures (from `conftest.py`)
- **`test_data_dir`**: Temporary directory with sample weather files
- **`sample_weather_lines`**: Valid weather data for testing
- **`invalid_weather_lines`**: Invalid data patterns for error testing
- **`setup_django_settings`**: Django configuration for tests

### Local Fixtures
- **`mock_logger`**: Mock logger for testing log output
- **`parser`**: WeatherDataParser instance with mock logger

## Performance Benchmarks

### Typical Performance Metrics
- **Unit Test Suite**: ~0.5 seconds (26 tests)
- **Integration Test Suite**: ~0.4 seconds (10 tests)
- **Parser Performance**: 10,000+ lines/second processing rate
- **Memory Usage**: Stable memory usage across large datasets

### Performance Test Examples
```bash
# Run performance tests with timing
pytest tests/scripts/test_weather_parser_integration.py::TestWeatherDataParserIntegration::test_performance_with_realistic_data -v -s

# Run memory tests
pytest tests/scripts/test_weather_parser_integration.py::TestWeatherDataParserIntegration::test_memory_usage_with_large_dataset -v
```

## Continuous Integration

### Pre-commit Hooks
The test suite integrates with pre-commit hooks to ensure code quality:
```bash
# Run tests as part of pre-commit
pre-commit run --all-files
```

### Test Configuration
Test configuration is defined in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = ["--strict-markers", "--strict-config"]
testpaths = ["tests"]
markers = [
    "unit: unit tests",
    "integration: integration tests",
    "db: tests requiring database",
]
```

## Test Development Guidelines

### Writing New Tests
1. **Unit Tests**: Test individual methods in isolation
2. **Integration Tests**: Test realistic scenarios with multiple components
3. **Use Fixtures**: Leverage shared fixtures for common test data
4. **Mock External Dependencies**: Use mocks for logging, databases, etc.
5. **Parametrize Tests**: Use `@pytest.mark.parametrize` for multiple inputs
6. **Clear Test Names**: Use descriptive test method names

### Test Organization
- Place unit tests close to the code being tested
- Use integration tests for end-to-end scenarios
- Group related tests in test classes
- Use appropriate markers for test categorization

### Example Test Structure
```python
class TestWeatherDataParser:
    """Test suite for WeatherDataParser class."""

    @pytest.fixture
    def parser(self, mock_logger):
        """Create parser instance for testing."""
        return WeatherDataParser(mock_logger)

    def test_parse_valid_data(self, parser):
        """Test parsing valid weather data."""
        # Arrange
        line = "20230615\t289\t178\t25"

        # Act
        result = parser.parse_weather_line(line, 1)

        # Assert
        assert result is not None
        date_obj, max_temp, min_temp, precipitation = result
        assert max_temp == 289
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project root
   cd /path/to/weather-data-engineering-api

   # Run tests with proper Python path
   PYTHONPATH=. pytest tests/
   ```

2. **Django Configuration Issues**
   ```bash
   # Set Django settings module
   export DJANGO_SETTINGS_MODULE=core_django.core.settings
   pytest tests/
   ```

3. **Missing Dependencies**
   ```bash
   # Install test dependencies
   pip install pytest pytest-django
   ```

### Debugging Tests
```bash
# Run with debugging output
pytest tests/ -v -s --tb=long

# Run specific test with debugging
pytest tests/scripts/test_weather_parser.py::TestWeatherDataParser::test_parse_valid_weather_line -v -s

# Run with Python debugger
pytest tests/ --pdb
```

## Contributing

When contributing new tests:
1. Follow the existing test structure and naming conventions
2. Add appropriate docstrings and comments
3. Include both positive and negative test cases
4. Update this README if adding new test categories
5. Ensure all tests pass before submitting

## Test Reports

### Coverage Reports
```bash
# Generate HTML coverage report
pytest tests/ --cov=scripts --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Test Results
All tests should pass with the following expected results:
- **Unit Tests**: 26/26 passing
- **Integration Tests**: 10/10 passing
- **Total**: 36/36 passing
- **Execution Time**: < 1 second
