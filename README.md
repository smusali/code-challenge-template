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

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/smusali/code-challenge-template.git
   cd code-challenge-template
   ```

2. **Install dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

5. **Access the API**
   - API Endpoints: http://localhost:8000/api/
   - Interactive Docs: http://localhost:8000/docs
   - OpenAPI Spec: http://localhost:8000/openapi.json

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
# Ingest weather data
poetry run ingest-wx --src ./wx_data --db-url $DATABASE_URL

# Calculate yearly statistics
poetry run compute-yearly-stats --db-url $DATABASE_URL
```

### Features
- **Idempotent**: Safe to run multiple times without duplicates
- **Efficient**: Streaming parser with minimal memory footprint
- **Observable**: Comprehensive logging and metrics
- **Resumable**: Skip unchanged files using checksums

## 🧪 Testing

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

### Code Quality
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public APIs
- Maintain test coverage >90%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Weather data provided by [Corteva](https://github.com/corteva/code-challenge-template)
- Built for the Corteva Data Engineering Challenge
- Inspired by modern data engineering best practices

---

**Note**: This is a demonstration project showcasing data engineering capabilities including ETL pipelines, API development, and cloud architecture design.
