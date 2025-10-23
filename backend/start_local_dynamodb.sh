#!/bin/bash
# Script to start DynamoDB Local and DynamoDB Admin for development

set -e

echo "Starting DynamoDB Local development environment..."
echo ""

# Start DynamoDB Local using Docker Compose
echo "1. Starting DynamoDB Local (port 8002)..."
cd "$(dirname "$0")"
docker-compose up -d dynamodb-local

# Wait for DynamoDB Local to be ready
echo "2. Waiting for DynamoDB Local to be ready..."
sleep 3

# Check if DynamoDB Local is responding
echo "3. Checking DynamoDB Local health..."
if curl -s http://localhost:8002/ > /dev/null 2>&1; then
    echo "   ✓ DynamoDB Local is running on port 8002"
else
    echo "   ✗ DynamoDB Local is not responding. Check docker-compose logs."
    exit 1
fi

# Start DynamoDB Admin if not already running
echo "4. Starting DynamoDB Admin (port 8001)..."
if lsof -i :8001 > /dev/null 2>&1; then
    echo "   ✓ DynamoDB Admin is already running on port 8001"
else
    echo "   Starting DynamoDB Admin in the background..."
    DYNAMO_ENDPOINT=http://localhost:8002 dynamodb-admin &
    sleep 2
    echo "   ✓ DynamoDB Admin started on port 8001"
fi

echo ""
echo "=========================================="
echo "DynamoDB Local Development Environment"
echo "=========================================="
echo "DynamoDB Local:  http://localhost:8002"
echo "DynamoDB Admin:  http://localhost:8001"
echo ""
echo "To create tables, run:"
echo "  uv run python backend/scripts/create_dynamodb_tables.py"
echo ""
echo "To stop DynamoDB Local:"
echo "  docker-compose down"
echo ""
echo "To stop DynamoDB Admin:"
echo "  pkill -f dynamodb-admin"
echo "=========================================="
