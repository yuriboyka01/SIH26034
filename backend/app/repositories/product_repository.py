"""
Phase 3: Product information repository.

Provides data-access methods for the product_info table.
Follows the same pattern as OCRRepository.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.product_info import ProductInfo


class ProductInfoRepository:
    """Data access for structured product information records."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, record: ProductInfo) -> ProductInfo:
        """Persist a new ProductInfo record. Does NOT commit — caller commits."""
        self.db.add(record)
        self.db.flush()
        return record

    def get_by_ocr_result_id(self, ocr_result_id: UUID) -> Optional[ProductInfo]:
        """Return the ProductInfo linked to a given OCR result, or None."""
        return (
            self.db.query(ProductInfo)
            .filter(ProductInfo.ocr_result_id == ocr_result_id)
            .first()
        )

    def get_by_inspection_id(self, inspection_id: UUID) -> list:
        """
        Return all ProductInfo records whose OCR result belongs to an inspection.

        Joins through ocr_results → inspection_images → inspections.
        """
        from app.models.ocr_result import OCRResult as OCRResultModel
        from app.models.inspection_image import InspectionImage

        return (
            self.db.query(ProductInfo)
            .join(OCRResultModel, ProductInfo.ocr_result_id == OCRResultModel.id)
            .join(InspectionImage, OCRResultModel.image_id == InspectionImage.id)
            .filter(InspectionImage.inspection_id == inspection_id)
            .all()
        )

    def delete_for_ocr_result(self, ocr_result_id: UUID) -> None:
        """Delete existing ProductInfo for an OCR result (for re-analysis)."""
        self.db.query(ProductInfo).filter(
            ProductInfo.ocr_result_id == ocr_result_id
        ).delete()

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()
