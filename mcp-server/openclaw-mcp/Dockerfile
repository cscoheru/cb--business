FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server.py .
COPY openclaw_mcp/ ./openclaw_mcp/

# Expose port
EXPOSE 8001

# Set environment variables
ENV OPENCLAW_BASE_URL=http://103.59.103.85:18789
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
