#!/bin/bash
# IAM Permissions Validation Script
# Validates that Lambda functions have correct IAM permissions for SageMaker

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

echo "=========================================="
echo "IAM Permissions Validation"
echo "=========================================="
echo ""

FUNCTION_NAME="innergy-blueprint-detection-dev-inferenceHandler"

# Check if function exists
echo "Checking Lambda function: $FUNCTION_NAME"
if aws lambda get-function --function-name "$FUNCTION_NAME" &> /dev/null; then
    print_success "Lambda function exists"
else
    print_error "Lambda function not found"
    echo "Deploy first with: cd backend && serverless deploy --stage dev"
    exit 1
fi

# Get function's IAM role
ROLE_ARN=$(aws lambda get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --query 'Role' \
    --output text)

print_info "Lambda Role ARN: $ROLE_ARN"

# Extract role name from ARN
ROLE_NAME=$(echo "$ROLE_ARN" | awk -F/ '{print $NF}')

echo ""
echo "Checking IAM permissions..."
echo ""

# Check attached policies
ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
    --role-name "$ROLE_NAME" \
    --query 'AttachedPolicies[*].PolicyName' \
    --output json)

print_info "Attached Policies:"
echo "$ATTACHED_POLICIES" | jq -r '.[]' | while read policy; do
    echo "  - $policy"
done

# Get inline policies
INLINE_POLICIES=$(aws iam list-role-policies \
    --role-name "$ROLE_NAME" \
    --query 'PolicyNames' \
    --output json)

if [ "$(echo $INLINE_POLICIES | jq '. | length')" -gt 0 ]; then
    echo ""
    print_info "Inline Policies:"
    echo "$INLINE_POLICIES" | jq -r '.[]' | while read policy; do
        echo "  - $policy"

        # Get policy document
        POLICY_DOC=$(aws iam get-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-name "$policy" \
            --query 'PolicyDocument' \
            --output json)

        # Check for SageMaker permissions
        SAGEMAKER_PERMS=$(echo "$POLICY_DOC" | jq -r '
            .Statement[] |
            select(.Effect == "Allow") |
            select(.Action[] | contains("sagemaker"))
        ')

        if [ -n "$SAGEMAKER_PERMS" ]; then
            print_success "  SageMaker permissions found"
        else
            print_error "  No SageMaker permissions found"
        fi

        # Check for S3 permissions
        S3_PERMS=$(echo "$POLICY_DOC" | jq -r '
            .Statement[] |
            select(.Effect == "Allow") |
            select(.Action[] | contains("s3"))
        ')

        if [ -n "$S3_PERMS" ]; then
            print_success "  S3 permissions found"
        else
            print_error "  No S3 permissions found"
        fi
    done
fi

echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""

# Check environment variables
ENV_VARS=$(aws lambda get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --query 'Environment.Variables' \
    --output json)

SAGEMAKER_ENDPOINT=$(echo "$ENV_VARS" | jq -r '.SAGEMAKER_ENDPOINT // "not set"')
BUCKET_NAME=$(echo "$ENV_VARS" | jq -r '.BUCKET_NAME // "not set"')

echo "Environment Variables:"
echo "  SAGEMAKER_ENDPOINT: $SAGEMAKER_ENDPOINT"
echo "  BUCKET_NAME: $BUCKET_NAME"
echo ""

if [ "$SAGEMAKER_ENDPOINT" != "not set" ] && [ "$BUCKET_NAME" != "not set" ]; then
    print_success "All required environment variables are set"
else
    print_error "Some environment variables are missing"
fi

print_success "IAM validation complete"
echo ""
echo "Next steps:"
echo "1. Test Lambda function: python backend/test_lambda_sagemaker.py --check-config"
echo "2. Test SageMaker integration: python backend/test_lambda_sagemaker.py"
