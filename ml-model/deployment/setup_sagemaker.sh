#!/bin/bash
# SageMaker Setup and Validation Script
# Validates AWS credentials, IAM roles, and prerequisites for SageMaker deployment

set -e  # Exit on error

echo "=========================================="
echo "SageMaker Deployment Prerequisites Check"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check AWS CLI
echo "Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not installed"
    echo "Install with: brew install awscli (macOS) or pip install awscli"
    exit 1
else
    AWS_VERSION=$(aws --version 2>&1)
    print_success "AWS CLI installed: $AWS_VERSION"
fi

# Check AWS credentials
echo ""
echo "Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    print_success "AWS credentials valid"
    echo "  Account ID: $ACCOUNT_ID"
    echo "  User ARN: $USER_ARN"
else
    print_error "AWS credentials not configured or invalid"
    echo "Configure with: aws configure"
    exit 1
fi

# Check Python
echo ""
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not installed"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    print_success "Python installed: $PYTHON_VERSION"
fi

# Check required Python packages
echo ""
echo "Checking Python dependencies..."
MISSING_PACKAGES=()

if ! python3 -c "import sagemaker" &> /dev/null; then
    MISSING_PACKAGES+=("sagemaker")
fi
if ! python3 -c "import boto3" &> /dev/null; then
    MISSING_PACKAGES+=("boto3")
fi
if ! python3 -c "import torch" &> /dev/null; then
    MISSING_PACKAGES+=("torch")
fi

if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
    print_success "All required Python packages installed"
else
    print_warning "Missing packages: ${MISSING_PACKAGES[*]}"
    echo "Install with: pip install ${MISSING_PACKAGES[*]}"
fi

# Check SageMaker IAM role
echo ""
echo "Checking SageMaker IAM role..."
ROLE_NAME="SageMakerExecutionRole"

if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
    print_success "SageMaker role exists"
    echo "  Role ARN: $ROLE_ARN"

    # Save role ARN to config file
    echo "$ROLE_ARN" > .sagemaker_role_arn
    print_success "Role ARN saved to .sagemaker_role_arn"
else
    print_error "SageMaker role '$ROLE_NAME' not found"
    echo ""
    echo "Create role with:"
    echo "  ./create_sagemaker_role.sh"
    exit 1
fi

# Check S3 bucket
echo ""
echo "Checking S3 bucket..."
BUCKET_NAME="innergy-blueprints-dev"

if aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
    print_success "S3 bucket exists: $BUCKET_NAME"
else
    print_warning "S3 bucket '$BUCKET_NAME' not found"
    echo "Create with: aws s3 mb s3://$BUCKET_NAME"
fi

# Check for trained model
echo ""
echo "Checking for trained model..."
MODEL_PATH="../training/runs/train/blueprint_detector/weights/best.pt"

if [ -f "$MODEL_PATH" ]; then
    print_success "Trained model found: $MODEL_PATH"
    MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    echo "  Model size: $MODEL_SIZE"
else
    print_warning "Trained model not found at $MODEL_PATH"
    echo "Train model first with: cd ../training && python train_enhanced.py"
    echo ""
    echo "For testing, you can download a pre-trained YOLOv5 model:"
    echo "  wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt -O $MODEL_PATH"
fi

# Summary
echo ""
echo "=========================================="
echo "Setup Summary"
echo "=========================================="

if [ ${#MISSING_PACKAGES[@]} -eq 0 ] && [ -f "$MODEL_PATH" ]; then
    print_success "All prerequisites met! Ready to deploy."
    echo ""
    echo "Deploy to SageMaker with:"
    echo "  python deploy_sagemaker.py --model-path $MODEL_PATH --role-arn $ROLE_ARN"
    echo ""
    echo "Or use the automated deploy script:"
    echo "  ./deploy_automated.sh"
elif [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
    print_warning "Prerequisites OK, but model not found"
    echo ""
    echo "Next steps:"
    echo "1. Train model: cd ../training && python train_enhanced.py"
    echo "2. Then deploy: ./deploy_automated.sh"
else
    print_warning "Some prerequisites missing"
    echo ""
    echo "Next steps:"
    echo "1. Install missing packages: pip install ${MISSING_PACKAGES[*]}"
    echo "2. Train model: cd ../training && python train_enhanced.py"
    echo "3. Then run this script again: ./setup_sagemaker.sh"
fi

echo ""
