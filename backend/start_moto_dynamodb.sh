#!/bin/bash
# Start moto DynamoDB server (Python-based, no Docker needed)

echo "Starting moto DynamoDB server on port 8002..."
echo ""
echo "Installing moto if needed..."

# Install moto[server] if not already installed
pip3 install 'moto[server]' > /dev/null 2>&1 || {
    echo "Installing moto..."
    pip3 install 'moto[server]'
}

echo ""
echo "Starting DynamoDB Local (moto) on http://localhost:8002"
echo "Press Ctrl+C to stop"
echo ""

# Start moto server
moto_server dynamodb -p 8002
