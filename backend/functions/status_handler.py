import json
import boto3
import os
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'innergy-blueprints-dev')

def lambda_handler(event, context):
    """
    Lambda function to check processing status of a blueprint.
    Returns current status, progress stage, and estimated time remaining.
    """
    try:
        # Get blueprint ID from path parameters
        blueprint_id = event.get('pathParameters', {}).get('blueprintId')

        if not blueprint_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Missing blueprintId parameter'
                })
            }

        # Find the status file in S3
        # The file structure is: uploads/{sessionId}/{blueprintId}/status.json

        try:
            # List objects with prefix matching the blueprint ID
            response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f'uploads/',
                MaxKeys=100
            )

            # Find the status file for this blueprint
            status_key = None
            for obj in response.get('Contents', []):
                if blueprint_id in obj['Key'] and obj['Key'].endswith('status.json'):
                    status_key = obj['Key']
                    break

            if not status_key:
                # Status file not found - check if results exist
                results_key = None
                for obj in response.get('Contents', []):
                    if blueprint_id in obj['Key'] and obj['Key'].endswith('results.json'):
                        results_key = obj['Key']
                        break

                if results_key:
                    # Results exist, processing is complete
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Content-Type',
                            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                        },
                        'body': json.dumps({
                            'blueprintId': blueprint_id,
                            'status': 'completed',
                            'stage': 'complete',
                            'progress': 100,
                            'estimatedTimeRemaining': 0,
                            'message': 'Processing completed successfully'
                        })
                    }
                else:
                    # Neither status nor results found
                    return {
                        'statusCode': 404,
                        'headers': {
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Content-Type',
                            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                        },
                        'body': json.dumps({
                            'error': 'Blueprint not found or processing not started'
                        })
                    }

            # Retrieve the status file
            response = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=status_key
            )

            status = json.loads(response['Body'].read().decode('utf-8'))

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(status)
            }

        except s3_client.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Status not found for this blueprint ID'
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
