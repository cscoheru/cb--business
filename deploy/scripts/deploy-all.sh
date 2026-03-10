#!/bin/bash
# CB Business Deployment Script
# Deploys all services to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="/Users/kjonekong/Documents/cb-Business"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ADMIN_DIR="$PROJECT_ROOT/admin"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CB Business Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to confirm deployment
confirm() {
    local prompt=$1
    echo -e "${YELLOW}? $prompt${NC}"
    read -p "[y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists vercel; then
    echo -e "${RED}✗ Vercel CLI not found. Install with: npm install -g vercel${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Vercel CLI installed${NC}"

if ! command_exists railway; then
    echo -e "${RED}✗ Railway CLI not found. Install with: npm install -g railway${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Railway CLI installed${NC}"

echo ""

# Deploy Backend
if confirm "Deploy backend to Railway?"; then
    echo -e "${BLUE}Deploying backend to Railway...${NC}"
    cd "$BACKEND_DIR"

    # Check if Railway is linked
    if [ ! -f ".railway/config.json" ]; then
        echo -e "${YELLOW}Railway project not linked. Linking now...${NC}"
        railway init || true
    fi

    railway up
    echo -e "${GREEN}✓ Backend deployed${NC}"
    echo -e "  URL: $(railway domain 2>/dev/null || echo 'Check Railway dashboard')"
    echo ""
fi

# Deploy Frontend
if confirm "Deploy frontend to Vercel?"; then
    echo -e "${BLUE}Deploying frontend to Vercel...${NC}"
    cd "$FRONTEND_DIR"

    # Check if Vercel is linked
    if [ ! -f ".vercel/project.json" ]; then
        echo -e "${YELLOW}Vercel project not linked. Linking now...${NC}"
        vercel link --yes
    fi

    vercel --prod
    echo -e "${GREEN}✓ Frontend deployed${NC}"
    echo -e "  URL: https://cb.3strategy.cc"
    echo ""
fi

# Deploy Admin
if confirm "Deploy admin panel to Vercel?"; then
    echo -e "${BLUE}Deploying admin panel to Vercel...${NC}"
    cd "$ADMIN_DIR"

    # Check if Vercel is linked
    if [ ! -f ".vercel/project.json" ]; then
        echo -e "${YELLOW}Vercel project not linked. Linking now...${NC}"
        vercel link --yes
    fi

    vercel --prod
    echo -e "${GREEN}✓ Admin panel deployed${NC}"
    echo -e "  URL: https://admin.cb.3strategy.cc"
    echo ""
fi

# Post-deployment verification
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Frontend:  ${GREEN}https://cb.3strategy.cc${NC}"
echo -e "Admin:     ${GREEN}https://admin.cb.3strategy.cc${NC}"
echo -e "API:       ${GREEN}https://api.cb.3strategy.cc${NC}"
echo ""

# Run health checks
echo -e "${BLUE}Running health checks...${NC}"

# Check frontend
if curl -s -o /dev/null -w "%{http_code}" https://cb.3strategy.cc | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend health check failed${NC}"
fi

# Check admin
if curl -s -o /dev/null -w "%{http_code}" https://admin.cb.3strategy.cc | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ Admin panel is accessible${NC}"
else
    echo -e "${RED}✗ Admin panel health check failed${NC}"
fi

# Check API
API_HEALTH=$(curl -s https://api.cb.3strategy.cc/health || echo "{}")
if echo "$API_HEALTH" | grep -q "healthy\|status"; then
    echo -e "${GREEN}✓ API is accessible${NC}"
else
    echo -e "${YELLOW}⚠ API health check returned: $API_HEALTH${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Verify all services are working"
echo -e "  2. Test user registration and login"
echo -e "  3. Check API documentation at https://api.cb.3strategy.cc/docs"
echo -e "  4. Monitor logs: railway logs (backend)"
echo ""
