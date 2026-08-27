"""
OCR Result SQLAlchemy model.

Stores the normalized result of running OCR on a single InspectionImage.
Child table ocr_text_blocks stores each detected text region.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class QualityStatus(str, enum.Enum):
    """Image quality classification."""
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class OCRResult(Base):
    """Persisted OCR result for one InspectionImage."""
    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inspection_images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Engine metadata
    engine = Column(String(50), nullable=False, default="paddleocr")
    engine_version = Column(String(50), nullable=True)

    # Concatenated full text for easy searching
    full_text = Column(Text, nullable=True)

    # Performance
    processing_time_ms = Column(Integer, nullable=True)

    # Preprocessing applied (comma-separated list e.g. "resize,grayscale,denoise")
    preprocessing_applied = Column(String(500), nullable=True)

    # Quality assessment
    quality_status = Column(SAEnum(QualityStatus), nullable=False, default=QualityStatus.GOOD)
    quality_blur_score = Column(Float, nullable=True)
    quality_brightness_score = Column(Float, nullable=True)
    quality_issues = Column(String(500), nullable=True)  # comma-separated issue codes

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    image = relationship("InspectionImage", back_populates="ocr_results")
    text_blocks = relationship("OCRTextBlock", back_populates="ocr_result", cascade="all, delete-orphan")
    product_info = relationship("ProductInfo", back_populates="ocr_result", uselist=False, cascade="all, delete-orphan")
    compliance_report = relationship("ComplianceReport", back_populates="ocr_result", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OCRResult image={self.image_id} engine={self.engine}>"


class OCRTextBlock(Base):
    """A single detected text region within an OCR result."""
    __tablename__ = "ocr_text_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocr_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ocr_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Text content
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)

    # Confidence 0.0 – 1.0
    confidence = Column(Float, nullable=False)

    # Bounding box as [x1, y1, x2, y2] stored as floats
    # These are absolute pixel coordinates on the original image
    bbox_x1 = Column(Float, nullable=True)
    bbox_y1 = Column(Float, nullable=True)
    bbox_x2 = Column(Float, nullable=True)
    bbox_y2 = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship
    ocr_result = relationship("OCRResult", back_populates="text_blocks")

    @property
    def bbox(self) -> list:
        """Return bbox as [x1, y1, x2, y2]."""
        return [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]

    def __repr__(self):
        return f"<OCRTextBlock '{self.raw_text[:30]}' conf={self.confidence:.2f}>"
