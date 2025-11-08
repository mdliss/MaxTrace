#!/bin/bash
# Automated SageMaker Deployment Script
# Deploys YOLOv5 model to SageMaker with validation and error handling

set -e  # Exit on error

echo "=========================================="
echo "Automated SageMaker Model Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

# Configuration
MODEL_PATH="../training/runs/train/blueprint_detector/weights/best.pt"
ROLE_ARN_FILE=".sagemaker_role_arn"
INSTANCE_TYPE="${SAGEMAKER_INSTANCE_TYPE:-ml.m5.large}"
INSTANCE_COUNT="${SAGEMAKER_INSTANCE_COUNT:-1}"
ENDPOINT_CONFIG_FILE=".sagemaker_endpoint.json"

# Check prerequisites
echo "Step 1: Checking prerequisites..."
if [ ! -f "$ROLE_ARN_FILE" ]; then
    print_error "SageMaker role ARN not found"
    echo "Run setup first: ./setup_sagemaker.sh"
    exit 1
fi

ROLE_ARN=$(cat "$ROLE_ARN_FILE")
print_success "Role ARN loaded: $ROLE_ARN"

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    print_error "Model not found at $MODEL_PATH"
    echo ""
    echo "Options:"
    echo "1. Train model: cd ../training && python train_enhanced.py"
    echo "2. Use pre-trained YOLOv5m for testing:"
    echo "   mkdir -p $(dirname $MODEL_PATH)"
    echo "   wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt -O $MODEL_PATH"
    exit 1
fi

print_success "Model found: $MODEL_PATH"

# Deploy model
echo ""
echo "Step 2: Deploying model to SageMaker..."
echo "  Instance type: $INSTANCE_TYPE"
echo "  Instance count: $INSTANCE_COUNT"
echo ""

print_info "This will take 5-10 minutes. Please wait..."

# Run Python deployment script
python3 deploy_sagemaker.py \
    --model-path "$MODEL_PATH" \
    --role-arn "$ROLE_ARN" \
    --instance-type "$INSTANCE_TYPE" \
    --instance-count "$INSTANCE_COUNT" \
    2>&1 | tee deployment.log

# Check if deployment succeeded
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Deployment completed successfully!"

    # Extract endpoint name from log
    ENDPOINT_NAME=$(grep "Endpoint Name:" deployment.log | awk '{print $3}')

    if [ -n "$ENDPOINT_NAME" ]; then
        # Save endpoint configuration
        cat > "$ENDPOINT_CONFIG_FILE" <<EOF
{
  "endpoint_name": "$ENDPOINT_NAME",
  "instance_type": "$INSTANCE_TYPE",
  "instance_count": $INSTANCE_COUNT,
  "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "model_path": "$MODEL_PATH",
  "role_arn": "$ROLE_ARN"
}
EOF
        print_success "Endpoint configuration saved to $ENDPOINT_CONFIG_FILE"

        # Display next steps
        echo ""
        echo "=========================================="
        echo "Deployment Complete! 🎉"
        echo "=========================================="
        echo ""
        echo "Endpoint Name: $ENDPOINT_NAME"
        echo ""
        echo "Next Steps:"
        echo ""
        echo "1. Test the endpoint:"
        echo "   python test_endpoint.py --endpoint-name $ENDPOINT_NAME"
        echo ""
        echo "2. Update Lambda function environment variable:"
        echo "   aws lambda update-function-configuration \\"
        echo "     --function-name innergy-blueprint-detection-dev-inferenceHandler \\"
        echo "     --environment Variables=\"{SAGEMAKER_ENDPOINT=$ENDPOINT_NAME}\""
        echo ""
        echo "3. Monitor endpoint:"
        echo "   aws sagemaker describe-endpoint --endpoint-name $ENDPOINT_NAME"
        echo ""
        echo "4. View CloudWatch logs:"
        echo "   aws logs tail /aws/sagemaker/Endpoints/$ENDPOINT_NAME --follow"
        echo ""
        echo "⚠️  Remember: SageMaker endpoints cost ~\$0.12/hour"
        echo "   Delete when not in use: aws sagemaker delete-endpoint --endpoint-name $ENDPOINT_NAME"
        echo ""
    fi
else
    print_error "Deployment failed. Check deployment.log for details"
    exit 1
fi
