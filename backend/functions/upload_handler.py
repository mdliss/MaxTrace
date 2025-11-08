import json
import boto3
import uuid
import os
from datetime import datetime
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'innergy-blueprints-dev')

def lambda_handler(event, context):
    """
    Lambda function to handle blueprint uploads.
    Generates a presigned URL for direct S3 upload from the frontend.
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))

        # Get file metadata from request
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        file_size = body.get('fileSize')
        session_id = body.get('sessionId')

        if not all([file_name, file_type, file_size, session_id]):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Missing required fields: fileName, fileType, fileSize, sessionId'
                })
            }

        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
        if file_type not in allowed_types:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Invalid file type. Only PNG, JPG, and PDF are allowed.'
                })
            }

        # Validate file size (10MB max)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'File size exceeds 10MB limit.'
                })
            }

        # Generate unique blueprint ID
        blueprint_id = f"blueprint-{uuid.uuid4().hex[:12]}"

        # Create S3 object key
        file_extension = file_name.split('.')[-1]
        s3_key = f"uploads/{session_id}/{blueprint_id}/original.{file_extension}"

        # Generate presigned URL for PUT upload (valid for 5 minutes)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_key,
                'ContentType': file_type
            },
            ExpiresIn=300  # 5 minutes
        )

        # Create metadata object
        metadata = {
            'blueprintId': blueprint_id,
            'sessionId': session_id,
            'fileName': file_name,
            'uploadedAt': datetime.utcnow().isoformat() + 'Z',
            'fileSize': file_size,
            'format': file_extension,
            's3Key': s3_key
        }

        # Store metadata in S3
        metadata_key = f"uploads/{session_id}/{blueprint_id}/metadata.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=metadata_key,
            Body=json.dumps(metadata),
            ContentType='application/json'
        )

        # Create initial status
        status_key = f"uploads/{session_id}/{blueprint_id}/status.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=status_key,
            Body=json.dumps({
                'blueprintId': blueprint_id,
                'status': 'processing',
                'stage': 'upload',
                'progress': 10,
                'estimatedTimeRemaining': 20,
                'message': 'Blueprint uploaded, preparing for processing...',
                'updatedAt': datetime.utcnow().isoformat() + 'Z'
            }),
            ContentType='application/json'
        )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'blueprintId': blueprint_id,
                'uploadUrl': presigned_url,
                's3Key': s3_key,
                'message': 'Presigned URL generated successfully'
            })
        }

    except ClientError as e:
        print(f"S3 Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'error': 'Failed to generate upload URL',
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
