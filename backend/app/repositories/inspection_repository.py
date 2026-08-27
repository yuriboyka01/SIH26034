"""
Inspection data access repository.
"""

from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.inspection import Inspection, InspectionStatus


class InspectionRepository:
    """Repository for inspection database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, inspection: Inspection) -> Inspection:
        """Create a new inspection."""
        self.db.add(inspection)
        self.db.commit()
        self.db.refresh(inspection)
        return inspection

    def get_by_id(self, inspection_id: UUID) -> Optional[Inspection]:
        """Find an inspection by ID."""
        return self.db.query(Inspection).filter(Inspection.id == inspection_id).first()

    def list_by_user(self, user_id: UUID, skip: int = 0, limit: int = 50) -> List[Inspection]:
        """List inspections created by a specific user."""
        return (
            self.db.query(Inspection)
            .filter(Inspection.created_by == user_id)
            .order_by(Inspection.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(self, inspection_id: UUID, status: InspectionStatus) -> Optional[Inspection]:
        """Update an inspection's status."""
        inspection = self.get_by_id(inspection_id)
        if inspection:
            inspection.status = status
            self.db.commit()
            self.db.refresh(inspection)
        return inspection

    def get_counts_by_user(self, user_id: UUID) -> Dict[str, int]:
        """Get inspection counts grouped by status for a user."""
        results = (
            self.db.query(Inspection.status, func.count(Inspection.id))
            .filter(Inspection.created_by == user_id)
            .group_by(Inspection.status)
            .all()
        )

        counts = {status.value: 0 for status in InspectionStatus}
        for status, count in results:
            counts[status.value] = count

        return counts
