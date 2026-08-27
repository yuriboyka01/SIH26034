"""
Inspection service — business logic for inspection lifecycle management.
"""

import random
import string
from datetime import datetime, timezone
from typing import List, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.inspection import Inspection, InspectionStatus
from app.repositories.inspection_repository import InspectionRepository
from app.core.exceptions import NotFoundError
from app.core.logging import log_inspection_event


class InspectionService:
    """Handles inspection business logic."""

    def __init__(self, db: Session):
        self.repo = InspectionRepository(db)

    def _generate_inspection_number(self) -> str:
        """Generate a unique inspection number: INS-YYYYMMDD-XXXX."""
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"INS-{date_part}-{random_part}"

    def create_inspection(
        self, product_name: str, brand: str, user_id: UUID
    ) -> Inspection:
        """Create a new inspection with auto-generated inspection number."""
        inspection = Inspection(
            inspection_number=self._generate_inspection_number(),
            product_name=product_name,
            brand=brand,
            created_by=user_id,
            status=InspectionStatus.CREATED,
        )
        inspection = self.repo.create(inspection)
        log_inspection_event("CREATED", str(inspection.id), str(user_id))
        return inspection

    def get_inspection(self, inspection_id: UUID, user_id: UUID) -> Inspection:
        """
        Get an inspection by ID, ensuring it belongs to the requesting user.

        Raises:
            NotFoundError: If inspection not found or doesn't belong to user.
        """
        inspection = self.repo.get_by_id(inspection_id)
        if not inspection or inspection.created_by != user_id:
            raise NotFoundError(
                code="INSPECTION_NOT_FOUND",
                message="Inspection not found.",
            )
        return inspection

    def list_inspections(
        self, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Inspection]:
        """List inspections for a user."""
        return self.repo.list_by_user(user_id, skip=skip, limit=limit)

    def update_status(
        self, inspection_id: UUID, status: InspectionStatus
    ) -> Inspection:
        """Update an inspection's status."""
        inspection = self.repo.update_status(inspection_id, status)
        if not inspection:
            raise NotFoundError(
                code="INSPECTION_NOT_FOUND",
                message="Inspection not found.",
            )
        log_inspection_event(f"STATUS_CHANGED_TO_{status.value}", str(inspection_id))
        return inspection

    def get_dashboard_stats(self, user_id: UUID) -> Dict[str, int]:
        """Get inspection statistics for the dashboard."""
        counts = self.repo.get_counts_by_user(user_id)
        total = sum(counts.values())
        return {
            "total": total,
            "created": counts.get("CREATED", 0),
            "images_uploaded": counts.get("IMAGES_UPLOADED", 0),
            "processing": counts.get("PROCESSING", 0),
            "completed": counts.get("COMPLETED", 0),
            "needs_review": counts.get("NEEDS_REVIEW", 0),
        }
