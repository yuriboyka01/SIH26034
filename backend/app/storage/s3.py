"""
S3-compatible storage implementation.

Works with AWS S3 directly, and with any S3-compatible provider
(Cloudflare R2, Backblaze B2, MinIO) by setting S3_ENDPOINT_URL.

This exists because Render's filesystem is ephemeral — files written to
local disk (LocalStorageService) do NOT survive a redeploy or restart.
Use this backend in production by setting STORAGE_BACKEND=s3.
"""

import os
from typing import Optional

from app.storage.base import StorageService
from app.core.logging import logger

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception


class S3StorageService(StorageService):
    """Store files in an S3-compatible object store."""

    def __init__(
        self,
        bucket: str,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        if boto3 is None:
            raise RuntimeError(
                "boto3 is not installed. Run: pip install boto3"
            )
        if not bucket:
            raise RuntimeError("S3_BUCKET must be set when STORAGE_BACKEND=s3")

        self.bucket = bucket
        session_kwargs = {}
        if access_key_id and secret_access_key:
            session_kwargs["aws_access_key_id"] = access_key_id
            session_kwargs["aws_secret_access_key"] = secret_access_key
        if region:
            session_kwargs["region_name"] = region

        client_kwargs = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self.client = boto3.client("s3", **session_kwargs, **client_kwargs)

    def upload(self, file_content: bytes, filename: str) -> str:
        """Upload file bytes to the bucket under `filename` as the key."""
        self.client.put_object(Bucket=self.bucket, Key=filename, Body=file_content)
        logger.info(f"STORAGE(s3) | FILE_SAVED | key={filename}")
        return filename

    def delete(self, file_path: str) -> bool:
        """Delete an object from the bucket."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_path)
            logger.info(f"STORAGE(s3) | FILE_DELETED | key={file_path}")
            return True
        except ClientError as e:
            logger.error(f"STORAGE(s3) | DELETE_FAILED | key={file_path} | error={e}")
            return False

    def get(self, file_path: str) -> Optional[bytes]:
        """Read an object's bytes from the bucket."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=file_path)
            return response["Body"].read()
        except ClientError:
            return None

    def get_full_path(self, file_path: str) -> str:
        """
        No local filesystem path exists for S3 objects.
        Returns the S3 key itself — callers that need actual bytes must use
        get() instead, or download_to_temp_file() for tools that require a
        real file path (e.g. OpenCV/PaddleOCR).
        """
        return file_path

    def download_to_temp_file(self, file_path: str, suffix: str = "") -> Optional[str]:
        """
        Download an object to a local temp file and return its path.
        Caller is responsible for deleting the temp file when done.
        Used by the OCR pipeline, which needs a real filesystem path.
        """
        import tempfile

        content = self.get(file_path)
        if content is None:
            return None

        if not suffix and "." in file_path:
            _, ext = os.path.splitext(file_path)
            if ext:
                suffix = ext

        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        return tmp_path
