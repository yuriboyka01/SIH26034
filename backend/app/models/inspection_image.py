"""
Inspection image model.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ImageType(str, enum.Enum):
    """Types of package images."""
    FRONT = "FRONT"
    BACK = "BACK"
    SIDE = "SIDE"
    OTHER = "OTHER"


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(255), unique=True, nullable=False)
    file_path = Column(String(1000), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    image_type = Column(SAEnum(ImageType), nullable=False, default=ImageType.OTHER)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    inspection = relationship("Inspection", back_populates="images")
    ocr_results = relationship("OCRResult", back_populates="image", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InspectionImage {self.original_filename}>"

