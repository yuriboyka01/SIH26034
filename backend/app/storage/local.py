"""
Local filesystem storage implementation.

Stores files in a local directory for Phase 1 development.
"""

import os
from typing import Optional

from app.storage.base import StorageService
from app.core.logging import logger


class LocalStorageService(StorageService):
    """Store files on the local filesystem."""

    def __init__(self, upload_dir: str):
        self.upload_dir = os.path.abspath(upload_dir)
        os.makedirs(self.upload_dir, exist_ok=True)

    def upload(self, file_content: bytes, filename: str) -> str:
        """Save file to local filesystem."""
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"STORAGE | FILE_SAVED | filename={filename}")
        return filename

    def delete(self, file_path: str) -> bool:
        """Delete a file from local filesystem."""
        full_path = self.get_full_path(file_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"STORAGE | FILE_DELETED | path={file_path}")
                return True
            return False
        except OSError as e:
            logger.error(f"STORAGE | DELETE_FAILED | path={file_path} | error={e}")
            return False

    def get(self, file_path: str) -> Optional[bytes]:
        """Read a file from local filesystem."""
        full_path = self.get_full_path(file_path)
        try:
            with open(full_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def get_full_path(self, file_path: str) -> str:
        """Get the absolute filesystem path."""
        return os.path.join(self.upload_dir, file_path)
