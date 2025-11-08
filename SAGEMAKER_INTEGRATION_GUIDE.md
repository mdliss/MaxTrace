# SageMaker Integration Guide for MaxTrace

Complete guide for YOLOv5 architectural element detection with AWS SageMaker.

## Overview

MaxTrace uses YOLOv5 deployed on AWS SageMaker to detect architectural elements (walls, doors, windows, rooms, stairs, furniture, fixtures) in blueprint images.

## Architecture

```
User Upload → S3 → Lambda (Inference) → SageMaker Endpoint → Results → S3
                ↓                               ↓
            Metadata                        YOLOv5 Model
```

## Components

### 1. ML Model (ml-model/)

**Dataset Configuration**: `ml-model/data/blueprint_dataset.yaml`
- 7 architectural element classes
- YOLO format annotations
- Train/val/test splits

**Training**: `ml-model/training/train_enhanced.py`
- YOLOv5m base model
- 100 epochs default
- Configurable batch size, image size
- GPU/CPU support

**Deployment**: `ml-model/deployment/`
- Automated deployment scripts
- SageMaker endpoint setup
- Testing and validation tools

### 2. Lambda Function (backend/)

**Inference Handler**: `backend/functions/inference_handler.py`
- SageMaker endpoint invocation
- Retry logic with exponential backoff
- Multi-class detection support
- S3 result storage
- Real-time status updates

**Configuration**: `backend/serverless.yml`
- IAM permissions (S3, SageMaker)
- Environment variables
- Timeout and memory settings

## Quick Start

### Prerequisites

1. AWS Account with:
   - SageMaker access
   - Lambda access
   - S3 access
   - IAM permissions

2. Tools installed:
   - AWS CLI configured
   - Python 3.9+
   - Node.js (for serverless)

### Step 1: Prepare Dataset

```bash
cd ml-model/data

# Option A: Generate synthetic data for testing
python download_sample_data.py --generate-synthetic --num-images=50

# Option B: Use your own dataset
# Place images in data/blueprints/images/{train,val}
# Place labels in data/blueprints/labels/{train,val}

# Validate dataset
python prepare_dataset.py --validate
```

### Step 2: Train Model (Optional)

```bash
cd ml-model/training

# Train with default settings
python train_enhanced.py

# Or customize
python train_enhanced.py \
  --epochs 50 \
  --batch-size 8 \
  --img-size 640 \
  --weights yolov5m.pt
```

**For testing**: Download pre-trained model
```bash
mkdir -p runs/train/blueprint_detector/weights
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt \
  -O runs/train/blueprint_detector/weights/best.pt
```

### Step 3: Deploy to SageMaker

```bash
cd ml-model/deployment

# Validate prerequisites
./setup_sagemaker.sh

# Deploy (automated)
./deploy_automated.sh

# Or manual deployment
python deploy_sagemaker.py \
  --model-path ../training/runs/train/blueprint_detector/weights/best.pt \
  --role-arn arn:aws:iam::971422717446:role/SageMakerExecutionRole \
  --instance-type ml.m5.large
```

**Output**:
- Endpoint name (e.g., `yolov5-blueprint-detector-20250108-123456`)
- Endpoint ARN
- Configuration file: `.sagemaker_endpoint.json`

### Step 4: Update Lambda Environment Variable

```bash
# Get endpoint name from deployment
ENDPOINT_NAME=$(cat ml-model/deployment/.sagemaker_endpoint.json | jq -r '.endpoint_name')

# Update Lambda function
aws lambda update-function-configuration \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --environment Variables="{SAGEMAKER_ENDPOINT=$ENDPOINT_NAME}"
```

Or set as environment variable before deploying backend:
```bash
export SAGEMAKER_ENDPOINT=yolov5-blueprint-detector-20250108-123456
cd backend
serverless deploy --stage dev
```

### Step 5: Test Integration

```bash
# Test SageMaker endpoint
cd ml-model/deployment
python test_endpoint.py --s3-uri s3://innergy-blueprints-dev/test/sample.png

# Test Lambda function
cd backend
python test_lambda_sagemaker.py --check-config
python test_lambda_sagemaker.py

# Validate IAM permissions
./validate_iam_permissions.sh
```

## Error Handling

### Implemented Error Handling

**1. Retry Logic** (in `inference_handler.py`)
- Exponential backoff (1s, 2s, 4s)
- 3 retries by default (configurable via `SAGEMAKER_MAX_RETRIES`)
- Handles transient errors:
  - ServiceUnavailable
  - ThrottlingException
  - InternalFailure
  - Timeouts

**2. Error Categories**

| Error Type | Retryable | Handler |
|------------|-----------|---------|
| ModelError | No | Return 500 with details |
| ServiceUnavailable | Yes | Retry with backoff |
| ThrottlingException | Yes | Retry with backoff |
| ValidationError | No | Return 400 with details |
| NetworkTimeout | Yes | Retry with backoff |

**3. Status Updates**
- All errors update S3 status to 'failed'
- Detailed error messages stored
- Timestamps for debugging

### Common Errors

**Endpoint Not Found**
```
Error: Could not find endpoint "yolov5-blueprint-detector"
```
**Fix**: Update Lambda environment variable with correct endpoint name

**403 Forbidden**
```
Error: User: arn:aws:iam::XXX:role/YYY is not authorized to perform: sagemaker:InvokeEndpoint
```
**Fix**: Add SageMaker permissions to Lambda IAM role (already configured in serverless.yml)

**Model Inference Failed**
```
Error: Model inference failed: Invalid input format
```
**Fix**: Check image format, ensure S3 URI is accessible

**Timeout**
```
Error: Timeout waiting for SageMaker response
```
**Fix**: Increase Lambda timeout in serverless.yml (currently 60s)

## Monitoring

### CloudWatch Metrics

**Lambda Metrics**:
- Invocations
- Duration
- Errors
- Throttles

**SageMaker Metrics**:
- ModelLatency
- Invocations
- Invocation4XXErrors
- Invocation5XXErrors

### CloudWatch Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/innergy-blueprint-detection-dev-inferenceHandler --follow

# SageMaker endpoint logs
ENDPOINT_NAME=yolov5-blueprint-detector-20250108-123456
aws logs tail /aws/sagemaker/Endpoints/$ENDPOINT_NAME --follow
```

### Custom Metrics

Lambda function logs:
- Blueprint ID
- Processing time
- Detection counts by element class
- Confidence scores
- S3 keys for results

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BUCKET_NAME` | innergy-blueprints-dev | S3 bucket for uploads |
| `SAGEMAKER_ENDPOINT` | yolov5-blueprint-detector | SageMaker endpoint name |
| `MODEL_VERSION` | yolov5-v1.0 | Model version identifier |
| `SAGEMAKER_MAX_RETRIES` | 3 | Max retry attempts |
| `SAGEMAKER_RETRY_DELAY` | 1.0 | Initial retry delay (seconds) |

### IAM Permissions

**Lambda Execution Role** (configured in serverless.yml):

```yaml
- Effect: Allow
  Action:
    - s3:PutObject
    - s3:GetObject
    - s3:DeleteObject
  Resource:
    - arn:aws:s3:::innergy-blueprints-dev/*

- Effect: Allow
  Action:
    - sagemaker:InvokeEndpoint
  Resource:
    - arn:aws:sagemaker:us-east-1:*:endpoint/yolov5-blueprint-detector
```

**SageMaker Execution Role**:
```
arn:aws:iam::971422717446:role/SageMakerExecutionRole
```

Permissions:
- AmazonSageMakerFullAccess
- AmazonS3FullAccess

## API Response Format

### Success Response

```json
{
  "statusCode": 200,
  "body": {
    "message": "Inference completed successfully",
    "blueprintId": "blueprint-123",
    "results": {
      "blueprintId": "blueprint-123",
      "modelVersion": "yolov5-v1.0",
      "processingTime": 2.34,
      "detectedAt": "2025-01-08T12:34:56Z",
      "detections": [
        {
          "roomId": 1,
          "class": "wall",
          "confidence": 0.89,
          "boundingBox": {
            "x": 100,
            "y": 50,
            "width": 800,
            "height": 10
          },
          "area": 8000
        },
        {
          "roomId": 2,
          "class": "door",
          "confidence": 0.75,
          "boundingBox": {
            "x": 450,
            "y": 300,
            "width": 80,
            "height": 100
          },
          "area": 8000
        }
      ],
      "statistics": {
        "totalDetections": 25,
        "totalRooms": 25,
        "avgConfidence": 0.78,
        "elementCounts": {
          "wall": 12,
          "door": 4,
          "window": 6,
          "room": 1,
          "stair": 1,
          "furniture": 1,
          "fixture": 0
        },
        "processingSteps": ["upload", "inference", "postprocess"]
      },
      "dimensions": {
        "width": 1024,
        "height": 768
      }
    }
  }
}
```

### Error Response

```json
{
  "statusCode": 500,
  "body": {
    "error": "Failed to invoke SageMaker endpoint",
    "details": "Endpoint 'yolov5-blueprint-detector' not found"
  }
}
```

## Cost Optimization

### Development
- Use `ml.m5.large` (~$0.12/hour)
- Delete endpoint when not in use
- Use synthetic data for testing

### Production
- Enable auto-scaling (1-3 instances)
- Use `ml.m5.xlarge` for better performance
- Consider SageMaker Serverless Inference for variable load
- Set up CloudWatch alarms for cost monitoring

### Monthly Estimates
- Lambda: $0 (within free tier)
- S3: $1-5 (storage + requests)
- SageMaker: $83/month (ml.m5.large 24/7) or $0 (on-demand only)

## Troubleshooting Checklist

- [ ] AWS credentials configured: `aws sts get-caller-identity`
- [ ] SageMaker endpoint deployed: `aws sagemaker describe-endpoint --endpoint-name NAME`
- [ ] Lambda environment variable set: `aws lambda get-function-configuration --function-name NAME`
- [ ] IAM permissions validated: `./backend/validate_iam_permissions.sh`
- [ ] S3 bucket accessible: `aws s3 ls s3://innergy-blueprints-dev/`
- [ ] Test image uploaded: `aws s3 cp test.png s3://innergy-blueprints-dev/test/`
- [ ] Lambda function test: `python backend/test_lambda_sagemaker.py`
- [ ] CloudWatch logs checked for errors

## Next Steps

1. **Training**: Collect real blueprint dataset, train production model
2. **Testing**: End-to-end testing with various blueprint types
3. **Monitoring**: Set up CloudWatch dashboards and alarms
4. **Optimization**: Fine-tune model, optimize inference performance
5. **Scaling**: Configure auto-scaling based on load
6. **Security**: Review IAM policies, enable VPC endpoints

## Support Resources

- **AWS SageMaker**: https://docs.aws.amazon.com/sagemaker/
- **YOLOv5**: https://docs.ultralytics.com/
- **Serverless Framework**: https://www.serverless.com/framework/docs/
- **Project Documentation**:
  - ml-model/README.md
  - ml-model/deployment/DEPLOYMENT_GUIDE.md
  - AWS_SETUP.md
