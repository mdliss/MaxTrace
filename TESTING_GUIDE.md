# MaxTrace Testing Guide

Complete guide to test the blueprint analysis system end-to-end.

## Testing Options

### Option 1: Quick Test with Pre-trained Model (Recommended for Initial Testing)

This validates the entire pipeline without training a custom model.

### Option 2: Full Test with Custom Trained Model

Complete workflow including model training.

---

## Option 1: Quick Pipeline Test (30 minutes)

### Step 1: Deploy Pre-trained YOLOv5 Model

```bash
# Navigate to ML model directory
cd ml-model/deployment

# Download pre-trained YOLOv5 model for testing
mkdir -p ../training/runs/train/blueprint_detector/weights
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt \
  -O ../training/runs/train/blueprint_detector/weights/best.pt

# Verify prerequisites
./setup_sagemaker.sh
```

**Expected Output:**
```
✅ AWS CLI installed
✅ AWS credentials valid
✅ Python installed
✅ SageMaker role exists: arn:aws:iam::971422717446:role/SageMakerExecutionRole
✅ S3 bucket exists: innergy-blueprints-dev
✅ Trained model found
```

### Step 2: Deploy to SageMaker

```bash
# Deploy model (takes 5-10 minutes)
./deploy_automated.sh
```

**Expected Output:**
```
✅ Deployment completed successfully!
Endpoint Name: yolov5-blueprint-detector-20250108-123456
```

**Save the endpoint name!** You'll need it for the next step.

### Step 3: Update Lambda Environment Variable

```bash
# Set endpoint name (replace with your actual endpoint name from step 2)
ENDPOINT_NAME="yolov5-blueprint-detector-20250108-123456"

aws lambda update-function-configuration \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --environment Variables="{
    BUCKET_NAME=innergy-blueprints-dev,
    SAGEMAKER_ENDPOINT=$ENDPOINT_NAME,
    MODEL_VERSION=yolov5-v1.0,
    SAGEMAKER_MAX_RETRIES=3,
    SAGEMAKER_RETRY_DELAY=1.0
  }"
```

**Expected Output:**
```json
{
  "FunctionName": "innergy-blueprint-detection-dev-inferenceHandler",
  "Environment": {
    "Variables": {
      "SAGEMAKER_ENDPOINT": "yolov5-blueprint-detector-20250108-123456",
      ...
    }
  }
}
```

### Step 4: Test SageMaker Endpoint Directly

```bash
cd ml-model/deployment

# Upload a test image to S3
aws s3 cp ../../test-blueprint.png s3://innergy-blueprints-dev/test/test-blueprint.png

# Test the endpoint
python test_endpoint.py \
  --endpoint-name $ENDPOINT_NAME \
  --s3-uri s3://innergy-blueprints-dev/test/test-blueprint.png \
  --confidence 0.5
```

**Expected Output:**
```
✅ Endpoint is ready for inference
✅ Inference completed in 2.34s

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
```

### Step 5: Test Lambda Function

```bash
cd ../../backend

# Validate IAM permissions
./validate_iam_permissions.sh

# Test Lambda configuration
python test_lambda_sagemaker.py --check-config

# Test Lambda inference
python test_lambda_sagemaker.py
```

**Expected Output:**
```
✅ Lambda function found
Environment Variables:
  SAGEMAKER_ENDPOINT: yolov5-blueprint-detector-20250108-123456

✅ Lambda invocation completed in 3.45s

Detection Results:
  Blueprint ID: test-1234567890
  Total Detections: 12
  Element Breakdown:
    wall: 8
    door: 2
    window: 2
```

### Step 6: Test Frontend Upload Flow

```bash
# Navigate to frontend
cd ../frontend

# Start development server (if not already running)
npm run dev
```

Open browser to http://localhost:5173

**Test Steps:**
1. Click "Upload Blueprint"
2. Select a blueprint image (PNG/JPG)
3. Click "Analyze"
4. Watch real-time processing status
5. View detection results with bounding boxes

**Expected Flow:**
- Upload progress: 0% → 100%
- Processing stages: "Uploading..." → "Processing..." → "Complete"
- Results page shows:
  - Blueprint image with bounding boxes
  - Detected elements list
  - Element counts by type
  - Confidence scores

### Step 7: Test Production Deployment

```bash
# Test deployed frontend
open http://maxtrace-frontend.s3-website-us-east-1.amazonaws.com
```

Same test flow as Step 6, but on the deployed site.

---

## Option 2: Full Test with Custom Model (4-8 hours)

### Step 1: Prepare Dataset

```bash
cd ml-model/data

# Option A: Generate synthetic data for testing
python download_sample_data.py --generate-synthetic --num-images=100

# Option B: Use your own annotated blueprint dataset
# Place in data/blueprints/images/{train,val}
# and data/blueprints/labels/{train,val}

# Validate dataset
python prepare_dataset.py --validate
```

**Expected Output:**
```
✅ Training set size: 80 images
✅ Validation set size: 20 images
✅ Dataset is valid and ready for training!
```

### Step 2: Train Model

```bash
cd ../training

# Train with default settings (takes 2-6 hours depending on hardware)
python train_enhanced.py \
  --epochs 100 \
  --batch-size 16 \
  --img-size 640 \
  --weights yolov5m.pt
```

**Expected Output:**
```
Training complete! Model saved in runs/train/blueprint_detector/weights/best.pt

Performance Metrics:
  Precision: 0.75
  Recall: 0.68
  mAP@0.5: 0.72
```

### Step 3: Deploy Custom Model

Follow Steps 2-7 from Option 1, using your trained model.

---

## Component-by-Component Testing

### Test 1: S3 Upload Handler

```bash
cd backend

# Invoke upload handler directly
aws lambda invoke \
  --function-name innergy-blueprint-detection-dev-uploadHandler \
  --payload '{
    "body": "{\"fileName\":\"test.png\",\"fileType\":\"image/png\",\"fileSize\":1000000,\"sessionId\":\"test-session-123\"}"
  }' \
  response.json

cat response.json
```

**Expected Output:**
```json
{
  "statusCode": 200,
  "body": {
    "blueprintId": "...",
    "uploadUrl": "https://innergy-blueprints-dev.s3.amazonaws.com/...",
    "expiresIn": 3600
  }
}
```

### Test 2: Inference Handler

```bash
# Invoke inference handler
aws lambda invoke \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --payload '{
    "body": "{\"blueprintId\":\"test-123\",\"sessionId\":\"test-session-123\",\"confidence\":0.5}"
  }' \
  response.json

cat response.json
```

**Expected Output:**
```json
{
  "statusCode": 200,
  "body": {
    "message": "Inference completed successfully",
    "results": {
      "detections": [...],
      "statistics": {
        "totalDetections": 12,
        "elementCounts": {...}
      }
    }
  }
}
```

### Test 3: Results Handler

```bash
# Get results
aws lambda invoke \
  --function-name innergy-blueprint-detection-dev-resultsHandler \
  --payload '{
    "pathParameters": {"blueprintId": "test-123"},
    "queryStringParameters": {"sessionId": "test-session-123"}
  }' \
  response.json

cat response.json
```

### Test 4: API Gateway Endpoints

```bash
API_URL="https://s4fsv92lt6.execute-api.us-east-1.amazonaws.com/dev"

# Test upload endpoint
curl -X POST $API_URL/upload \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "test.png",
    "fileType": "image/png",
    "fileSize": 1000000,
    "sessionId": "test-session-curl"
  }'

# Test detect endpoint (after uploading an image)
curl -X POST $API_URL/detect \
  -H "Content-Type: application/json" \
  -d '{
    "blueprintId": "blueprint-123",
    "sessionId": "test-session-curl",
    "confidence": 0.5
  }'

# Test results endpoint
curl $API_URL/results/blueprint-123?sessionId=test-session-curl
```

---

## End-to-End Integration Test Script

Create a file `test_e2e.sh`:

```bash
#!/bin/bash
set -e

echo "=== End-to-End Integration Test ==="

# 1. Upload test image
echo "1. Uploading test image..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  https://s4fsv92lt6.execute-api.us-east-1.amazonaws.com/dev/upload \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "test-blueprint.png",
    "fileType": "image/png",
    "fileSize": 1000000,
    "sessionId": "e2e-test-'$(date +%s)'"
  }')

BLUEPRINT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.blueprintId')
SESSION_ID=$(echo $UPLOAD_RESPONSE | jq -r '.sessionId')
UPLOAD_URL=$(echo $UPLOAD_RESPONSE | jq -r '.uploadUrl')

echo "✅ Blueprint ID: $BLUEPRINT_ID"

# 2. Upload actual file to S3
echo "2. Uploading file to S3..."
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/png" \
  --data-binary @test-blueprint.png

echo "✅ File uploaded"

# 3. Trigger inference
echo "3. Triggering inference..."
DETECT_RESPONSE=$(curl -s -X POST \
  https://s4fsv92lt6.execute-api.us-east-1.amazonaws.com/dev/detect \
  -H "Content-Type: application/json" \
  -d "{
    \"blueprintId\": \"$BLUEPRINT_ID\",
    \"sessionId\": \"$SESSION_ID\",
    \"confidence\": 0.5
  }")

echo "✅ Inference triggered"

# 4. Wait for processing
echo "4. Waiting for processing (30s)..."
sleep 30

# 5. Get results
echo "5. Fetching results..."
RESULTS=$(curl -s "https://s4fsv92lt6.execute-api.us-east-1.amazonaws.com/dev/results/$BLUEPRINT_ID?sessionId=$SESSION_ID")

DETECTIONS=$(echo $RESULTS | jq -r '.detections | length')
echo "✅ Detected $DETECTIONS elements"

echo ""
echo "=== Test Complete ==="
echo "Results:"
echo $RESULTS | jq '.'
```

Run it:
```bash
chmod +x test_e2e.sh
./test_e2e.sh
```

---

## Troubleshooting Common Issues

### Issue: Endpoint Not Found

```
Error: Could not find endpoint "yolov5-blueprint-detector"
```

**Fix:**
```bash
# Check if endpoint exists
aws sagemaker list-endpoints

# Update Lambda with correct endpoint name
aws lambda update-function-configuration \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --environment Variables="{SAGEMAKER_ENDPOINT=your-actual-endpoint-name}"
```

### Issue: Permission Denied

```
Error: User is not authorized to perform: sagemaker:InvokeEndpoint
```

**Fix:**
```bash
# Validate IAM permissions
cd backend
./validate_iam_permissions.sh

# Redeploy backend if needed
serverless deploy --stage dev
```

### Issue: Model Inference Failed

```
Error: Model inference failed: Invalid input format
```

**Fix:**
- Check image is uploaded to S3 correctly
- Verify S3 URI format: `s3://bucket/key`
- Check CloudWatch logs for details

### Issue: Slow Inference (>30s)

**Possible Causes:**
- Cold start (first request after deployment)
- Large image size
- Small SageMaker instance

**Fix:**
- Wait for endpoint to warm up (try again)
- Resize images to 640x640 before upload
- Use larger instance type (ml.m5.xlarge)

---

## Performance Benchmarks

**Expected Performance:**
- Upload: < 5 seconds
- Inference: 2-10 seconds (first request may take 30s due to cold start)
- Results retrieval: < 1 second
- End-to-end: < 20 seconds

**SageMaker Endpoint:**
- ml.m5.large: 2-5 seconds per image
- ml.m5.xlarge: 1-3 seconds per image
- ml.g4dn.xlarge (GPU): < 1 second per image

---

## Monitoring

### CloudWatch Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/innergy-blueprint-detection-dev-inferenceHandler --follow

# SageMaker logs
ENDPOINT_NAME=$(cat ml-model/deployment/.sagemaker_endpoint.json | jq -r '.endpoint_name')
aws logs tail /aws/sagemaker/Endpoints/$ENDPOINT_NAME --follow
```

### CloudWatch Metrics

1. Go to AWS Console → CloudWatch → Dashboards
2. View Lambda metrics: Invocations, Duration, Errors
3. View SageMaker metrics: ModelLatency, Invocations

---

## Clean Up After Testing

```bash
# Delete SageMaker endpoint (to stop charges)
ENDPOINT_NAME=$(cat ml-model/deployment/.sagemaker_endpoint.json | jq -r '.endpoint_name')
aws sagemaker delete-endpoint --endpoint-name $ENDPOINT_NAME
aws sagemaker delete-endpoint-config --endpoint-config-name $ENDPOINT_NAME
aws sagemaker delete-model --model-name $ENDPOINT_NAME

# Clear S3 test files
aws s3 rm s3://innergy-blueprints-dev/test/ --recursive
aws s3 rm s3://innergy-blueprints-dev/uploads/ --recursive
```

---

## Next Steps After Testing

1. ✅ Verify all components work end-to-end
2. ✅ Test with multiple blueprint types
3. ✅ Measure performance and accuracy
4. ⬜ Collect real blueprint dataset
5. ⬜ Train production model
6. ⬜ Set up monitoring and alerts
7. ⬜ Configure auto-scaling for production
8. ⬜ Add authentication (if needed)

---

## Quick Reference

**Test Commands:**
```bash
# Deploy model
cd ml-model/deployment && ./deploy_automated.sh

# Test endpoint
python test_endpoint.py --s3-uri s3://innergy-blueprints-dev/test/sample.png

# Test Lambda
cd ../../backend && python test_lambda_sagemaker.py

# Test frontend
cd ../frontend && npm run dev

# Clean up
aws sagemaker delete-endpoint --endpoint-name ENDPOINT_NAME
```

**Important URLs:**
- Frontend: http://maxtrace-frontend.s3-website-us-east-1.amazonaws.com
- API: https://s4fsv92lt6.execute-api.us-east-1.amazonaws.com/dev
- AWS Console: https://console.aws.amazon.com/
