#!/bin/bash

# Market Matrix - Quick Deployment Script for Ubuntu VPS
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 Market Matrix Deployment Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo ./deploy.sh)${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from .env.production template..."
    cp .env.production .env
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and update these values:${NC}"
    echo "  - DB_PASSWORD"
    echo "  - JWT_SECRET"
    echo "  - SECRET_KEY"
    echo ""
    echo "Generate secrets with: openssl rand -hex 32"
    echo ""
    read -p "Press Enter after you've updated .env..."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✓ Docker Compose already installed${NC}"
fi

echo ""
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Services are running${NC}"
else
    echo -e "${RED}✗ Services failed to start${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🧪 Testing API..."
sleep 5

# Test health endpoint
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
    echo "Check logs with: docker-compose logs backend"
    exit 1
fi

echo ""
echo "=================================="
echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo "=================================="
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 API is running at:"
echo "  - Local: http://localhost:8000"
echo "  - Health: http://localhost:8000/api/v1/health"
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker-compose logs -f backend"
echo "  - Restart: docker-compose restart"
echo "  - Stop: docker-compose down"
echo "  - Update: git pull && docker-compose up -d --build"
echo ""
echo "🔐 Next steps:"
echo "  1. Setup Nginx reverse proxy (see DEPLOYMENT_UBUNTU_VPS.md)"
echo "  2. Configure SSL with Let's Encrypt"
echo "  3. Setup firewall (ufw)"
echo "  4. Configure domain DNS"
echo ""
echo "📚 Full guide: DEPLOYMENT_UBUNTU_VPS.md"
echo ""
