"""
Abstract storage interface.

Defines the contract for file storage services.
Phase 1 uses LocalStorageService; future phases can implement
S3StorageService, MinIOStorageService, GCSStorageService, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional


class StorageService(ABC):
    """Abstract base class for file storage operations."""

    @abstractmethod
    def upload(self, file_content: bytes, filename: str) -> str:
        """
        Upload a file to storage.

        Args:
            file_content: The raw file bytes.
            filename: The generated unique filename (NOT the original user filename).

        Returns:
            The stored file path/key that can be used to retrieve or delete the file.
        """
        ...

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: The stored file path/key.

        Returns:
            True if deletion succeeded, False if file was not found.
        """
        ...

    @abstractmethod
    def get(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve a file's content from storage.

        Args:
            file_path: The stored file path/key.

        Returns:
            The file bytes, or None if not found.
        """
        ...

    @abstractmethod
    def get_full_path(self, file_path: str) -> str:
        """
        Get the absolute filesystem path for a stored file.

        Args:
            file_path: The stored file path/key.

        Returns:
            The absolute path to the file.
        """
        ...
