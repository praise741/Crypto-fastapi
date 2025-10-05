#!/usr/bin/env bash
# =================================================================
# MARKET MATRIX - VPS DEPLOYMENT SCRIPT
# =================================================================
# This script deploys Market Matrix on Ubuntu VPS with Docker
# Uses 100% free APIs - no API keys required

set -euo pipefail

# ---------- CONFIGURATION ----------
# GitHub User and PAT should be set as environment variables
# export GITHUB_USER="your_github_username"
# export GITHUB_PAT="your_github_pat_token"
GITHUB_USER="${GITHUB_USER:-$(whoami)}"
REPO_URL="https://github.com/${GITHUB_USER}/Crypto-fastapi.git"
APP_DIR="/root/Crypto-fastapi"
SITE_NAME="marketmatrix"
BACKUP_DIR="/root/backup_$(date +%Y%m%d_%H%M%S)"
# -----------------------------------------

# Color codes for output
RED='\033[0;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
say(){ printf "\n${GREEN}== %s ==${NC}\n" "$*"; }
warn(){ printf "\n${YELLOW}!! %s !!${NC}\n" "$*"; }
error(){ printf "\n${RED}ERROR: %s${NC}\n" "$*"; }
info(){ printf "\n${BLUE}ℹ️  %s${NC}\n" "$*"; }
die(){ error "$*"; exit 1; }

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    die "Please run as root: sudo bash deploy-vps.sh"
fi

# Get server IP and create fake domain
IP="$(hostname -I | awk '{print $1}')"
[ -n "${IP}" ] || die "Could not determine server IP"
FAKE_DOMAIN="api-${IP//./-}.sslip.io"

say "🚀 Starting Market Matrix Deployment"
info "Server IP: ${IP}"
info "Fake Domain: ${FAKE_DOMAIN}"

# System Update
say "📦 Updating OS & installing base tools"
apt update -y && apt upgrade -y
apt install -y curl ca-certificates gnupg lsb-release git nginx ufw jq htop

# Stop and remove old Laravel app and Nginx sites
say "🧹 Cleaning up old installations"
mkdir -p "${BACKUP_DIR}"
if [ -d /var/www/brandify ]; then
    tar -C / -czf "${BACKUP_DIR}/brandify.tgz" var/www/brandify || true
    rm -rf /var/www/brandify
fi

# Remove brandify-related nginx sites
for f in /etc/nginx/sites-enabled/brandify* /etc/nginx/sites-available/brandify*; do
    [ -e "$f" ] && mv "$f" "${BACKUP_DIR}/" || true
done

# Install Docker
say "🐳 Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable --now docker
else
    info "Docker already installed"
fi

# Install Docker Compose
say "🔧 Installing Docker Compose"
if ! command -v docker-compose >/dev/null 2>&1; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    info "Docker Compose already installed"
fi

# Configure Git credentials
say "🔑 Configuring Git credentials"
git config --global user.name "${GITHUB_USER}"
git config --global user.email "${GITHUB_USER}@users.noreply.github.com"

# Check if GitHub PAT is set
if [ -z "${GITHUB_PAT:-}" ]; then
    warn "GitHub PAT not set. Please set GITHUB_PAT environment variable."
    warn "Example: export GITHUB_PAT=your_token_here"
    exit 1
fi

git config --global credential.helper store
echo "https://${GITHUB_USER}:${GITHUB_PAT}@github.com" > /root/.git-credentials
chmod 600 /root/.git-credentials

# Clone or update repository
say "📥 Cloning repository: ${REPO_URL}"
REPO_URL_WITH_TOKEN="https://${GITHUB_USER}:${GITHUB_PAT}@github.com/${GITHUB_USER}/Crypto-fastapi.git"

if [ -d "${APP_DIR}/.git" ]; then
    cd "${APP_DIR}"
    git remote set-url origin "${REPO_URL_WITH_TOKEN}"
    git fetch --all --prune
    git reset --hard origin/main || git reset --hard origin/master || true
else
    rm -rf "${APP_DIR}"
    git clone "${REPO_URL_WITH_TOKEN}" "${APP_DIR}"
    cd "${APP_DIR}"
fi

# Create production environment file
say "⚙️  Creating production environment"
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        cp .env.production .env
    else
        touch .env
    fi
fi

# Generate secure secrets
DB_PASSWORD="$(openssl rand -hex 16)"
JWT_SECRET="$(openssl rand -hex 32)"
SECRET_KEY="$(openssl rand -hex 32)"

# Helper function to upsert environment variables
upsert_env () {
    local key="$1" val="$2"
    if grep -qE "^[# ]*${key}=" .env; then
        sed -i "s|^[# ]*${key}=.*|${key}=${val}|" .env
    else
        echo "${key}=${val}" >> .env
    fi
}

# Set production environment variables
upsert_env DATABASE_URL "postgresql+psycopg2://marketmatrix:${DB_PASSWORD}@postgres:5432/marketmatrix"
upsert_env SQLITE_FALLBACK "true"
upsert_env DB_PASSWORD "${DB_PASSWORD}"
upsert_env JWT_SECRET "${JWT_SECRET}"
upsert_env SECRET_KEY "${SECRET_KEY}"
upsert_env ENVIRONMENT "production"
upsert_env DOMAIN "${FAKE_DOMAIN}"
upsert_env COINGECKO_API_KEY ""
upsert_env BINANCE_API_KEY ""
upsert_env FEATURE_PREDICTIONS "1"
upsert_env FEATURE_DASHBOARD "1"
upsert_env FEATURE_ADVANCED_TOOLS "1"
upsert_env FEATURE_WEB3_HEALTH "1"
upsert_env FEATURE_PORTFOLIO "1"
upsert_env FEATURE_INSIGHTS "1"
upsert_env FEATURE_WALLET "0"

# Build and start Docker services
say "🏗️  Building and starting Docker services"
docker-compose build --no-cache
docker-compose down
docker-compose up -d

# Wait for containers to start
say "⏳ Waiting for containers to initialize"
sleep 15

# Check container health
say "🏥 Checking service health"
docker-compose ps

# Wait for backend to be healthy
info "Waiting for backend health check..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
        info "Backend is healthy!"
        break
    fi
    if [ $attempt -eq $max_attempts ]; then
        warn "Backend health check failed after $max_attempts attempts"
        warn "Check logs: docker-compose logs -f backend"
        break
    fi
    echo "Attempt $attempt/$max_attempts..."
    sleep 5
    attempt=$((attempt + 1))
done

# Configure Nginx reverse proxy
say "🌐 Configuring Nginx reverse proxy"
cat >/etc/nginx/sites-available/${SITE_NAME} <<NGINX
server {
    listen 80;
    server_name ${FAKE_DOMAIN};

    # Increase timeouts for long-running API requests
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # Handle preflight requests
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINX

# Enable site
ln -sf /etc/nginx/sites-available/${SITE_NAME} /etc/nginx/sites-enabled/${SITE_NAME}
[ -e /etc/nginx/sites-enabled/default ] && rm -f /etc/nginx/sites-enabled/default

# Create self-signed SSL certificate
say "🔒 Creating SSL certificate"
SSL_DIR="/etc/ssl/${SITE_NAME}"
mkdir -p "${SSL_DIR}"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${SSL_DIR}/${SITE_NAME}.key" \
  -out "${SSL_DIR}/${SITE_NAME}.crt" \
  -subj "/CN=${FAKE_DOMAIN}"

# Add HTTPS server block
cat >/etc/nginx/sites-available/${SITE_NAME}-ssl <<NGINX
server {
    listen 443 ssl http2;
    server_name ${FAKE_DOMAIN};

    ssl_certificate     ${SSL_DIR}/${SITE_NAME}.crt;
    ssl_certificate_key ${SSL_DIR}/${SITE_NAME}.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Increase timeouts for long-running API requests
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
    }

    # Handle preflight requests
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        proxy_pass http://127.0.0.1:8000;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name ${FAKE_DOMAIN};
    return 301 https://\$host\$request_uri;
}
NGINX

# Enable SSL site
ln -sf /etc/nginx/sites-available/${SITE_NAME}-ssl /etc/nginx/sites-enabled/${SITE_NAME}-ssl

# Test and reload Nginx
say "🔄 Testing and reloading Nginx"
nginx -t
if [ $? -eq 0 ]; then
    systemctl restart nginx
    info "Nginx reloaded successfully"
else
    error "Nginx configuration error"
    exit 1
fi

# Configure firewall
say "🛡️  Configuring firewall"
ufw allow 22/tcp || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
yes | ufw enable || true
ufw status || true

# Final health checks
say "🏥 Final health checks"

# Local health check
if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    info "✅ Local backend health: OK"
else
    warn "⚠️  Local backend health failed. Check: docker-compose logs -f backend"
fi

# Public HTTPS health check (self-signed cert, so -k)
if curl -kfsS "https://${FAKE_DOMAIN}/api/v1/health" >/dev/null 2>&1; then
    info "✅ Public HTTPS health: OK (${FAKE_DOMAIN})"
else
    warn "⚠️  Public HTTPS health failed. Check /var/log/nginx/error.log"
fi

# Test API endpoints
info "Testing API endpoints..."
endpoints=(
    "/api/v1/health"
    "/api/v1/market/prices"
    "/api/v1/token-health/BTC"
    "/api/v1/predictions?symbol=BTC&horizon=24h"
)

for endpoint in "${endpoints[@]}"; do
    if curl -fsS "http://127.0.0.1:8000${endpoint}" >/dev/null 2>&1; then
        info "✅ $endpoint - Working"
    else
        warn "⚠️  $endpoint - Failed"
    fi
done

echo
echo "================================================================="
echo "🎉 MARKET MATRIX DEPLOYMENT COMPLETED!"
echo "================================================================="
echo "📍 Server Information:"
echo "   HTTPS URL:     https://${FAKE_DOMAIN}"
echo "   Local API:     http://127.0.0.1:8000/api/v1/health"
echo "   Public API:    https://${FAKE_DOMAIN}/api/v1/health"
echo ""
echo "🔧 Management Commands:"
echo "   Check logs:    docker-compose logs -f backend"
echo "   Restart:       docker-compose restart"
echo "   Stop:          docker-compose down"
echo "   Update:        cd ${APP_DIR} && git pull && docker-compose build && docker-compose up -d"
echo ""
echo "🔐 Security:"
echo "   DB Password:   ${DB_PASSWORD}"
echo "   JWT Secret:    ${JWT_SECRET}"
echo "   SECRET_KEY:    ${SECRET_KEY}"
echo ""
echo "📁 Important Paths:"
echo "   App Directory: ${APP_DIR}"
echo "   Config File:   ${APP_DIR}/.env"
echo "   Docker Logs:   ${APP_DIR}/docker-compose logs"
echo "   Nginx Logs:    /var/log/nginx/error.log"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test the API endpoints manually"
echo "   2. Set up monitoring (optional)"
echo "   3. Configure backup strategy"
echo "   4. Consider adding custom domain"
echo "================================================================="

# Show container status
echo ""
echo "📊 Container Status:"
docker-compose ps