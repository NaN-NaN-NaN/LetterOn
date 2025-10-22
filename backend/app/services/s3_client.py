"""
LetterOn Server - AWS S3 Client
Purpose: Handle S3 operations for letter image storage
Testing: Mock boto3 S3 client in tests
AWS Deployment: Ensure S3 read/write permissions in IAM role

This module provides:
- Image upload to S3
- Presigned URL generation for secure access
- Image deletion
- S3 key generation with proper prefixes
"""

import logging
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

from app.settings import settings
from app.utils.helpers import generate_uuid, sanitize_filename

logger = logging.getLogger(__name__)


class S3Client:
    """
    Client for AWS S3 operations.

    Handles uploading letter images and generating access URLs.
    """

    def __init__(self):
        """Initialize boto3 S3 client with configured credentials."""
        aws_config = settings.get_aws_credentials()
        self.client = boto3.client('s3', **aws_config)
        self.bucket_name = settings.s3_bucket_name
        logger.info(f"S3 client initialized for bucket: {self.bucket_name}")

    def generate_s3_key(self, letter_id: str, filename: str) -> str:
        """
        Generate S3 object key for a letter image.

        Args:
            letter_id: Unique letter identifier
            filename: Original filename

        Returns:
            str: S3 key in format: letters/{letter_id}/{timestamp}_{filename}

        Example:
            key = s3_client.generate_s3_key("abc123", "scan.jpg")
            # Returns: "letters/abc123/20240115_123045_scan.jpg"
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(filename)
        s3_key = f"{settings.s3_image_prefix}{letter_id}/{timestamp}_{safe_filename}"
        return s3_key

    def upload_file(
        self,
        file_content: BinaryIO,
        s3_key: str,
        content_type: str = "image/jpeg",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_content: File content as binary stream
            s3_key: S3 object key (path)
            content_type: MIME type of the file
            metadata: Optional metadata to attach to S3 object

        Returns:
            str: S3 key of uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            logger.info(f"Uploading file to S3: {s3_key}")

            extra_args = {
                'ContentType': content_type,
            }

            if metadata:
                extra_args['Metadata'] = metadata

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                **extra_args
            )

            logger.info(f"File uploaded successfully: {s3_key}")
            return s3_key

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"AWS ClientError uploading to S3: {error_code} - {error_msg}")
            raise Exception(f"Failed to upload file to S3: {error_msg}")

        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}", exc_info=True)
            raise

    def upload_letter_image(
        self,
        file_content: BinaryIO,
        letter_id: str,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> dict:
        """
        Upload a letter image to S3 with proper organization.

        Args:
            file_content: Image file content
            letter_id: Letter ID for organizing images
            filename: Original filename
            content_type: Image MIME type

        Returns:
            Dict with upload details:
            {
                "s3_key": "letters/123/image.jpg",
                "url": "https://...",
                "bucket": "bucket-name"
            }
        """
        # Generate S3 key
        s3_key = self.generate_s3_key(letter_id, filename)

        # Upload to S3
        self.upload_file(
            file_content=file_content,
            s3_key=s3_key,
            content_type=content_type,
            metadata={
                'letter_id': letter_id,
                'original_filename': filename
            }
        )

        # Generate presigned URL
        url = self.generate_presigned_url(s3_key, expiration=3600)

        return {
            "s3_key": s3_key,
            "url": url,
            "bucket": self.bucket_name
        }

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for secure access to an S3 object.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            str: Presigned URL for accessing the object

        Example:
            url = s3_client.generate_presigned_url("letters/123/image.jpg")
            # Returns: "https://bucket.s3.amazonaws.com/...?X-Amz-Signature=..."
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            # Return public URL as fallback (requires bucket to be public)
            return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key to delete

        Returns:
            bool: True if deletion successful
        """
        try:
            logger.info(f"Deleting file from S3: {s3_key}")

            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            logger.info(f"File deleted successfully: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting from S3: {str(e)}")
            return False

    def delete_letter_images(self, letter_id: str) -> int:
        """
        Delete all images associated with a letter.

        Args:
            letter_id: Letter ID

        Returns:
            int: Number of images deleted
        """
        try:
            prefix = f"{settings.s3_image_prefix}{letter_id}/"
            logger.info(f"Deleting all images for letter: {letter_id}")

            # List objects with prefix
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                logger.info("No images found to delete")
                return 0

            # Delete all objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]

            self.client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects_to_delete}
            )

            deleted_count = len(objects_to_delete)
            logger.info(f"Deleted {deleted_count} images for letter {letter_id}")
            return deleted_count

        except ClientError as e:
            logger.error(f"Error deleting letter images: {str(e)}")
            return 0

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            s3_key: S3 object key

        Returns:
            bool: True if file exists
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False


# Global S3 client instance
s3_client = S3Client()
