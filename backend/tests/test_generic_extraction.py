import json
import os
import pytest
from unittest.mock import patch, MagicMock

from app.ai.extraction import extract_product_info

@patch("app.ai.extraction.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_test_key"})
def test_generic_extraction_with_fuzzy_matching(mock_groq):
    """
    Test the generic extraction and robust evidence mapping logic.
    Provides synthetic OCR blocks completely unrelated to any specific product.
    """
    # Mock Groq client
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    mock_response = MagicMock()
    # Mock the LLM returning structured JSON data for a fake "Super Widget"
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "product_name": {"value": "Super Widget", "evidence": None},
        "brand_name": {"value": "Acme Corp", "evidence": {"source_text": "Acme Corporation"}},
        "manufacturer": {"value": "Acme Mfg Ltd", "evidence": {"source_text": "Mfd by Acme Mfg Ltd"}},
        "net_quantity": {"value": "1 kg", "evidence": {"source_text": "Net Wt. 1 kg"}},
        "mrp": {"value": "999.00", "evidence": {"source_text": "MRP: 999.00 (incl taxes)"}},
        "manufacturing_date": {"value": "01/2026", "evidence": {"source_text": "Mfg: 01/2026"}},
        "expiry_date": {"value": "12/2027", "evidence": {"source_text": "Exp: 12/2027"}},
        "batch_number": {"value": "XYZ-987", "evidence": {"source_text": "Batch: XYZ-987"}},
        "country_of_origin": {"value": "USA", "evidence": {"source_text": "Made in USA"}},
        "ingredients": {"value": "Steel, Plastic", "evidence": {"source_text": "Contents: Steel, Plastic"}},
        "license_number": {"value": "LIC-12345", "evidence": {"source_text": "Lic No. LIC-12345"}},
        "customer_care": {"value": "1-800-ACME", "evidence": {"source_text": "Call 1-800-ACME"}},
        "warnings": {"value": "Choking Hazard", "evidence": {"source_text": "Warning: Choking Hazard"}}
    })
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    # Provide arbitrary, noisy OCR blocks (with slight typos to test fuzzy matching)
    synthetic_blocks = [
        {"text": "Acme  Corporation", "confidence": 0.98, "bbox": [10, 10, 50, 20]}, # Whitespace variation
        {"text": "Mfd by Acme Mfg Ltd.", "confidence": 0.99, "bbox": [10, 30, 100, 40]}, # Punctuation variation
        {"text": "Net Wt 1 kg", "confidence": 0.97, "bbox": [10, 50, 60, 60]}, # Missing punctuation
        {"text": "MRP: 999.00(incl taxes)", "confidence": 0.95, "bbox": [10, 70, 80, 80]}, # Missing space
        {"text": "Mfg: 01/2026", "confidence": 0.96, "bbox": [10, 90, 70, 100]},
        {"text": "Exp: 12/2027", "confidence": 0.96, "bbox": [10, 110, 70, 120]},
        {"text": "Batch: XYZ-987", "confidence": 0.99, "bbox": [10, 130, 80, 140]},
        {"text": "Made in U.S.A", "confidence": 0.94, "bbox": [10, 150, 60, 160]}, # Slightly different (USA vs U.S.A)
        {"text": "Contents: Steel, Plastic", "confidence": 0.98, "bbox": [10, 170, 120, 180]},
        {"text": "Lic No. LIC-12345", "confidence": 0.99, "bbox": [10, 190, 90, 200]},
        {"text": "Call 1-800-ACME", "confidence": 0.95, "bbox": [10, 210, 80, 220]},
        {"text": "Warning: Choking Hazard", "confidence": 0.99, "bbox": [10, 230, 100, 240]},
    ]

    result = extract_product_info(synthetic_blocks, inspection_product_name="Super Widget")

    assert result is not None
    assert result.extraction_version == "2.0-groq"
    assert result.product_name == "Super Widget"
    assert result.brand_name == "Acme Corp"
    
    # Test fuzzy evidence mapping for brand_name
    brand_field = next(f for f in result.fields if f.field_name == "brand_name")
    assert brand_field.detection_status == "DETECTED"
    assert brand_field.evidence.source_text == "Acme Corporation"
    assert brand_field.evidence.confidence == 0.98
    assert brand_field.evidence.bbox == [10, 10, 50, 20]
    
    # Test net quantity (punctuation difference handling)
    qty_field = next(f for f in result.fields if f.field_name == "net_quantity")
    assert qty_field.detection_status == "DETECTED"
    assert qty_field.evidence.confidence == 0.97
    
    # Test country of origin (fuzzy matching should handle 'USA' vs 'U.S.A')
    origin_field = next(f for f in result.fields if f.field_name == "country_of_origin")
    assert origin_field.detection_status == "DETECTED"
    assert origin_field.evidence.confidence == 0.94
    assert origin_field.evidence.bbox == [10, 150, 60, 160]


@patch("app.ai.extraction.Groq")
@patch.dict(os.environ, {"GROQ_API_KEY": "fake_test_key"})
def test_generic_extraction_fail_closed_mapping(mock_groq):
    """
    Test that if the LLM hallucinates evidence that cannot be found in the OCR blocks,
    the mapping fails closed: the value is returned, but detection_status is UNCERTAIN
    and no bbox is associated.
    """
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    mock_response = MagicMock()
    # Mock LLM returning evidence that doesn't exist in the blocks
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "product_name": {"value": "Fake Item", "evidence": None},
        "brand_name": {"value": "FakeBrand", "evidence": {"source_text": "This text is not in OCR"}},
        "manufacturer": {"value": None, "evidence": None},
        "net_quantity": {"value": None, "evidence": None},
        "mrp": {"value": None, "evidence": None},
        "manufacturing_date": {"value": None, "evidence": None},
        "expiry_date": {"value": None, "evidence": None},
        "batch_number": {"value": None, "evidence": None},
        "country_of_origin": {"value": None, "evidence": None},
        "ingredients": {"value": None, "evidence": None},
        "license_number": {"value": None, "evidence": None},
        "customer_care": {"value": None, "evidence": None},
        "warnings": {"value": None, "evidence": None}
    })
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    blocks = [{"text": "Just some random text", "confidence": 0.99, "bbox": [0,0,10,10]}]
    result = extract_product_info(blocks, inspection_product_name="Fake Item")

    assert result is not None
    brand_field = next(f for f in result.fields if f.field_name == "brand_name")
    
    # Value is extracted...
    assert brand_field.value == "FakeBrand"
    # ...but it failed to map evidence, so it fails closed to UNCERTAIN
    assert brand_field.detection_status == "UNCERTAIN"
    assert brand_field.evidence.bbox is None
    assert brand_field.evidence.confidence == 0.0
