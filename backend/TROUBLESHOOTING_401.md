# Troubleshooting 401 Unauthorized Login Error

## The Problem

You're getting `401 Unauthorized` when trying to login, even though the user exists in AWS DynamoDB.

## Root Cause

Your backend was configured to use **local DynamoDB** (moto on port 8002), but your user was created in **AWS DynamoDB** (remote). These are two separate databases!

## Solution Applied

I've updated your `.env` file to comment out the local endpoint:

```env
# Use AWS DynamoDB (remote)
# DYNAMODB_ENDPOINT=http://localhost:8002

# Use local DynamoDB
DYNAMODB_ENDPOINT=http://localhost:8002
```

## How to Debug Login Issues

### Step 1: Check which database your backend is using

Run the debug script with your email:

```bash
cd backend
uv run python debug_user.py your-email@example.com
```

This will show:
- Which DynamoDB endpoint is being used
- Whether the user exists in that database
- User details if found

### Step 2: Test the login

```bash
uv run python test_login.py your-email@example.com your-password
```

This will show the exact response from the login endpoint.

### Step 3: Check the backend logs

Look at your FastAPI terminal for detailed log messages:

```
INFO:app.api.auth:Login attempt for email: user@example.com
WARNING:app.api.auth:Login failed: user not found - user@example.com
```

Or:

```
INFO:app.api.auth:Login attempt for email: user@example.com
WARNING:app.api.auth:Login failed: incorrect password - user@example.com
```

## Common Scenarios

### Scenario 1: User in AWS, Backend Using Local DB

**Problem**: `DYNAMODB_ENDPOINT=http://localhost:8002` is set

**Solution**: Comment out or remove that line:
```bash
# DYNAMODB_ENDPOINT=http://localhost:8002
```

Restart your FastAPI server or trigger a reload:
```bash
touch app/main.py
```

### Scenario 2: User in Local DB, Backend Using AWS

**Problem**: `DYNAMODB_ENDPOINT` is commented out or empty

**Solution**: Uncomment and set to local:
```bash
DYNAMODB_ENDPOINT=http://localhost:8002
```

Make sure moto is running:
```bash
moto_server -p 8002
```

### Scenario 3: Password Doesn't Match

**Symptoms**: User is found, but password verification fails

**Cause**: The password you're entering doesn't match the hashed password in the database

**Solutions**:
1. Use the correct password you registered with
2. Register a new user using the `/auth/register` endpoint
3. Reset the user's password (you'll need to implement this endpoint)

## Quick Commands

**Check if user exists in AWS DynamoDB:**
```bash
aws dynamodb get-item \
  --table-name LetterOn-Users \
  --key '{"user_id": {"S": "your-user-id"}}' \
  --region eu-central-1
```

**Query user by email (requires GSI):**
```bash
aws dynamodb query \
  --table-name LetterOn-Users \
  --index-name email-index \
  --key-condition-expression "email = :email" \
  --expression-attribute-values '{":email":{"S":"your@email.com"}}' \
  --region eu-central-1
```

**Switch between Local and AWS DynamoDB:**
```bash
# Use AWS (remote)
sed -i '' 's/^DYNAMODB_ENDPOINT=/#DYNAMODB_ENDPOINT=/' .env

# Use Local
sed -i '' 's/^#DYNAMODB_ENDPOINT=/DYNAMODB_ENDPOINT=/' .env
```

## Testing Login Flow

### 1. Register a new user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 2. Login with that user

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 3. Use the token

```bash
TOKEN="your-token-here"

curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Current Configuration

After my changes, your backend is now configured to use **AWS DynamoDB** (remote), so it should find your user that was created in AWS.

If you're still getting 401 errors, run the debug script:

```bash
cd backend
uv run python debug_user.py your-email@example.com
```

This will tell you exactly what's happening!
