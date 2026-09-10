import os
import pytest
from app.ai.ocr_service import extract, OCREngineUnavailableError
from app.ai.models import OCRResult

# Find the absolute path to the Images directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGES_DIR = os.path.join(BASE_DIR, "Images")

def test_ocr_integration_on_real_image():
    """Verify PaddleOCR runs and extracts text blocks from a real image."""
    test_image = os.path.join(IMAGES_DIR, "GOLD_front.jpeg")
    
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found at {test_image}")
        
    try:
        result: OCRResult = extract(test_image)
        
        # Verify result structure
        assert result.engine == "paddle", "Engine must be paddle, no fallback allowed"
        assert result.blocks is not None
        assert len(result.blocks) > 0, "OCR should find at least one text block"
        
        # Verify block contents
        first_block = result.blocks[0]
        assert hasattr(first_block, "raw_text")
        assert hasattr(first_block, "normalized_text")
        assert hasattr(first_block, "confidence")
        assert hasattr(first_block, "bbox")
        
        assert isinstance(first_block.confidence, float)
        assert len(first_block.bbox) == 4
        
        # Verify EasyOCR was not used
        assert "easyocr" not in result.engine.lower()
        
    except OCREngineUnavailableError:
        pytest.fail("OCR Engine was unavailable during integration test.")
