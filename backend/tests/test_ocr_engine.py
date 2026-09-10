import pytest
from app.ai.ocr_service import _get_ocr, OCREngineUnavailableError

def test_paddlepaddle_importable():
    """Verify paddlepaddle is importable."""
    try:
        import paddle
        assert paddle.__version__ is not None
    except ImportError:
        pytest.fail("paddlepaddle is not installed or importable")

def test_paddleocr_importable():
    """Verify paddleocr is importable."""
    try:
        import paddleocr
        assert paddleocr.__version__ is not None
    except ImportError:
        pytest.fail("paddleocr is not installed or importable")

def test_ocr_engine_initialization():
    """Verify the OCR engine initializes correctly as PaddleOCR."""
    try:
        instance, version, engine_name = _get_ocr()
        assert instance is not None
        assert version != "unknown"
        assert engine_name == "paddle"
    except Exception as e:
        pytest.fail(f"OCR engine failed to initialize: {e}")
