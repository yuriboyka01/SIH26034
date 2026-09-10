"""
Image service — business logic for image upload, validation, and deletion.
"""

import uuid
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.inspection_image import InspectionImage, ImageType
from app.models.inspection import InspectionStatus
from app.repositories.image_repository import ImageRepository
from app.repositories.inspection_repository import InspectionRepository
from app.storage.factory import get_storage_service
from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.logging import log_image_event


# Allowed MIME types and their corresponding extensions
ALLOWED_MIME_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class ImageService:
    """Handles image upload and management business logic."""

    def __init__(self, db: Session):
        self.image_repo = ImageRepository(db)
        self.inspection_repo = InspectionRepository(db)
        self.storage = get_storage_service()

    def _validate_file(self, file: UploadFile) -> tuple[str, str]:
        """
        Validate uploaded file MIME type and extension.

        Returns:
            Tuple of (mime_type, extension)

        Raises:
            BadRequestError: If file type is invalid or file is too large.
        """
        # Validate MIME type
        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            raise BadRequestError(
                code="IMAGE_TYPE_NOT_SUPPORTED",
                message="Only JPG, JPEG, PNG and WEBP images are supported.",
            )

        # Validate extension
        filename = file.filename or ""
        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise BadRequestError(
                code="IMAGE_TYPE_NOT_SUPPORTED",
                message="Only JPG, JPEG, PNG and WEBP images are supported.",
            )

        # Cross-check MIME type and extension
        allowed_exts = ALLOWED_MIME_TYPES.get(content_type, [])
        if ext not in allowed_exts:
            raise BadRequestError(
                code="IMAGE_TYPE_MISMATCH",
                message="File extension does not match the detected file type.",
            )

        return content_type, ext

    async def upload_image(
        self,
        file: UploadFile,
        inspection_id: UUID,
        image_type: ImageType = ImageType.OTHER,
    ) -> InspectionImage:
        """
        Upload and store an image for an inspection.

        Raises:
            BadRequestError: If file is invalid.
            NotFoundError: If inspection not found.
        """
        # Validate file type
        mime_type, ext = self._validate_file(file)

        # Read file content
        content = await file.read()

        # Validate file size
        file_size = len(content)
        if file_size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise BadRequestError(
                code="IMAGE_TOO_LARGE",
                message=f"Image file size exceeds the maximum of {max_mb:.0f}MB.",
            )

        if file_size == 0:
            raise BadRequestError(
                code="EMPTY_FILE",
                message="Uploaded file is empty.",
            )

        # Generate unique storage filename
        stored_filename = f"{uuid.uuid4().hex}{ext}"

        # Store file
        file_path = self.storage.upload(content, stored_filename)

        # Create database record
        image = InspectionImage(
            inspection_id=inspection_id,
            original_filename=file.filename or "unknown",
            stored_filename=stored_filename,
            file_path=file_path,
            mime_type=mime_type,
            file_size=file_size,
            image_type=image_type,
        )
        image = self.image_repo.create(image)

        # Update inspection status to IMAGES_UPLOADED if currently CREATED
        inspection = self.inspection_repo.get_by_id(inspection_id)
        if inspection and inspection.status == InspectionStatus.CREATED:
            self.inspection_repo.update_status(inspection_id, InspectionStatus.IMAGES_UPLOADED)

        log_image_event("UPLOADED", str(image.id), str(inspection_id))
        return image

    def delete_image(self, image_id: UUID, inspection_id: UUID) -> None:
        """
        Delete an image from storage and database.

        Raises:
            NotFoundError: If image not found.
        """
        image = self.image_repo.get_by_id(image_id)
        if not image or image.inspection_id != inspection_id:
            raise NotFoundError(
                code="IMAGE_NOT_FOUND",
                message="Image not found.",
            )

        # Delete from storage
        self.storage.delete(image.file_path)

        # Delete from database
        self.image_repo.delete(image)

        # If no more images, revert inspection status to CREATED
        remaining = self.image_repo.count_by_inspection(inspection_id)
        if remaining == 0:
            self.inspection_repo.update_status(inspection_id, InspectionStatus.CREATED)

        log_image_event("DELETED", str(image_id), str(inspection_id))

    def get_image_url(self, image: InspectionImage) -> str:
        """Generate the API URL for accessing an image."""
        return f"/api/images/{image.stored_filename}"
