# Contributing to Weather Data Engineering API

Thank you for your interest in contributing to the Weather Data Engineering API! This document provides guidelines and information for contributors to help maintain code quality and ensure smooth collaboration.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Security](#security)
- [Community](#community)

## 🤝 Code of Conduct

This project follows the GitHub Community Guidelines. By participating, you are expected to be respectful and professional. Please report unacceptable behavior to [project maintainers](mailto:your-email@example.com).

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.11+** (recommended: 3.11 for best compatibility)
- **Git** for version control
- **Docker** (optional, for containerized development)
- **PostgreSQL** (for local database development)

### First-Time Contributors

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/weather-data-engineering-api.git
   cd weather-data-engineering-api
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/smusali/weather-data-engineering-api.git
   ```

## 🔧 Development Setup

### Local Environment Setup

1. **Create and activate virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Install development dependencies**:
   ```bash
   pip install pytest pytest-cov black isort ruff mypy pre-commit
   ```

4. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Set up database**:
   ```bash
   # Option 1: Local PostgreSQL
   createdb weather_db

   # Option 2: Docker
   docker run -d --name weather-postgres \
     -e POSTGRES_DB=weather_db \
     -e POSTGRES_USER=weather_user \
     -e POSTGRES_PASSWORD=your_password \
     -p 5432:5432 postgres:15
   ```

7. **Run Django migrations**:
   ```bash
   PYTHONPATH=. python core_django/manage.py migrate
   ```

8. **Verify setup**:
   ```bash
   PYTHONPATH=. python core_django/manage.py check
   python run_tests.py --smoke
   ```

### Docker Development (Alternative)

For a fully containerized development environment:

```bash
# Start all services
docker-compose up --build

# Run tests in container
docker-compose exec web python run_tests.py

# Access shell in container
docker-compose exec web bash
```

## 🔄 Contributing Process

### Workflow Overview

1. **Create an issue** (for bugs/features) or **find an existing one**
2. **Fork and clone** the repository
3. **Create a feature branch** from `main`
4. **Make your changes** following our standards
5. **Write/update tests** for your changes
6. **Run the test suite** locally
7. **Commit your changes** with conventional commits
8. **Push to your fork** and **create a pull request**
9. **Address feedback** from code review
10. **Merge** once approved

### Branch Naming

Use descriptive branch names with prefixes:

- `feature/add-weather-aggregation` - New features
- `fix/temperature-conversion-bug` - Bug fixes
- `docs/update-api-examples` - Documentation updates
- `refactor/optimize-database-queries` - Code refactoring
- `test/improve-coverage` - Test improvements

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

Examples:
feat(api): add temperature aggregation endpoint
fix(db): resolve connection timeout in production
docs(readme): update installation instructions
test(weather): add unit tests for weather parsing
refactor(utils): optimize pagination helper functions
ci(github): add security scanning workflow
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `chore`

## 📏 Code Standards

### Python Code Style

We follow [PEP 8](https://pep8.org/) with these tools:

- **Black** for code formatting
- **isort** for import sorting
- **Ruff** for linting
- **MyPy** for type checking

### Code Quality Rules

1. **Type Hints**: All functions must have type hints
   ```python
   def process_weather_data(data: Dict[str, Any]) -> List[WeatherRecord]:
       """Process raw weather data into structured records."""
       # Implementation
   ```

2. **Docstrings**: Public functions/classes need docstrings
   ```python
   def calculate_temperature_average(records: List[DailyWeather]) -> float:
       """
       Calculate the average temperature from daily weather records.

       Args:
           records: List of daily weather records

       Returns:
           Average temperature in Celsius

       Raises:
           ValueError: If records list is empty
       """
   ```

3. **Error Handling**: Use appropriate exception handling
   ```python
   try:
       result = risky_operation()
   except SpecificException as e:
       logger.error(f"Operation failed: {e}")
       raise CustomException(f"Failed to process: {e}") from e
   ```

4. **Logging**: Use structured logging
   ```python
   import logging

   logger = logging.getLogger(__name__)
   logger.info("Processing weather data", extra={"station_id": station_id})
   ```

### Code Organization

- **FastAPI routes**: Place in `src/routers/`
- **Data models**: Use `src/models/` for Pydantic models
- **Business logic**: Keep in service classes in `src/services/`
- **Utilities**: Common functions in `src/utils/`
- **Tests**: Mirror structure in `tests/`

## 🧪 Testing Guidelines

### Test Requirements

All contributions must include appropriate tests:

1. **Unit Tests**: Test individual functions/classes
2. **Integration Tests**: Test API endpoints and database interactions
3. **Performance Tests**: For optimization changes

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test modules
python run_tests.py --module weather
python run_tests.py --module api

# Run with coverage
python run_tests.py --coverage

# Run performance tests
python run_tests.py --performance
```

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient

class TestWeatherAPI:
    """Test suite for weather API endpoints."""

    def test_get_weather_stations_success(self, client: TestClient):
        """Test successful retrieval of weather stations."""
        response = client.get("/api/v2/weather-stations")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_get_weather_stations_pagination(self, client: TestClient):
        """Test weather stations endpoint pagination."""
        response = client.get("/api/v2/weather-stations?page=1&page_size=5")
        data = response.json()
        assert len(data["data"]) <= 5
        assert "pagination" in data
```

### Test Coverage

- Maintain **>90% code coverage**
- Cover **happy paths** and **error scenarios**
- Include **edge cases** and **boundary conditions**
- Test **API responses** and **database interactions**

## 📚 Documentation

### Documentation Requirements

When contributing, update relevant documentation:

1. **API Documentation**: Auto-generated via FastAPI/OpenAPI
2. **Code Comments**: For complex logic
3. **README Updates**: For setup/usage changes
4. **CHANGELOG**: For user-facing changes

### API Documentation

FastAPI automatically generates documentation, but ensure:

- **Clear endpoint descriptions**
- **Example requests/responses**
- **Parameter descriptions**
- **Error response documentation**

```python
@router.get("/weather-stations", response_model=PaginatedResponse[WeatherStationResponse])
async def list_weather_stations(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[WeatherStationResponse]:
    """
    List weather stations with pagination.

    Retrieves a paginated list of weather stations with their metadata
    including geographic coordinates, elevation, and operational status.

    Returns:
        Paginated response containing weather station data

    Raises:
        HTTPException: 400 for invalid pagination parameters
        HTTPException: 500 for database errors
    """
```

## 🔍 Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run quality checks**:
   ```bash
   # Format code
   black .
   isort .

   # Lint code
   ruff check .
   mypy src/

   # Run tests
   python run_tests.py
   ```

3. **Update documentation** if needed

### PR Template

Use this template for pull requests:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
- [ ] Tests added/updated for changes

## Screenshots (if applicable)
Add screenshots for UI changes.

## Related Issues
Closes #issue_number
```

### Review Process

1. **Automated checks** must pass (CI/CD, tests, linting)
2. **Code owner review** required (see CODEOWNERS)
3. **Two approvals** required for sensitive files
4. **All conversations resolved** before merge
5. **Squash and merge** preferred for clean history

## 🐛 Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. macOS 12.6]
- Python: [e.g. 3.11.5]
- Browser: [e.g. Chrome 94]

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests

For new features:

```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
Describe how you envision this feature working.

**Alternatives Considered**
Any alternative approaches you've considered.

**Additional Context**
Any other context or screenshots about the feature request.
```

## 🔒 Security

### Security Issues

**DO NOT** file GitHub issues for security vulnerabilities. Instead:

1. **Email directly**: [security@example.com](mailto:security@example.com)
2. **Include**: Detailed description, steps to reproduce, impact assessment
3. **Wait for response** before public disclosure

### Security Best Practices

- **Never commit secrets** (API keys, passwords, certificates)
- **Use environment variables** for sensitive configuration
- **Validate all inputs** in API endpoints
- **Follow OWASP guidelines** for web security
- **Update dependencies** regularly

## 👥 Community

### Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bugs and feature requests
- **Email**: [maintainers@example.com](mailto:maintainers@example.com) for private matters

### Communication Guidelines

- **Be respectful** and professional
- **Search existing issues** before creating new ones
- **Provide detailed information** in issue reports
- **Be patient** with review feedback
- **Help others** when you can

### Recognition

Contributors are recognized in:

- **README.md** contributors section
- **CHANGELOG.md** for significant contributions
- **GitHub contributors** page
- **Release notes** for major features

## 📊 Project Stats

We track these metrics for project health:

- **Code Coverage**: Target >90%
- **Test Success Rate**: Target >99%
- **Performance**: API response time <500ms (p95)
- **Security**: Zero critical vulnerabilities
- **Documentation**: Up-to-date with code changes

## 🎯 Good First Issues

New contributors should look for issues labeled:

- `good first issue` - Perfect for newcomers
- `help wanted` - Community help appreciated
- `documentation` - Documentation improvements
- `tests` - Test coverage improvements

## 📝 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## 🙏 Thank You!

Your contributions help make this project better for everyone. Whether it's code, documentation, bug reports, or feature suggestions, every contribution is valuable.

For questions about contributing, feel free to reach out to the maintainers or open a discussion on GitHub.
