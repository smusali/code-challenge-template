# Weather Data Ingestion - Docker Setup

This directory contains Docker configurations for batch data processing and ingestion tasks.

## 🚀 Quick Start

### 1. Run Complete Data Pipeline

```bash
# Navigate to docker directory
cd docker

# Run full data pipeline (weather data + crop yield + yearly stats)
docker-compose -f docker-compose.ingest.yml up ingest

# Or run in background
docker-compose -f docker-compose.ingest.yml up -d ingest
```

### 2. Initialize Database Step by Step

```bash
# Start database
docker-compose -f docker-compose.ingest.yml up -d postgres

# Run migrations
docker-compose -f docker-compose.ingest.yml --profile setup up migrate

# Initialize weather data
docker-compose -f docker-compose.ingest.yml --profile init up init-weather

# Initialize crop yield data
docker-compose -f docker-compose.ingest.yml --profile init up init-crops

# Calculate yearly statistics
docker-compose -f docker-compose.ingest.yml --profile init up calc-stats
```

### 3. Health Check

```bash
# Check system health
docker-compose -f docker-compose.ingest.yml --profile check up health-check
```

## 📋 Available Commands

### Batch Processing Commands

| Command | Description | Example |
|---------|-------------|---------|
| `weather-data` | Initialize weather station and daily weather data | `docker run weather-ingest weather-data` |
| `crop-yield` | Initialize crop yield data | `docker run weather-ingest crop-yield` |
| `yearly-stats` | Calculate yearly weather statistics | `docker run weather-ingest yearly-stats` |
| `full-pipeline` | Run complete data pipeline | `docker run weather-ingest full-pipeline` |
| `migrate` | Run database migrations | `docker run weather-ingest migrate` |
| `health` | Run system health check | `docker run weather-ingest health` |
| `shell` | Open Django shell | `docker run -it weather-ingest shell` |
| `custom` | Run custom Django management command | `docker run weather-ingest custom collectstatic --noinput` |

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BATCH_SIZE` | Batch size for data processing | 1000 | `BATCH_SIZE=2000` |
| `VERBOSITY` | Django command verbosity level | 1 | `VERBOSITY=2` |
| `CLEAR_DATA` | Clear existing data before import | false | `CLEAR_DATA=true` |
| `TARGET_YEAR` | Process specific year for yearly stats | - | `TARGET_YEAR=2020` |
| `TARGET_STATION` | Process specific station for yearly stats | - | `TARGET_STATION=USC00110072` |

## 🔧 Advanced Usage

### Custom Batch Processing

```bash
# Run with custom settings
docker-compose -f docker-compose.ingest.yml run \
  -e BATCH_SIZE=5000 \
  -e VERBOSITY=2 \
  -e CLEAR_DATA=true \
  ingest weather-data

# Process specific year
docker-compose -f docker-compose.ingest.yml run \
  -e TARGET_YEAR=2020 \
  ingest yearly-stats

# Process specific station
docker-compose -f docker-compose.ingest.yml run \
  -e TARGET_STATION=USC00110072 \
  ingest yearly-stats
```

### Development Mode

```bash
# Run with shell access
docker-compose -f docker-compose.ingest.yml run --rm ingest shell

# Run custom Django commands
docker-compose -f docker-compose.ingest.yml run --rm ingest custom check
docker-compose -f docker-compose.ingest.yml run --rm ingest custom showmigrations
```

### Performance Tuning

```bash
# High-performance ingestion
docker-compose -f docker-compose.ingest.yml run \
  -e BATCH_SIZE=10000 \
  -e OMP_NUM_THREADS=2 \
  -e OPENBLAS_NUM_THREADS=2 \
  --cpus="2.0" \
  --memory="4g" \
  ingest full-pipeline
```

## 📁 Directory Structure

```
docker/
├── Dockerfile.ingest           # Ingestion container definition
├── batch-entrypoint.sh        # Batch processing entrypoint script
├── docker-compose.ingest.yml   # Ingestion docker-compose
├── README.ingest.md           # This documentation
└── init-db.sql               # Database initialization
```

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check if postgres is running
docker-compose -f docker-compose.ingest.yml ps postgres

# Check database logs
docker-compose -f docker-compose.ingest.yml logs postgres

# Wait for database to be ready
docker-compose -f docker-compose.ingest.yml up -d postgres
sleep 10
```

#### Out of Memory Error
```bash
# Reduce batch size
docker-compose -f docker-compose.ingest.yml run \
  -e BATCH_SIZE=500 \
  ingest weather-data

# Increase container memory
docker-compose -f docker-compose.ingest.yml run \
  --memory="2g" \
  ingest weather-data
```

#### Permission Errors
```bash
# Check file permissions
ls -la ../wx_data/
ls -la ../yld_data/

# Fix permissions if needed
chmod -R 755 ../wx_data/ ../yld_data/
```

### Debugging

```bash
# Run with verbose output
docker-compose -f docker-compose.ingest.yml run \
  -e VERBOSITY=2 \
  ingest weather-data

# Check container logs
docker-compose -f docker-compose.ingest.yml logs ingest

# Interactive debugging
docker-compose -f docker-compose.ingest.yml run --rm ingest shell
```

## 🎯 Production Deployment

### Kubernetes Deployment

```yaml
# Example Kubernetes Job
apiVersion: batch/v1
kind: Job
metadata:
  name: weather-data-ingest
spec:
  template:
    spec:
      containers:
      - name: ingest
        image: weather-api:ingest
        command: ["/usr/local/bin/batch-entrypoint.sh"]
        args: ["full-pipeline"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: weather-db-secret
              key: database-url
        - name: BATCH_SIZE
          value: "2000"
        - name: VERBOSITY
          value: "2"
      restartPolicy: Never
```

### AWS Batch

```bash
# Build and push to ECR
docker build -f docker/Dockerfile.ingest -t weather-ingest .
docker tag weather-ingest:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/weather-ingest:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/weather-ingest:latest

# Submit job to AWS Batch
aws batch submit-job \
  --job-name weather-data-ingest \
  --job-queue weather-ingest-queue \
  --job-definition weather-ingest-job \
  --parameters command=full-pipeline,batchSize=2000
```

## 📊 Performance Metrics

### Expected Processing Times

| Task | Records | Time (approx) | Memory Usage |
|------|---------|---------------|--------------|
| Weather Data | 1.73M | 2-5 minutes | 200-500MB |
| Crop Yield | 30 | <1 minute | 50MB |
| Yearly Stats | 5K | 1-2 minutes | 100-200MB |
| Full Pipeline | All | 3-8 minutes | 500MB-1GB |

### Optimization Tips

1. **Increase batch size** for faster processing (up to 10,000)
2. **Use SSD storage** for data files
3. **Allocate sufficient memory** (2-4GB recommended)
4. **Use dedicated database** for production workloads
5. **Enable connection pooling** for database connections

---

*For more information, see the main project README.md*
