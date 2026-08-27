"""
Image API routes.

POST   /api/inspections/{id}/images              — Upload an image
DELETE /api/inspections/{id}/images/{image_id}    — Delete an image
GET    /api/images/{stored_filename}              — Serve an image file
"""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.inspection_image import ImageType
from app.schemas.image import ImageResponse
from app.services.image_service import ImageService
from app.services.inspection_service import InspectionService
from app.storage.local import LocalStorageService

router = APIRouter(tags=["Images"])


@router.post(
    "/api/inspections/{inspection_id}/images",
    response_model=ImageResponse,
    status_code=201,
)
async def upload_image(
    inspection_id: UUID,
    file: UploadFile = File(...),
    image_type: str = Form(default="OTHER"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an image to an inspection."""
    # Verify the inspection belongs to the current user
    inspection_service = InspectionService(db)
    inspection_service.get_inspection(inspection_id, current_user.id)

    # Parse image type
    try:
        img_type = ImageType(image_type.upper())
    except ValueError:
        img_type = ImageType.OTHER

    image_service = ImageService(db)
    image = await image_service.upload_image(
        file=file,
        inspection_id=inspection_id,
        image_type=img_type,
    )

    return ImageResponse(
        id=image.id,
        original_filename=image.original_filename,
        stored_filename=image.stored_filename,
        mime_type=image.mime_type,
        file_size=image.file_size,
        image_type=image.image_type.value,
        url=image_service.get_image_url(image),
        created_at=image.created_at,
    )


@router.delete(
    "/api/inspections/{inspection_id}/images/{image_id}",
    status_code=204,
)
def delete_image(
    inspection_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an image from an inspection."""
    # Verify the inspection belongs to the current user
    inspection_service = InspectionService(db)
    inspection_service.get_inspection(inspection_id, current_user.id)

    image_service = ImageService(db)
    image_service.delete_image(image_id, inspection_id)


@router.get("/api/images/{stored_filename}")
def serve_image(stored_filename: str):
    """Serve a stored image file."""
    storage = LocalStorageService(settings.UPLOAD_DIR)
    full_path = storage.get_full_path(stored_filename)

    import os
    if not os.path.exists(full_path):
        raise NotFoundError(
            code="IMAGE_NOT_FOUND",
            message="Image file not found.",
        )

    return FileResponse(full_path)
