"""
Inspection API routes.

POST /api/inspections              — Create a new inspection
GET  /api/inspections              — List user's inspections
GET  /api/inspections/{id}         — Get inspection details with images
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.inspection import InspectionCreate, InspectionResponse, InspectionListResponse
from app.schemas.image import ImageResponse
from app.services.inspection_service import InspectionService
from app.services.image_service import ImageService

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])


@router.post("", response_model=InspectionResponse, status_code=201)
def create_inspection(
    data: InspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new inspection."""
    service = InspectionService(db)
    inspection = service.create_inspection(
        product_name=data.product_name,
        brand=data.brand,
        user_id=current_user.id,
        establishment_name=data.establishment_name,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    image_service = ImageService(db)
    return _build_inspection_response(inspection, image_service)


@router.get("", response_model=List[InspectionListResponse])
def list_inspections(
    response: Response,
    search: Optional[str] = None,
    status: Optional[str] = None,
    compliance_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List inspections for the current user, with optional search and filters."""
    service = InspectionService(db)
    
    inspections, total_count = service.search_inspections(
        user_id=current_user.id,
        search_term=search,
        status=status,
        compliance_status=compliance_status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )

    # Set pagination headers so we don't break existing JSON array response schema
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Page"] = str((skip // limit) + 1 if limit > 0 else 1)
    response.headers["X-Page-Size"] = str(limit)

    result = []
    for insp in inspections:
        result.append(
            InspectionListResponse(
                id=insp.id,
                inspection_number=insp.inspection_number,
                product_name=insp.product_name,
                brand=insp.brand,
                status=insp.status.value,
                created_at=insp.created_at,
                image_count=len(insp.images) if insp.images else 0,
            )
        )
    return result


@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inspection details including uploaded images."""
    service = InspectionService(db)
    inspection = service.get_inspection(inspection_id, current_user.id)
    image_service = ImageService(db)
    return _build_inspection_response(inspection, image_service)


def _build_inspection_response(inspection, image_service: ImageService) -> InspectionResponse:
    """Build an InspectionResponse with image URLs populated."""
    images = []
    for img in (inspection.images or []):
        image_resp = ImageResponse(
            id=img.id,
            original_filename=img.original_filename,
            stored_filename=img.stored_filename,
            mime_type=img.mime_type,
            file_size=img.file_size,
            image_type=img.image_type.value if hasattr(img.image_type, 'value') else img.image_type,
            url=image_service.get_image_url(img),
            created_at=img.created_at,
        )
        images.append(image_resp)

    return InspectionResponse(
        id=inspection.id,
        inspection_number=inspection.inspection_number,
        product_name=inspection.product_name,
        brand=inspection.brand,
        status=inspection.status.value if hasattr(inspection.status, 'value') else inspection.status,
        created_by=inspection.created_by,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
        establishment_name=inspection.establishment_name,
        latitude=inspection.latitude,
        longitude=inspection.longitude,
        images=images,
    )
