"""
Analysis API routes.

POST /api/inspections/{inspection_id}/analyze  — Run OCR on all images
GET  /api/inspections/{inspection_id}/analysis — Get persisted OCR results
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/inspections", tags=["Analysis"])


@router.post("/{inspection_id}/analyze", response_model=AnalysisResponse)
def analyze_inspection(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger OCR analysis on all images of an inspection.

    Runs image quality assessment, OpenCV preprocessing, and PaddleOCR.
    Results are persisted in PostgreSQL and returned in the response.
    Re-running replaces previous results.
    """
    service = AnalysisService(db)
    result = service.analyze_inspection(inspection_id, current_user.id)
    return result


@router.get("/{inspection_id}/analysis", response_model=AnalysisResponse)
def get_analysis_results(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return persisted OCR analysis results for an inspection without re-running.

    Use this to reload results on page refresh.
    """
    service = AnalysisService(db)
    result = service.get_analysis_results(inspection_id, current_user.id)
    return result
