# LetterOn Lambda Functions - Complete Summary

## 📦 What's Been Created

I've created two AWS Lambda functions for your LetterOn application with complete deployment automation.

### Directory Structure

```
backend/lambda-functions/
├── README.md                      # Complete documentation
├── QUICKSTART.md                  # 5-minute deployment guide
├── deploy-all.sh                  # Deploy both functions
├── deploy-ocr-handler.sh          # Deploy OCR handler only
├── deploy-llm-handler.sh          # Deploy LLM handler only
│
├── ocr-handler/
│   ├── lambda_function.py         # OCR processing code
│   └── requirements.txt           # Dependencies (boto3)
│
├── llm-handler/
│   ├── lambda_function.py         # LLM analysis code
│   └── requirements.txt           # Dependencies (boto3)
│
└── iam-policies/
    ├── ocr-handler-policy.json    # IAM policy for OCR
    └── llm-handler-policy.json    # IAM policy for LLM
```

## 🎯 Function Overview

### 1. LetterOnOCRHandler

**What it does**: Extracts text from letter images using AWS Textract

**Input**:
```json
{
  "s3_keys": ["letters/image1.jpg"],
  "bucket": "letteron-images"
}
```

**Output**:
```json
{
  "ocr_results": [{
    "s3_key": "letters/image1.jpg",
    "text": "Dear Customer...",
    "confidence": 95.5,
    "line_count": 12
  }]
}
```

**AWS Services Used**:
- AWS Textract (OCR)
- S3 (image storage)
- CloudWatch Logs

**Configuration**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 5 minutes
- Cost: ~$0.0015 per letter

---

### 2. LetterOnLLMHandler

**What it does**: AI-powered letter analysis using Claude via AWS Bedrock

**Capabilities**:
1. **Analyze**: Categorize letters (bill, official, personal, etc.)
2. **Summarize**: Create concise summaries
3. **Suggest Reply**: Generate draft responses
4. **Chat**: Q&A about letter content

**Input (analyze)**:
```json
{
  "letter_content": "Dear Customer, Your bill is $125.50...",
  "task": "analyze"
}
```

**Output (analyze)**:
```json
{
  "category": "bill",
  "action_status": "action-needed",
  "summary": "Electricity bill for $125.50 due Jan 31",
  "key_points": ["Amount: $125.50", "Due: Jan 31, 2024"],
  "suggested_actions": ["Pay by January 31, 2024"],
  "due_date": "2024-01-31",
  "amount": 125.50
}
```

**AWS Services Used**:
- AWS Bedrock (Claude 3.5 Sonnet)
- CloudWatch Logs

**Configuration**:
- Runtime: Python 3.11
- Memory: 1024 MB
- Timeout: 5 minutes
- Cost: ~$0.01-0.05 per letter

## 🚀 Deployment Instructions

### Quick Deploy (Recommended)

```bash
cd backend/lambda-functions
./deploy-all.sh
```

This will:
1. ✅ Create IAM roles and policies
2. ✅ Package Lambda functions
3. ✅ Deploy to AWS
4. ✅ Configure environment variables
5. ✅ Run basic tests

### Prerequisites

Before deploying:

1. **AWS CLI configured**:
   ```bash
   aws configure
   # Enter your AWS credentials
   # Region: eu-central-1
   ```

2. **Enable Bedrock Model Access** (for LLM handler):
   - Go to: https://console.aws.amazon.com/bedrock/home?region=eu-central-1#/modelaccess
   - Enable: **Anthropic Claude 3.5 Sonnet**
   - Wait 5-10 minutes for activation

3. **S3 Bucket exists**:
   ```bash
   aws s3 ls s3://letteron-images/
   ```

### Deployment Steps

1. **Deploy both functions**:
   ```bash
   cd backend/lambda-functions
   ./deploy-all.sh
   ```

2. **Enable Bedrock** (if not done already):
   - Visit Bedrock console
   - Enable Claude 3.5 Sonnet model access

3. **Test OCR Handler**:
   ```bash
   aws lambda invoke \
     --function-name LetterOnOCRHandler \
     --payload '{"s3_keys":["test/sample.jpg"]}' \
     response.json
   ```

4. **Test LLM Handler**:
   ```bash
   aws lambda invoke \
     --function-name LetterOnLLMHandler \
     --payload '{"letter_content":"Test","task":"analyze"}' \
     response.json
   ```

## 🔧 Backend Integration

Your FastAPI backend is already configured to use these functions. The `.env` file has:

```env
LAMBDA_OCR_FUNCTION_NAME=LetterOnOCRHandler
LAMBDA_LLM_FUNCTION_NAME=LetterOnLLMHandler
```

### Example Usage in Backend

The backend can invoke these functions through the service layer:

```python
# In your FastAPI route
from app.services.ocr import process_images
from app.services.llm import analyze_letter

# Process OCR
ocr_results = await process_images(
    s3_keys=["letters/image1.jpg"],
    bucket="letteron-images"
)

# Analyze with AI
analysis = await analyze_letter(
    letter_content=ocr_results[0]['text'],
    sender_info={"name": "John Doe"}
)
```

## 💰 Cost Estimation

### Monthly Costs (1,000 letters)

| Service | Cost | Notes |
|---------|------|-------|
| Lambda Invocations | Free | Within free tier (1M requests/month) |
| AWS Textract | ~$1.50 | $1.50 per 1,000 pages |
| AWS Bedrock (Claude) | ~$10-50 | Depends on letter length |
| **Total** | **~$12-52** | Per 1,000 letters processed |

### Cost Optimization Tips

1. **Cache results**: Don't re-analyze the same letter
2. **Batch processing**: Process multiple images together
3. **Use provisioned capacity**: For consistent high volume
4. **Monitor usage**: Set up CloudWatch billing alarms

## 📊 Monitoring

### View Logs

```bash
# OCR Handler logs
aws logs tail /aws/lambda/LetterOnOCRHandler --follow

# LLM Handler logs
aws logs tail /aws/lambda/LetterOnLLMHandler --follow
```

### Check Function Status

```bash
# List functions
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `LetterOn`)]'

# Get function details
aws lambda get-function --function-name LetterOnOCRHandler
```

### Set Up Alarms

```bash
# Create error alarm
aws cloudwatch put-metric-alarm \
  --alarm-name LetterOnOCRErrors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=LetterOnOCRHandler
```

## 🔍 Troubleshooting

### Common Issues

**1. "Access Denied" when deploying**
```bash
# Check your AWS credentials
aws sts get-caller-identity

# Ensure you have required permissions:
# - IAM: Create roles and policies
# - Lambda: Create and manage functions
```

**2. "Model not found" in LLM handler**
```bash
# Enable Bedrock model access
# Go to: https://console.aws.amazon.com/bedrock/
# Enable: Anthropic Claude 3.5 Sonnet
# Wait 5-10 minutes
```

**3. OCR handler can't read S3 images**
```bash
# Check IAM role has S3 read permission
aws iam get-role-policy \
  --role-name LetterOnOCRHandlerRole \
  --policy-name LetterOnOCRHandlerRolePolicy

# Verify image exists
aws s3 ls s3://letteron-images/letters/
```

**4. Lambda timeout**
```bash
# Increase timeout (max 15 minutes)
aws lambda update-function-configuration \
  --function-name LetterOnOCRHandler \
  --timeout 600
```

## 🔄 Updating Functions

### Update Code

Just re-run the deployment script:
```bash
./deploy-ocr-handler.sh  # Updates if exists
```

### Update Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name LetterOnOCRHandler \
  --environment "Variables={S3_BUCKET_NAME=new-bucket}"
```

### Rollback

```bash
# List versions
aws lambda list-versions-by-function --function-name LetterOnOCRHandler

# Rollback to previous version
aws lambda update-alias \
  --function-name LetterOnOCRHandler \
  --name production \
  --function-version 1
```

## 🗑️ Cleanup

If you need to remove everything:

```bash
# Delete Lambda functions
aws lambda delete-function --function-name LetterOnOCRHandler
aws lambda delete-function --function-name LetterOnLLMHandler

# Delete IAM roles (detach policies first)
aws iam detach-role-policy \
  --role-name LetterOnOCRHandlerRole \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/LetterOnOCRHandlerRolePolicy

aws iam delete-role --role-name LetterOnOCRHandlerRole

# Similar for LLM handler role
```

## 📚 Documentation

- **README.md**: Complete documentation with examples
- **QUICKSTART.md**: 5-minute deployment guide
- **Lambda Functions Code**: Fully commented with docstrings
- **IAM Policies**: JSON files with explanations

## 🎉 What You Get

After deployment, you have:

✅ **Two production-ready Lambda functions**
✅ **Automated deployment scripts**
✅ **IAM roles and policies configured**
✅ **Comprehensive documentation**
✅ **Testing commands and examples**
✅ **Monitoring and logging setup**
✅ **Cost optimization tips**

## 🔗 Integration Flow

```
User uploads letter images
         ↓
FastAPI backend receives images
         ↓
Backend uploads to S3
         ↓
Backend invokes LetterOnOCRHandler
         ↓
OCR extracts text from images
         ↓
Backend invokes LetterOnLLMHandler
         ↓
Claude analyzes and categorizes
         ↓
Backend stores results in DynamoDB
         ↓
User sees analyzed letter in UI
```

## 🚦 Next Steps

1. ✅ **Deploy functions**: `./deploy-all.sh`
2. ✅ **Enable Bedrock**: Model access for Claude
3. ✅ **Test functions**: Run test commands
4. ✅ **Monitor logs**: Check CloudWatch
5. ✅ **Integrate with backend**: Already configured!

## 📞 Support

For issues:
1. Check CloudWatch Logs for errors
2. Review IAM permissions
3. Verify Bedrock model access
4. Test functions individually
5. Check AWS service quotas

---

**Ready to deploy?** Run `./deploy-all.sh` and your Lambda functions will be live in 5 minutes! 🚀
