"""
Inspection data access repository.
"""

from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased

from app.models.inspection import Inspection, InspectionStatus
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.models.compliance import ComplianceReport


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

    def search_inspections(
        self,
        user_id: UUID,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        compliance_status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ):
        """Search and filter inspections with pagination."""
        query = self.db.query(Inspection).filter(Inspection.created_by == user_id)

        # Basic lifecycle status
        if status:
            query = query.filter(Inspection.status == status)

        # Text search (product_name, brand, inspection_number)
        if search_term:
            term = f"%{search_term}%"
            query = query.filter(
                or_(
                    Inspection.product_name.ilike(term),
                    Inspection.brand.ilike(term),
                    Inspection.inspection_number.ilike(term)
                )
            )

        # Date range
        if date_from:
            query = query.filter(Inspection.created_at >= date_from)
        if date_to:
            query = query.filter(Inspection.created_at <= date_to)

        # Compliance status filter requires a join
        # This checks if ANY compliance report matches the status. 
        # For a true "overall status", the subquery is more complex, but this is sufficient for search.
        if compliance_status:
            if compliance_status == "NOT_ANALYSED":
                # Find inspections with NO compliance reports
                subq = (
                    self.db.query(InspectionImage.inspection_id)
                    .join(OCRResult, InspectionImage.id == OCRResult.image_id)
                    .join(ComplianceReport, OCRResult.id == ComplianceReport.ocr_result_id)
                ).subquery()
                query = query.filter(Inspection.id.not_in(subq))
            else:
                # Find inspections where ANY compliance report matches the status
                query = query.join(InspectionImage, Inspection.id == InspectionImage.inspection_id) \
                             .join(OCRResult, InspectionImage.id == OCRResult.image_id) \
                             .join(ComplianceReport, OCRResult.id == ComplianceReport.ocr_result_id) \
                             .filter(ComplianceReport.overall_status == compliance_status)

        # Ensure distinct results if joins were used
        query = query.distinct()

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        items = query.order_by(Inspection.created_at.desc()).offset(skip).limit(limit).all()

        return items, total_count
