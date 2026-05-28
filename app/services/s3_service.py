import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Handles all AWS S3 file operations for TaskFlow API."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-load the S3 client so it's only created when needed."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=current_app.config["AWS_S3_REGION"],
                aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
            )
        return self._client

    def upload_file(self, file_obj, original_filename, content_type, folder="attachments"):
        """
        Upload a file to S3 and return the S3 key and public URL.

        Args:
            file_obj: File-like object (from Flask request.files)
            original_filename: Original filename from the upload
            content_type: MIME type of the file
            folder: S3 folder/prefix (e.g. 'attachments', 'avatars')

        Returns:
            dict with 's3_key', 's3_url', 'filename'
        """
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
        unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        s3_key = f"{folder}/{unique_filename}"
        bucket = current_app.config["AWS_S3_BUCKET"]
        region = current_app.config["AWS_S3_REGION"]

        try:
            client = self._get_client()
            client.upload_fileobj(
                file_obj,
                bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ContentDisposition": f'inline; filename="{original_filename}"',
                },
            )
            s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded file to S3: {s3_key}")
            return {
                "s3_key": s3_key,
                "s3_url": s3_url,
                "filename": unique_filename,
            }
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise ValueError("AWS credentials not configured. Check environment variables.")
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise ValueError(f"File upload failed: {e.response['Error']['Message']}")

    def delete_file(self, s3_key):
        """
        Delete a file from S3 by its key.

        Args:
            s3_key: The S3 object key to delete

        Returns:
            True on success
        """
        bucket = current_app.config["AWS_S3_BUCKET"]
        try:
            client = self._get_client()
            client.delete_object(Bucket=bucket, Key=s3_key)
            logger.info(f"Deleted file from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            raise ValueError(f"File deletion failed: {e.response['Error']['Message']}")

    def generate_presigned_url(self, s3_key, expiration=3600):
        """
        Generate a presigned URL for private S3 files.

        Args:
            s3_key: The S3 object key
            expiration: URL expiry time in seconds (default 1 hour)

        Returns:
            Presigned URL string
        """
        bucket = current_app.config["AWS_S3_BUCKET"]
        try:
            client = self._get_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise ValueError("Could not generate download URL")

    def file_exists(self, s3_key):
        """Check if a file exists in S3."""
        bucket = current_app.config["AWS_S3_BUCKET"]
        try:
            client = self._get_client()
            client.head_object(Bucket=bucket, Key=s3_key)
            return True
        except ClientError:
            return False


s3_service = S3Service()
