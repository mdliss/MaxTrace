# YOLOv5 Blueprint Room Detection Model

This directory contains the machine learning model infrastructure for detecting room boundaries in architectural blueprints.

## Directory Structure

```
ml-model/
├── training/          # Model training scripts
│   └── train.py      # YOLOv5 training script
├── deployment/       # SageMaker deployment scripts
│   ├── inference.py  # SageMaker inference handler
│   └── deploy_sagemaker.py  # Deployment automation
├── data/            # Dataset and configuration
│   └── blueprint_dataset.yaml  # Dataset config
└── requirements.txt # Python dependencies
```

## Setup

### 1. Prepare Dataset

Create a dataset in YOLO format:

```
data/blueprints/
├── images/
│   ├── train/     # Training images (PNG/JPG)
│   ├── val/       # Validation images
│   └── test/      # Test images
└── labels/
    ├── train/     # Training annotations (.txt)
    ├── val/       # Validation annotations
    └── test/      # Test annotations
```

**Annotation Format:**
- Each image needs a corresponding .txt file
- Format: `<class> <x_center> <y_center> <width> <height>`
- All values normalized (0-1)
- Example: `0 0.5 0.5 0.3 0.4`

**Recommended Tools:**
- [LabelImg](https://github.com/heartexlabs/labelImg)
- [Roboflow](https://roboflow.com)
- [CVAT](https://github.com/opencv/cvat)

**Minimum Dataset Size:** 100+ annotated blueprints

### 2. Install Dependencies

```bash
cd ml-model
pip install -r requirements.txt
```

### 3. Train Model

```bash
cd training
python train.py
```

**Training Parameters:**
- Epochs: 100 (adjustable in train.py)
- Image Size: 640x640
- Batch Size: 16
- Base Model: YOLOv5m (medium)

**Output:** Trained model saved to `runs/train/blueprint_detector/weights/best.pt`

## Deployment to SageMaker

### Prerequisites

1. AWS account with SageMaker access
2. IAM role with permissions:
   - SageMaker full access
   - S3 read/write access
   - CloudWatch logs access

### Deploy Endpoint

```bash
cd deployment
python deploy_sagemaker.py \
  --model-path ../training/runs/train/blueprint_detector/weights/best.pt \
  --role-arn arn:aws:iam::YOUR_ACCOUNT:role/SageMakerRole \
  --instance-type ml.m5.large \
  --instance-count 1
```

**Parameters:**
- `--model-path`: Path to trained model weights
- `--role-arn`: IAM role ARN (required)
- `--instance-type`: EC2 instance type (default: ml.m5.large)
- `--instance-count`: Number of instances for auto-scaling
- `--endpoint-name`: Custom endpoint name (optional)
- `--test-image`: S3 URI to test deployment (optional)

### Test Deployment

```bash
python deploy_sagemaker.py \
  --model-path best.pt \
  --role-arn arn:aws:iam::123456789:role/SageMakerRole \
  --test-image s3://innergy-blueprints-dev/test/sample-blueprint.png
```

## Update Lambda Function

After deployment, update the Lambda inference handler environment variable:

```bash
aws lambda update-function-configuration \
  --function-name innergy-blueprint-detection-dev-inferenceHandler \
  --environment Variables="{SAGEMAKER_ENDPOINT=yolov5-blueprint-detector-TIMESTAMP}"
```

Or update in `backend/serverless.yml`:

```yaml
environment:
  SAGEMAKER_ENDPOINT: yolov5-blueprint-detector-TIMESTAMP
```

## Model Performance Targets

- **Inference Time:** < 30 seconds per blueprint
- **Detection Accuracy:** ≥ 75% on validation set
- **Confidence Threshold:** 0.5 (adjustable via API)

## Cost Optimization

**Development:**
- Use `ml.m5.large` instances
- Single instance (no auto-scaling)
- Delete endpoint when not in use

**Production:**
- Enable auto-scaling (1-3 instances)
- Use `ml.m5.xlarge` for better performance
- Consider SageMaker Serverless Inference for variable load

**Delete Endpoint:**
```bash
aws sagemaker delete-endpoint --endpoint-name ENDPOINT_NAME
```

## Troubleshooting

**Training Issues:**
- Ensure dataset YAML paths are correct
- Check image/label file alignment
- Verify annotations are in YOLO format
- Monitor GPU memory usage

**Deployment Issues:**
- Verify IAM role permissions
- Check S3 bucket accessibility
- Ensure PyTorch version compatibility
- Review CloudWatch logs for errors

**Inference Issues:**
- Validate input image format
- Check confidence threshold settings
- Monitor endpoint metrics in CloudWatch
- Verify S3 URI format in requests
