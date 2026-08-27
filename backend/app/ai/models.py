"""
Phase 2 OCR data models.

These are pure Python dataclasses — NOT database models.
They form the internal contract between OCR service and consumers (API, Phase 3 declaration parser).
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OCRTextBlock:
    """A single detected text region."""
    raw_text: str
    normalized_text: str
    confidence: float
    # [x1, y1, x2, y2] in absolute pixels on the original image
    bbox: List[float]


@dataclass
class ImageQuality:
    """Result of image quality analysis."""
    status: str          # "GOOD" | "FAIR" | "POOR"
    blur_score: float    # 0.0 = very blurry, higher = sharper (Laplacian variance)
    brightness_score: float  # 0.0–1.0 normalised mean brightness
    issues: List[str] = field(default_factory=list)
    # Possible issue codes: IMAGE_TOO_SMALL, IMAGE_TOO_BLURRY, IMAGE_TOO_DARK, IMAGE_TOO_BRIGHT


@dataclass
class OCRResult:
    """
    Normalized output of the OCR pipeline for a single image.

    This is the contract consumed by Phase 3 (declaration extraction).
    It does NOT expose PaddleOCR internals.
    """
    image_path: str
    engine: str                          # e.g. "paddleocr"
    engine_version: str                  # e.g. "2.8.0"
    blocks: List[OCRTextBlock]
    full_text: str                       # All detected text joined by newlines
    processing_time_ms: int
    preprocessing_applied: List[str]     # e.g. ["resize", "grayscale", "denoise"]
    quality: ImageQuality


@dataclass
class AnalysisResult:
    """
    Full analysis result for a single image — passed to API layer and persistence.
    """
    image_id: str
    ocr: Optional[OCRResult]
    error: Optional[str] = None  # Set if analysis failed for this image
