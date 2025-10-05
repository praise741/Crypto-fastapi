FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for Prophet and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data /app/logs /app/alembic/versions

# Make scripts executable
RUN chmod +x scripts/run-migrations.sh 2>/dev/null || true

# Create non-root user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser

# Change ownership of app directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
ENV PORT=8000
EXPOSE 8000

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
    print('Health check passed:', response.status_code)
    sys.exit(0 if response.status_code == 200 else 1)
except Exception as e:
    print('Health check failed:', str(e))
    sys.exit(1)
" || exit 1

# Run database migrations first, then start the application
CMD /bin/bash -c "
echo '🚀 Starting Market Matrix...'
echo '📊 Running database migrations...'
python scripts/run-migrations.sh || echo '⚠️ Migration script failed, continuing anyway...'
echo '🌐 Starting FastAPI application...'
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
"
