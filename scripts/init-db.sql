-- Market Matrix Database Initialization Script
-- This script is executed when PostgreSQL container starts

-- Create extensions needed for the application
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional indexes for better performance
-- These will be created by Alembic migrations, but we add basic ones here

-- Create a simple test table to verify database connection
CREATE TABLE IF NOT EXISTS health_check (
    id SERIAL PRIMARY KEY,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'healthy'
);

-- Insert initial health check
INSERT INTO health_check (status) VALUES ('database_initialized') ON CONFLICT DO NOTHING;

-- Grant permissions to the marketmatrix user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO marketmatrix;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO marketmatrix;