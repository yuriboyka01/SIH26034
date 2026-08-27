"""
Phase 3: ProductInfo SQLAlchemy model.

Stores the structured product information extracted from OCR text blocks
for a given inspection. Linked to ocr_results via ocr_result_id.

One ProductInfo record is created per OCR result (per image).
The full JSON representation is stored in a Text column for flexibility,
with individual top-level fields indexed for querying.
"""

import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProductInfo(Base):
    """
    Persisted structured product information for one OCR result.

    All string fields store the extracted text verbatim.
    None / NULL = not detected in OCR.
    The `fields_json` column stores the full evidence-linked field list
    from StructuredProductData.fields for the Phase 4 rules engine.
    """
    __tablename__ = "product_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocr_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ocr_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Top-level extracted fields (null = NOT DETECTED)
    product_name = Column(String(500), nullable=True)
    brand_name = Column(String(255), nullable=True)
    manufacturer = Column(Text, nullable=True)
    net_quantity = Column(String(200), nullable=True)
    mrp = Column(String(100), nullable=True)
    manufacturing_date = Column(String(100), nullable=True)
    expiry_date = Column(String(100), nullable=True)
    batch_number = Column(String(200), nullable=True)
    country_of_origin = Column(String(200), nullable=True)
    ingredients = Column(Text, nullable=True)
    license_number = Column(String(300), nullable=True)
    customer_care = Column(String(200), nullable=True)
    warnings = Column(Text, nullable=True)

    # Full evidence-linked fields as JSON (for Phase 4 rules engine)
    fields_json = Column(Text, nullable=True)  # JSON string

    # Extraction metadata
    total_blocks_processed = Column(Integer, nullable=True)
    extraction_version = Column(String(20), nullable=True, default="1.0")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship back to OCRResult
    ocr_result = relationship("OCRResult", back_populates="product_info")

    def get_fields(self) -> list:
        """Deserialize fields_json to a list of field dicts."""
        if self.fields_json:
            try:
                return json.loads(self.fields_json)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_fields(self, fields: list) -> None:
        """Serialize a list of field dicts to fields_json."""
        self.fields_json = json.dumps(fields, ensure_ascii=False)

    def __repr__(self):
        return f"<ProductInfo mrp={self.mrp} net_qty={self.net_quantity}>"
