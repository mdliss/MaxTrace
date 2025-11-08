"""
Lambda Function Testing Script for SageMaker Integration
Tests the inference handler with SageMaker endpoint
"""
import boto3
import json
import sys
import time
from datetime import datetime

lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

def test_inference_handler(
    function_name='innergy-blueprint-detection-dev-inferenceHandler',
    blueprint_id=None,
    session_id=None,
    s3_uri=None,
    confidence=0.5
):
    """
    Test the inference Lambda function

    Args:
        function_name: Name of the Lambda function
        blueprint_id: Blueprint ID (generated if not provided)
        session_id: Session ID (generated if not provided)
        s3_uri: S3 URI of test image (optional, will use uploaded image if not provided)
        confidence: Confidence threshold (0-1)

    Returns:
        dict: Lambda response
    """

    # Generate IDs if not provided
    if not blueprint_id:
        blueprint_id = f"test-{int(time.time())}"

    if not session_id:
        session_id = f"test-session-{int(time.time())}"

    print(f"\n{'='*60}")
    print("Testing Lambda Inference Handler")
    print(f"{'='*60}")
    print(f"Function: {function_name}")
    print(f"Blueprint ID: {blueprint_id}")
    print(f"Session ID: {session_id}")
    print(f"Confidence: {confidence}")
    print()

    # If S3 URI provided, create metadata
    if s3_uri:
        bucket_name = 'innergy-blueprints-dev'
        s3_key = f"uploads/{session_id}/{blueprint_id}/image.png"

        # Create metadata
        metadata = {
            'blueprintId': blueprint_id,
            'sessionId': session_id,
            's3Key': s3_key,
            'uploadedAt': datetime.utcnow().isoformat() + 'Z'
        }

        metadata_key = f"uploads/{session_id}/{blueprint_id}/metadata.json"

        print(f"Creating metadata at s3://{bucket_name}/{metadata_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata),
            ContentType='application/json'
        )

    # Prepare Lambda payload
    payload = {
        'body': json.dumps({
            'blueprintId': blueprint_id,
            'sessionId': session_id,
            'confidence': confidence
        })
    }

    try:
        print("Invoking Lambda function...")
        start_time = time.time()

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        end_time = time.time()
        duration = end_time - start_time

        # Parse response
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))

        print(f"\n✅ Lambda invocation completed in {duration:.2f}s")
        print(f"\n{'='*60}")
        print("Lambda Response")
        print(f"{'='*60}")
        print(f"Status Code: {response_payload.get('statusCode')}")

        if response_payload.get('statusCode') == 200:
            body = json.loads(response_payload.get('body', '{}'))
            results = body.get('results', {})

            print(f"\n📊 Detection Results:")
            print(f"  Blueprint ID: {results.get('blueprintId')}")
            print(f"  Model Version: {results.get('modelVersion')}")
            print(f"  Processing Time: {results.get('processingTime')}s")

            stats = results.get('statistics', {})
            print(f"\n📈 Statistics:")
            print(f"  Total Detections: {stats.get('totalDetections', 0)}")
            print(f"  Average Confidence: {stats.get('avgConfidence', 0):.2f}")

            element_counts = stats.get('elementCounts', {})
            if element_counts:
                print(f"\n🏗️  Element Breakdown:")
                for element_class, count in element_counts.items():
                    print(f"    {element_class}: {count}")

            detections = results.get('detections', [])
            if detections:
                print(f"\n📍 Detected Elements (first 5):")
                for detection in detections[:5]:
                    print(f"    - {detection.get('class', 'unknown')}: "
                          f"confidence={detection.get('confidence', 0):.2f}, "
                          f"bbox={detection.get('boundingBox', {})}")

                if len(detections) > 5:
                    print(f"    ... and {len(detections) - 5} more")

        else:
            error_body = json.loads(response_payload.get('body', '{}'))
            print(f"\n❌ Error: {error_body.get('error')}")
            print(f"Details: {error_body.get('details')}")

        return response_payload

    except Exception as e:
        print(f"\n❌ Error invoking Lambda: {str(e)}")
        return None

def test_endpoint_config():
    """
    Test if SageMaker endpoint is configured correctly

    Returns:
        bool: True if configuration is valid
    """
    print(f"\n{'='*60}")
    print("Checking Lambda Configuration")
    print(f"{'='*60}")

    try:
        function_name = 'innergy-blueprint-detection-dev-inferenceHandler'
        response = lambda_client.get_function_configuration(FunctionName=function_name)

        env_vars = response.get('Environment', {}).get('Variables', {})

        print("\n✅ Lambda function found")
        print("\nEnvironment Variables:")
        print(f"  BUCKET_NAME: {env_vars.get('BUCKET_NAME', 'not set')}")
        print(f"  SAGEMAKER_ENDPOINT: {env_vars.get('SAGEMAKER_ENDPOINT', 'not set')}")
        print(f"  MODEL_VERSION: {env_vars.get('MODEL_VERSION', 'not set')}")
        print(f"  SAGEMAKER_MAX_RETRIES: {env_vars.get('SAGEMAKER_MAX_RETRIES', 'not set')}")
        print(f"  SAGEMAKER_RETRY_DELAY: {env_vars.get('SAGEMAKER_RETRY_DELAY', 'not set')}")

        # Check if endpoint is set
        endpoint = env_vars.get('SAGEMAKER_ENDPOINT')
        if not endpoint or endpoint == 'yolov5-blueprint-detector':
            print("\n⚠️  Warning: Using default endpoint name")
            print("   Update with actual endpoint from deployment:")
            print("   aws lambda update-function-configuration \\")
            print("     --function-name innergy-blueprint-detection-dev-inferenceHandler \\")
            print("     --environment Variables=\"{SAGEMAKER_ENDPOINT=your-endpoint-name}\"")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test Lambda SageMaker Integration')

    parser.add_argument('--check-config', action='store_true',
                       help='Check Lambda configuration only')
    parser.add_argument('--function-name', type=str,
                       default='innergy-blueprint-detection-dev-inferenceHandler',
                       help='Lambda function name')
    parser.add_argument('--blueprint-id', type=str,
                       help='Blueprint ID (generated if not provided)')
    parser.add_argument('--session-id', type=str,
                       help='Session ID (generated if not provided)')
    parser.add_argument('--s3-uri', type=str,
                       help='S3 URI of test image')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Confidence threshold (0-1)')

    args = parser.parse_args()

    if args.check_config:
        test_endpoint_config()
    else:
        # Check config first
        if not test_endpoint_config():
            print("\n❌ Configuration check failed")
            sys.exit(1)

        # Run inference test
        result = test_inference_handler(
            function_name=args.function_name,
            blueprint_id=args.blueprint_id,
            session_id=args.session_id,
            s3_uri=args.s3_uri,
            confidence=args.confidence
        )

        if result and result.get('statusCode') == 200:
            print("\n✅ Test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Test failed")
            sys.exit(1)
