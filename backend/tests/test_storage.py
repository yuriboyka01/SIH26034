"""
Tests for storage abstraction: LocalStorageService, S3StorageService,
factory, and serve_image endpoint.
"""

import io
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.inspection_image import InspectionImage, ImageType
from app.storage.base import StorageService
from app.storage.factory import get_storage_service, reset_storage_service
from app.storage.local import LocalStorageService
from app.storage.s3 import S3StorageService


# ============================================================================
# LocalStorageService Tests
# ============================================================================

def test_local_storage_lifecycle(tmp_path):
    storage = LocalStorageService(str(tmp_path))
    data = b"hello local storage"
    filename = f"{uuid.uuid4().hex}.txt"

    # Upload
    stored = storage.upload(data, filename)
    assert stored == filename

    # Full path
    full_path = storage.get_full_path(filename)
    assert os.path.exists(full_path)

    # Download to temp file
    downloaded = storage.download_to_temp_file(filename)
    assert downloaded == full_path

    # Get
    content = storage.get(filename)
    assert content == data

    # Delete
    assert storage.delete(filename) is True
    assert storage.delete(filename) is False
    assert storage.get(filename) is None
    assert storage.download_to_temp_file(filename) is None


# ============================================================================
# S3StorageService Tests (Mocked boto3)
# ============================================================================

def test_s3_storage_initialization():
    with patch("boto3.client") as mock_boto:
        svc = S3StorageService(
            bucket="test-bucket",
            region="ap-south-1",
            endpoint_url="https://s3.example.com",
            access_key_id="test-key",
            secret_access_key="test-secret",
        )
        assert svc.bucket == "test-bucket"
        mock_boto.assert_called_once_with(
            "s3",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="ap-south-1",
            endpoint_url="https://s3.example.com",
        )


def test_s3_storage_lifecycle():
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client

        # Mock get_object return
        test_bytes = b"fake-s3-content"
        mock_body = MagicMock()
        mock_body.read.return_value = test_bytes
        mock_client.get_object.return_value = {"Body": mock_body}

        svc = S3StorageService(bucket="my-bucket")

        # Upload
        res = svc.upload(test_bytes, "test.jpg")
        assert res == "test.jpg"
        mock_client.put_object.assert_called_once_with(
            Bucket="my-bucket", Key="test.jpg", Body=test_bytes
        )

        # Get
        retrieved = svc.get("test.jpg")
        assert retrieved == test_bytes

        # Get full path returns key
        assert svc.get_full_path("test.jpg") == "test.jpg"

        # Download to temp file auto-detects extension
        tmp_file = svc.download_to_temp_file("test.jpg")
        assert tmp_file is not None
        try:
            assert tmp_file.endswith(".jpg")
            with open(tmp_file, "rb") as f:
                assert f.read() == test_bytes
        finally:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

        # Delete
        assert svc.delete("test.jpg") is True
        mock_client.delete_object.assert_called_once_with(
            Bucket="my-bucket", Key="test.jpg"
        )


# ============================================================================
# Factory Tests
# ============================================================================

def test_storage_factory():
    reset_storage_service()

    # Default is local
    settings.STORAGE_BACKEND = "local"
    local_svc = get_storage_service()
    assert isinstance(local_svc, LocalStorageService)

    # Switching to S3
    with patch("boto3.client") as mock_boto:
        settings.STORAGE_BACKEND = "s3"
        settings.S3_BUCKET = "mock-bucket"
        reset_storage_service()

        s3_svc = get_storage_service()
        assert isinstance(s3_svc, S3StorageService)
        # Singleton cached
        assert get_storage_service() is s3_svc

        # Reset
        reset_storage_service()
        settings.STORAGE_BACKEND = "local"
        settings.S3_BUCKET = None


# ============================================================================
# Serve Image Endpoint Tests
# ============================================================================

def test_serve_image_local(client: TestClient, upload_dir):
    # Write a test file in upload_dir
    filename = "serve_test.jpg"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(b"image-data")

    response = client.get(f"/api/images/{filename}")
    assert response.status_code == 200
    assert response.content == b"image-data"


def test_serve_image_not_found(client: TestClient):
    response = client.get("/api/images/nonexistent_file_123.jpg")
    assert response.status_code == 404


def test_serve_image_s3(client: TestClient, setup_database):
    reset_storage_service()
    settings.STORAGE_BACKEND = "s3"
    settings.S3_BUCKET = "test-bucket"

    mock_storage = MagicMock(spec=StorageService)
    mock_storage.get.return_value = b"s3-raw-bytes"

    try:
        with patch("app.api.images.get_storage_service", return_value=mock_storage):
            response = client.get("/api/images/remote_image.jpg")
            assert response.status_code == 200
            assert response.content == b"s3-raw-bytes"
            assert response.headers["content-type"] == "application/octet-stream"
    finally:
        reset_storage_service()
        settings.STORAGE_BACKEND = "local"
        settings.S3_BUCKET = None
