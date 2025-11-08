"""
Deploy YOLOv5 model to AWS SageMaker
"""
import boto3
import sagemaker
from sagemaker.pytorch import PyTorchModel
from datetime import datetime
import os

def deploy_model(
    model_path='runs/train/blueprint_detector/weights/best.pt',
    role_arn=None,
    instance_type='ml.m5.large',
    instance_count=1,
    endpoint_name=None
):
    """
    Deploy YOLOv5 model to SageMaker endpoint

    Args:
        model_path: Local path to trained model weights
        role_arn: AWS IAM role ARN with SageMaker permissions
        instance_type: EC2 instance type for endpoint
        instance_count: Number of instances (for auto-scaling)
        endpoint_name: Custom endpoint name (optional)
    """

    # Initialize SageMaker session
    sagemaker_session = sagemaker.Session()
    region = sagemaker_session.boto_region_name

    # Get execution role if not provided
    if role_arn is None:
        role_arn = sagemaker.get_execution_role()

    print(f"Using role: {role_arn}")
    print(f"Deploying to region: {region}")

    # Generate endpoint name if not provided
    if endpoint_name is None:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        endpoint_name = f'yolov5-blueprint-detector-{timestamp}'

    # Create model archive
    print("Creating model archive...")
    model_archive = create_model_archive(model_path)

    # Upload model to S3
    print("Uploading model to S3...")
    s3_model_uri = sagemaker_session.upload_data(
        path=model_archive,
        key_prefix='models/yolov5-blueprint'
    )
    print(f"Model uploaded to: {s3_model_uri}")

    # Create PyTorch model
    print("Creating SageMaker model...")
    pytorch_model = PyTorchModel(
        model_data=s3_model_uri,
        role=role_arn,
        framework_version='1.12.0',
        py_version='py38',
        entry_point='inference.py',
        source_dir='deployment',
        sagemaker_session=sagemaker_session
    )

    # Deploy model to endpoint
    print(f"Deploying endpoint: {endpoint_name}")
    print(f"Instance type: {instance_type}")
    print(f"Instance count: {instance_count}")

    predictor = pytorch_model.deploy(
        instance_type=instance_type,
        initial_instance_count=instance_count,
        endpoint_name=endpoint_name,
        wait=True
    )

    print("\n" + "="*50)
    print("DEPLOYMENT SUCCESSFUL!")
    print("="*50)
    print(f"Endpoint Name: {endpoint_name}")
    print(f"Endpoint ARN: arn:aws:sagemaker:{region}:{sagemaker_session.account_id()}:endpoint/{endpoint_name}")
    print("\nUpdate your Lambda function environment variables:")
    print(f"  SAGEMAKER_ENDPOINT={endpoint_name}")
    print("="*50)

    return predictor, endpoint_name


def create_model_archive(model_path):
    """
    Create a tar.gz archive of the model and inference code
    """
    import tarfile
    import shutil

    # Create temporary directory
    temp_dir = 'temp_model_package'
    os.makedirs(temp_dir, exist_ok=True)

    # Copy model weights
    shutil.copy(model_path, os.path.join(temp_dir, 'best.pt'))

    # Create archive
    archive_path = 'model.tar.gz'
    with tarfile.open(archive_path, 'w:gz') as tar:
        tar.add(temp_dir, arcname='.')

    # Cleanup
    shutil.rmtree(temp_dir)

    print(f"Model archive created: {archive_path}")
    return archive_path


def test_endpoint(endpoint_name, test_image_s3_uri):
    """
    Test the deployed endpoint with a sample image

    Args:
        endpoint_name: Name of the deployed endpoint
        test_image_s3_uri: S3 URI of test image
    """
    import json

    runtime = boto3.client('sagemaker-runtime')

    payload = {
        's3_uri': test_image_s3_uri,
        'confidence': 0.5
    }

    print(f"Testing endpoint {endpoint_name}...")
    print(f"Test image: {test_image_s3_uri}")

    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=json.dumps(payload)
    )

    result = json.loads(response['Body'].read().decode())
    print(f"\nDetection Results:")
    print(f"Total rooms detected: {result['totalRooms']}")
    print(f"Average confidence: {result['avgConfidence']:.2f}")

    for detection in result['detections']:
        print(f"\nRoom {detection['roomId']}:")
        print(f"  Bounding Box: {detection['boundingBox']}")
        print(f"  Confidence: {detection['confidence']:.2f}")
        print(f"  Area: {detection['area']} pixels")

    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Deploy YOLOv5 to SageMaker')
    parser.add_argument('--model-path', type=str,
                       default='runs/train/blueprint_detector/weights/best.pt',
                       help='Path to trained model weights')
    parser.add_argument('--role-arn', type=str, required=True,
                       help='AWS IAM role ARN with SageMaker permissions')
    parser.add_argument('--instance-type', type=str, default='ml.m5.large',
                       help='EC2 instance type')
    parser.add_argument('--instance-count', type=int, default=1,
                       help='Number of instances')
    parser.add_argument('--endpoint-name', type=str, default=None,
                       help='Custom endpoint name')
    parser.add_argument('--test-image', type=str, default=None,
                       help='S3 URI of test image to validate deployment')

    args = parser.parse_args()

    # Deploy model
    predictor, endpoint_name = deploy_model(
        model_path=args.model_path,
        role_arn=args.role_arn,
        instance_type=args.instance_type,
        instance_count=args.instance_count,
        endpoint_name=args.endpoint_name
    )

    # Test endpoint if test image provided
    if args.test_image:
        test_endpoint(endpoint_name, args.test_image)
