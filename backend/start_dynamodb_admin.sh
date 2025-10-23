#!/bin/bash
# Simple script to start DynamoDB Admin pointing to DynamoDB Local on port 8002

echo "Starting DynamoDB Admin on port 8001..."
echo "Connecting to DynamoDB Local at: http://localhost:8002"
echo ""
echo "Make sure DynamoDB Local is running on port 8002 first!"
echo "Access DynamoDB Admin at: http://localhost:8001"
echo ""

DYNAMO_ENDPOINT=http://localhost:8002 dynamodb-admin
