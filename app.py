from src.configuration.aws_connection import S3Connection
from src.constants import TRAINING_BUCKET_NAME
from src.logger import logging

try:
    # Initialize connection
    aws_conn = S3Connection()
    
    # Try to list files in your bucket
    logging.info(f"Checking bucket: {TRAINING_BUCKET_NAME}")
    response = aws_conn.s3_client.list_objects_v2(Bucket=TRAINING_BUCKET_NAME)
    
    if 'Contents' in response:
        print("✅ Connection Successful! Found files in bucket.")
    else:
        print("✅ Connection Successful! Bucket is currently empty.")

except Exception as e:
    print(f"❌ Connection Failed: {e}")