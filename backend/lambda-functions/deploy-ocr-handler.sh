#!/bin/bash
# Deploy LetterOn OCR Handler Lambda Function
set -e

echo "=========================================="
echo "Deploying OCR Handler Lambda Function"
echo "=========================================="

# Load environment variables from .env file
ENV_FILE="../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    echo ""
    echo "Please create a .env file with the following contents:"
    echo ""
    echo "AWS_ACCESS_KEY_ID=your_access_key_here"
    echo "AWS_SECRET_ACCESS_KEY=your_secret_key_here"
    echo "AWS_SESSION_TOKEN=your_session_token_here  # Optional, for temporary credentials"
    echo "AWS_REGION=eu-central-1  # Optional, defaults to eu-central-1"
    echo ""
    exit 1
fi

echo "Loading credentials from .env file..."

# Clear any existing AWS environment variables to ensure we use only .env credentials
unset AWS_PROFILE
unset AWS_DEFAULT_PROFILE

# Load .env file and export only AWS variables
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove leading/trailing whitespace and quotes
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    
    # Export only AWS-related variables
    if [[ "$key" =~ ^AWS_.* ]]; then
        export "$key=$value"
        echo "  ✓ Loaded $key"
    fi
done < "$ENV_FILE"

# Validate required credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo ""
    echo "❌ Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in .env file"
    exit 1
fi

echo ""
echo "✓ Credentials loaded successfully from .env file"
echo "✓ Using ONLY credentials from .env (ignoring any local AWS profiles)"

# Configuration
FUNCTION_NAME="LetterOnOCRHandler"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
REGION="${AWS_REGION:-eu-central-1}"  # Use region from .env or default to eu-central-1
ROLE_NAME="LetterOnOCRHandlerRole"
S3_BUCKET="letteron-images"

# Set default region if not in .env
export AWS_DEFAULT_REGION="$REGION"

# Get account ID using credentials from .env
echo ""
echo "Verifying AWS credentials from .env..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to authenticate with AWS using credentials from .env"
    echo "Please verify your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file"
    exit 1
fi

echo "✓ Successfully authenticated with AWS"
echo "AWS Account ID: $ACCOUNT_ID"

# Get caller identity info for confirmation
CALLER_ARN=$(aws sts get-caller-identity --query Arn --output text)
CALLER_USER=$(aws sts get-caller-identity --query UserId --output text)

# Confirm deployment
echo ""
echo "=========================================="
echo "⚠️  DEPLOYMENT CONFIRMATION"
echo "=========================================="
echo "Account ID: $ACCOUNT_ID"
echo "Caller ARN: $CALLER_ARN"
echo "User ID: $CALLER_USER"
echo "Region: $REGION"
echo "Function: $FUNCTION_NAME"
echo ""
echo "Using credentials from: $ENV_FILE"
echo "=========================================="
echo ""
read -p "Continue with deployment? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Navigate to OCR handler directory
cd "$(dirname "$0")/ocr-handler"

# Step 1: Create IAM Role if it doesn't exist
echo ""
echo "Step 1: Creating IAM Role..."
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

if aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
    echo "✓ Role $ROLE_NAME already exists"
else
    echo "Creating role $ROLE_NAME..."
    # Create trust policy
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Role for LetterOn OCR Handler Lambda"
    
    echo "✓ Role created"
fi

# Step 2: Attach policies
echo ""
echo "Step 2: Attaching IAM policies..."

# Attach basic execution policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    2>/dev/null || echo "Policy already attached"

# Create and attach custom policy
POLICY_NAME="${ROLE_NAME}Policy"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

if aws iam get-policy --policy-arn $POLICY_ARN 2>/dev/null; then
    echo "✓ Policy $POLICY_NAME already exists"
else
    echo "Creating custom policy..."
    aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document file://../iam-policies/ocr-handler-policy.json \
        --description "Policy for LetterOn OCR Handler Lambda"
    echo "✓ Policy created"
fi

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN \
    2>/dev/null || echo "Custom policy already attached"

echo "✓ Policies attached"

# Wait for role to be ready
echo ""
echo "Waiting for IAM role to propagate..."
sleep 10

# Step 3: Package Lambda function
echo ""
echo "Step 3: Packaging Lambda function..."

# Create deployment package directory
rm -rf package
mkdir -p package

# Install dependencies (boto3 is already included in Lambda runtime)
# pip install --target ./package -r requirements.txt

# Copy Lambda function
cp lambda_function.py package/

# Create ZIP file
cd package
zip -r ../function.zip . > /dev/null
cd ..

# Add Lambda function to ZIP
zip -g function.zip lambda_function.py > /dev/null

echo "✓ Package created: function.zip"

# Step 4: Deploy Lambda function
echo ""
echo "Step 4: Deploying Lambda function..."

if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION > /dev/null
    
    # Update configuration (note: AWS_REGION is automatically available, don't set it)
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler $HANDLER \
        --role $ROLE_ARN \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={S3_BUCKET_NAME=${S3_BUCKET}}" \
        --region $REGION > /dev/null
    
    echo "✓ Function updated"
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://function.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={S3_BUCKET_NAME=${S3_BUCKET}}" \
        --region $REGION > /dev/null
    
    echo "✓ Function created"
fi

# Step 5: Test the function
echo ""
echo "Step 5: Testing Lambda function..."

cat > /tmp/test-event.json <<EOF
{
  "s3_keys": ["test/sample.jpg"],
  "bucket": "${S3_BUCKET}"
}
EOF

echo "Invoking function with test event..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file:///tmp/test-event.json \
    --region $REGION \
    /tmp/response.json > /dev/null 2>&1 || echo "Note: Test invocation may fail if test image doesn't exist"

if [ -f /tmp/response.json ]; then
    echo "Response:"
    cat /tmp/response.json | python3 -m json.tool 2>/dev/null || cat /tmp/response.json
fi

# Cleanup
echo ""
echo "Cleaning up..."
rm -rf package function.zip

echo ""
echo "=========================================="
echo "✅ OCR Handler Lambda deployed successfully!"
echo "=========================================="
echo "Function Name: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Role ARN: $ROLE_ARN"
echo "Account: $ACCOUNT_ID"
echo ""
echo "Deployed using credentials from: $ENV_FILE"
echo ""
echo "Test the function:"
echo "  aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"s3_keys\":[\"your-image.jpg\"]}' response.json"
echo ""