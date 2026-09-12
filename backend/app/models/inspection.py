"""
Inspection model.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class InspectionStatus(str, enum.Enum):
    """Inspection lifecycle statuses."""
    CREATED = "CREATED"
    IMAGES_UPLOADED = "IMAGES_UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_number = Column(String(50), unique=True, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(500), nullable=False)
    brand = Column(String(255), nullable=False)
    status = Column(
        SAEnum(InspectionStatus),
        nullable=False,
        default=InspectionStatus.CREATED,
    )
    # Geo-tagging: captured client-side via the browser Geolocation API at
    # inspection creation. All nullable — an inspector without GPS access
    # (or who declines the permission prompt) must still be able to create
    # an inspection.
    establishment_name = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    creator = relationship("User", back_populates="inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inspection {self.inspection_number}>"
