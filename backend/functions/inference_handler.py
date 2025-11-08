import json
import boto3
import os
import time
from datetime import datetime
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
sagemaker_client = boto3.client('sagemaker-runtime')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'innergy-blueprints-dev')
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT', 'yolov5-blueprint-detector')
MODEL_VERSION = os.environ.get('MODEL_VERSION', 'yolov5-v1.0')
MAX_RETRIES = int(os.environ.get('SAGEMAKER_MAX_RETRIES', '3'))
RETRY_DELAY = float(os.environ.get('SAGEMAKER_RETRY_DELAY', '1.0'))

def invoke_sagemaker_with_retry(endpoint_name, payload, max_retries=MAX_RETRIES):
    """
    Invoke SageMaker endpoint with exponential backoff retry logic

    Args:
        endpoint_name: Name of the SageMaker endpoint
        payload: Request payload
        max_retries: Maximum number of retry attempts

    Returns:
        dict: Parsed response from SageMaker

    Raises:
        Exception: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = sagemaker_client.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/json',
                Accept='application/json',
                Body=json.dumps(payload)
            )

            result = json.loads(response['Body'].read().decode('utf-8'))
            return result

        except sagemaker_client.exceptions.ModelError as e:
            # Model errors are not retryable
            print(f"Model error (not retrying): {str(e)}")
            raise

        except Exception as e:
            error_msg = str(e)
            print(f"Attempt {attempt + 1}/{max_retries} failed: {error_msg}")

            # Check if error is retryable
            is_retryable = (
                'ServiceUnavailable' in error_msg or
                'ThrottlingException' in error_msg or
                'InternalFailure' in error_msg or
                'timeout' in error_msg.lower()
            )

            if attempt < max_retries - 1 and is_retryable:
                # Exponential backoff
                delay = RETRY_DELAY * (2 ** attempt)
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"Max retries reached or non-retryable error")
                raise

def lambda_handler(event, context):
    """
    Lambda function to trigger SageMaker inference.
    This will be fully implemented in Task 5.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        blueprint_id = body.get('blueprintId')
        session_id = body.get('sessionId')

        # Get optional confidence threshold (default 0.5)
        confidence = body.get('confidence', 0.5)

        if not all([blueprint_id, session_id]):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Missing required fields: blueprintId, sessionId'
                })
            }

        # Get metadata to find the S3 key for the uploaded blueprint
        metadata_key = f"uploads/{session_id}/{blueprint_id}/metadata.json"

        try:
            metadata_response = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=metadata_key
            )
            metadata = json.loads(metadata_response['Body'].read().decode('utf-8'))
            s3_key = metadata.get('s3Key')

            if not s3_key:
                raise ValueError("S3 key not found in metadata")

        except s3_client.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Blueprint metadata not found'
                })
            }

        # Construct S3 URI for SageMaker
        s3_uri = f"s3://{BUCKET_NAME}/{s3_key}"

        # Prepare payload for SageMaker endpoint
        payload = {
            's3_uri': s3_uri,
            'confidence': confidence
        }

        print(f"Invoking SageMaker endpoint: {SAGEMAKER_ENDPOINT}")
        print(f"Blueprint: {blueprint_id}, S3 URI: {s3_uri}")

        # Record start time for processing metrics
        start_time = time.time()

        # Update status: preprocessing
        status_key = f"uploads/{session_id}/{blueprint_id}/status.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=status_key,
            Body=json.dumps({
                'blueprintId': blueprint_id,
                'status': 'processing',
                'stage': 'preprocessing',
                'progress': 25,
                'estimatedTimeRemaining': 15,
                'message': 'Preparing image for inference...',
                'updatedAt': datetime.utcnow().isoformat() + 'Z'
            }),
            ContentType='application/json'
        )

        try:
            # Update status: inference
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=status_key,
                Body=json.dumps({
                    'blueprintId': blueprint_id,
                    'status': 'processing',
                    'stage': 'inference',
                    'progress': 50,
                    'estimatedTimeRemaining': 10,
                    'message': 'Running AI model inference...',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }),
                ContentType='application/json'
            )

            # Invoke SageMaker endpoint with retry logic
            result = invoke_sagemaker_with_retry(SAGEMAKER_ENDPOINT, payload)

            # Update status: postprocess
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=status_key,
                Body=json.dumps({
                    'blueprintId': blueprint_id,
                    'status': 'processing',
                    'stage': 'postprocess',
                    'progress': 75,
                    'estimatedTimeRemaining': 5,
                    'message': 'Finalizing detection results...',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }),
                ContentType='application/json'
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Calculate statistics by element class
            detections = result.get('detections', [])
            class_counts = {}
            for detection in detections:
                element_class = detection.get('class', 'unknown')
                class_counts[element_class] = class_counts.get(element_class, 0) + 1

            # Format results according to PRD specification
            formatted_results = {
                'blueprintId': blueprint_id,
                'modelVersion': MODEL_VERSION,
                'processingTime': round(processing_time, 2),
                'detectedAt': datetime.utcnow().isoformat() + 'Z',
                'detections': detections,
                'statistics': {
                    'totalDetections': len(detections),
                    'totalRooms': result.get('totalRooms', 0),
                    'avgConfidence': round(result.get('avgConfidence', 0), 2),
                    'elementCounts': class_counts,
                    'processingSteps': ['upload', 'inference', 'postprocess']
                },
                'dimensions': result.get('dimensions', {})
            }

            # Store results in S3
            results_key = f"uploads/{session_id}/{blueprint_id}/results.json"
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=results_key,
                Body=json.dumps(formatted_results),
                ContentType='application/json'
            )

            # Update status: complete
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=status_key,
                Body=json.dumps({
                    'blueprintId': blueprint_id,
                    'status': 'completed',
                    'stage': 'complete',
                    'progress': 100,
                    'estimatedTimeRemaining': 0,
                    'message': 'Processing completed successfully',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }),
                ContentType='application/json'
            )

            print(f"Results stored at s3://{BUCKET_NAME}/{results_key}")
            print(f"Detected {formatted_results['statistics']['totalDetections']} elements in {processing_time:.2f}s")
            print(f"Element breakdown: {class_counts}")

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'message': 'Inference completed successfully',
                    'blueprintId': blueprint_id,
                    'results': formatted_results
                })
            }

        except sagemaker_client.exceptions.ModelError as e:
            print(f"SageMaker Model Error: {str(e)}")
            # Update status: failed
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=status_key,
                Body=json.dumps({
                    'blueprintId': blueprint_id,
                    'status': 'failed',
                    'stage': 'failed',
                    'progress': 0,
                    'estimatedTimeRemaining': 0,
                    'message': f'Model inference failed: {str(e)}',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }),
                ContentType='application/json'
            )
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Model inference failed',
                    'details': str(e)
                })
            }

        except Exception as e:
            print(f"SageMaker invocation error: {str(e)}")
            # Update status: failed
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=status_key,
                Body=json.dumps({
                    'blueprintId': blueprint_id,
                    'status': 'failed',
                    'stage': 'failed',
                    'progress': 0,
                    'estimatedTimeRemaining': 0,
                    'message': f'Failed to invoke SageMaker endpoint: {str(e)}',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }),
                ContentType='application/json'
            )
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Failed to invoke SageMaker endpoint',
                    'details': str(e)
                })
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
