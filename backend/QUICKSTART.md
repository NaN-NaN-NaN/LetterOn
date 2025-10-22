# LetterOn Server - Quick Start Guide

This guide will get you up and running with the LetterOn backend in 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.10+ installed
- [ ] AWS Account with configured credentials
- [ ] Two Lambda functions deployed:
  - `LetterOnOCRHandler`
  - `LetterOnLLMHandler`
- [ ] S3 bucket created (e.g., `letteron-images`)

## Step 1: Clone and Setup (1 minute) ⚡️

**This project uses [uv](https://github.com/astral-sh/uv) - an extremely fast Python package manager!**

```bash
cd /Users/nan/Project/LetterOn/backend

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install ALL dependencies in one command! 🚀
uv sync

# That's it! UV automatically:
# - Creates virtual environment (.venv)
# - Installs all dependencies
# - Creates lock file (uv.lock)
```

**Alternative (old way with pip):**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure Environment (2 minutes)

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your AWS credentials:

```bash
# REQUIRED - Generate a secret key
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# S3 Bucket
S3_BUCKET_NAME=letteron-images

# Lambda Functions (use your actual function names)
LAMBDA_OCR_FUNCTION_NAME=LetterOnOCRHandler
LAMBDA_LLM_FUNCTION_NAME=LetterOnLLMHandler
```

## Step 3: Create DynamoDB Tables (2 minutes)

```bash
python scripts/create_dynamodb_tables.py
```

Expected output:
```
✓ LetterOn-Users created successfully
✓ LetterOn-Letters created successfully
✓ LetterOn-Reminders created successfully
✓ LetterOn-Conversations created successfully
```

## Step 4: Start the Server (1 minute)

```bash
# With uv (recommended - no need to activate venv!)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or traditional way (activate venv first)
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: `http://localhost:8000`

## Step 5: Test the API (3 minutes)

### 5.1 Open API Documentation

Visit: `http://localhost:8000/docs`

You'll see interactive Swagger UI with all endpoints.

### 5.2 Test Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "LetterOn Server",
  "environment": "development"
}
```

### 5.3 Register a Test User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Expected response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "...",
    "name": "Test User",
    "email": "test@example.com"
  }
}
```

Save the `token` - you'll need it for authenticated requests!

### 5.4 Test Authenticated Endpoint

```bash
# Replace YOUR_TOKEN with the token from step 5.3
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:
```json
{
  "id": "...",
  "name": "Test User",
  "email": "test@example.com"
}
```

## Step 6: Test Letter Upload (Optional)

If you have a test image:

```bash
curl -X POST http://localhost:8000/letters/process-images \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@/path/to/letter-image.jpg"
```

This will:
1. Upload image to S3
2. Call OCR Lambda
3. Call LLM Lambda for analysis
4. Return structured letter data

## Common Issues & Solutions

### Issue: "Invalid or expired token"
**Solution:** Generate a new token by logging in again:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}'
```

### Issue: "Table not found" error
**Solution:** Run the table creation script:
```bash
python scripts/create_dynamodb_tables.py
```

### Issue: "Access Denied" AWS error
**Solution:** Check your AWS credentials and IAM permissions. You need:
- S3: `PutObject`, `GetObject`
- Lambda: `InvokeFunction`
- DynamoDB: `PutItem`, `GetItem`, `Query`, `UpdateItem`

### Issue: Lambda function not found
**Solution:** Verify Lambda function names in `.env` match your deployed functions:
```bash
aws lambda list-functions --query 'Functions[*].FunctionName'
```

### Issue: Port 8000 already in use
**Solution:** Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## Next Steps

### For Development
1. **Run Tests:**
   ```bash
   pytest tests/ -v
   ```

2. **Enable Debug Logging:**
   Edit `.env`:
   ```
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

3. **Use Docker:**
   ```bash
   docker-compose up
   ```

### For Production

1. **Deploy to AWS ECS:**
   ```bash
   ./deploy_aws.sh
   ```

2. **Set up monitoring:**
   - Enable CloudWatch Logs
   - Create CloudWatch Alarms
   - Set up X-Ray tracing

3. **Security hardening:**
   - Use AWS Secrets Manager for credentials
   - Enable HTTPS with ALB
   - Configure WAF rules
   - Set up rate limiting

## API Endpoints Summary

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/auth/register` | POST | Register user | No |
| `/auth/login` | POST | Login user | No |
| `/auth/logout` | POST | Logout user | Yes |
| `/letters/process-images` | POST | Upload & process letter images | Yes |
| `/letters` | GET | List letters | Yes |
| `/letters/{id}` | GET | Get letter details | Yes |
| `/letters/{id}` | PATCH | Update letter | Yes |
| `/letters/{id}` | DELETE | Delete letter | Yes |
| `/chat` | POST | Chat about letter | Yes |
| `/search` | GET | Search letters | Yes |
| `/reminders` | POST | Create reminder | Yes |
| `/reminders` | GET | List reminders | Yes |

## Support

- **Documentation:** See `README.md` for full documentation
- **API Docs:** Visit `http://localhost:8000/docs` when server is running
- **Issues:** Report bugs on GitHub

## Congratulations! 🎉

You've successfully set up LetterOn Server. Your backend is now ready to process physical letters with AI!

Start your frontend with:
```bash
cd ../frontend
npm run dev
```

Then upload a letter image and watch the magic happen!
