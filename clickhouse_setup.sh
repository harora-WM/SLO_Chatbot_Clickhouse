#!/bin/bash
# ClickHouse Setup Script
# Sets up ClickHouse server using Docker for Kafka data ingestion

set -e  # Exit on any error

echo "====================================================="
echo "ClickHouse Setup Script"
echo "====================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker is installed"

# Check if ClickHouse container already exists
if docker ps -a --format '{{.Names}}' | grep -q '^clickhouse-server$'; then
    echo ""
    echo "ClickHouse container already exists."

    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q '^clickhouse-server$'; then
        echo "✓ ClickHouse is already running"
    else
        echo "Starting existing ClickHouse container..."
        docker start clickhouse-server
        echo "✓ ClickHouse container started"
    fi
else
    echo ""
    echo "Creating new ClickHouse container..."
    echo "This will:"
    echo "  - Pull ClickHouse server image (if not cached)"
    echo "  - Start ClickHouse on ports 8123 (HTTP) and 9000 (native)"
    echo "  - Create persistent data volume"
    echo ""

    docker run -d \
        --name clickhouse-server \
        --ulimit nofile=262144:262144 \
        -p 8123:8123 \
        -p 9000:9000 \
        clickhouse/clickhouse-server

    echo "✓ ClickHouse container created and started"
fi

# Wait for ClickHouse to be ready
echo ""
echo "Waiting for ClickHouse to be ready..."
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8123/ping > /dev/null 2>&1; then
        echo "✓ ClickHouse is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "  Waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: ClickHouse did not start within expected time"
    echo "Check logs with: docker logs clickhouse-server"
    exit 1
fi

# Test connection
echo ""
echo "Testing ClickHouse connection..."
CLICKHOUSE_VERSION=$(curl -s http://localhost:8123/?query=SELECT%20version())

if [ -n "$CLICKHOUSE_VERSION" ]; then
    echo "✓ Successfully connected to ClickHouse"
    echo "  Version: $CLICKHOUSE_VERSION"
else
    echo "Error: Could not query ClickHouse"
    exit 1
fi

# Display connection info
echo ""
echo "====================================================="
echo "ClickHouse Setup Complete!"
echo "====================================================="
echo ""
echo "Connection Details:"
echo "  HTTP Interface:   http://localhost:8123"
echo "  Native Interface: localhost:9000"
echo "  Username:         default"
echo "  Password:         (empty)"
echo ""
echo "Useful Commands:"
echo "  View logs:        docker logs clickhouse-server"
echo "  Stop server:      docker stop clickhouse-server"
echo "  Start server:     docker start clickhouse-server"
echo "  Restart server:   docker restart clickhouse-server"
echo "  Remove container: docker rm -f clickhouse-server"
echo ""
echo "ClickHouse Client (interactive SQL):"
echo "  docker exec -it clickhouse-server clickhouse-client"
echo ""
echo "Next Step:"
echo "  Run: python kafka_to_clickhouse.py"
echo "====================================================="
