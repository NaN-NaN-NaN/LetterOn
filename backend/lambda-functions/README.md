# LetterOn Lambda Functions

This directory contains AWS Lambda functions for the LetterOn application.

## Overview

| Function | Purpose | AWS Services Used |
|----------|---------|-------------------|
| **LetterOnOCRHandler** | Extract text from letter images | AWS Textract, S3 |
| **LetterOnLLMHandler** | AI-powered letter analysis and chat | AWS Bedrock (Claude) |

## Architecture

```
┌─────────────┐
│   FastAPI   │
│   Backend   │
└──────┬──────┘
       │
       ├─────► LetterOnOCRHandler ──► AWS Textract ──► Text Output
       │
       └─────► LetterOnLLMHandler ──► AWS Bedrock ──► AI Analysis
```

## Prerequisites

### 1. AWS CLI Configuration

Make sure AWS CLI is installed and configured:

```bash
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `eu-central-1`

### 2. Required AWS Permissions

Your AWS user/role needs these permissions:
- IAM: Create roles and policies
- Lambda: Create and manage functions
- Textract: Detect and analyze documents
- Bedrock: Invoke models
- S3: Read objects from your bucket
- CloudWatch Logs: Create log groups and streams

### 3. Enable Bedrock Model Access

**IMPORTANT**: Before using the LLM handler, enable Bedrock model access:

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" in the left sidebar
3. Click "Manage model access"
4. Enable: **Anthropic Claude 3.5 Sonnet**
5. Click "Save changes"
6. Wait for access to be granted (usually a few minutes)

## Quick Start

### Deploy All Functions

```bash
cd lambda-functions
./deploy-all.sh
```

This will deploy both Lambda functions with all necessary IAM roles and policies.

### Deploy Individual Functions

```bash
# Deploy only OCR handler
./deploy-ocr-handler.sh

# Deploy only LLM handler
./deploy-llm-handler.sh
```

## Function Details

### LetterOnOCRHandler

**Purpose**: Extract text from images using AWS Textract

**Input**:
```json
{
  "s3_keys": ["letters/image1.jpg", "letters/image2.jpg"],
  "bucket": "letteron-images"
}
```

**Output**:
```json
{
  "statusCode": 200,
  "body": {
    "ocr_results": [
      {
        "s3_key": "letters/image1.jpg",
        "text": "Extracted text from the image...",
        "confidence": 95.5,
        "line_count": 12,
        "blocks": [...]
      }
    ],
    "total_processed": 1
  }
}
```

**Configuration**:
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Environment Variables**:
  - `S3_BUCKET_NAME`: Your S3 bucket for images

**Testing**:
```bash
aws lambda invoke \
  --function-name LetterOnOCRHandler \
  --payload '{"s3_keys":["test/sample.jpg"],"bucket":"letteron-images"}' \
  response.json

cat response.json | python3 -m json.tool
```

---

### LetterOnLLMHandler

**Purpose**: AI-powered letter analysis using Claude via AWS Bedrock

**Tasks Supported**:
1. **analyze** - Categorize and extract key information
2. **summarize** - Create concise summaries
3. **suggest_reply** - Generate reply suggestions
4. **chat** - Q&A about letter content

**Input (analyze)**:
```json
{
  "letter_content": "Dear Customer, Your bill is $125.50...",
  "ocr_text": "Additional OCR extracted text...",
  "sender_info": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "task": "analyze"
}
```

**Output (analyze)**:
```json
{
  "statusCode": 200,
  "body": {
    "category": "bill",
    "action_status": "action-needed",
    "summary": "Electricity bill for $125.50 due by Jan 31, 2024",
    "key_points": [
      "Bill amount: $125.50",
      "Due date: January 31, 2024",
      "Account: Electricity"
    ],
    "suggested_actions": [
      "Pay by January 31, 2024",
      "Set up automatic payment"
    ],
    "due_date": "2024-01-31",
    "amount": 125.50,
    "confidence": "high"
  }
}
```

**Configuration**:
- **Runtime**: Python 3.11
- **Memory**: 1024 MB (higher for AI processing)
- **Timeout**: 300 seconds (5 minutes)
- **Model**: Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0)

**Testing**:
```bash
aws lambda invoke \
  --function-name LetterOnLLMHandler \
  --payload '{"letter_content":"Test letter","task":"analyze"}' \
  response.json

cat response.json | python3 -m json.tool
```

## IAM Policies

### OCR Handler Policy

Located at: `iam-policies/ocr-handler-policy.json`

Permissions:
- CloudWatch Logs (write)
- S3 GetObject (read images)
- Textract DetectDocumentText and AnalyzeDocument

### LLM Handler Policy

Located at: `iam-policies/llm-handler-policy.json`

Permissions:
- CloudWatch Logs (write)
- Bedrock InvokeModel (Claude models)

## Integration with Backend

### Update Backend Configuration

After deploying, your backend `.env` should have:

```env
LAMBDA_OCR_FUNCTION_NAME=LetterOnOCRHandler
LAMBDA_LLM_FUNCTION_NAME=LetterOnLLMHandler
```

### Using from FastAPI Backend

The backend already has service modules to invoke these functions:

```python
# OCR Processing
from app.services.ocr import process_images

results = await process_images(
    s3_keys=["letters/image1.jpg"],
    bucket="letteron-images"
)

# LLM Analysis
from app.services.llm import analyze_letter

analysis = await analyze_letter(
    letter_content="Letter text...",
    ocr_text="OCR text...",
    sender_info={"name": "John", "email": "john@example.com"}
)
```

## Monitoring and Logs

### View Lambda Logs

```bash
# OCR Handler logs
aws logs tail /aws/lambda/LetterOnOCRHandler --follow

# LLM Handler logs
aws logs tail /aws/lambda/LetterOnLLMHandler --follow
```

### Check Function Status

```bash
# Get function configuration
aws lambda get-function-configuration --function-name LetterOnOCRHandler

# List all Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `LetterOn`)].FunctionName'
```

### Monitor Invocations

View metrics in AWS Console:
1. Go to [Lambda Console](https://console.aws.amazon.com/lambda/)
2. Select your function
3. Click "Monitor" tab
4. View invocations, duration, errors, and throttles

## Cost Estimation

### OCR Handler
- **Textract**: $1.50 per 1,000 pages (DetectDocumentText)
- **Lambda**: Free tier includes 1M requests/month
- **Estimate**: ~$0.0015 per letter (1 page)

### LLM Handler
- **Bedrock (Claude 3.5 Sonnet)**:
  - Input: $3.00 per million tokens
  - Output: $15.00 per million tokens
- **Lambda**: Free tier includes 1M requests/month
- **Estimate**: ~$0.01-0.05 per letter analysis (depending on length)

**Example monthly costs** (1,000 letters/month):
- OCR: ~$1.50
- LLM Analysis: ~$10-50
- **Total**: ~$12-52/month

## Troubleshooting

### OCR Handler Issues

**Error: "Access Denied" for S3**
- Check that the IAM role has `s3:GetObject` permission
- Verify the S3 bucket name is correct
- Ensure images exist in the bucket

**Error: "Textract operation timed out"**
- Increase Lambda timeout (default is 300 seconds)
- Check image size (max 5MB for Textract)

### LLM Handler Issues

**Error: "You don't have access to the model"**
- Enable Bedrock model access (see Prerequisites)
- Wait a few minutes for access to propagate
- Verify you're in a region that supports Bedrock

**Error: "Rate exceeded"**
- Implement exponential backoff in your backend
- Consider using Lambda concurrency limits
- Upgrade to Bedrock provisioned throughput for higher rates

**Response is cut off**
- Increase `max_tokens` in the function code
- Default is 2000 tokens (~1500 words)

## Updating Functions

### Update Function Code

```bash
cd lambda-functions
./deploy-ocr-handler.sh  # Updates if already exists
```

### Update Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name LetterOnOCRHandler \
  --environment "Variables={S3_BUCKET_NAME=new-bucket-name}"
```

### Update IAM Permissions

Edit the policy JSON in `iam-policies/`, then:

```bash
aws iam create-policy-version \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/LetterOnOCRHandlerRolePolicy \
  --policy-document file://iam-policies/ocr-handler-policy.json \
  --set-as-default
```

## Cleanup

### Delete Lambda Functions

```bash
aws lambda delete-function --function-name LetterOnOCRHandler
aws lambda delete-function --function-name LetterOnLLMHandler
```

### Delete IAM Roles and Policies

```bash
# Detach policies
aws iam detach-role-policy \
  --role-name LetterOnOCRHandlerRole \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/LetterOnOCRHandlerRolePolicy

# Delete policy
aws iam delete-policy \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/LetterOnOCRHandlerRolePolicy

# Delete role
aws iam delete-role --role-name LetterOnOCRHandlerRole
```

## Advanced Configuration

### Using VPC

To access resources in a VPC (e.g., private databases):

```bash
aws lambda update-function-configuration \
  --function-name LetterOnOCRHandler \
  --vpc-config SubnetIds=subnet-xxx,SecurityGroupIds=sg-xxx
```

### Provisioned Concurrency

For consistent performance:

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name LetterOnLLMHandler \
  --provisioned-concurrent-executions 2
```

### Environment-Specific Deployments

Use function aliases for different environments:

```bash
# Create alias
aws lambda create-alias \
  --function-name LetterOnOCRHandler \
  --name production \
  --function-version 1

# Update backend to use: LetterOnOCRHandler:production
```

## Support

For issues or questions:
1. Check CloudWatch Logs for detailed error messages
2. Review AWS documentation for Textract and Bedrock
3. Verify IAM permissions are correct
4. Test functions individually before backend integration

## License

Copyright © 2024 LetterOn. All rights reserved.
