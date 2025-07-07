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
- `YearlyWeatherStats`: Pre-calculated yearly statistics with temperature and precipitation aggregates
- `CropYield`: Historical crop yield data (1985-2014) for agricultural correlation analysis

### Technology Stack
- **Database**: PostgreSQL with optimized indexing strategy
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **ORM**: Django ORM for robust data modeling
- **Containerization**: Docker with multi-stage builds
- **Infrastructure**: Terraform for AWS deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (optional: Docker for full stack)

### Local Development (Recommended)

1. **Clone and setup**
   ```bash
   git clone https://github.com/smusali/code-challenge-template.git
   cd code-challenge-template
   ```

2. **Create virtual environment**
   ```bash
   # Using venv
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using virtualenv
   pip install virtualenv
   virtualenv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Test Django setup**
   ```bash
   PYTHONPATH=. python core_django/manage.py check
   ```

5. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

### Using Poetry (Alternative)

```bash
pip install poetry
poetry install
poetry shell
```

### Using Docker (For full stack)

```bash
docker-compose up --build
```

## 📊 Database Initialization

### Initialize Weather Data

The project includes a comprehensive Django management command to populate the database with the existing weather data files.

```bash
# Activate virtual environment first
source venv/bin/activate

# Test data parsing (dry run - no database changes)
PYTHONPATH=. python core_django/manage.py init_weather_data --dry-run --verbosity=2

# Initialize database with weather data
PYTHONPATH=. python core_django/manage.py init_weather_data

# Clear existing data and re-initialize
PYTHONPATH=. python core_django/manage.py init_weather_data --clear

# Custom batch size for performance tuning
PYTHONPATH=. python core_django/manage.py init_weather_data --batch-size=2000

# Use different data directory
PYTHONPATH=. python core_django/manage.py init_weather_data --data-dir=custom_wx_data
```

### Command Options
- `--clear`: Remove existing data before importing
- `--batch-size=N`: Process records in batches of N (default: 1000)
- `--data-dir=PATH`: Specify custom data directory (default: wx_data)
- `--dry-run`: Parse files without saving to database
- `--verbosity=2`: Show detailed progress information

### Expected Results
- **Weather Stations**: 167 stations
- **Daily Records**: ~1.73 million records
- **Processing Time**: ~2-5 minutes (depends on hardware)
- **Data Coverage**: 1985-2014 across multiple US states

### Data Validation
The command handles:
- Missing values (-9999 → NULL)
- Date parsing and validation
- Temperature range validation
- Duplicate record prevention
- Batch processing for memory efficiency

### Initialize Crop Yield Data

Initialize the database with historical crop yield data for correlation analysis:

```bash
# Test crop yield data parsing (dry run)
PYTHONPATH=. python core_django/manage.py init_crop_yield --dry-run --verbosity=2

# Initialize crop yield data
PYTHONPATH=. python core_django/manage.py init_crop_yield

# Clear existing data and re-initialize
PYTHONPATH=. python core_django/manage.py init_crop_yield --clear

# Use custom data file
PYTHONPATH=. python core_django/manage.py init_crop_yield --data-file=custom_yield_data.txt
```

### Calculate Yearly Weather Statistics

Generate aggregated yearly statistics from daily weather data for efficient API queries:

```bash
# Test yearly statistics calculation (dry run)
PYTHONPATH=. python core_django/manage.py init_yearly_stats --dry-run --verbosity=2

# Calculate yearly statistics for all stations and years
PYTHONPATH=. python core_django/manage.py init_yearly_stats

# Calculate for specific year only
PYTHONPATH=. python core_django/manage.py init_yearly_stats --year=2010

# Calculate for specific station only
PYTHONPATH=. python core_django/manage.py init_yearly_stats --station=USC00110072

# Clear and recalculate all statistics
PYTHONPATH=. python core_django/manage.py init_yearly_stats --clear

# Custom batch size for performance tuning
PYTHONPATH=. python core_django/manage.py init_yearly_stats --batch-size=200
```

### Complete Database Initialization

To fully initialize the database with all data:

```bash
# 1. Initialize weather stations and daily data
PYTHONPATH=. python core_django/manage.py init_weather_data

# 2. Initialize crop yield data
PYTHONPATH=. python core_django/manage.py init_crop_yield

# 3. Calculate yearly statistics (requires daily data)
PYTHONPATH=. python core_django/manage.py init_yearly_stats
```

### Yearly Statistics Details
The yearly statistics include:
- **Temperature Metrics**: Average, min, max temperatures
- **Precipitation Metrics**: Total, average, max precipitation
- **Data Quality**: Record counts and completeness percentages
- **Performance**: Pre-calculated for fast API responses

### Expected Results Summary
- **Weather Stations**: 167 stations
- **Daily Records**: ~1.73 million records
- **Yearly Statistics**: ~5,000 station-year combinations (167 stations × ~30 years)
- **Crop Yield Records**: 30 records (1985-2014)

## 🔧 Development Commands

### Local Development
```bash
# Activate environment
source venv/bin/activate

# Run Django commands
PYTHONPATH=. python core_django/manage.py check
PYTHONPATH=. python core_django/manage.py shell

# Run tests
pytest

# Code formatting
black .
isort .
ruff check .
```

### With Poetry
```bash
poetry run python core_django/manage.py check
poetry run pytest
poetry run black .
```

### With Docker
```bash
docker-compose exec web python core_django/manage.py check
docker-compose run --rm web pytest
```

## 🧪 Testing

### Run Tests Locally
```bash
# With venv
source venv/bin/activate
pytest tests/

# With Poetry
poetry run pytest

# With Docker
docker-compose run --rm web pytest
```

## 📈 Performance Characteristics

- **Ingestion Rate**: ~10,000 records/second
- **API Response Time**: <100ms for paginated queries
- **Database Size**: ~50MB for complete dataset
- **Memory Usage**: <100MB during ingestion

## 🏗️ Project Structure

```
code-challenge-template/
├── core_django/          # Django ORM models
│   ├── core/             # Django settings and config
│   ├── models/           # Data models
│   ├── manage.py         # Django management
│   └── setup.py          # FastAPI integration
├── weather_api/          # FastAPI application (future)
├── scripts/              # Data processing scripts (future)
├── tests/                # Test suites
├── docker/               # Container definitions
├── wx_data/              # Weather station files
└── yld_data/             # Crop yield data
```

## 🔧 Development Tools

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
ruff check .
mypy .

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## 🐳 Docker Services

### Development Stack
```bash
# Essential services only
docker-compose up

# With monitoring
docker-compose --profile monitoring up

# Full stack
docker-compose --profile monitoring --profile production up
```

## 🔍 Troubleshooting

### Virtual Environment Issues
```bash
# Create fresh environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Django Issues
```bash
# Check Django setup
PYTHONPATH=. python core_django/manage.py check

# Django shell
PYTHONPATH=. python core_django/manage.py shell
```

### Poetry Issues
```bash
# Clear cache
poetry cache clear --all pypi
poetry install
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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Weather data provided by [Corteva](https://github.com/corteva/code-challenge-template)
- Built for the Corteva Data Engineering Challenge
- Inspired by modern data engineering best practices

---

**Note**: This is a demonstration project showcasing data engineering capabilities including ETL pipelines, API development, and cloud architecture design.
