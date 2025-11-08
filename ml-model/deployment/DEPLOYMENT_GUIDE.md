# SageMaker Deployment Guide

Complete guide for deploying YOLOv5 blueprint detection model to AWS SageMaker.

## Quick Start

### 1. Prerequisites Check

Run the setup validation script:

```bash
cd ml-model/deployment
./setup_sagemaker.sh
```

This checks:
- AWS CLI installation and credentials
- Python and required packages
- SageMaker IAM role
- S3 bucket access
- Trained model availability

### 2. Automated Deployment

Deploy with one command:

```bash
./deploy_automated.sh
```

This script:
- Validates prerequisites
- Packages the model
- Uploads to S3
- Creates SageMaker endpoint
- Saves endpoint configuration
- Provides next steps

Deployment takes 5-10 minutes.

### 3. Test Endpoint

Test with a sample image:

```bash
# Using S3 image
python test_endpoint.py --s3-uri s3://innergy-blueprints-dev/test/sample.png

# Using local image
python test_endpoint.py --local-image path/to/blueprint.jpg

# Performance test
python test_endpoint.py --s3-uri s3://bucket/image.png --performance-test 10
```

## Detailed Instructions

### Prerequisites

#### AWS Account Setup

1. **IAM User with Permissions:**
   - AmazonS3FullAccess
   - AmazonSageMakerFullAccess
   - IAMReadOnlyAccess
   - CloudWatchFullAccess

2. **Configure AWS CLI:**
   ```bash
   aws configure
   ```

3. **SageMaker Execution Role:**
   Already created: `arn:aws:iam::971422717446:role/SageMakerExecutionRole`

#### Python Dependencies

Install required packages:

```bash
cd ml-model
pip install -r requirements.txt
```

Required packages:
- sagemaker>=2.150.0
- boto3>=1.26.0
- torch>=1.12.0
- pillow>=9.0.0

#### Trained Model

You need a trained YOLOv5 model at:
```
ml-model/training/runs/train/blueprint_detector/weights/best.pt
```

**Option 1: Train your own model**
```bash
cd ml-model/training
python train_enhanced.py --epochs 100 --batch-size 16
```

**Option 2: Use pre-trained YOLOv5 for testing**
```bash
mkdir -p ml-model/training/runs/train/blueprint_detector/weights
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt \
  -O ml-model/training/runs/train/blueprint_detector/weights/best.pt
```

### Manual Deployment

If you prefer manual control:

```bash
cd ml-model/deployment

python deploy_sagemaker.py \
  --model-path ../training/runs/train/blueprint_detector/weights/best.pt \
  --role-arn arn:aws:iam::971422717446:role/SageMakerExecutionRole \
  --instance-type ml.m5.large \
  --instance-count 1
```

**Instance Type Options:**
- `ml.m5.large`: $0.115/hour (recommended for dev)
- `ml.m5.xlarge`: $0.23/hour (better performance)
- `ml.m5.2xlarge`: $0.46/hour (production)
- `ml.g4dn.xlarge`: $0.736/hour (GPU, fastest)

### Testing

#### Basic Test

```bash
python test_endpoint.py \
  --endpoint-name yolov5-blueprint-detector-TIMESTAMP \
  --s3-uri s3://innergy-blueprints-dev/test/sample.png \
  --confidence 0.5
```

#### Performance Test

```bash
python test_endpoint.py \
  --endpoint-name yolov5-blueprint-detector-TIMESTAMP \
  --s3-uri s3://innergy-blueprints-dev/test/sample.png \
  --performance-test 20
```

This runs 20 inference requests and reports:
- Average inference time
- Min/max times
- Success rate

#### Expected Results

```
Detection Results
================================================
Total Detections: 12
Average Confidence: 0.78
Image Dimensions: 1024x768

Detected Elements:
  Element 1:
    Class: wall
    Confidence: 0.89
    Bounding Box: {'x': 100, 'y': 50, 'width': 800, 'height': 10}
    Area: 8000 pixels

  Element 2:
    Class: door
    Confidence: 0.75
    Bounding Box: {'x': 450, 'y': 300, 'width': 80, 'height': 100}
    Area: 8000 pixels
...
```

### Integration with Lambda

After deployment, update Lambda function:

```bash
# Get endpoint name
ENDPOINT_NAME=$(cat .sagemaker_endpoint.json | jq -r '.endpoint_name')

# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --environment Variables="{SAGEMAKER_ENDPOINT=$ENDPOINT_NAME}"
```

Or update in `backend/serverless.yml`:

```yaml
functions:
  inferenceHandler:
    environment:
      SAGEMAKER_ENDPOINT: yolov5-blueprint-detector-TIMESTAMP
```

Then redeploy:
```bash
cd backend
serverless deploy --stage dev
```

## Monitoring

### CloudWatch Metrics

View endpoint metrics in AWS Console:
- Invocations
- ModelLatency
- OverheadLatency
- Invocation4XXErrors
- Invocation5XXErrors

### CloudWatch Logs

Stream endpoint logs:

```bash
ENDPOINT_NAME=$(cat .sagemaker_endpoint.json | jq -r '.endpoint_name')

aws logs tail /aws/sagemaker/Endpoints/$ENDPOINT_NAME --follow
```

### Check Endpoint Status

```bash
aws sagemaker describe-endpoint --endpoint-name ENDPOINT_NAME
```

## Troubleshooting

### Endpoint Creation Failed

Check CloudWatch logs:
```bash
aws logs tail /aws/sagemaker/TrainingJobs/TRAINING_JOB_NAME --follow
```

Common issues:
- Insufficient IAM permissions
- Invalid model format
- Missing dependencies in inference code

### Inference Errors

**403 Forbidden:**
- SageMaker role lacks S3 access
- S3 bucket in different region

**413 Payload Too Large:**
- Image exceeds 5MB limit
- Resize image before sending

**500 Internal Server Error:**
- Model loading failed
- Check inference.py for errors
- Review CloudWatch logs

**Slow Inference (>30s):**
- Cold start on first request (normal)
- Consider larger instance type
- Check image size (resize to 640x640 recommended)

### High Costs

**Optimize costs:**
- Delete endpoint when not in use
- Use Serverless Inference for low/variable traffic
- Use smaller instance types for development

## Cost Management

### Pricing (us-east-1)

**Instance Costs per Hour:**
- ml.m5.large: $0.115
- ml.m5.xlarge: $0.230
- ml.m5.2xlarge: $0.460
- ml.g4dn.xlarge: $0.736 (GPU)

**Monthly Estimates:**
- 24/7 ml.m5.large: ~$83/month
- 8 hours/day ml.m5.large: ~$28/month
- On-demand only: ~$0/month (pay per request)

### Delete Endpoint

**Important:** Always delete endpoints when not in use!

```bash
# Get endpoint name
ENDPOINT_NAME=$(cat .sagemaker_endpoint.json | jq -r '.endpoint_name')

# Delete endpoint
aws sagemaker delete-endpoint --endpoint-name $ENDPOINT_NAME

# Delete endpoint configuration
aws sagemaker delete-endpoint-config --endpoint-config-name $ENDPOINT_NAME

# Delete model
aws sagemaker delete-model --model-name $ENDPOINT_NAME
```

Or use CLI:
```bash
./cleanup_endpoint.sh
```

## Auto-Scaling

Enable auto-scaling for production:

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace sagemaker \
  --resource-id endpoint/ENDPOINT_NAME/variant/AllTraffic \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --min-capacity 1 \
  --max-capacity 3

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace sagemaker \
  --resource-id endpoint/ENDPOINT_NAME/variant/AllTraffic \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --policy-name scaling-policy-1 \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

## Best Practices

1. **Development**: Use ml.m5.large, delete when not in use
2. **Staging**: Use ml.m5.xlarge, enable auto-scaling
3. **Production**: Use ml.m5.2xlarge or GPU instances, monitor metrics
4. **Cost Optimization**: Consider SageMaker Serverless Inference for variable load
5. **Monitoring**: Set up CloudWatch alarms for errors and latency
6. **Security**: Use VPC endpoints for private access
7. **Testing**: Always test with sample data before production
8. **Versioning**: Tag endpoints with model version/date

## Next Steps

After successful deployment:

1. ✅ Test endpoint with various blueprint images
2. ✅ Monitor performance metrics
3. ✅ Update Lambda function to use endpoint
4. ✅ Test end-to-end workflow (upload → detect → results)
5. ✅ Set up CloudWatch alarms
6. ✅ Document endpoint name and configuration
7. ✅ Plan for model updates and A/B testing

## Support

For issues:
- Check CloudWatch logs first
- Review troubleshooting section
- Verify IAM permissions
- Test with simpler pre-trained model

Resources:
- AWS SageMaker Docs: https://docs.aws.amazon.com/sagemaker/
- YOLOv5 Docs: https://docs.ultralytics.com/
- Project README: ../README.md
