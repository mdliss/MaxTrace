# AWS Setup Guide for Innergy Blueprint Detection

Complete guide to set up AWS infrastructure for the MVP.

## Prerequisites

- AWS Account
- AWS CLI installed
- Node.js and npm installed
- Python 3.9+ installed
- Git installed

## Step 1: Install AWS CLI

### macOS
```bash
brew install awscli
```

### Verify Installation
```bash
aws --version
```

## Step 2: Configure AWS Credentials

### Create IAM User

1. Go to AWS Console → IAM → Users
2. Click "Add users"
3. Username: `innergy-deployment`
4. Access type: ✓ Programmatic access
5. Attach policies:
   - `AmazonS3FullAccess`
   - `AWSLambda_FullAccess`
   - `IAMFullAccess`
   - `AmazonSageMakerFullAccess`
   - `CloudWatchFullAccess`
6. Download credentials CSV

### Configure CLI
```bash
aws configure
```

Enter:
- AWS Access Key ID: `[from CSV]`
- AWS Secret Access Key: `[from CSV]`
- Default region: `us-east-1`
- Default output format: `json`

### Verify Configuration
```bash
aws sts get-caller-identity
```

## Step 3: Create S3 Bucket

```bash
# Create bucket for dev environment
aws s3 mb s3://innergy-blueprints-dev --region us-east-1

# Enable CORS
aws s3api put-bucket-cors \
  --bucket innergy-blueprints-dev \
  --cors-configuration file://backend/s3-cors.json
```

Create `backend/s3-cors.json`:
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

### Set Lifecycle Policy (7-day auto-delete)
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket innergy-blueprints-dev \
  --lifecycle-configuration file://backend/s3-lifecycle.json
```

Create `backend/s3-lifecycle.json`:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldBlueprints",
      "Status": "Enabled",
      "Prefix": "uploads/",
      "Expiration": {
        "Days": 7
      }
    }
  ]
}
```

## Step 4: Create IAM Role for SageMaker

```bash
# Create trust policy
cat > sagemaker-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name SageMakerExecutionRole \
  --assume-role-policy-document file://sagemaker-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name SageMakerExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

aws iam attach-role-policy \
  --role-name SageMakerExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Get role ARN (save this!)
aws iam get-role --role-name SageMakerExecutionRole --query 'Role.Arn' --output text
```

**Save the ARN** - you'll need it for SageMaker deployment.

## Step 5: Deploy Backend Lambda Functions

### Install Serverless Framework
```bash
cd backend
npm install
npm install -g serverless
```

### Deploy
```bash
serverless deploy --stage dev
```

**Output will include:**
- API Gateway endpoints
- Lambda function ARNs
- S3 bucket name

**Save the API Gateway URL** - you'll need it for the frontend.

Example output:
```
endpoints:
  POST - https://abc123.execute-api.us-east-1.amazonaws.com/dev/upload
  POST - https://abc123.execute-api.us-east-1.amazonaws.com/dev/detect
  GET - https://abc123.execute-api.us-east-1.amazonaws.com/dev/results/{blueprintId}
```

## Step 6: Deploy SageMaker Model (Optional - for production)

### Prerequisites
- Trained YOLOv5 model (`best.pt`)
- SageMaker execution role ARN from Step 4

### Deploy
```bash
cd ml-model/deployment

python deploy_sagemaker.py \
  --model-path ../training/runs/train/blueprint_detector/weights/best.pt \
  --role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole \
  --instance-type ml.m5.large \
  --endpoint-name yolov5-blueprint-detector
```

**Save the endpoint name** - update Lambda environment variable:
```bash
aws lambda update-function-configuration \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --environment Variables="{SAGEMAKER_ENDPOINT=yolov5-blueprint-detector-TIMESTAMP}"
```

## Step 7: Configure Frontend

Update frontend API configuration:

Create `frontend/src/config.js`:
```javascript
export const API_BASE_URL = 'https://YOUR_API_GATEWAY_URL/dev';
```

Update `frontend/.env`:
```
VITE_API_BASE_URL=https://YOUR_API_GATEWAY_URL/dev
```

## Step 8: Test the Setup

### Test S3 Upload
```bash
aws s3 cp test-blueprint.png s3://innergy-blueprints-dev/test/
```

### Test Lambda Functions
```bash
# Test upload handler
aws lambda invoke \
  --function-name innergy-blueprint-detection-dev-uploadHandler \
  --payload '{"body": "{\"fileName\":\"test.png\",\"fileType\":\"image/png\",\"fileSize\":1000000,\"sessionId\":\"test-session\"}"}' \
  response.json

cat response.json
```

### Test API Gateway
```bash
curl -X POST https://YOUR_API_GATEWAY_URL/dev/upload \
  -H "Content-Type: application/json" \
  -d '{"fileName":"test.png","fileType":"image/png","fileSize":1000000,"sessionId":"test-session"}'
```

## Step 9: Monitor and Debug

### View Lambda Logs
```bash
# Upload handler logs
serverless logs -f uploadHandler -t

# Inference handler logs
serverless logs -f inferenceHandler -t

# Results handler logs
serverless logs -f resultsHandler -t
```

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/innergy-blueprint-detection-dev-uploadHandler --follow
```

## Cost Estimates (MVP)

**Monthly costs for light usage:**
- S3 Storage: $0.50 - $2
- Lambda: $0 - $5 (within free tier)
- API Gateway: $0 - $3 (within free tier)
- SageMaker (if deployed): $50 - $200 (ml.m5.large ~$0.115/hour)
- CloudWatch: $0 - $2

**Total MVP: $50 - $212/month** (mostly SageMaker if always on)

**Cost Optimization:**
- Delete SageMaker endpoint when not in use
- Use S3 lifecycle policies (already configured)
- Stay within Lambda free tier (1M requests/month)

## Cleanup (Delete Everything)

```bash
# Delete serverless stack
cd backend
serverless remove --stage dev

# Delete SageMaker endpoint
aws sagemaker delete-endpoint --endpoint-name yolov5-blueprint-detector

# Delete S3 bucket
aws s3 rb s3://innergy-blueprints-dev --force

# Delete IAM roles
aws iam delete-role --role-name SageMakerExecutionRole
```

## Troubleshooting

### Lambda Permission Errors
- Check IAM role has S3 and SageMaker permissions
- Verify bucket name in environment variables

### CORS Errors
- Verify S3 CORS configuration
- Check API Gateway CORS settings in serverless.yml

### SageMaker Endpoint Not Found
- Verify endpoint name in Lambda environment variables
- Check endpoint status: `aws sagemaker describe-endpoint --endpoint-name NAME`

### 403 Forbidden on S3
- Check bucket policy and CORS
- Verify presigned URL hasn't expired

## Next Steps

1. ✓ Complete AWS setup
2. Train YOLOv5 model on blueprint dataset
3. Deploy SageMaker endpoint
4. Test end-to-end workflow
5. Deploy frontend to S3 + CloudFront (Task 10)
