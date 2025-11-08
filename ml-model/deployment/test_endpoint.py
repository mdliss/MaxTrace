"""
SageMaker Endpoint Testing Script
Tests deployed YOLOv5 endpoint with sample images and validates responses
"""
import argparse
import boto3
import json
import time
from pathlib import Path
import sys

def load_endpoint_config():
    """Load endpoint configuration from saved file"""
    config_file = Path('.sagemaker_endpoint.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def check_endpoint_status(endpoint_name):
    """
    Check if endpoint is in service

    Args:
        endpoint_name: Name of the SageMaker endpoint

    Returns:
        bool: True if endpoint is in service
    """
    sagemaker = boto3.client('sagemaker')

    try:
        response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        status = response['EndpointStatus']

        print(f"Endpoint Status: {status}")

        if status == 'InService':
            print("✅ Endpoint is ready for inference")
            return True
        elif status == 'Creating':
            print("⏳ Endpoint is still being created. Please wait...")
            return False
        elif status == 'Failed':
            print("❌ Endpoint creation failed")
            print(f"Failure Reason: {response.get('FailureReason', 'Unknown')}")
            return False
        else:
            print(f"⚠️  Endpoint in unexpected status: {status}")
            return False

    except sagemaker.exceptions.ClientError as e:
        print(f"❌ Error checking endpoint: {e}")
        return False

def test_endpoint_with_s3(endpoint_name, s3_uri, confidence=0.5):
    """
    Test endpoint with an image from S3

    Args:
        endpoint_name: Name of the SageMaker endpoint
        s3_uri: S3 URI of test image (s3://bucket/key)
        confidence: Confidence threshold (0-1)

    Returns:
        dict: Inference results
    """
    runtime = boto3.client('sagemaker-runtime')

    print(f"\n{'='*60}")
    print("Testing Endpoint with S3 Image")
    print(f"{'='*60}")
    print(f"Endpoint: {endpoint_name}")
    print(f"Image: {s3_uri}")
    print(f"Confidence: {confidence}")
    print()

    payload = {
        's3_uri': s3_uri,
        'confidence': confidence
    }

    try:
        print("Invoking endpoint...")
        start_time = time.time()

        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )

        end_time = time.time()
        inference_time = end_time - start_time

        result = json.loads(response['Body'].read().decode())

        print(f"\n✅ Inference completed in {inference_time:.2f} seconds")
        print(f"\n{'='*60}")
        print("Detection Results")
        print(f"{'='*60}")
        print(f"Total Detections: {result.get('totalRooms', 0)}")
        print(f"Average Confidence: {result.get('avgConfidence', 0):.2f}")

        if 'dimensions' in result:
            print(f"Image Dimensions: {result['dimensions']['width']}x{result['dimensions']['height']}")

        if result.get('detections'):
            print(f"\nDetected Elements:")
            for detection in result['detections'][:10]:  # Show first 10
                print(f"\n  Element {detection['roomId']}:")
                print(f"    Class: {detection.get('class', 'unknown')}")
                print(f"    Confidence: {detection['confidence']:.2f}")
                print(f"    Bounding Box: {detection['boundingBox']}")
                print(f"    Area: {detection['area']} pixels")

            if len(result['detections']) > 10:
                print(f"\n  ... and {len(result['detections']) - 10} more detections")
        else:
            print("\n  No elements detected (confidence may be too high)")

        return result

    except Exception as e:
        print(f"\n❌ Error invoking endpoint: {e}")
        return None

def test_endpoint_with_local_image(endpoint_name, image_path, confidence=0.5):
    """
    Test endpoint with a local image file

    Args:
        endpoint_name: Name of the SageMaker endpoint
        image_path: Path to local image file
        confidence: Confidence threshold (0-1)

    Returns:
        dict: Inference results
    """
    runtime = boto3.client('sagemaker-runtime')

    print(f"\n{'='*60}")
    print("Testing Endpoint with Local Image")
    print(f"{'='*60}")
    print(f"Endpoint: {endpoint_name}")
    print(f"Image: {image_path}")
    print(f"Confidence: {confidence}")
    print()

    # Read image file
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    try:
        print("Invoking endpoint...")
        start_time = time.time()

        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='image/jpeg',  # or 'image/png'
            Body=image_bytes
        )

        end_time = time.time()
        inference_time = end_time - start_time

        result = json.loads(response['Body'].read().decode())

        print(f"\n✅ Inference completed in {inference_time:.2f} seconds")
        print(f"\n{'='*60}")
        print("Detection Results")
        print(f"{'='*60}")
        print(f"Total Detections: {result.get('totalRooms', 0)}")
        print(f"Average Confidence: {result.get('avgConfidence', 0):.2f}")

        if 'dimensions' in result:
            print(f"Image Dimensions: {result['dimensions']['width']}x{result['dimensions']['height']}")

        if result.get('detections'):
            print(f"\nDetected Elements:")
            for detection in result['detections'][:10]:
                print(f"\n  Element {detection['roomId']}:")
                print(f"    Class: {detection.get('class', 'unknown')}")
                print(f"    Confidence: {detection['confidence']:.2f}")
                print(f"    Bounding Box: {detection['boundingBox']}")

            if len(result['detections']) > 10:
                print(f"\n  ... and {len(result['detections']) - 10} more detections")

        return result

    except Exception as e:
        print(f"\n❌ Error invoking endpoint: {e}")
        return None

def run_performance_test(endpoint_name, s3_uri, num_requests=10):
    """
    Run performance test with multiple requests

    Args:
        endpoint_name: Name of endpoint
        s3_uri: S3 URI of test image
        num_requests: Number of requests to send

    Returns:
        dict: Performance statistics
    """
    print(f"\n{'='*60}")
    print(f"Performance Test: {num_requests} requests")
    print(f"{'='*60}\n")

    runtime = boto3.client('sagemaker-runtime')
    payload = {'s3_uri': s3_uri, 'confidence': 0.5}

    times = []
    successes = 0
    failures = 0

    for i in range(num_requests):
        try:
            start = time.time()
            response = runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            end = time.time()

            times.append(end - start)
            successes += 1
            print(f"  Request {i+1}/{num_requests}: {times[-1]:.2f}s ✅")

        except Exception as e:
            failures += 1
            print(f"  Request {i+1}/{num_requests}: Failed ❌")

    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n{'='*60}")
        print("Performance Summary")
        print(f"{'='*60}")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {successes}")
        print(f"Failed: {failures}")
        print(f"Average Time: {avg_time:.2f}s")
        print(f"Min Time: {min_time:.2f}s")
        print(f"Max Time: {max_time:.2f}s")
        print(f"Success Rate: {(successes/num_requests)*100:.1f}%")

        return {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'successes': successes,
            'failures': failures
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test SageMaker Endpoint')

    parser.add_argument('--endpoint-name', type=str,
                       help='Name of the SageMaker endpoint (auto-detected if not provided)')
    parser.add_argument('--s3-uri', type=str,
                       help='S3 URI of test image (e.g., s3://bucket/key)')
    parser.add_argument('--local-image', type=str,
                       help='Path to local image file')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Confidence threshold (0-1)')
    parser.add_argument('--performance-test', type=int,
                       help='Run performance test with N requests')

    args = parser.parse_args()

    # Auto-detect endpoint name
    endpoint_name = args.endpoint_name
    if not endpoint_name:
        config = load_endpoint_config()
        if config:
            endpoint_name = config['endpoint_name']
            print(f"ℹ️  Using endpoint from config: {endpoint_name}\n")
        else:
            print("❌ No endpoint name provided and no config file found")
            print("Provide --endpoint-name or run deploy_automated.sh first")
            sys.exit(1)

    # Check endpoint status
    if not check_endpoint_status(endpoint_name):
        sys.exit(1)

    # Run tests
    if args.performance_test:
        if not args.s3_uri:
            print("❌ --s3-uri required for performance test")
            sys.exit(1)
        run_performance_test(endpoint_name, args.s3_uri, args.performance_test)

    elif args.local_image:
        if not Path(args.local_image).exists():
            print(f"❌ Image file not found: {args.local_image}")
            sys.exit(1)
        test_endpoint_with_local_image(endpoint_name, args.local_image, args.confidence)

    elif args.s3_uri:
        test_endpoint_with_s3(endpoint_name, args.s3_uri, args.confidence)

    else:
        print("❌ Provide either --s3-uri or --local-image")
        print("\nExamples:")
        print("  python test_endpoint.py --s3-uri s3://innergy-blueprints-dev/test/sample.png")
        print("  python test_endpoint.py --local-image ../data/test/blueprint.jpg")
        print("  python test_endpoint.py --s3-uri s3://bucket/image.png --performance-test 10")
        sys.exit(1)
