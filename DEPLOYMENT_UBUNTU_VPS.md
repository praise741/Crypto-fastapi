# 🚀 Ubuntu VPS Deployment Guide

Complete guide to deploy Market Matrix on your Ubuntu VPS using Docker.

---

## 📋 Prerequisites

- Ubuntu 20.04+ VPS
- At least 2GB RAM
- 20GB storage
- Root or sudo access
- Domain name (optional but recommended)

---

## 🔧 Step 1: Initial VPS Setup

### Connect to your VPS

```bash
ssh root@your-vps-ip
```

### Update system

```bash
apt update && apt upgrade -y
```

### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start Docker
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
```

### Install Docker Compose

```bash
# Download Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Install Git

```bash
apt install git -y
```

---

## 📦 Step 2: Clone Your Repository

```bash
# Navigate to home directory
cd /root

# Clone your repository
git clone https://github.com/yourusername/Crypto-fastapi.git

# Or if you're uploading files manually:
mkdir -p /root/Crypto-fastapi
cd /root/Crypto-fastapi
```

---

## 🔐 Step 3: Configure Environment Variables

### Create production environment file

```bash
cd /root/Crypto-fastapi

# Copy the production template
cp .env.production .env

# Edit with nano
nano .env
```

### Update these values in .env:

```bash
# IMPORTANT: Change these passwords!
DB_PASSWORD=YourSecurePassword123!

# IMPORTANT: Change these secrets (use random strings)
JWT_SECRET=your-random-32-character-string-here
SECRET_KEY=another-random-32-character-string

# Optional: Add API keys if you have them
COINGECKO_API_KEY=
BINANCE_API_KEY=

# Your domain (if you have one)
DOMAIN=yourdomain.com
```

**Generate secure secrets:**
```bash
# Generate random secrets
openssl rand -hex 32
openssl rand -hex 32
```

Save and exit (Ctrl+X, then Y, then Enter)

---

## 🐳 Step 4: Build and Start Services

### Build Docker images

```bash
cd /root/Crypto-fastapi

# Build the images
docker-compose build
```

### Start all services

```bash
# Start in detached mode
docker-compose up -d
```

### Verify services are running

```bash
# Check status
docker-compose ps

# Should show:
# marketmatrix-backend    running
# marketmatrix-postgres   running
# marketmatrix-redis      running
```

### Check logs

```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend
```

---

## ✅ Step 5: Test the API

### Test from VPS

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Market prices
curl http://localhost:8000/api/v1/market/prices

# Token health
curl http://localhost:8000/api/v1/token-health/BTC

# Dashboard
curl http://localhost:8000/api/v1/dashboard
```

### Test from your computer

```bash
# Replace YOUR_VPS_IP with your actual IP
curl http://YOUR_VPS_IP:8000/api/v1/health
```

---

## 🌐 Step 6: Setup Nginx (Reverse Proxy)

### Install Nginx

```bash
apt install nginx -y
```

### Create Nginx configuration

```bash
nano /etc/nginx/sites-available/marketmatrix
```

### Add this configuration:

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;  # Change this to your domain or IP

    # Increase timeouts for Prophet predictions
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Enable the site

```bash
# Create symbolic link
ln -s /etc/nginx/sites-available/marketmatrix /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

---

## 🔒 Step 7: Setup SSL (Let's Encrypt)

### Install Certbot

```bash
apt install certbot python3-certbot-nginx -y
```

### Get SSL certificate

```bash
# Replace with your domain
certbot --nginx -d api.yourdomain.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (option 2)
```

### Auto-renewal

```bash
# Test renewal
certbot renew --dry-run

# Certbot automatically sets up a cron job for renewal
```

---

## 🔥 Step 8: Configure Firewall

```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

---

## 📊 Step 9: Monitoring and Maintenance

### View logs

```bash
# Real-time logs
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Check resource usage

```bash
# Docker stats
docker stats

# System resources
htop  # Install with: apt install htop
```

### Restart services

```bash
# Restart all services
docker-compose restart

# Restart backend only
docker-compose restart backend

# Restart with rebuild
docker-compose down
docker-compose up -d --build
```

### Update application

```bash
cd /root/Crypto-fastapi

# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

---

## 🗄️ Step 10: Database Management

### Backup database

```bash
# Create backup directory
mkdir -p /root/backups

# Backup PostgreSQL
docker exec marketmatrix-postgres pg_dump -U marketmatrix marketmatrix > /root/backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore database

```bash
# Restore from backup
docker exec -i marketmatrix-postgres psql -U marketmatrix marketmatrix < /root/backups/backup_20240104_120000.sql
```

### Access database

```bash
# Connect to PostgreSQL
docker exec -it marketmatrix-postgres psql -U marketmatrix -d marketmatrix

# Common commands:
# \dt          - List tables
# \d+ table    - Describe table
# SELECT * FROM market_data LIMIT 10;
# \q           - Quit
```

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready - wait 30 seconds and restart
# 2. Port already in use - check: netstat -tulpn | grep 8000
# 3. Environment variables - check .env file
```

### Redis connection error

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis
docker exec -it marketmatrix-redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
```

### PostgreSQL connection error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker exec -it marketmatrix-postgres psql -U marketmatrix -d marketmatrix -c "SELECT 1;"
```

### Out of memory

```bash
# Check memory usage
free -h

# Restart services to free memory
docker-compose restart

# If persistent, upgrade VPS RAM
```

### Disk space full

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Remove old logs
truncate -s 0 /var/log/nginx/access.log
truncate -s 0 /var/log/nginx/error.log
```

---

## 📈 Performance Optimization

### Increase workers (if you have 4GB+ RAM)

Edit `docker-compose.yml`:
```yaml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Increase Redis memory

Edit `docker-compose.yml`:
```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Enable Nginx caching

Add to Nginx config:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location / {
    proxy_cache api_cache;
    proxy_cache_valid 200 30s;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    # ... rest of proxy settings
}
```

---

## 🔄 Automatic Backups

### Create backup script

```bash
nano /root/backup.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec marketmatrix-postgres pg_dump -U marketmatrix marketmatrix > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable:
```bash
chmod +x /root/backup.sh
```

### Schedule with cron

```bash
crontab -e
```

Add:
```bash
# Daily backup at 2 AM
0 2 * * * /root/backup.sh >> /var/log/backup.log 2>&1
```

---

## 📊 Monitoring Setup (Optional)

### Install monitoring tools

```bash
# Install Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /root/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Install Grafana
docker run -d \
  --name grafana \
  -p 3001:3000 \
  grafana/grafana
```

---

## ✅ Final Checklist

- [ ] VPS updated and secured
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned
- [ ] Environment variables configured
- [ ] Services running (docker-compose ps)
- [ ] API accessible (curl test)
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Backups scheduled
- [ ] Monitoring setup (optional)

---

## 🎉 Success!

Your Market Matrix API is now running on:
- **HTTP**: http://your-vps-ip:8000
- **HTTPS**: https://api.yourdomain.com (if SSL configured)

### Test endpoints:

```bash
# Health check
curl https://api.yourdomain.com/api/v1/health

# Market data
curl https://api.yourdomain.com/api/v1/market/prices

# Token health
curl https://api.yourdomain.com/api/v1/token-health/BTC

# Predictions
curl https://api.yourdomain.com/api/v1/predictions/BTC

# Dashboard
curl https://api.yourdomain.com/api/v1/dashboard
```

---

## 📞 Support

If you encounter issues:
1. Check logs: `docker-compose logs -f backend`
2. Verify environment variables: `cat .env`
3. Test database: `docker exec -it marketmatrix-postgres psql -U marketmatrix`
4. Test Redis: `docker exec -it marketmatrix-redis redis-cli ping`

---

## 🔄 Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f backend

# Rebuild and restart
docker-compose up -d --build

# Check status
docker-compose ps

# Backup database
docker exec marketmatrix-postgres pg_dump -U marketmatrix marketmatrix > backup.sql

# Update code
git pull && docker-compose up -d --build
```

---

**Your Market Matrix platform is now live and ready to help users escape the matrix!** 🚀
