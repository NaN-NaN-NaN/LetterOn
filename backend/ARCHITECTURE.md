# LetterOn Server - Architecture Documentation

## System Overview

LetterOn Server is a Python FastAPI backend that processes physical letters using AI. It integrates with existing AWS Lambda functions for OCR and LLM processing, uses DynamoDB for data persistence, and S3 for image storage.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│              HTTP/REST API (JWT Authentication)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Routes Layer                                         │  │
│  │  • /auth      - Authentication endpoints                 │  │
│  │  • /letters   - Letter CRUD, upload, process             │  │
│  │  • /chat      - Conversational AI                        │  │
│  │  • /search    - Full-text search                         │  │
│  │  • /reminders - Reminder management                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                            │  │
│  │  • Lambda Client    - Invoke OCR/LLM Lambdas            │  │
│  │  • S3 Client        - Image upload/download              │  │
│  │  • DynamoDB Client  - Database operations                │  │
│  │  • Auth Service     - JWT token management               │  │
│  │  • Scheduler        - Background reminder checks         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────┬──────────────┬──────────────┬─────────────────┘
                 │              │              │
                 ▼              ▼              ▼
    ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │   AWS Lambda   │ │   AWS S3     │ │  AWS DynamoDB    │
    │                │ │              │ │                  │
    │ • OCR Handler  │ │ • Letter     │ │ • Users          │
    │   (Textract)   │ │   Images     │ │ • Letters        │
    │                │ │              │ │ • Reminders      │
    │ • LLM Handler  │ │              │ │ • Conversations  │
    │   (Bedrock)    │ │              │ │                  │
    └────────────────┘ └──────────────┘ └──────────────────┘
```

## Project Structure

```
backend/
├── app/                          # Application code
│   ├── api/                      # API route handlers
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── letters.py            # Letter CRUD and processing
│   │   ├── chat.py               # Conversational AI
│   │   ├── search.py             # Search functionality
│   │   └── reminders.py          # Reminder management
│   │
│   ├── services/                 # Business logic and AWS clients
│   │   ├── lambda_client.py      # Lambda invocation wrapper
│   │   ├── s3_client.py          # S3 operations
│   │   ├── dynamo.py             # DynamoDB access layer
│   │   ├── auth.py               # JWT and password hashing
│   │   └── reminder_scheduler.py # Background task scheduler
│   │
│   ├── utils/                    # Utility functions
│   │   ├── logger.py             # Structured logging
│   │   └── helpers.py            # Helper functions
│   │
│   ├── prompts/                  # LLM prompt templates
│   │   ├── analyze_prompt.txt    # Letter analysis prompt
│   │   └── chat_prompt.txt       # Chat conversation prompt
│   │
│   ├── main.py                   # FastAPI app entry point
│   ├── settings.py               # Configuration management
│   ├── models.py                 # Pydantic data models
│   └── dependencies.py           # FastAPI dependencies (auth)
│
├── tests/                        # Unit and integration tests
│   ├── test_dynamo.py            # DynamoDB tests (moto)
│   └── test_auth.py              # Auth endpoint tests
│
├── scripts/                      # Utility scripts
│   └── create_dynamodb_tables.py # DynamoDB table setup
│
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container image definition
├── docker-compose.yml            # Local development setup
├── deploy_aws.sh                 # AWS deployment script
├── README.md                     # Full documentation
├── QUICKSTART.md                 # Quick setup guide
└── ARCHITECTURE.md               # This file
```

## Core Components

### 1. API Layer (`app/api/`)

#### Authentication (`auth.py`)
- **POST /auth/register**: Create new user account
- **POST /auth/login**: Authenticate and get JWT token
- **POST /auth/logout**: Invalidate session (client-side)
- **GET /auth/me**: Get current user info

**Technologies:**
- JWT tokens (python-jose)
- bcrypt password hashing (passlib)

#### Letters (`letters.py`)
- **POST /letters/process-images**: Upload images → OCR → AI analysis
- **GET /letters**: List letters with filters
- **GET /letters/{id}**: Get letter details
- **PATCH /letters/{id}**: Update letter properties
- **DELETE /letters/{id}**: Delete letter (soft/hard)
- **POST /letters/{id}/snooze**: Snooze until date
- **POST /letters/{id}/archive**: Archive letter
- **POST /letters/{id}/restore**: Restore letter
- **POST /letters/{id}/translate**: Translate content

**Workflow for Image Processing:**
```
1. User uploads images (max 3, 1MB each)
2. Backend validates and uploads to S3
3. Call LetterOnOCRHandler Lambda with S3 keys
4. Extract text from OCR response
5. Call LetterOnLLMHandler Lambda with analysis prompt
6. Parse structured JSON response
7. Create letter record in DynamoDB
8. Return letter data to frontend
```

#### Chat (`chat.py`)
- **POST /chat**: Ask AI about a letter
- **DELETE /chat/{letter_id}/history**: Clear conversation

**Conversation Flow:**
```
1. Load letter content from DynamoDB
2. Load conversation history (last 50 messages)
3. Build prompt with context
4. Call LLM Lambda for response
5. Save user message and AI response
6. Return AI response with full history
```

#### Search (`search.py`)
- **GET /search?q=query**: Full-text search across letters
- **GET /search/suggestions**: Autocomplete suggestions

**Search Fields:**
- Subject
- Sender name
- Content
- OCR text
- AI suggestions

#### Reminders (`reminders.py`)
- **POST /reminders**: Create reminder for letter
- **GET /reminders**: List user reminders
- **GET /reminders/{id}**: Get reminder details
- **PATCH /reminders/{id}**: Update reminder
- **DELETE /reminders/{id}**: Delete reminder

### 2. Service Layer (`app/services/`)

#### Lambda Client (`lambda_client.py`)
Wrapper for AWS Lambda invocations.

**Key Functions:**
- `invoke_lambda(function_name, payload, sync=True)`
- `invoke_ocr_lambda(s3_keys)` → OCR results
- `invoke_llm_lambda(input_text, prompt_template)` → LLM response

**Integration Points:**
- **LetterOnOCRHandler**: Expects `{bucket, keys}`, returns `{text, pages, metadata}`
- **LetterOnLLMHandler**: Expects `{input_text, prompt_template, temperature}`, returns `{response, metadata}`

#### S3 Client (`s3_client.py`)
Manages letter image storage in S3.

**Key Functions:**
- `upload_letter_image(file_content, letter_id, filename)`
- `generate_presigned_url(s3_key, expiration=3600)`
- `delete_letter_images(letter_id)`

**S3 Structure:**
```
letteron-images/
└── letters/
    └── {letter_id}/
        ├── 20240115_123045_image1.jpg
        ├── 20240115_123046_image2.jpg
        └── 20240115_123047_image3.jpg
```

#### DynamoDB Client (`dynamo.py`)
Complete CRUD layer for all database operations.

**Tables:**
1. **LetterOn-Users**
   - Partition key: `user_id`
   - GSI: `email-index` (for login)

2. **LetterOn-Letters**
   - Partition key: `letter_id`
   - GSI: `user_id-index` + `record_created_at` (for listing)

3. **LetterOn-Reminders**
   - Partition key: `reminder_id`
   - GSI: `user_id-index` (for user reminders)

4. **LetterOn-Conversations**
   - Partition key: `conversation_id`
   - GSI: `letter_id-index` + `timestamp` (for chat history)

**Key Functions:**
- User: `create_user`, `get_user_by_id`, `get_user_by_email`, `update_user`
- Letter: `create_letter`, `get_letter`, `get_letters_by_user`, `update_letter`, `delete_letter`, `search_letters`
- Reminder: `create_reminder`, `get_reminders_by_user`, `get_pending_reminders`, `update_reminder`, `delete_reminder`
- Conversation: `create_conversation_message`, `get_conversation_history`

#### Auth Service (`auth.py`)
JWT token and password management.

**Key Functions:**
- `hash_password(password)` → bcrypt hash
- `verify_password(plain, hashed)` → bool
- `create_access_token(data)` → JWT string
- `verify_token(token)` → user_id or None

**JWT Payload:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "exp": 1705000000,
  "iat": 1704900000
}
```

#### Reminder Scheduler (`reminder_scheduler.py`)
Background task to check and send reminders.

**Implementation:**
- APScheduler runs `check_and_process_reminders()` every 60 seconds
- Queries DynamoDB for pending reminders
- Marks reminders as sent after processing

**Production Deployment:**
- Deploy as separate Lambda function
- Trigger with EventBridge rule: `rate(1 minute)`
- Send notifications via SNS/SES

### 3. Data Models (`app/models.py`)

All Pydantic models for request/response validation.

**Key Enums:**
- `LetterCategory`: 15 letter types (government, billing, insurance, etc.)
- `ActionStatus`: require-action, action-done, no-action-needed
- `MessageRole`: user, assistant

**Request Models:**
- `UserRegisterRequest`, `UserLoginRequest`
- `LetterUpdate`, `ImageProcessRequest`
- `ChatRequest`, `ReminderCreate`

**Response Models:**
- `AuthResponse`, `LetterResponse`, `ChatResponse`
- `ReminderResponse`, `SearchResponse`

### 4. Configuration (`app/settings.py`)

Centralized configuration using Pydantic Settings.

**Environment Variables:**
```bash
# Security
SECRET_KEY                    # JWT signing key (min 32 chars)

# AWS
AWS_REGION                    # us-east-1
AWS_ACCESS_KEY_ID            # (optional, uses default boto3)
AWS_SECRET_ACCESS_KEY        # (optional, uses default boto3)

# Services
S3_BUCKET_NAME               # letteron-images
LAMBDA_OCR_FUNCTION_NAME     # LetterOnOCRHandler
LAMBDA_LLM_FUNCTION_NAME     # LetterOnLLMHandler

# DynamoDB
DYNAMODB_USERS_TABLE         # LetterOn-Users
DYNAMODB_LETTERS_TABLE       # LetterOn-Letters
DYNAMODB_REMINDERS_TABLE     # LetterOn-Reminders
DYNAMODB_CONVERSATIONS_TABLE # LetterOn-Conversations

# Application
DEBUG                        # true/false
LOG_LEVEL                    # INFO/DEBUG/WARNING
CORS_ORIGINS                 # http://localhost:3000,http://localhost:5173
```

## Data Flow

### 1. User Registration/Login
```
1. Frontend → POST /auth/register {name, email, password}
2. Backend validates input
3. Hash password with bcrypt
4. Create user in DynamoDB
5. Generate JWT token
6. Return {token, user}
```

### 2. Letter Processing
```
1. Frontend → POST /letters/process-images (multipart form with images)
2. Backend validates files (size, type, count)
3. Generate letter_id (UUID)
4. Upload images to S3: letters/{letter_id}/timestamp_filename.jpg
5. Call LetterOnOCRHandler Lambda with S3 keys
6. Receive OCR text
7. Build analysis prompt from template
8. Call LetterOnLLMHandler Lambda with OCR text + prompt
9. Parse JSON response (subject, category, action_status, etc.)
10. Create letter record in DynamoDB
11. Return structured letter data to frontend
```

### 3. Chat Interaction
```
1. Frontend → POST /chat {letter_id, message}
2. Backend loads letter from DynamoDB
3. Load conversation history (last 50 messages)
4. Build chat prompt with context
5. Call LetterOnLLMHandler Lambda
6. Save user message to DynamoDB
7. Save AI response to DynamoDB
8. Return {message, conversation_history}
```

### 4. Reminder Processing
```
Background Scheduler (every 60 seconds):
1. Query DynamoDB for reminders where:
   - sent = false
   - reminder_time <= current_time
2. For each pending reminder:
   - Process reminder (log/email/notification)
   - Update reminder: sent = true
3. Repeat
```

## Authentication & Security

### JWT Authentication Flow
```
1. User logs in with email/password
2. Server verifies credentials against DynamoDB
3. Server generates JWT token with user_id and email
4. Frontend stores token (localStorage/sessionStorage)
5. All subsequent requests include: Authorization: Bearer {token}
6. Server validates token on every protected endpoint
7. Extract user_id from token, verify user exists
8. Allow request to proceed
```

### Protected Endpoints
All endpoints except `/health`, `/auth/register`, `/auth/login` require JWT token.

**Dependency Injection:**
```python
@router.get("/letters")
async def list_letters(user_id: str = Depends(get_current_user_id)):
    # user_id is automatically extracted from JWT token
    ...
```

### Security Best Practices
1. **Password Hashing**: bcrypt with automatic salt
2. **JWT Expiration**: 24 hours (configurable)
3. **CORS**: Restrict origins to frontend URLs
4. **Input Validation**: Pydantic models validate all inputs
5. **AWS Permissions**: Least privilege IAM roles
6. **Secrets**: Use AWS Secrets Manager in production
7. **HTTPS**: Always use TLS in production

## Deployment

### Local Development
```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your values
python scripts/create_dynamodb_tables.py

# Run
uvicorn app.main:app --reload --port 8000
```

### Docker
```bash
docker build -t backend .
docker run -p 8000:8000 --env-file .env backend
```

### AWS ECS Fargate (Recommended)
```bash
./deploy_aws.sh
```

**Architecture:**
```
Internet
   ↓
Application Load Balancer (ALB)
   ↓
ECS Service (2+ tasks for HA)
   ↓
Fargate Tasks (Docker containers)
   ↓
VPC with private/public subnets
```

**Required AWS Resources:**
- ECR repository for Docker image
- ECS cluster
- ECS task definition (1 vCPU, 2GB RAM)
- ECS service with auto-scaling
- Application Load Balancer
- CloudWatch Logs group
- IAM roles (task execution + task role)

### AWS Lambda (Alternative)
Use Mangum adapter to wrap FastAPI:
```python
from mangum import Mangum
handler = Mangum(app)
```

## Monitoring & Observability

### CloudWatch Logs
All logs are JSON-formatted for easy parsing:
```json
{
  "timestamp": "2024-01-15T12:34:56",
  "level": "INFO",
  "logger": "app.api.letters",
  "message": "Letter created",
  "letter_id": "abc123",
  "user_id": "xyz789"
}
```

### Key Metrics to Monitor
- API request latency (p50, p95, p99)
- Lambda invocation success rate
- DynamoDB read/write capacity
- S3 upload success rate
- JWT token validation errors
- 4xx/5xx error rates

### CloudWatch Alarms (Recommended)
- API 5xx errors > 1% for 5 minutes
- Lambda errors > 5% for 5 minutes
- DynamoDB throttling detected
- ECS task unhealthy

## Performance Optimization

### Current Performance
- Typical request latency: 50-200ms (excluding Lambda)
- OCR processing: 2-5 seconds per image
- LLM analysis: 3-8 seconds
- Image upload: 500ms-2s depending on size

### Optimization Strategies

1. **Caching**
   - Cache letter data in Redis (5 min TTL)
   - Cache OCR results (permanent)
   - Cache user data (1 hour TTL)

2. **Database**
   - Use DynamoDB on-demand billing
   - Add read replicas for global access
   - Implement batch operations

3. **Lambda**
   - Use provisioned concurrency for LLM Lambda
   - Optimize Lambda memory/CPU allocation
   - Implement response caching

4. **CDN**
   - Serve S3 images via CloudFront
   - Cache static assets
   - Use presigned URLs with long expiration

5. **Async Processing**
   - Make OCR/LLM processing asynchronous
   - Use SQS queue for image processing
   - Return immediately, notify via WebSocket

## Testing Strategy

### Unit Tests (`tests/`)
- Mock AWS services with moto
- Test business logic in isolation
- Fast execution (< 5 seconds)

```bash
pytest tests/test_dynamo.py -v
pytest tests/test_auth.py -v
```

### Integration Tests
- Use LocalStack for AWS services
- Test end-to-end workflows
- Verify Lambda integrations

### Load Testing
```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Locust
locust -f locustfile.py --host http://localhost:8000
```

## Troubleshooting

### Common Issues

1. **"Invalid or expired token"**
   - Check SECRET_KEY is consistent
   - Verify token hasn't expired (24h default)
   - Ensure Authorization header format: `Bearer {token}`

2. **"Lambda invocation failed"**
   - Verify Lambda function names in .env
   - Check IAM permissions for Lambda invoke
   - Review Lambda function logs in CloudWatch

3. **"Table not found"**
   - Run `python scripts/create_dynamodb_tables.py`
   - Verify table names in .env match DynamoDB
   - Check AWS region is correct

4. **"Access Denied" (S3/DynamoDB)**
   - Verify AWS credentials
   - Check IAM role permissions
   - Ensure resources exist in correct region

## Future Enhancements

### Phase 2
- [ ] Email notifications for reminders (SES)
- [ ] Push notifications (SNS/FCM)
- [ ] Bulk operations (batch delete, archive)
- [ ] Export letters (PDF, CSV)
- [ ] Advanced search (Elasticsearch/OpenSearch)

### Phase 3
- [ ] Multi-user organizations/teams
- [ ] Role-based access control (RBAC)
- [ ] Audit logging
- [ ] GraphQL API
- [ ] WebSocket support for real-time updates

### Phase 4
- [ ] Mobile app backend
- [ ] Machine learning for category prediction
- [ ] OCR confidence scoring
- [ ] Duplicate letter detection
- [ ] Automated bill payment integration

## Contributing

### Development Workflow
1. Create feature branch
2. Write code + tests
3. Run `pytest tests/ -v`
4. Ensure test coverage > 80%
5. Submit PR with description

### Code Style
- PEP 8 for Python code
- Type hints for all functions
- Docstrings for public APIs
- Comments for complex logic

## Support

- **Documentation**: See README.md
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Issues**: GitHub Issues
- **Email**: support@letteron.com

---

**Version**: 1.0.0
**Last Updated**: January 2024
**Maintained By**: LetterOn Development Team
