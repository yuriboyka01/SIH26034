"""
Storage backend factory.

Reads STORAGE_BACKEND from settings ("local" | "s3") and returns the
matching StorageService implementation. Everything else in the app
should call get_storage_service() instead of importing LocalStorageService
or S3StorageService directly, so switching backends is a one-line env
var change (STORAGE_BACKEND=s3) with no code change.
"""

from app.core.config import settings
from app.storage.base import StorageService
from app.storage.local import LocalStorageService

_storage_instance: StorageService | None = None


def get_storage_service() -> StorageService:
    """
    Return the active storage backend.

    The S3 client is cached process-wide (real setup cost, and safe to
    reuse). The local backend is intentionally NOT cached — it's cheap to
    construct and must always reflect the current settings.UPLOAD_DIR,
    since tests (see conftest.py's `upload_dir` fixture) patch that value
    per-test. Caching it here would pin every caller to whichever tmp dir
    happened to be active on first use.
    """
    global _storage_instance
    backend = (settings.STORAGE_BACKEND or "local").lower()

    if backend == "s3":
        if _storage_instance is None:
            from app.storage.s3 import S3StorageService
            _storage_instance = S3StorageService(
                bucket=settings.S3_BUCKET,
                region=settings.S3_REGION,
                endpoint_url=settings.S3_ENDPOINT_URL,
                access_key_id=settings.S3_ACCESS_KEY_ID,
                secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            )
        return _storage_instance

    return LocalStorageService(settings.UPLOAD_DIR)


def reset_storage_service() -> None:
    """Clear the cached S3 client. Useful in tests that switch backends."""
    global _storage_instance
    _storage_instance = None
