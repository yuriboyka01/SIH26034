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
from app.schemas.dashboard import DashboardAnalyticsResponse
from app.services.inspection_service import InspectionService
from app.services.dashboard_service import DashboardService

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


@router.get("/analytics", response_model=DashboardAnalyticsResponse)
def get_compliance_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Phase 5 compliance analytics (KPIs, violations, recent)."""
    service = DashboardService(db)
    return service.get_dashboard_analytics()
