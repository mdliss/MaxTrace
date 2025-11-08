"""
SageMaker Inference Script for YOLOv5 Blueprint Detection
This script is deployed to SageMaker endpoint for model inference.
"""
import json
import torch
import io
import os
from PIL import Image
import boto3

# Model will be loaded from /opt/ml/model directory on SageMaker
MODEL_PATH = '/opt/ml/model/best.pt'

def model_fn(model_dir):
    """
    Load the YOLOv5 model from the model directory.
    Called once when the endpoint starts.
    """
    print(f"Loading model from {model_dir}")

    # Load YOLOv5 model
    model = torch.hub.load('ultralytics/yolov5', 'custom',
                          path=os.path.join(model_dir, 'best.pt'),
                          force_reload=True)

    model.eval()

    # Set confidence threshold
    model.conf = 0.5  # Default confidence threshold

    print("Model loaded successfully")
    return model


def input_fn(request_body, content_type):
    """
    Deserialize and prepare the input data.

    Args:
        request_body: The request body
        content_type: Content type of the request

    Returns:
        Deserialized input data
    """
    if content_type == 'application/json':
        # Input format: {"s3_uri": "s3://bucket/key", "confidence": 0.5}
        input_data = json.loads(request_body)
        return input_data
    elif content_type.startswith('image/'):
        # Direct image upload
        return {'image_bytes': request_body}
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model):
    """
    Perform prediction on the input data.

    Args:
        input_data: Deserialized input data
        model: Loaded model

    Returns:
        Prediction results
    """
    # Set confidence threshold if provided
    if 'confidence' in input_data:
        model.conf = input_data['confidence']

    # Load image from S3 or bytes
    if 's3_uri' in input_data:
        # Download from S3
        s3 = boto3.client('s3')
        bucket, key = input_data['s3_uri'].replace('s3://', '').split('/', 1)

        response = s3.get_object(Bucket=bucket, Key=key)
        image_bytes = response['Body'].read()
        image = Image.open(io.BytesIO(image_bytes))
    elif 'image_bytes' in input_data:
        # Use provided image bytes
        image = Image.open(io.BytesIO(input_data['image_bytes']))
    else:
        raise ValueError("Input must contain either 's3_uri' or 'image_bytes'")

    # Get image dimensions
    img_width, img_height = image.size

    # Run inference
    results = model(image)

    # Extract predictions
    predictions = results.pandas().xyxy[0]  # Pandas DataFrame

    # Format output
    detections = []
    for _, row in predictions.iterrows():
        detection = {
            'roomId': len(detections) + 1,
            'boundingBox': {
                'x': int(row['xmin']),
                'y': int(row['ymin']),
                'width': int(row['xmax'] - row['xmin']),
                'height': int(row['ymax'] - row['ymin'])
            },
            'confidence': float(row['confidence']),
            'class': row['name'],
            'area': int((row['xmax'] - row['xmin']) * (row['ymax'] - row['ymin']))
        }
        detections.append(detection)

    return {
        'detections': detections,
        'dimensions': {'width': img_width, 'height': img_height},
        'totalRooms': len(detections),
        'avgConfidence': sum(d['confidence'] for d in detections) / len(detections) if detections else 0
    }


def output_fn(prediction, accept):
    """
    Serialize the prediction output.

    Args:
        prediction: Prediction results
        accept: Accept header content type

    Returns:
        Serialized prediction
    """
    if accept == 'application/json':
        return json.dumps(prediction), accept
    else:
        raise ValueError(f"Unsupported accept type: {accept}")
