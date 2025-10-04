# 🔧 Redis and Docker Setup Explained

## Redis Configuration

### Yes, You're Using Redis Locally (in Docker)

Your application uses **Redis as a caching layer** to improve performance and reduce API calls to free services.

### How Redis is Configured

**1. In Development (Local)**:
```bash
# .env.sample
REDIS_URL=redis://localhost:6379/0
```
- Redis runs on your local machine
- Port 6379 (default Redis port)
- Database 0

**2. In Production (Docker)**:
```bash
# docker-compose.yml
REDIS_URL=redis://redis:6379/0
```
- Redis runs in a Docker container named `redis`
- Containers communicate via Docker network
- `redis` is the hostname (Docker DNS resolves it)

### Redis Configuration in docker-compose.yml

```yaml
redis:
  image: redis:7-alpine              # Lightweight Redis image
  container_name: marketmatrix-redis
  restart: unless-stopped            # Auto-restart on failure
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"                    # Expose port (optional)
  volumes:
    - redis_data:/data               # Persist data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Command breakdown**:
- `--appendonly yes`: Enable persistence (save data to disk)
- `--maxmemory 256mb`: Limit Redis memory to 256MB
- `--maxmemory-policy allkeys-lru`: When full, remove least recently used keys

### What Redis Caches

Your application caches:

| Data | Cache Key | Duration |
|------|-----------|----------|
| Market prices | `market_prices` | 30 seconds |
| Token health | `token_health:BTC` | 10 minutes |
| Predictions | `predictions:BTC:24h` | 1 hour |
| Dashboard data | `dashboard` | 1 minute |
| OHLCV data | `ohlcv:BTC:1h:100` | 5 minutes |

### How Caching Works

**File**: `app/core/cache.py`

```python
import redis
import pickle

redis_client = redis.from_url(settings.REDIS_URL)

def cache_result(key: str, ttl: int, loader_func):
    # Try to get from cache
    cached = redis_client.get(key)
    
    if cached:
        # Cache hit - return immediately
        return pickle.loads(cached)
    
    # Cache miss - call function
    result = loader_func()
    
    # Store in cache with TTL
    redis_client.setex(key, ttl, pickle.dumps(result))
    
    return result
```

**Example usage**:
```python
def get_cached_prices(db: Session):
    cache_key = "market_prices"
    
    def _loader():
        # Call CoinGecko API
        return fetch_prices_from_coingecko()
    
    # Cache for 30 seconds
    return cache_result(cache_key, 30, _loader)
```

---

## Docker Setup Explained

### What Docker Does

Docker packages your application with all dependencies into **containers**:
- **Backend container**: Python + FastAPI + Prophet
- **PostgreSQL container**: Database
- **Redis container**: Cache
- **Frontend container** (optional): Next.js

### Why Docker?

**Benefits**:
1. **Consistency**: Same environment everywhere (dev, staging, prod)
2. **Isolation**: Each service in its own container
3. **Easy deployment**: One command to start everything
4. **Scalability**: Easy to add more containers
5. **Portability**: Works on any server with Docker

### Docker Compose Architecture

```
┌─────────────────────────────────────────────────┐
│                Docker Network                    │
│  (marketmatrix-network)                         │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   Backend    │  │  PostgreSQL  │            │
│  │   (FastAPI)  │◄─┤  (Database)  │            │
│  │   Port 8000  │  │   Port 5432  │            │
│  └──────┬───────┘  └──────────────┘            │
│         │                                        │
│         │          ┌──────────────┐            │
│         └─────────►│    Redis     │            │
│                    │   (Cache)    │            │
│                    │   Port 6379  │            │
│                    └──────────────┘            │
│                                                  │
└─────────────────────────────────────────────────┘
         │
         │ Nginx Reverse Proxy
         ▼
    Internet (Port 80/443)
```

### Updated Dockerfile Explained

```dockerfile
FROM python:3.11-slim
# Base image: Python 3.11 (lightweight)

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Prevent Python from writing .pyc files
# Ensure Python output is sent straight to terminal

WORKDIR /app
# Set working directory

# Install system dependencies for Prophet
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Prophet needs C++ compiler

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# Install Python dependencies

COPY . .
# Copy application code

RUN mkdir -p /app/data
# Create directory for SQLite (if used)

EXPOSE 8000
# Expose port 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1
# Docker will check if app is healthy

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
# Start FastAPI with 2 workers
```

### Updated docker-compose.yml Explained

**Backend Service**:
```yaml
backend:
  build: .                          # Build from Dockerfile
  container_name: marketmatrix-backend
  restart: unless-stopped           # Auto-restart on crash
  ports:
    - "8000:8000"                   # Map port 8000
  environment:
    - DATABASE_URL=postgresql+psycopg2://marketmatrix:${DB_PASSWORD}@postgres:5432/marketmatrix
    - REDIS_URL=redis://redis:6379/0
    # ... more env vars
  depends_on:
    postgres:
      condition: service_healthy    # Wait for DB to be ready
    redis:
      condition: service_healthy    # Wait for Redis to be ready
  networks:
    - marketmatrix-network          # Join network
```

**PostgreSQL Service**:
```yaml
postgres:
  image: postgres:15-alpine         # Official PostgreSQL image
  container_name: marketmatrix-postgres
  restart: unless-stopped
  environment:
    POSTGRES_USER: marketmatrix
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_DB: marketmatrix
  volumes:
    - postgres_data:/var/lib/postgresql/data  # Persist data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U marketmatrix"]
    interval: 10s
```

**Redis Service**:
```yaml
redis:
  image: redis:7-alpine             # Official Redis image
  container_name: marketmatrix-redis
  restart: unless-stopped
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data              # Persist cache
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

**Volumes** (Data Persistence):
```yaml
volumes:
  postgres_data:    # Database data survives container restarts
  redis_data:       # Cache data survives container restarts
```

**Networks**:
```yaml
networks:
  marketmatrix-network:
    driver: bridge  # Containers can talk to each other
```

---

## Environment Variables Flow

### Development (.env.sample)
```bash
DATABASE_URL=sqlite:///./crypto.db    # Local SQLite
REDIS_URL=redis://localhost:6379/0    # Local Redis
```

### Production (.env)
```bash
DATABASE_URL=postgresql+psycopg2://marketmatrix:${DB_PASSWORD}@postgres:5432/marketmatrix
REDIS_URL=redis://redis:6379/0
```

**Note**: In Docker, `postgres` and `redis` are hostnames that Docker DNS resolves to the container IPs.

---

## Deployment Flow on Ubuntu VPS

### Step-by-step what happens:

1. **Clone repository** to VPS
   ```bash
   git clone your-repo
   cd Crypto-fastapi
   ```

2. **Create .env file**
   ```bash
   cp .env.production .env
   nano .env  # Edit passwords and secrets
   ```

3. **Build Docker images**
   ```bash
   docker-compose build
   ```
   - Downloads base images (Python, PostgreSQL, Redis)
   - Installs dependencies (Prophet, FastAPI, etc.)
   - Creates custom backend image

4. **Start containers**
   ```bash
   docker-compose up -d
   ```
   - Starts PostgreSQL container
   - Starts Redis container
   - Waits for them to be healthy
   - Starts backend container
   - Backend connects to PostgreSQL and Redis

5. **Verify services**
   ```bash
   docker-compose ps
   ```
   - All services should show "Up"

6. **Test API**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

7. **Setup Nginx** (reverse proxy)
   - Routes external traffic to backend container
   - Handles SSL/HTTPS

8. **Setup SSL** (Let's Encrypt)
   - Free SSL certificate
   - Auto-renewal

---

## Quick Commands Reference

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# Check status
docker-compose ps

# Rebuild and restart
docker-compose up -d --build

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Docker

```bash
# List running containers
docker ps

# View container logs
docker logs marketmatrix-backend

# Execute command in container
docker exec -it marketmatrix-backend bash

# View container stats
docker stats

# Clean up unused images/containers
docker system prune -a
```

### Redis

```bash
# Connect to Redis CLI
docker exec -it marketmatrix-redis redis-cli

# Inside Redis CLI:
PING                    # Test connection
KEYS *                  # List all keys
GET market_prices       # Get cached value
TTL market_prices       # Check time to live
FLUSHALL                # Clear all cache (careful!)
INFO memory             # Check memory usage
```

### PostgreSQL

```bash
# Connect to database
docker exec -it marketmatrix-postgres psql -U marketmatrix -d marketmatrix

# Inside psql:
\dt                     # List tables
\d+ market_data         # Describe table
SELECT COUNT(*) FROM market_data;
\q                      # Quit
```

---

## Monitoring Redis

### Check Redis memory usage

```bash
docker exec -it marketmatrix-redis redis-cli INFO memory
```

### Check cached keys

```bash
docker exec -it marketmatrix-redis redis-cli KEYS "*"
```

### Clear specific cache

```bash
# Clear market prices cache
docker exec -it marketmatrix-redis redis-cli DEL market_prices

# Clear all token health caches
docker exec -it marketmatrix-redis redis-cli --scan --pattern "token_health:*" | xargs docker exec -i marketmatrix-redis redis-cli DEL
```

---

## Troubleshooting

### Redis connection refused

```bash
# Check if Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Test connection
docker exec -it marketmatrix-redis redis-cli ping
```

### Backend can't connect to Redis

```bash
# Check environment variable
docker exec marketmatrix-backend env | grep REDIS_URL

# Should show: REDIS_URL=redis://redis:6379/0

# Test connection from backend
docker exec -it marketmatrix-backend python -c "from app.core.redis import get_redis_client; print(get_redis_client().ping())"
```

### Cache not working

```bash
# Check if Redis is accepting connections
docker exec -it marketmatrix-redis redis-cli ping

# Check cache keys
docker exec -it marketmatrix-redis redis-cli KEYS "*"

# Monitor Redis in real-time
docker exec -it marketmatrix-redis redis-cli MONITOR
```

---

## Summary

### Redis Setup
- ✅ Redis runs in Docker container
- ✅ Caches API responses to reduce external calls
- ✅ Configured with 256MB memory limit
- ✅ Data persists across restarts
- ✅ Automatic eviction of old keys (LRU policy)

### Docker Setup
- ✅ Backend, PostgreSQL, and Redis in separate containers
- ✅ Containers communicate via Docker network
- ✅ Data persists in Docker volumes
- ✅ Auto-restart on failure
- ✅ Health checks ensure services are ready
- ✅ One command deployment: `docker-compose up -d`

### Cost
- ✅ Redis: $0 (runs in Docker)
- ✅ PostgreSQL: $0 (runs in Docker)
- ✅ Docker: $0 (free and open source)
- ✅ VPS: $5-10/month (DigitalOcean, Hetzner, etc.)

**Total: $5-10/month for entire production setup!** 🎉
