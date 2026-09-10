import json
import os
import pytest

from app.ai.extraction import extract_product_info

@pytest.mark.skipif("GROQ_API_KEY" not in os.environ, reason="Live integration test requires GROQ_API_KEY")
def test_live_groq_extraction():
    """
    Live integration test against the real Groq API.
    Verifies the model parsing and schema validation work end-to-end.
    """
    # Simple synthetic blocks to avoid needing heavy OCR in the test
    synthetic_blocks = [
        {"text": "Super Energy Drink", "confidence": 0.99, "bbox": [10, 10, 50, 20]},
        {"text": "Mfg by: Beverage Co", "confidence": 0.99, "bbox": [10, 30, 100, 40]},
        {"text": "Net Vol 250ml", "confidence": 0.97, "bbox": [10, 50, 60, 60]},
        {"text": "MRP: Rs. 50", "confidence": 0.95, "bbox": [10, 70, 80, 80]},
        {"text": "Best before 6 months from manufacture", "confidence": 0.96, "bbox": [10, 90, 70, 100]},
        {"text": "Batch: AB-123", "confidence": 0.99, "bbox": [10, 130, 80, 140]},
        {"text": "Contains Caffeine", "confidence": 0.99, "bbox": [10, 230, 100, 240]},
    ]
    
    result = extract_product_info(synthetic_blocks, inspection_product_name="Super Energy Drink")

    assert result is not None
    assert result.extraction_version in ["2.0-groq", "1.0-fallback"]
    assert result.product_name == "Super Energy Drink"
    assert "50" in result.mrp
    
    # We should have successfully mapped the evidence back to OCR blocks
    mrp_field = next(f for f in result.fields if f.field_name == "mrp")
    assert mrp_field.detection_status == "DETECTED"
    assert mrp_field.evidence is not None
    assert mrp_field.evidence.confidence > 0.0
