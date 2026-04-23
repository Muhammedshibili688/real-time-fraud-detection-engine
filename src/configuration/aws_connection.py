import boto3
import os
import sys
from src.exception import FraudException
from src.logger import logging

class S3Connection:
    """
    Singleton-style class to establish and manage a connection to AWS S3.
    It reads credentials from environment variables for security.
    """
    s3_client = None
    s3_resource = None

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initializes the S3 connection if it hasn't been established yet.
        """
        try:
            if S3Connection.s3_client is None or S3Connection.s3_resource is None:
                # 1. Fetch credentials from environment
                # These are set via 'aws configure' or your .env file
                access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
                secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

                # 2. Validation: Ensure keys are present
                if access_key_id is None or secret_access_key is None:
                    logging.warning("AWS Credentials not found in environment variables.")

                # 3. Create Session and Clients
                session = boto3.Session(
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    region_name=region_name
                )
                
                S3Connection.s3_resource = session.resource('s3')
                S3Connection.s3_client = session.client('s3')
                
                logging.info(f"Successfully established S3 Connection in region: {region_name}")

            # Assign class-level clients to the instance
            self.s3_resource = S3Connection.s3_resource
            self.s3_client = S3Connection.s3_client

        except Exception as e:
            raise FraudException(e, sys)