# Weather Data Engineering API

A comprehensive data engineering solution for ingesting, analyzing, and serving weather data through a REST API.

## 🌤️ Overview

This project implements a complete data pipeline for weather station data, featuring:

- **Data Ingestion**: Efficient processing of weather station files with duplicate detection
- **Data Analysis**: Automated calculation of yearly weather statistics
- **REST API**: High-performance API with filtering, pagination, and auto-documentation
- **Cloud Ready**: Designed for AWS deployment with Infrastructure as Code

## 📊 Data Sources

- **Weather Data**: Historical records from 1985-2014 across Nebraska, Iowa, Illinois, Indiana, and Ohio
- **Crop Yield Data**: Corn yield statistics for agricultural correlation analysis

## 🏗️ Architecture

### Data Models
- `WeatherStation`: Station metadata and geographic information
- `DailyWeather`: Raw weather observations with temperature and precipitation
- `YearlyWeatherStats`: Aggregated statistics for efficient querying
- `CropYield`: Agricultural yield data for correlation analysis

### Technology Stack
- **Database**: PostgreSQL with optimized indexing strategy
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **ORM**: Django ORM for robust data modeling
- **Containerization**: Docker with multi-stage builds
- **Infrastructure**: Terraform for AWS deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Setup Options

Choose one of the following setup methods:

#### Option 1: Poetry (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/smusali/code-challenge-template.git
   cd code-challenge-template
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # Or using pip
   pip install poetry
   ```

3. **Install dependencies**
   ```bash
   poetry install --with dev,lint
   ```

4. **Activate Poetry shell**
   ```bash
   poetry shell
   ```

5. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

#### Option 2: Virtual Environment (venv)

1. **Clone the repository**
   ```bash
   git clone https://github.com/smusali/code-challenge-template.git
   cd code-challenge-template
   ```

2. **Create and activate virtual environment**
   ```bash
   python3.11 -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Upgrade pip and install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Generate requirements.txt from Poetry** (if needed)
   ```bash
   # If requirements.txt doesn't exist, generate it:
   poetry export -f requirements.txt --output requirements.txt --with dev,lint
   ```

5. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

#### Option 3: Docker (Easiest)

1. **Clone and run with Docker Compose**
   ```bash
   git clone https://github.com/smusali/code-challenge-template.git
   cd code-challenge-template
   docker-compose up --build
   ```

### Development Commands

#### With Poetry
```bash
# Run API server
poetry run uvicorn weather_api.main:app --reload

# Run tests
poetry run pytest

# Run pre-commit hooks
poetry run pre-commit run --all-files

# Data ingestion
poetry run python -m scripts.ingest_wx --src ./wx_data

# Django management
poetry run python core_django/manage.py migrate
```

#### With venv
```bash
# Activate environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run API server
uvicorn weather_api.main:app --reload

# Run tests
pytest

# Run pre-commit hooks
pre-commit run --all-files

# Data ingestion
python -m scripts.ingest_wx --src ./wx_data

# Django management
python core_django/manage.py migrate
```

#### With Docker
```bash
# Run with essential services only (development)
docker-compose up

# Run with all services including monitoring
docker-compose --profile monitoring up

# Run tests in container
docker-compose exec web poetry run pytest

# Data ingestion
docker-compose run --rm ingestion python -m scripts.ingest_wx --src /app/wx_data
```

### Access Points

Once running, access these endpoints:
- **API Endpoints**: http://localhost:8000/api/
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Database Admin**: http://localhost:5050 (pgAdmin)
- **Monitoring**: http://localhost:3000 (Grafana)

## 📡 API Endpoints

### Weather Data
- `GET /api/weather` - Raw weather observations
- `GET /api/weather/stats` - Aggregated yearly statistics

### Query Parameters
- `station_id`: Filter by weather station
- `date`: Specific date (YYYY-MM-DD)
- `start_date` / `end_date`: Date range filtering
- `page` / `page_size`: Pagination controls

### Example Usage
```bash
# Get all weather data for station USC00110072
curl "http://localhost:8000/api/weather?station_id=USC00110072"

# Get yearly stats for 2010-2014
curl "http://localhost:8000/api/weather/stats?start_date=2010-01-01&end_date=2014-12-31"
```

## 🔧 Data Pipeline

### Ingestion Process
```bash
# Poetry
poetry run python -m scripts.ingest_wx --src ./wx_data --db-url $DATABASE_URL

# venv
python -m scripts.ingest_wx --src ./wx_data --db-url $DATABASE_URL

# Docker
docker-compose run --rm ingestion python -m scripts.ingest_wx --src /app/wx_data
```

### Calculate Statistics
```bash
# Poetry
poetry run python -m scripts.compute_yearly_stats --db-url $DATABASE_URL

# venv
python -m scripts.compute_yearly_stats --db-url $DATABASE_URL
```

### Features
- **Idempotent**: Safe to run multiple times without duplicates
- **Efficient**: Streaming parser with minimal memory footprint
- **Observable**: Comprehensive logging and metrics
- **Resumable**: Skip unchanged files using checksums

## 🧪 Testing

### Poetry
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=weather_api --cov-report=html

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/e2e/
```

### venv
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=weather_api --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Docker
```bash
# Run tests in container
docker-compose exec web poetry run pytest

# Run tests with fresh container
docker-compose run --rm web poetry run pytest
```

## 📈 Performance Characteristics

- **Ingestion Rate**: ~10,000 records/second
- **API Response Time**: <100ms for paginated queries
- **Database Size**: ~50MB for complete dataset
- **Memory Usage**: <100MB during ingestion

## 🏗️ Project Structure

```
code-challenge-template/
├── weather_api/          # FastAPI application
├── core_django/          # Django ORM models
├── scripts/              # Data processing scripts
├── tests/                # Test suites
├── docker/               # Container definitions
├── infrastructure/       # Terraform modules
├── wx_data/              # Weather station files
└── yld_data/             # Crop yield data
```

## 🔧 Development Tools

### Code Quality
```bash
# Poetry
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run mypy .

# venv
black .
isort .
ruff check .
mypy .
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 🐳 Docker Services

### Development (Default)
- `web`: FastAPI application with hot reloading
- `db`: PostgreSQL database
- `redis`: Cache layer
- `pgadmin`: Database administration

### With Profiles
```bash
# Include monitoring
docker-compose --profile monitoring up

# Include production services
docker-compose --profile production up

# Include data processing
docker-compose --profile data-processing up

# All services
docker-compose --profile monitoring --profile production --profile data-processing up
```

## 🚀 Cloud Deployment

The application is designed for AWS deployment using:
- **AWS Lambda** + API Gateway for serverless API
- **Amazon Aurora PostgreSQL** for managed database
- **AWS Batch** for scheduled data ingestion
- **EventBridge** for cron scheduling
- **CloudWatch** for monitoring and logs

See `infrastructure/` directory for Terraform configurations.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Quality Standards
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public APIs
- Maintain test coverage >90%
- Use conventional commit messages

## 🔍 Troubleshooting

### Common Issues

#### Poetry Issues
```bash
# Clear cache and reinstall
poetry cache clear --all pypi
poetry install --with dev,lint
```

#### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up
```

#### Database Connection
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Reset database
docker-compose down -v
docker-compose up db
```

#### Dependencies
```bash
# Update all dependencies
poetry update

# Or with venv
pip install --upgrade -r requirements.txt
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Weather data provided by [Corteva](https://github.com/corteva/code-challenge-template)
- Built for the Corteva Data Engineering Challenge
- Inspired by modern data engineering best practices

---

**Note**: This is a demonstration project showcasing data engineering capabilities including ETL pipelines, API development, and cloud architecture design.
