#!/bin/bash
# CB Business Rollback Script
# Rolls back all services to previous deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/Users/kjonekong/Documents/cb-Business"

echo -e "${RED}========================================${NC}"
echo -e "${RED}  CB Business Rollback Script${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Confirmation
echo -e "${YELLOW}WARNING: This will rollback all deployments!${NC}"
read -p "Are you sure? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled."
    exit 0
fi

# Rollback Frontend
echo -e "${BLUE}Rolling back frontend...${NC}"
cd "$PROJECT_ROOT/frontend"
vercel rollback --yes
echo -e "${GREEN}✓ Frontend rolled back${NC}"

# Rollback Admin
echo -e "${BLUE}Rolling back admin panel...${NC}"
cd "$PROJECT_ROOT/admin"
vercel rollback --yes
echo -e "${GREEN}✓ Admin panel rolled back${NC}"

# Note: Railway rollback is different
echo -e "${YELLOW}Note: Railway rollback must be done via dashboard${NC}"
echo -e "  Go to: https://railway.app/project/your-project/deployments"
echo ""

echo -e "${GREEN}Rollback complete!${NC}"
