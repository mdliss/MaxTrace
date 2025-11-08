import json
import boto3
import os
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'innergy-blueprints-dev')

def lambda_handler(event, context):
    """
    Lambda function to retrieve detection results.
    Returns the results.json file from S3.
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

        # Find the results file in S3
        # The file structure is: uploads/{sessionId}/{blueprintId}/results.json
        # We'll need to search for it since we don't have sessionId in the request

        try:
            # List objects with prefix matching the blueprint ID
            response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f'uploads/',
                MaxKeys=100
            )

            # Find the results file for this blueprint
            results_key = None
            for obj in response.get('Contents', []):
                if blueprint_id in obj['Key'] and obj['Key'].endswith('results.json'):
                    results_key = obj['Key']
                    break

            if not results_key:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        'error': 'Results not found for this blueprint ID'
                    })
                }

            # Retrieve the results file
            response = s3_client.get_object(
                Bucket=BUCKET_NAME,
                Key=results_key
            )

            results = json.loads(response['Body'].read().decode('utf-8'))

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(results)
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
                    'error': 'Results not found for this blueprint ID'
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
