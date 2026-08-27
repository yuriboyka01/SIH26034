"""
Phase 3: Product Information API route.

GET /api/inspections/{inspection_id}/product-info
  — Return structured product data extracted from OCR for all images of an inspection.

This endpoint is read-only; extraction is triggered by POST /analyze.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.product_info import ProductInfoResponse
from app.repositories.inspection_repository import InspectionRepository
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/api/inspections", tags=["Product Information"])


@router.get("/{inspection_id}/product-info", response_model=ProductInfoResponse)
def get_product_info(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return structured product information for an inspection.

    Extraction is run automatically as part of POST /analyze.
    Use this endpoint to retrieve the persisted results without re-running analysis.

    Returns a list of ProductInfoSchema — one per analysed image.
    Fields with None values were NOT detected in the OCR text.
    """
    # Verify inspection ownership
    insp_repo = InspectionRepository(db)
    inspection = insp_repo.get_by_id(inspection_id)
    if not inspection or inspection.created_by != current_user.id:
        raise NotFoundError(code="INSPECTION_NOT_FOUND", message="Inspection not found.")

    extraction_svc = ExtractionService(db)
    product_info_list = extraction_svc.get_for_inspection(inspection_id)

    return {
        "inspection_id": str(inspection_id),
        "status": inspection.status.value,
        "product_info_list": product_info_list,
    }
