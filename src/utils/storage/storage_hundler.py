import boto3
import asyncio
import io
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from middlewares.errors.error_handler import handle_exceptions
from src.utils.logger.logger import initialize_logging, custom_logger
from src.utils.task_utils.loader import emulator

load_dotenv()

initialize_logging()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')


# S3 client
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


@handle_exceptions
async def create_bucket(bucket_name):
    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
        )
        custom_logger(f'Bucket {bucket_name} created successfully.', 'info')
        return bucket_name
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            custom_logger(f'Storage stream to bucket: {bucket_name} open...', 'warn')
            return bucket_name
        else:
            custom_logger(f'Error creating bucket: {e}', 'error')
            raise e


@handle_exceptions
async def save_stream_to_s3(data_stream, file_key, content_type='application/octet-stream'):
    try:
        # Ensure the bucket exists
        await create_bucket(AWS_BUCKET_NAME)

        # Define the upload coroutine
        async def upload_file():
            emulator(is_in_progress=True)
            try:
                s3_client.upload_fileobj(
                    data_stream,
                    AWS_BUCKET_NAME,
                    file_key,
                    ExtraArgs={'ContentType': content_type}
                )
                emulator(is_in_progress=False)
                custom_logger(f'File {file_key} uploaded successfully to {AWS_BUCKET_NAME}.', 'info')
            except ClientError as e:
                custom_logger(f'Error uploading file: {e}', 'error')
                emulator(is_in_progress=False)
                raise e

        # Run the upload coroutine and await its completion
        await upload_file()

    except Exception as e:
        custom_logger(f'Failed to save stream to S3: {e}', 'error')
        raise e