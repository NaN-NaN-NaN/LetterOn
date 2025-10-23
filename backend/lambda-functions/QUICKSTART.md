# Lambda Functions - Quick Start Guide

## Deploy in 5 Minutes

### Step 1: Prerequisites

Ensure you have:
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ AWS credentials with Lambda, IAM, Textract, and Bedrock permissions
- ✅ Region set to `eu-central-1` (or update scripts to your region)

### Step 2: Deploy Functions

```bash
cd lambda-functions
./deploy-all.sh
```

This will:
1. Create IAM roles and policies
2. Package and deploy both Lambda functions
3. Configure environment variables
4. Run basic tests

### Step 3: Enable Bedrock Model Access

⚠️ **CRITICAL**: Before using the LLM handler:

1. Go to: https://console.aws.amazon.com/bedrock/home?region=eu-central-1#/modelaccess
2. Click "Manage model access"
3. Enable: **Anthropic Claude 3.5 Sonnet**
4. Wait ~5 minutes for activation

### Step 4: Test the Functions

**Test OCR Handler:**
```bash
# Upload a test image to S3 first
aws s3 cp test-letter.jpg s3://letteron-images/test/

# Invoke the function
aws lambda invoke \
  --function-name LetterOnOCRHandler \
  --payload '{"s3_keys":["test/test-letter.jpg"]}' \
  response.json

cat response.json | python3 -m json.tool
```

**Test LLM Handler:**
```bash
aws lambda invoke \
  --function-name LetterOnLLMHandler \
  --payload '{"letter_content":"Dear Customer, Your electricity bill for January is $125.50. Please pay by Jan 31.","task":"analyze"}' \
  response.json

cat response.json | python3 -m json.tool
```

### Step 5: Verify Backend Configuration

Check that your backend `.env` has:
```env
LAMBDA_OCR_FUNCTION_NAME=LetterOnOCRHandler
LAMBDA_LLM_FUNCTION_NAME=LetterOnLLMHandler
```

✅ **Done!** Your Lambda functions are ready to use.

## Common Commands

### View Logs
```bash
# OCR logs
aws logs tail /aws/lambda/LetterOnOCRHandler --follow

# LLM logs
aws logs tail /aws/lambda/LetterOnLLMHandler --follow
```

### Update Functions
```bash
# Re-run deployment to update
./deploy-ocr-handler.sh
./deploy-llm-handler.sh
```

### Check Status
```bash
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `LetterOn`)].FunctionName'
```

## Troubleshooting

### "Access Denied" Error
- Check IAM permissions for your AWS user
- Ensure Lambda execution role has correct policies
- Verify S3 bucket permissions

### "Model not found" for Bedrock
- Enable Bedrock model access (Step 3)
- Wait 5-10 minutes after enabling
- Check you're in the correct region

### Lambda Timeout
- Default is 300 seconds (5 min)
- Increase if needed for large images/long letters
- Check CloudWatch Logs for actual duration

## What's Next?

1. **Integration**: Your FastAPI backend can now invoke these functions
2. **Monitoring**: Set up CloudWatch alarms for errors
3. **Optimization**: Tune memory and timeout based on usage
4. **Scaling**: Configure concurrency limits if needed

See [README.md](README.md) for detailed documentation.
