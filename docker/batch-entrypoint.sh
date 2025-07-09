#!/bin/bash
set -e

# Batch Entrypoint Script for Weather Data Engineering API
# Handles various data ingestion and processing tasks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARN $(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS $(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to wait for database
wait_for_db() {
    log "Waiting for database connection..."

    until python -c "
import django
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
    "; do
        warn "Database is not ready yet. Waiting 5 seconds..."
        sleep 5
    done

    success "Database is ready!"
}

# Function to run Django management commands safely
run_django_command() {
    local command="$1"
    shift
    local args=("$@")

    log "Running Django command: $command ${args[*]}"

    cd /app/core_django
    if python manage.py "$command" "${args[@]}"; then
        success "Command '$command' completed successfully"
        return 0
    else
        error "Command '$command' failed"
        return 1
    fi
}

# Function to initialize weather data
init_weather_data() {
    log "Starting weather data initialization..."

    local batch_size="${BATCH_SIZE:-1000}"
    local verbosity="${VERBOSITY:-1}"
    local clear_flag=""

    if [ "${CLEAR_DATA:-false}" == "true" ]; then
        clear_flag="--clear"
        warn "Will clear existing data before import"
    fi

    run_django_command "init_weather_data" \
        --batch-size="$batch_size" \
        --verbosity="$verbosity" \
        $clear_flag
}

# Function to initialize crop yield data
init_crop_yield() {
    log "Starting crop yield data initialization..."

    local verbosity="${VERBOSITY:-1}"
    local clear_flag=""

    if [ "${CLEAR_DATA:-false}" == "true" ]; then
        clear_flag="--clear"
        warn "Will clear existing crop yield data before import"
    fi

    run_django_command "init_crop_yield" \
        --verbosity="$verbosity" \
        $clear_flag
}

# Function to calculate yearly statistics
init_yearly_stats() {
    log "Starting yearly statistics calculation..."

    local batch_size="${BATCH_SIZE:-200}"
    local verbosity="${VERBOSITY:-1}"
    local clear_flag=""
    local year_flag=""
    local station_flag=""

    if [ "${CLEAR_DATA:-false}" == "true" ]; then
        clear_flag="--clear"
        warn "Will clear existing yearly statistics before calculation"
    fi

    if [ -n "${TARGET_YEAR}" ]; then
        year_flag="--year=$TARGET_YEAR"
        log "Processing specific year: $TARGET_YEAR"
    fi

    if [ -n "${TARGET_STATION}" ]; then
        station_flag="--station=$TARGET_STATION"
        log "Processing specific station: $TARGET_STATION"
    fi

    run_django_command "init_yearly_stats" \
        --batch-size="$batch_size" \
        --verbosity="$verbosity" \
        $clear_flag \
        "$year_flag" \
        "$station_flag"
}

# Function to run complete data pipeline
full_pipeline() {
    log "Starting complete data pipeline..."

    if init_weather_data; then
        if init_crop_yield; then
            if init_yearly_stats; then
                success "Complete data pipeline finished successfully!"
            else
                error "Yearly statistics calculation failed"
                return 1
            fi
        else
            error "Crop yield initialization failed"
            return 1
        fi
    else
        error "Weather data initialization failed"
        return 1
    fi
}

# Function to run database migrations
migrate() {
    log "Running database migrations..."
    run_django_command "migrate"
}

# Function to check system health
health_check() {
    log "Running system health check..."

    # Check Django configuration
    if run_django_command "check"; then
        success "Django configuration is valid"
    else
        error "Django configuration check failed"
        return 1
    fi

    # Check database connection
    wait_for_db

    # Check data directories
    if [ -d "/app/wx_data" ] && [ "$(ls -A /app/wx_data)" ]; then
        success "Weather data directory exists and contains files"
    else
        warn "Weather data directory is empty or missing"
    fi

    if [ -d "/app/yld_data" ] && [ "$(ls -A /app/yld_data)" ]; then
        success "Crop yield data directory exists and contains files"
    else
        warn "Crop yield data directory is empty or missing"
    fi

    success "Health check completed"
}

# Function to show usage
show_usage() {
    echo "Weather Data Engineering API - Batch Processing"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  weather-data     Initialize weather station and daily weather data"
    echo "  crop-yield       Initialize crop yield data"
    echo "  yearly-stats     Calculate yearly weather statistics"
    echo "  full-pipeline    Run complete data pipeline (all above commands)"
    echo "  migrate          Run database migrations"
    echo "  health           Run system health check"
    echo "  shell            Open Django shell"
    echo "  custom           Run custom Django management command"
    echo ""
    echo "Environment Variables:"
    echo "  BATCH_SIZE       Batch size for data processing (default: 1000)"
    echo "  VERBOSITY        Django command verbosity level (default: 1)"
    echo "  CLEAR_DATA       Clear existing data before import (default: false)"
    echo "  TARGET_YEAR      Process specific year for yearly stats"
    echo "  TARGET_STATION   Process specific station for yearly stats"
    echo ""
    echo "Examples:"
    echo "  $0 weather-data"
    echo "  BATCH_SIZE=2000 CLEAR_DATA=true $0 full-pipeline"
    echo "  TARGET_YEAR=2020 $0 yearly-stats"
    echo "  $0 custom collectstatic --noinput"
}

# Main script logic
main() {
    log "Starting batch processing entrypoint..."

    # Wait for database to be ready
    wait_for_db

    # Parse command
    case "${1:-weather-data}" in
        "weather-data")
            init_weather_data
            ;;
        "crop-yield")
            init_crop_yield
            ;;
        "yearly-stats")
            init_yearly_stats
            ;;
        "full-pipeline")
            full_pipeline
            ;;
        "migrate")
            migrate
            ;;
        "health")
            health_check
            ;;
        "shell")
            log "Opening Django shell..."
            cd /app/core_django
            python manage.py shell
            ;;
        "custom")
            shift
            if [ $# -eq 0 ]; then
                error "Custom command requires arguments"
                show_usage
                exit 1
            fi
            run_django_command "$@"
            ;;
        "--help"|"-h"|"help")
            show_usage
            ;;
        *)
            error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        success "Batch processing completed successfully"
    else
        error "Batch processing failed with exit code $exit_code"
    fi

    exit $exit_code
}

# Trap signals for graceful shutdown
trap 'error "Received interrupt signal, shutting down..."; exit 130' INT TERM

# Run main function
main "$@"
