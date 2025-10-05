# Market Matrix - VPS Deployment Guide

## Overview

This guide provides a complete solution for deploying Market Matrix on an Ubuntu VPS using Docker. The deployment uses **100% free APIs** - no API keys required.

## Features Included

✅ **AI-Powered Price Predictions** - Prophet ML model with free CoinGecko data
✅ **Token Health Scanner** - Scam detection using DexScreener (free)
✅ **Market Analytics** - Correlations, volatility, trends analysis
✅ **Portfolio Tracking** - CSV upload, P&L calculations, allocation analysis
✅ **Real-time WebSockets** - Live price updates and notifications
✅ **Advanced Trading Tools** - Technical indicators, market depth
✅ **Community Insights** - Reddit sentiment analysis (optional)

## Quick Deploy (One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/praise741/Crypto-fastapi/main/deploy-vps.sh | bash
```

## Manual Deployment

### Prerequisites

- Ubuntu 20.04+ or Debian 10+
- Root or sudo access
- Minimum 2GB RAM, 1 CPU core
- 10GB+ disk space

### Step 1: Run Deployment Script

```bash
# Download and run the deployment script
wget https://raw.githubusercontent.com/praise741/Crypto-fastapi/main/deploy-vps.sh
chmod +x deploy-vps.sh
sudo bash deploy-vps.sh
```

### Step 2: Access Your Instance

The script will provide you with:
- **HTTPS URL**: `https://api-IP-ADDRESS.sslip.io`
- **Local API**: `http://localhost:8000/api/v1/health`

### Step 3: Test the Deployment

```bash
# Health check
curl -k https://api-IP-ADDRESS.sslip.io/api/v1/health

# Test market data
curl -k https://api-IP-ADDRESS.sslip.io/api/v1/market/prices

# Test token health
curl -k https://api-IP-ADDRESS.sslip.io/api/v1/token-health/BTC

# Test predictions
curl -k "https://api-IP-ADDRESS.sslip.io/api/v1/predictions?symbol=BTC&horizon=24h"
```

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health check |
| `/api/v1/market/prices` | GET | All cryptocurrency prices |
| `/api/v1/market/{symbol}/price` | GET | Single token price |
| `/api/v1/token-health/{symbol}` | GET | Token health analysis |
| `/api/v1/predictions?symbol=BTC&horizon=24h` | GET | AI price predictions |
| `/api/v1/analytics/correlations` | GET | Market correlations |
| `/api/v1/portfolio/upload` | POST | Upload portfolio CSV |
| `/api/v1/dashboard` | GET | Dashboard overview |

### WebSocket Endpoints

- `ws://your-domain/api/v1/ws/market` - Live price updates
- `ws://your-domain/api/v1/ws/predictions` - Live prediction updates

## Configuration

### Environment Variables

The deployment script automatically configures these variables:

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://marketmatrix:PASSWORD@postgres:5432/marketmatrix

# Security
SECRET_KEY=generated-secret-key
JWT_SECRET=generated-jwt-secret

# Feature Flags (All enabled)
FEATURE_PREDICTIONS=1
FEATURE_DASHBOARD=1
FEATURE_ADVANCED_TOOLS=1
FEATURE_WEB3_HEALTH=1
FEATURE_PORTFOLIO=1
FEATURE_INSIGHTS=1

# Free APIs (No keys required)
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
BINANCE_BASE_URL=https://api.binance.com/api/v3
DEXSCREENER_BASE_URL=https://api.dexscreener.com/latest/dex
```

### Custom Domain (Optional)

To use your own domain instead of the SSLIP.io domain:

1. Point your domain's A record to your VPS IP
2. Update `/etc/nginx/sites-available/marketmatrix-ssl`
3. Replace `api-IP-ADDRESS.sslip.io` with your domain
4. Reload Nginx: `systemctl reload nginx`

## Management Commands

### Docker Management

```bash
# View container status
docker-compose ps

# View logs
docker-compose logs -f backend

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update application
cd /root/Crypto-fastapi
git pull
docker-compose build
docker-compose up -d
```

### Database Management

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U marketmatrix -d marketmatrix

# Create database backup
docker-compose exec postgres pg_dump -U marketmatrix marketmatrix > backup.sql

# Restore database backup
docker-compose exec -T postgres psql -U marketmatrix marketmatrix < backup.sql
```

### SSL Certificate Management

The deployment uses self-signed certificates. For production:

```bash
# Install Certbot for Let's Encrypt
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring

### Health Monitoring

```bash
# Check system resources
htop

# Check disk usage
df -h

# Check memory usage
free -h

# Check Docker stats
docker stats
```

### Log Monitoring

```bash
# Application logs
tail -f /root/Crypto-fastapi/logs/app.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f --tail=100
```

## Troubleshooting

### Common Issues

1. **Backend not responding**
   ```bash
   # Check container status
   docker-compose ps

   # Check logs
   docker-compose logs backend

   # Restart service
   docker-compose restart backend
   ```

2. **Database connection issues**
   ```bash
   # Check PostgreSQL container
   docker-compose ps postgres

   # Test database connection
   docker-compose exec postgres pg_isready -U marketmatrix
   ```

3. **Nginx configuration errors**
   ```bash
   # Test Nginx config
   nginx -t

   # Check Nginx logs
   tail -f /var/log/nginx/error.log

   # Reload Nginx
   systemctl reload nginx
   ```

4. **SSL certificate issues**
   ```bash
   # Check certificate files
   ls -la /etc/ssl/marketmatrix/

   # Test SSL configuration
   openssl s_client -connect your-domain:443
   ```

### Performance Optimization

1. **Enable Redis persistence**
   ```bash
   # Edit docker-compose.yml
   # Add to redis command: --save 900 1 --save 300 10
   docker-compose restart redis
   ```

2. **Optimize PostgreSQL**
   ```bash
   # Edit docker-compose.yml
   # Add to postgres environment:
   # POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
   ```

3. **Increase worker processes**
   ```bash
   # Edit docker-compose.yml
   # Change backend command to: --workers 4
   ```

## Security

### Default Security Features

- Non-root Docker user
- Self-signed SSL certificates
- Security headers in Nginx
- Rate limiting on API endpoints
- Input validation and sanitization

### Security Hardening

```bash
# Fail2Ban for SSH
apt install fail2ban
systemctl enable fail2ban

# UFW firewall rules
ufw deny 5432  # PostgreSQL (internal only)
ufw deny 6379  # Redis (internal only)

# Update regularly
apt update && apt upgrade -y
```

## Backup Strategy

### Automated Backup Script

```bash
#!/bin/bash
# /root/backup-marketmatrix.sh

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec postgres pg_dump -U marketmatrix marketmatrix > $BACKUP_DIR/db_$DATE.sql

# Config backup
cp /root/Crypto-fastapi/.env $BACKUP_DIR/env_$DATE

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "env_*" -mtime +7 -delete
```

### Schedule Backups

```bash
# Add to crontab
crontab -e
# Add: 0 2 * * * /root/backup-marketmatrix.sh
```

## API Rate Limits

The application uses free API tiers with these limits:

- **CoinGecko**: 50-100 requests/minute (no API key)
- **DexScreener**: Unlimited (free)
- **Binance**: 1200 requests/minute (public endpoints)

The application includes caching to minimize API calls.

## Support

### Documentation

- [API Documentation](https://your-domain/docs) - Interactive API docs
- [Project Repository](https://github.com/praise741/Crypto-fastapi) - Source code
- [Issues](https://github.com/praise741/Crypto-fastapi/issues) - Report bugs

### Community

- GitHub Issues for bug reports
- Pull requests for contributions
- Discussions for questions

## License

This project is licensed under the MIT License. See LICENSE file for details.

---

**🎉 Congratulations! Your Market Matrix instance is now running!**

The platform provides a complete crypto intelligence solution using only free APIs and open-source technologies.