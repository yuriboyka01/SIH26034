"""
Models package. Import all models here so Alembic can discover them.
"""

from app.models.user import User, UserRole
from app.models.inspection import Inspection, InspectionStatus
from app.models.inspection_image import InspectionImage, ImageType
from app.models.ocr_result import OCRResult, OCRTextBlock, QualityStatus
from app.models.product_info import ProductInfo  # Phase 3

__all__ = [
    "User",
    "UserRole",
    "Inspection",
    "InspectionStatus",
    "InspectionImage",
    "ImageType",
    "OCRResult",
    "OCRTextBlock",
    "QualityStatus",
    "ProductInfo",
]
