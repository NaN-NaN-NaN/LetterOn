#!/bin/bash

# LetterOn Server - AWS ECS Deployment Script
# Purpose: Automated deployment to AWS ECS Fargate
# Testing: chmod +x deploy_aws.sh && ./deploy_aws.sh
# AWS Deployment: Run from local machine or CI/CD pipeline

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (modify these values)
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
ECR_REPO_NAME="letteron-server"
ECS_CLUSTER_NAME="letteron-cluster"
ECS_SERVICE_NAME="letteron-service"
ECS_TASK_FAMILY="letteron-task"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}LetterOn Server - AWS ECS Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Install it from: https://www.docker.com/"
    exit 1
fi

# Get AWS Account ID if not set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}Getting AWS Account ID...${NC}"
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}AWS Account ID: $AWS_ACCOUNT_ID${NC}"
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

# Step 1: Create ECR repository (if not exists)
echo -e "\n${YELLOW}Step 1: Creating ECR repository...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${AWS_REGION}
echo -e "${GREEN}✓ ECR repository ready${NC}"

# Step 2: Login to ECR
echo -e "\n${YELLOW}Step 2: Logging in to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Step 3: Build Docker image
echo -e "\n${YELLOW}Step 3: Building Docker image...${NC}"
docker build -t ${ECR_REPO_NAME}:latest .
echo -e "${GREEN}✓ Docker image built${NC}"

# Step 4: Tag Docker image
echo -e "\n${YELLOW}Step 4: Tagging Docker image...${NC}"
IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"
docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:latest
docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image tagged: ${IMAGE_TAG}${NC}"

# Step 5: Push Docker image to ECR
echo -e "\n${YELLOW}Step 5: Pushing Docker image to ECR...${NC}"
docker push ${ECR_URI}:latest
docker push ${ECR_URI}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Step 6: Create/Update ECS Task Definition
echo -e "\n${YELLOW}Step 6: Creating ECS task definition...${NC}"

# Read environment variables from .env file
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment variables from .env...${NC}"
    ENV_VARS=$(cat .env | grep -v '^#' | grep -v '^$' | jq -R 'split("=") | {name: .[0], value: (.[1:] | join("="))}' | jq -s '.')
else
    echo -e "${RED}Warning: .env file not found. Task will use default environment variables.${NC}"
    ENV_VARS="[]"
fi

# Create task definition JSON
cat > task-definition.json <<EOF
{
  "family": "${ECS_TASK_FAMILY}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "${ECR_REPO_NAME}",
      "image": "${ECR_URI}:${IMAGE_TAG}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": ${ENV_VARS},
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${ECS_TASK_FAMILY}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region ${AWS_REGION}
echo -e "${GREEN}✓ Task definition registered${NC}"

# Clean up task definition file
rm task-definition.json

# Step 7: Create or Update ECS Service
echo -e "\n${YELLOW}Step 7: Updating ECS service...${NC}"

# Check if service exists
SERVICE_EXISTS=$(aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services ${ECS_SERVICE_NAME} --region ${AWS_REGION} --query 'services[0].status' --output text 2>/dev/null || echo "NONE")

if [ "$SERVICE_EXISTS" == "ACTIVE" ]; then
    echo -e "${YELLOW}Service exists, updating...${NC}"
    aws ecs update-service \
        --cluster ${ECS_CLUSTER_NAME} \
        --service ${ECS_SERVICE_NAME} \
        --task-definition ${ECS_TASK_FAMILY} \
        --force-new-deployment \
        --region ${AWS_REGION}
    echo -e "${GREEN}✓ Service updated${NC}"
else
    echo -e "${YELLOW}Service does not exist. Please create it manually in AWS Console.${NC}"
    echo -e "${YELLOW}Instructions:${NC}"
    echo "  1. Go to ECS Console: https://console.aws.amazon.com/ecs"
    echo "  2. Create cluster: ${ECS_CLUSTER_NAME}"
    echo "  3. Create service with task definition: ${ECS_TASK_FAMILY}"
    echo "  4. Configure load balancer and networking"
fi

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nDeployment Details:"
echo -e "  • ECR Image: ${ECR_URI}:${IMAGE_TAG}"
echo -e "  • Task Definition: ${ECS_TASK_FAMILY}"
echo -e "  • ECS Cluster: ${ECS_CLUSTER_NAME}"
echo -e "  • ECS Service: ${ECS_SERVICE_NAME}"

echo -e "\nNext Steps:"
echo -e "  1. Check ECS service status: aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services ${ECS_SERVICE_NAME} --region ${AWS_REGION}"
echo -e "  2. View logs: aws logs tail /ecs/${ECS_TASK_FAMILY} --follow --region ${AWS_REGION}"
echo -e "  3. Test API: curl https://your-load-balancer-url/health"

echo -e "\n${GREEN}Done!${NC}"
