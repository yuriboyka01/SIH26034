"""
Pydantic schemas for analysis / OCR API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel
from app.schemas.product_info import ProductInfoSchema


class OCRBlockSchema(BaseModel):
    text: str
    raw_text: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class OCRDataSchema(BaseModel):
    engine: str
    engine_version: Optional[str] = None
    full_text: str
    processing_time_ms: Optional[int] = None
    preprocessing_applied: List[str] = []
    blocks: List[OCRBlockSchema] = []


class QualitySchema(BaseModel):
    status: str  # GOOD | FAIR | POOR
    blur_score: Optional[float] = None
    brightness_score: Optional[float] = None
    issues: List[str] = []


class ImageAnalysisResult(BaseModel):
    image_id: str
    status: str  # OK | ERROR | NOT_ANALYSED
    quality: Optional[QualitySchema] = None
    ocr: Optional[OCRDataSchema] = None
    error: Optional[str] = None
    # Phase 3: structured product information (None if not yet extracted)
    product_info: Optional[ProductInfoSchema] = None


class AnalysisResponse(BaseModel):
    inspection_id: str
    status: str
    images: List[ImageAnalysisResult] = []
