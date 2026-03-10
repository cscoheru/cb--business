#!/bin/bash
# Railway startup script
set -e

echo "Starting FastAPI application..."
cd /workspace

# Try different startup methods
if command -v uvicorn &> /dev/null; then
    echo "Using uvicorn directly..."
    exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
else
    echo "Using python module..."
    exec python -m api
fi
