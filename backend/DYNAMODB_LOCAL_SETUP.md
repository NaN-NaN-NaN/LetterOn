# DynamoDB Local Development Setup

This guide explains how to use DynamoDB Local and DynamoDB Admin for local development.

## Problem

The 405 error you experienced occurred because DynamoDB Admin was trying to connect to port 8000, which is your FastAPI backend, not DynamoDB Local. DynamoDB Local wasn't running at all.

## Solution

The setup has been configured to use these ports:
- **Port 8000**: FastAPI backend
- **Port 8001**: DynamoDB Admin UI
- **Port 8002**: DynamoDB Local

## Prerequisites

You need to install DynamoDB Local. Choose one of these options:

### Option A: Using Docker (Recommended)

Make sure Docker Desktop is running, then:
```bash
cd backend
docker-compose up -d dynamodb-local
```

### Option B: Using LocalStack

```bash
brew install localstack
localstack start -d
```

### Option C: Download DynamoDB Local JAR

Download from: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html

```bash
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb -port 8002
```

## Quick Start

### Step 1: Start DynamoDB Local

**If using Docker (make sure Docker Desktop is running first):**
```bash
cd backend
./start_local_dynamodb.sh
```

**Or manually:**
```bash
cd backend
docker-compose up -d dynamodb-local
```

**If Docker isn't available, use LocalStack:**
```bash
localstack start -d
# DynamoDB will be available on port 4566
# Update .env: DYNAMODB_ENDPOINT=http://localhost:4566
```

### Step 2: Start DynamoDB Admin

**Using the helper script:**
```bash
cd backend
./start_dynamodb_admin.sh
```

**Or manually:**
```bash
DYNAMO_ENDPOINT=http://localhost:8002 dynamodb-admin
```

This will start DynamoDB Admin on http://localhost:8001

## Creating Tables

After DynamoDB Local is running, create the tables:

```bash
cd backend
uv run python scripts/create_dynamodb_tables.py
```

## Accessing the Services

- **DynamoDB Admin UI**: http://localhost:8001
- **DynamoDB Local**: http://localhost:8002
- **FastAPI Backend**: http://localhost:8000
- **FastAPI Docs**: http://localhost:8000/docs

## Environment Configuration

The `.env` file now includes:

```env
# For local development
DYNAMODB_ENDPOINT=http://localhost:8002

# For AWS production (comment out or remove DYNAMODB_ENDPOINT)
# DYNAMODB_ENDPOINT=
```

## Stopping Services

```bash
# Stop DynamoDB Local
docker-compose down

# Stop DynamoDB Admin
pkill -f dynamodb-admin

# Or find and kill the process
lsof -i :8001  # Find PID
kill <PID>
```

## Data Persistence

DynamoDB Local data is stored in `backend/dynamodb-data/` directory. This directory is:
- Created automatically by Docker Compose
- Added to `.gitignore` to prevent committing local data
- Persists across container restarts

To reset your local database:
```bash
rm -rf backend/dynamodb-data/
docker-compose restart dynamodb-local
uv run python scripts/create_dynamodb_tables.py
```

## Troubleshooting

### DynamoDB Admin shows "Cannot connect to DynamoDB"

Make sure DynamoDB Local is running:
```bash
curl http://localhost:8002/
```

If not running, start it:
```bash
docker-compose up -d dynamodb-local
```

### Port already in use

Check what's using the port:
```bash
lsof -i :8002  # for DynamoDB Local
lsof -i :8001  # for DynamoDB Admin
```

### Tables not showing in DynamoDB Admin

1. Make sure tables are created: `uv run python scripts/create_dynamodb_tables.py`
2. Refresh the DynamoDB Admin page
3. Check DynamoDB Admin is pointing to correct endpoint (http://localhost:8002)

## Production Deployment

When deploying to AWS:

1. Remove or comment out `DYNAMODB_ENDPOINT` in your production environment
2. The application will automatically use AWS DynamoDB
3. Ensure your ECS task role has proper DynamoDB permissions

```env
# Production .env (no endpoint = uses AWS DynamoDB)
# DYNAMODB_ENDPOINT=
```
