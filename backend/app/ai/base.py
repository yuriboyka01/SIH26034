"""
AI module placeholder interfaces.

These abstract classes define the contracts for future AI/ML services.
Phase 2+ will implement these interfaces with actual OCR, image processing,
and declaration extraction logic.

DO NOT add fake/mock implementations. These are interface contracts only.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from uuid import UUID


class ImagePreprocessingService(ABC):
    """
    Interface for image preprocessing operations.

    Phase 2 will implement:
    - Image enhancement (contrast, brightness)
    - Deskewing
    - Cropping
    - Noise reduction
    - Resolution normalization
    """

    @abstractmethod
    def preprocess(self, image_path: str) -> str:
        """
        Preprocess an image for OCR/analysis.

        Args:
            image_path: Path to the original image.

        Returns:
            Path to the preprocessed image.
        """
        raise NotImplementedError("Phase 2: Image preprocessing not yet implemented.")


class OCRService(ABC):
    """
    Interface for Optical Character Recognition.

    Phase 2 will implement:
    - Text extraction from package labels
    - Multi-language support
    - Confidence scoring
    - Bounding box detection for text regions
    """

    @abstractmethod
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from an image.

        Args:
            image_path: Path to the image.

        Returns:
            Dictionary with extracted text, bounding boxes, and confidence scores.
        """
        raise NotImplementedError("Phase 2: OCR not yet implemented.")


class DeclarationExtractionService(ABC):
    """
    Interface for extracting structured declarations from OCR text.

    Phase 3 will implement:
    - Product name extraction
    - Net quantity extraction
    - MRP extraction
    - Manufacturer details extraction
    - Date of manufacture / best before extraction
    - Consumer care details extraction
    """

    @abstractmethod
    def extract_declarations(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured declaration fields from OCR output.

        Args:
            ocr_result: Raw OCR output from OCRService.

        Returns:
            Dictionary of extracted declaration fields.
        """
        raise NotImplementedError("Phase 3: Declaration extraction not yet implemented.")


class AIAnalysisService(ABC):
    """
    Interface for the complete AI analysis pipeline.

    This orchestrates the full flow:
    Image → Preprocess → OCR → Declaration Extraction → Results

    Phase 2-3 will implement the full pipeline.
    """

    @abstractmethod
    def analyze_image(self, image_id: UUID) -> Dict[str, Any]:
        """
        Run the complete AI analysis pipeline on an image.

        Args:
            image_id: UUID of the InspectionImage to analyze.

        Returns:
            Complete analysis results including OCR text and extracted declarations.
        """
        raise NotImplementedError("Phase 2-3: AI analysis pipeline not yet implemented.")
