"""Tests for image upload and management endpoints."""

import io


def _create_inspection(client, auth_headers):
    """Helper to create an inspection."""
    response = client.post(
        "/api/inspections",
        json={"product_name": "Image Test Product", "brand": "Image Brand"},
        headers=auth_headers,
    )
    return response.json()["id"]


def _make_test_image(filename="test.jpg", content_type="image/jpeg", size=1024):
    """Create a minimal test file for upload."""
    content = b"\xff\xd8\xff\xe0" + b"\x00" * (size - 4)  # JPEG magic bytes
    return filename, io.BytesIO(content), content_type


def test_upload_valid_image(client, auth_headers, upload_dir):
    """Test uploading a valid image."""
    inspection_id = _create_inspection(client, auth_headers)

    filename, file_obj, content_type = _make_test_image()
    response = client.post(
        f"/api/inspections/{inspection_id}/images",
        files={"file": (filename, file_obj, content_type)},
        data={"image_type": "FRONT"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test.jpg"
    assert data["mime_type"] == "image/jpeg"
    assert data["image_type"] == "FRONT"
    assert "url" in data


def test_upload_updates_inspection_status(client, auth_headers, upload_dir):
    """Test that uploading an image updates inspection status to IMAGES_UPLOADED."""
    inspection_id = _create_inspection(client, auth_headers)

    filename, file_obj, content_type = _make_test_image()
    client.post(
        f"/api/inspections/{inspection_id}/images",
        files={"file": (filename, file_obj, content_type)},
        headers=auth_headers,
    )

    # Check inspection status
    response = client.get(f"/api/inspections/{inspection_id}", headers=auth_headers)
    assert response.json()["status"] == "IMAGES_UPLOADED"


def test_reject_invalid_mime_type(client, auth_headers, upload_dir):
    """Test that non-image files are rejected."""
    inspection_id = _create_inspection(client, auth_headers)

    response = client.post(
        f"/api/inspections/{inspection_id}/images",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IMAGE_TYPE_NOT_SUPPORTED"


def test_reject_oversized_file(client, auth_headers, upload_dir):
    """Test that files exceeding size limit are rejected."""
    from app.core.config import settings
    original_max = settings.MAX_UPLOAD_SIZE
    settings.MAX_UPLOAD_SIZE = 100  # Set very small limit

    inspection_id = _create_inspection(client, auth_headers)

    filename, file_obj, content_type = _make_test_image(size=200)
    response = client.post(
        f"/api/inspections/{inspection_id}/images",
        files={"file": (filename, file_obj, content_type)},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IMAGE_TOO_LARGE"

    settings.MAX_UPLOAD_SIZE = original_max


def test_delete_image(client, auth_headers, admin_auth_headers, upload_dir):
    """Test deleting an uploaded image."""
    inspection_id = _create_inspection(client, auth_headers)

    # Upload
    filename, file_obj, content_type = _make_test_image()
    upload_resp = client.post(
        f"/api/inspections/{inspection_id}/images",
        files={"file": (filename, file_obj, content_type)},
        headers=auth_headers,
    )
    image_id = upload_resp.json()["id"]

    # Delete
    response = client.delete(
        f"/api/inspections/{inspection_id}/images/{image_id}",
        headers=admin_auth_headers,
    )
    assert response.status_code == 204

    # Verify image is gone
    inspection_resp = client.get(
        f"/api/inspections/{inspection_id}", headers=auth_headers
    )
    assert len(inspection_resp.json()["images"]) == 0


def test_delete_image_not_found(client, auth_headers, admin_auth_headers, upload_dir):
    """Test deleting a non-existent image."""
    inspection_id = _create_inspection(client, auth_headers)

    response = client.delete(
        f"/api/inspections/{inspection_id}/images/00000000-0000-0000-0000-000000000000",
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_upload_unauthorized(client, upload_dir):
    """Test uploading without authentication."""
    response = client.post(
        "/api/inspections/00000000-0000-0000-0000-000000000000/images",
        files={"file": ("test.jpg", io.BytesIO(b"\xff\xd8"), "image/jpeg")},
    )
    assert response.status_code in (401, 403)
