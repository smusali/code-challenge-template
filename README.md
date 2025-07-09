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

### System Architecture Diagram

```mermaid
graph TB
    subgraph "External"
        Users[Users/Clients]
        Internet[Internet]
    end

    subgraph "AWS Cloud"
        subgraph "Public Subnets"
            ALB[Application Load Balancer]
            NAT[NAT Gateway]
        end

        subgraph "Private Subnets"
            ECS[ECS Fargate<br/>Weather API]
            RDS[(PostgreSQL RDS<br/>Weather Database)]
        end

        subgraph "Container Registry"
            ECR[Amazon ECR<br/>Docker Images]
        end

        subgraph "Storage & Data"
            S3[S3 Buckets<br/>Data Storage & Logs]
        end

        subgraph "Monitoring & Logging"
            CW[CloudWatch<br/>Metrics & Logs]
            SNS[SNS Topics<br/>Alerts]
        end

        subgraph "Networking"
            VPC[VPC - 10.0.0.0/16]
            IGW[Internet Gateway]
        end
    end

    %% External connections
    Users --> Internet
    Internet --> IGW
    IGW --> ALB

    %% Load balancer to application
    ALB --> ECS

    %% Application to database
    ECS --> RDS

    %% Container registry
    ECR --> ECS

    %% Storage connections
    ECS --> S3

    %% Monitoring connections
    ECS --> CW
    ALB --> CW
    RDS --> CW
    CW --> SNS

    %% Network routing
    ECS --> NAT
    NAT --> IGW

    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef database fill:#3F48CC,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef compute fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef storage fill:#569A31,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef network fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef external fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#FFFFFF

    class ALB,ECS,ECR,CW,SNS aws
    class RDS database
    class S3 storage
    class VPC,IGW,NAT network
    class Users,Internet external
```

### Data Flow

1. **External Access**: Users access the API through the internet via the Application Load Balancer
2. **Load Balancing**: ALB distributes traffic across ECS Fargate containers in private subnets
3. **API Processing**: ECS containers process requests using the FastAPI framework
4. **Data Access**: Application queries PostgreSQL RDS for weather data and statistics
5. **File Storage**: Raw data files and logs are stored in S3 buckets
6. **Container Management**: Docker images are stored and managed in Amazon ECR
7. **Monitoring**: CloudWatch collects metrics and logs from all components
8. **Alerting**: SNS sends notifications based on CloudWatch alarms
9. **Network Security**: Private subnets protect backend services, NAT Gateway enables outbound internet access

### Data Models

- `WeatherStation`: Station metadata and geographic information
- `DailyWeather`: Raw weather observations with temperature and precipitation
- `YearlyWeatherStats`: Pre-calculated yearly statistics with temperature and precipitation aggregates
- `CropYield`: Historical crop yield data (1985-2014) for agricultural correlation analysis

### Technology Stack

- **Cloud Platform**: Amazon Web Services (AWS)
- **Infrastructure**: Terraform for Infrastructure as Code
- **Compute**: ECS Fargate for serverless containers
- **Database**: PostgreSQL RDS with optimized indexing strategy
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **ORM**: Django ORM for robust data modeling
- **Containerization**: Docker with multi-stage builds
- **Monitoring**: CloudWatch for metrics, logging, and alerting
- **Storage**: S3 for object storage and data archival
- **Load Balancing**: Application Load Balancer with health checks
- **Networking**: VPC with public/private subnets across multiple AZs

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (3.11 recommended for best compatibility)
- **PostgreSQL 15+** (optional: Docker for full stack development)
- **Git** (for version control)
- **IDE/Editor** (VS Code, PyCharm, or similar)

### Local Development Setup

#### 1. Repository Setup

```bash
# Clone the repository
git clone https://github.com/smusali/weather-data-engineering-api.git
cd weather-data-engineering-api

# Verify Python version
python --version  # Should be 3.11+
```

#### 2. Virtual Environment Setup

**Option A: Using venv (Recommended)**
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Verify activation (should show project path)
which python
```

**Option B: Using conda**
```bash
# Create conda environment
conda create -n weather-api python=3.11
conda activate weather-api
```

#### 3. Dependencies Installation

```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest pytest-cov black isort ruff mypy pre-commit
```

#### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or your preferred editor
```

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/weather_db  # pragma: allowlist secret
DJANGO_SETTINGS_MODULE=core_django.core.settings

# Development Settings
DEBUG=True
TESTING=False

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# Logging
LOG_LEVEL=INFO
```

#### 5. Database Setup

**Option A: Local PostgreSQL**
```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# Create database and user
psql postgres
CREATE DATABASE weather_db;
CREATE USER weather_user WITH PASSWORD 'your_password';  # pragma: allowlist secret
GRANT ALL PRIVILEGES ON DATABASE weather_db TO weather_user;
\q
```

**Option B: Docker PostgreSQL**
```bash
# Start PostgreSQL container
docker run -d \
  --name weather-postgres \
  -e POSTGRES_DB=weather_db \
  -e POSTGRES_USER=weather_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:15

# Verify container is running
docker ps
```

#### 6. Django Setup and Verification

```bash
# Test Django configuration
PYTHONPATH=. python core_django/manage.py check

# Run Django migrations (if any)
PYTHONPATH=. python core_django/manage.py migrate

# Test database connection
PYTHONPATH=. python core_django/manage.py shell
# In shell: from django.db import connection; connection.ensure_connection()
```

### Development Workflow

#### 1. Data Initialization

```bash
# Initialize with sample data (quick start)
PYTHONPATH=. python core_django/manage.py init_weather_data --batch-size=100

# Or full data initialization (takes 2-5 minutes)
PYTHONPATH=. python core_django/manage.py init_weather_data
PYTHONPATH=. python core_django/manage.py init_crop_yield
PYTHONPATH=. python core_django/manage.py init_yearly_stats
```

#### 2. Running the API Server

```bash
# Activate virtual environment first
source venv/bin/activate

# Start the development server
cd core_django
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

#### 3. Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test modules
python run_tests.py --module health
python run_tests.py --module weather

# Run with coverage
python run_tests.py --coverage

# Run performance tests
python run_tests.py --performance
```

#### 4. Code Quality Checks

```bash
# Format code
black .
isort .

# Lint code
ruff check .
ruff check . --fix  # Auto-fix issues

# Type checking
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### IDE Configuration

#### VS Code Setup

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

Create `.vscode/launch.json` for debugging:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "program": "-m",
      "args": ["uvicorn", "src.main:app", "--reload"],
      "cwd": "${workspaceFolder}/core_django",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Django Shell",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/core_django/manage.py",
      "args": ["shell"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

#### PyCharm Setup

1. **Interpreter**: Point to `./venv/bin/python`
2. **Django Support**: Enable Django support, set Django project root to `core_django`
3. **Code Style**: Import settings from `.editorconfig`
4. **Run Configurations**:
   - FastAPI: `uvicorn src.main:app --reload`
   - Django: `manage.py shell`

### Development Best Practices

#### 1. Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

#### 2. Testing Workflow

```bash
# Before committing, always run:
python run_tests.py --smoke     # Quick smoke tests
black . && isort .              # Format code
ruff check . --fix              # Fix linting issues
python run_tests.py --coverage  # Full test suite
```

#### 3. Database Development

```bash
# Create Django migrations
PYTHONPATH=. python core_django/manage.py makemigrations

# Apply migrations
PYTHONPATH=. python core_django/manage.py migrate

# Access database shell
PYTHONPATH=. python core_django/manage.py dbshell

# Django shell for model testing
PYTHONPATH=. python core_django/manage.py shell
```

### Common Development Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError` when running scripts
```bash
# Solution: Always set PYTHONPATH
PYTHONPATH=. python core_django/manage.py command
```

#### 2. Database Connection Issues

**Problem**: `connection refused` or authentication errors
```bash
# Check PostgreSQL status
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Test connection manually
psql -h localhost -U weather_user -d weather_db

# Reset connection in Django shell
PYTHONPATH=. python core_django/manage.py shell
>>> from django.db import connection
>>> connection.close()
>>> connection.ensure_connection()
```

#### 3. Virtual Environment Issues

**Problem**: Wrong Python version or missing packages
```bash
# Recreate virtual environment
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Port Already in Use

**Problem**: `Address already in use` error
```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
kill -9 $(lsof -ti:8000)

# Or use different port
uvicorn src.main:app --reload --port 8001
```

#### 5. Data Initialization Fails

**Problem**: Database constraints or data format issues
```bash
# Clear and restart
PYTHONPATH=. python core_django/manage.py init_weather_data --clear --dry-run
PYTHONPATH=. python core_django/manage.py init_weather_data --clear

# Check data files exist
ls -la wx_data/
ls -la yld_data/
```

### Development Tools & Utilities

#### 1. Database Management

```bash
# Backup database
pg_dump weather_db > backup.sql

# Restore database
psql weather_db < backup.sql

# Reset database
PYTHONPATH=. python core_django/manage.py flush
```

#### 2. Performance Monitoring

```bash
# Monitor API performance
python run_tests.py --performance

# Database query analysis
PYTHONPATH=. python core_django/manage.py shell
>>> from django.db import connection
>>> connection.queries  # View recent queries
```

#### 3. API Testing

```bash
# Test endpoints manually
curl http://localhost:8000/health
curl http://localhost:8000/api/v2/weather-stations?page_size=5

# Interactive API docs
open http://localhost:8000/docs
```

### Quick Development Commands

```bash
# Daily development routine
source venv/bin/activate              # Activate environment
cd core_django && uvicorn src.main:app --reload &  # Start server
python run_tests.py --smoke           # Quick test
```

### Using Poetry (Alternative Approach)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Initialize project
poetry install

# Activate shell
poetry shell

# Run commands
poetry run python core_django/manage.py check
poetry run uvicorn src.main:app --reload
poetry run pytest
```

### Using Docker (Full Stack)

For a complete containerized development environment:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands in container
docker-compose exec web python core_django/manage.py check
docker-compose exec web python run_tests.py --smoke

# Stop services
docker-compose down
```

### Environment Configuration Template

Create a `.env.example` file in your project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://weather_user:your_password@localhost:5432/weather_db  # pragma: allowlist secret

# Django Settings
DJANGO_SETTINGS_MODULE=core_django.core.settings
SECRET_KEY=your-secret-key-here  # pragma: allowlist secret

# Development Settings
DEBUG=True
TESTING=False

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=verbose

# Performance Settings
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
API_WORKERS=1

# Security Settings (Development Only)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Optional: External Services
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
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
weather-data-engineering-api/
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
