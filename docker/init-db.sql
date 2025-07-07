-- Database initialization for Weather Data Engineering API
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions for enhanced functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for better performance (will be created properly by Django migrations)
-- This is just for initial setup

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create application-specific database settings
ALTER DATABASE weather_db SET log_statement = 'all';
ALTER DATABASE weather_db SET log_min_duration_statement = 1000;

-- Create read-only user for analytics/reporting
CREATE USER weather_reader WITH PASSWORD 'reader_pass';
GRANT CONNECT ON DATABASE weather_db TO weather_reader;
GRANT USAGE ON SCHEMA public TO weather_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO weather_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO weather_reader;

-- Create table for application metadata
CREATE TABLE IF NOT EXISTS app_metadata (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial metadata
INSERT INTO app_metadata (key, value) VALUES
    ('db_version', '1.0.0'),
    ('initialized_at', CURRENT_TIMESTAMP::text),
    ('schema_version', '1.0.0')
ON CONFLICT (key) DO NOTHING;

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Log successful initialization
INSERT INTO app_metadata (key, value) VALUES
    ('last_initialization', CURRENT_TIMESTAMP::text)
ON CONFLICT (key) DO UPDATE SET 
    value = CURRENT_TIMESTAMP::text,
    updated_at = CURRENT_TIMESTAMP; 
