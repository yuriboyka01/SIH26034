"""
Dashboard API routes.

GET /api/dashboard/stats — Get inspection count statistics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.inspection import DashboardStats
from app.services.inspection_service import InspectionService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inspection statistics for the dashboard."""
    service = InspectionService(db)
    stats = service.get_dashboard_stats(current_user.id)
    return DashboardStats(**stats)
