#!/bin/bash
# CB Business Health Check Script
# Checks all services and reports status

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Services
FRONTEND_URL="https://cb.3strategy.cc"
ADMIN_URL="https://admin.cb.3strategy.cc"
API_URL="https://api.cb.3strategy.cc"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CB Business Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check service
check_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -n "Checking $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" -L "$url" 2>/dev/null)

    if [ "$response" = "$expected_code" ] || echo "$response" | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        return 1
    fi
}

# Function to check API
check_api() {
    echo -n "Checking API Health... "

    response=$(curl -s "$API_URL/health" 2>/dev/null)

    if echo "$response" | grep -q "healthy\|status"; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "  Response: $response"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Response: $response"
        return 1
    fi
}

# Function to check SSL
check_ssl() {
    local name=$1
    local domain=$2

    echo -n "Checking SSL for $name... "

    cert=$(openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "$cert" | grep "notAfter" | sed 's/notAfter=/Expires: /'
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check DNS
check_dns() {
    local name=$1
    local domain=$2

    echo -n "Checking DNS for $name... "

    ip=$(dig +short "$domain" | head -1)

    if [ -n "$ip" ]; then
        echo -e "${GREEN}✓ OK${NC} ($ip)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Run checks
echo -e "${BLUE}DNS Checks${NC}"
check_dns "Frontend" "cb.3strategy.cc"
check_dns "Admin" "admin.cb.3strategy.cc"
check_dns "API" "api.cb.3strategy.cc"
echo ""

echo -e "${BLUE}SSL Certificate Checks${NC}"
check_ssl "Frontend" "cb.3strategy.cc"
check_ssl "Admin" "admin.cb.3strategy.cc"
check_ssl "API" "api.cb.3strategy.cc"
echo ""

echo -e "${BLUE}Service Availability${NC}"
check_service "Frontend" "$FRONTEND_URL"
check_service "Admin Panel" "$ADMIN_URL"
check_api
echo ""

# API endpoints
echo -e "${BLUE}API Endpoints${NC}"
endpoints=(
    "/health"
    "/docs"
    "/openapi.json"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "  $endpoint... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint" 2>/dev/null)
    if [ "$response" = "200" ] || [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}?${NC} (HTTP $response)"
    fi
done
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Health Check Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Quick links:"
echo -e "  Frontend:  $FRONTEND_URL"
echo -e "  Admin:     $ADMIN_URL"
echo -e "  API Docs:  ${API_URL}/docs"
echo ""
