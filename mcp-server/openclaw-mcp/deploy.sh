#!/bin/bash
# OpenClaw MCP HTTP Server Deployment Script
# Run this on HK server

set -e

echo "=== Deploying OpenClaw MCP HTTP Server ==="

# Configuration
IMAGE_NAME="openclaw-mcp-http"
CONTAINER_NAME="openclaw-mcp-server"
NETWORK="cb-network"
PORT=8001
OPENCLAW_BASE_URL="http://103.59.103.85:18789"

# Step 1: Create directory
echo "Step 1: Creating ~/openclaw-mcp-http directory..."
mkdir -p ~/openclaw-mcp-http
cd ~/openclaw-mcp-http

# Step 2: Copy files (if running locally)
echo "Step 2: Copying server files..."
# Files would be copied here from local machine

# Step 3: Build Docker image
echo "Step 3: Building Docker image..."
docker build -t $IMAGE_NAME:latest .

# Step 4: Stop existing container if running
echo "Step 4: Stopping existing container (if any)..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Step 5: Run new container
echo "Step 5: Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --network $NETWORK \
  -p $PORT:8001 \
  -e OPENCLAW_BASE_URL=$OPENCLAW_BASE_URL \
  -e PYTHONUNBUFFERED=1 \
  --restart unless-stopped \
  $IMAGE_NAME:latest

# Step 6: Verify deployment
echo "Step 6: Verifying deployment..."
sleep 3

echo ""
echo "=== Container Status ==="
docker ps --filter "name=$CONTAINER_NAME"

echo ""
echo "=== Health Check ==="
curl -s http://localhost:$PORT/health | python3 -m json.tool

echo ""
echo "=== MCP Tools List ==="
curl -s http://localhost:$PORT/tools | python3 -m json.tool

echo ""
echo "=== Deployment Complete ==="
echo "MCP HTTP Server is running at: http://103.59.103.85:$PORT"
echo "Container name: $CONTAINER_NAME"
echo "Network: $NETWORK"
echo ""
echo "To view logs:"
echo "  docker logs -f $CONTAINER_NAME"
echo ""
echo "To restart:"
echo "  docker restart $CONTAINER_NAME"
