# LetterOn Server

A Python FastAPI backend for the LetterOn application that processes physical letters using OCR and AI analysis. This server integrates with existing AWS Lambda functions for OCR and LLM processing, and uses DynamoDB for data persistence.

## Features

- 🔐 JWT-based authentication
- 📤 Multi-image upload with S3 storage
- 🤖 AI-powered letter analysis via AWS Bedrock
- 📝 OCR text extraction via AWS Textract
- 💬 Conversational AI chat about letters
- 🔍 Full-text search across letters
- ⏰ Reminder system with background scheduling
- 🏷️ 15 letter category classifications
- 🌐 Multi-language translation support
- 📊 Action status tracking and due dates

## Architecture

```
Frontend (React)
    ↓ HTTP/REST
FastAPI Backend (this project)
    ↓
    ├─→ AWS S3 (image storage)
    ├─→ AWS Lambda: LetterOnOCRHandler (Textract OCR)
    ├─→ AWS Lambda: LetterOnLLMHandler (Bedrock AI)
    └─→ AWS DynamoDB (data persistence)
```

## Prerequisites

- Python 3.10+
- AWS Account with configured credentials
- AWS Lambda functions deployed:
  - `LetterOnOCRHandler` (OCR processing)
  - `LetterOnLLMHandler` (LLM analysis)
- AWS Services:
  - S3 bucket for letter images
  - DynamoDB tables (see setup below)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Application
SECRET_KEY=your-secret-key-min-32-chars-long-for-jwt-signing
DEBUG=true
LOG_LEVEL=INFO

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# S3
S3_BUCKET_NAME=letteron-images

# Lambda Functions
LAMBDA_OCR_FUNCTION_NAME=LetterOnOCRHandler
LAMBDA_LLM_FUNCTION_NAME=LetterOnLLMHandler

# DynamoDB Tables
DYNAMODB_USERS_TABLE=LetterOn-Users
DYNAMODB_LETTERS_TABLE=LetterOn-Letters
DYNAMODB_REMINDERS_TABLE=LetterOn-Reminders
DYNAMODB_CONVERSATIONS_TABLE=LetterOn-Conversations

# CORS (Frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

## Local Development Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured in `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

Or use environment variables (recommended for production):
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

### 3. Create DynamoDB Tables

You can create tables either via AWS Console or using the provided script:

#### Option A: Using AWS Console

1. Go to AWS Console → DynamoDB → Tables → Create table

2. **LetterOn-Users**
   - Table name: `LetterOn-Users`
   - Partition key: `user_id` (String)
   - Read/Write capacity: On-demand
   - Add Global Secondary Index:
     - Index name: `email-index`
     - Partition key: `email` (String)

3. **LetterOn-Letters**
   - Table name: `LetterOn-Letters`
   - Partition key: `letter_id` (String)
   - Read/Write capacity: On-demand
   - Add Global Secondary Index:
     - Index name: `user_id-index`
     - Partition key: `user_id` (String)
     - Sort key: `record_created_at` (Number)

4. **LetterOn-Reminders**
   - Table name: `LetterOn-Reminders`
   - Partition key: `reminder_id` (String)
   - Read/Write capacity: On-demand
   - Add Global Secondary Index:
     - Index name: `user_id-index`
     - Partition key: `user_id` (String)

5. **LetterOn-Conversations**
   - Table name: `LetterOn-Conversations`
   - Partition key: `conversation_id` (String)
   - Read/Write capacity: On-demand
   - Add Global Secondary Index:
     - Index name: `letter_id-index`
     - Partition key: `letter_id` (String)
     - Sort key: `timestamp` (Number)

#### Option B: Using Python Script

```bash
python scripts/create_dynamodb_tables.py
```

### 4. Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Running with Docker

```bash
# Build the image
docker build -t backend .

# Run the container
docker run -p 8000:8000 --env-file .env backend

# Or use docker-compose
docker-compose up
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/logout` - Logout (invalidate token)

### Letters
- `POST /letters/process-images` - Upload and process letter images
- `GET /letters` - List all letters (with filters)
- `GET /letters/{letter_id}` - Get letter details
- `PATCH /letters/{letter_id}` - Update letter properties
- `DELETE /letters/{letter_id}` - Delete letter
- `POST /letters/{letter_id}/snooze` - Snooze letter
- `POST /letters/{letter_id}/archive` - Archive letter
- `POST /letters/{letter_id}/restore` - Restore letter
- `POST /letters/{letter_id}/translate` - Translate letter content

### Chat
- `POST /chat` - Chat with AI about a letter

### Search
- `GET /search` - Search letters by text

### Reminders
- `POST /reminders` - Create reminder
- `GET /reminders` - List reminders
- `PATCH /reminders/{reminder_id}` - Update reminder
- `DELETE /reminders/{reminder_id}` - Delete reminder

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_dynamo.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

## AWS Deployment Options

### Option 1: AWS ECS Fargate (Recommended for FastAPI)

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name backend
   ```

2. **Build and Push Docker Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build image
   docker build -t backend .

   # Tag image
   docker tag backend:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/backend:latest

   # Push image
   docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/backend:latest
   ```

3. **Create ECS Cluster**
   - Go to AWS Console → ECS → Clusters → Create Cluster
   - Choose "Networking only" (Fargate)
   - Name: `letteron-cluster`

4. **Create Task Definition**
   - Launch type: Fargate
   - Task memory: 2GB
   - Task CPU: 1 vCPU
   - Container: Use ECR image URL
   - Port mappings: 8000
   - Environment variables: Add all from `.env`

5. **Create Service**
   - Launch type: Fargate
   - Desired tasks: 2 (for high availability)
   - Load balancer: Application Load Balancer
   - Target group: Port 8000

6. **Configure Application Load Balancer**
   - Create ALB with public subnets
   - Configure health check: `/health`
   - SSL certificate (optional but recommended)

### Option 2: AWS Lambda + API Gateway

You can deploy FastAPI to Lambda using Mangum adapter:

1. Install Mangum: `pip install mangum`
2. Wrap FastAPI app in `app/main.py`:
   ```python
   from mangum import Mangum
   handler = Mangum(app)
   ```
3. Package code: `zip -r function.zip .`
4. Create Lambda function with Python 3.10 runtime
5. Upload ZIP file
6. Create API Gateway HTTP API
7. Integrate with Lambda function

### Option 3: EC2 Instance

1. Launch EC2 instance (t3.medium or larger)
2. Install Docker
3. Clone repository
4. Run with docker-compose
5. Configure security group to allow port 8000
6. Set up nginx reverse proxy (optional)
7. Configure SSL with Let's Encrypt (optional)

## Deployment Script

Use the provided deployment script for automated ECS deployment:

```bash
chmod +x deploy_aws.sh
./deploy_aws.sh
```

## Production Considerations

1. **Security**
   - Use AWS Secrets Manager for sensitive credentials
   - Enable HTTPS/TLS
   - Implement rate limiting
   - Add request validation and sanitization
   - Enable CORS only for trusted origins

2. **Performance**
   - Enable DynamoDB auto-scaling or use on-demand
   - Use CloudFront CDN for S3 images
   - Implement caching (Redis/ElastiCache)
   - Use connection pooling for DynamoDB

3. **Monitoring**
   - CloudWatch Logs for application logs
   - CloudWatch Metrics for custom metrics
   - AWS X-Ray for distributed tracing
   - Set up alarms for errors and latency

4. **Backup & Disaster Recovery**
   - Enable DynamoDB point-in-time recovery
   - S3 versioning for images
   - Cross-region replication (optional)

## Reminder Scheduler

The reminder system includes:
- Background task that checks reminders every minute (local development)
- Lambda function skeleton for production (`reminder_worker`)

To deploy the reminder worker Lambda:

1. Create a new Lambda function: `LetterOnReminderWorker`
2. Add CloudWatch Events rule (EventBridge):
   - Schedule expression: `rate(1 minute)`
   - Target: Lambda function `LetterOnReminderWorker`
3. Grant Lambda permissions to access DynamoDB and invoke LLM Lambda

## Troubleshooting

### Lambda Invocation Errors
- Check Lambda function names match environment variables
- Verify IAM permissions for Lambda invocation
- Check Lambda function logs in CloudWatch

### DynamoDB Access Errors
- Verify table names match environment variables
- Check IAM permissions for DynamoDB read/write
- Ensure GSI indexes are created correctly

### S3 Upload Errors
- Verify bucket name matches environment variable
- Check IAM permissions for S3 PutObject
- Ensure bucket exists and is in the same region

### JWT Token Issues
- Ensure SECRET_KEY is at least 32 characters
- Check token expiration time
- Verify token is sent in Authorization header

## Project Structure Details

- **app/main.py** - FastAPI application entry point, route registration
- **app/settings.py** - Configuration management using Pydantic
- **app/models.py** - Request/response schemas and data models
- **app/services/lambda_client.py** - Wrapper for AWS Lambda invocations
- **app/services/s3_client.py** - S3 upload/download operations
- **app/services/dynamo.py** - DynamoDB CRUD operations
- **app/services/auth.py** - JWT token generation and verification
- **app/api/** - API route handlers organized by domain
- **app/prompts/** - LLM prompt templates for analysis and chat
- **tests/** - Unit and integration tests

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub or contact the development team.
