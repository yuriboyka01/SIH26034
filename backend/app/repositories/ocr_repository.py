"""
OCR result repository — database access for ocr_results and ocr_text_blocks.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ocr_result import OCRResult as OCRResultModel, OCRTextBlock as OCRTextBlockModel


class OCRRepository:
    """Data access for OCR results and text blocks."""

    def __init__(self, db: Session):
        self.db = db

    def create_result(self, result: OCRResultModel) -> OCRResultModel:
        """Persist an OCR result (without text blocks)."""
        self.db.add(result)
        self.db.flush()  # get id without committing
        return result

    def create_text_block(self, block: OCRTextBlockModel) -> OCRTextBlockModel:
        """Persist one text block."""
        self.db.add(block)
        return block

    def commit(self):
        """Commit the current transaction."""
        self.db.commit()

    def get_by_image_id(self, image_id: UUID) -> Optional[OCRResultModel]:
        """Return the latest OCR result for an image, or None."""
        return (
            self.db.query(OCRResultModel)
            .filter(OCRResultModel.image_id == image_id)
            .order_by(OCRResultModel.created_at.desc())
            .first()
        )

    def delete_for_image(self, image_id: UUID) -> int:
        """Delete all OCR results (and cascade text blocks) for an image. Returns count."""
        count = (
            self.db.query(OCRResultModel)
            .filter(OCRResultModel.image_id == image_id)
            .count()
        )
        self.db.query(OCRResultModel).filter(OCRResultModel.image_id == image_id).delete()
        return count
