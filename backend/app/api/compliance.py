"""
Phase 4: Compliance API Routes.

GET /api/inspections/{inspection_id}/compliance
POST /api/inspections/{inspection_id}/compliance
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.compliance import ComplianceResponse
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/api/inspections", tags=["Compliance"])


@router.post("/{inspection_id}/compliance", response_model=ComplianceResponse)
def run_compliance(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluate compliance rules for all images in the inspection using the extracted ProductInfo.
    """
    svc = ComplianceService(db)
    return svc.run_compliance_for_inspection(inspection_id, current_user.id)


@router.get("/{inspection_id}/compliance", response_model=ComplianceResponse)
def get_compliance(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve persisted compliance reports for the inspection.
    """
    svc = ComplianceService(db)
    return svc.get_compliance_reports(inspection_id, current_user.id)
