"""
Inspection image data access repository.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.inspection_image import InspectionImage


class ImageRepository:
    """Repository for inspection image database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, image: InspectionImage) -> InspectionImage:
        """Create a new image record."""
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def get_by_id(self, image_id: UUID) -> Optional[InspectionImage]:
        """Find an image by ID."""
        return self.db.query(InspectionImage).filter(InspectionImage.id == image_id).first()

    def list_by_inspection(self, inspection_id: UUID) -> List[InspectionImage]:
        """List all images for an inspection."""
        return (
            self.db.query(InspectionImage)
            .filter(InspectionImage.inspection_id == inspection_id)
            .order_by(InspectionImage.created_at.asc())
            .all()
        )

    def delete(self, image: InspectionImage) -> None:
        """Delete an image record."""
        self.db.delete(image)
        self.db.commit()

    def count_by_inspection(self, inspection_id: UUID) -> int:
        """Count images for an inspection."""
        return (
            self.db.query(InspectionImage)
            .filter(InspectionImage.inspection_id == inspection_id)
            .count()
        )
