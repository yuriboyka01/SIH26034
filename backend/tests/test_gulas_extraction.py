import json
import os
import pytest
from unittest.mock import patch, MagicMock

from app.ai.extraction import extract_product_info

@pytest.fixture
def gulas_blocks():
    """Load the pre-extracted OCR blocks from Gulas images."""
    file_path = os.path.join(os.path.dirname(__file__), "gulas_blocks.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@patch("app.ai.extraction.genai")
@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key"})
def test_gulas_extraction_llm_success(mock_genai, gulas_blocks):
    """
    Test that the Gemini LLM extraction pathway successfully extracts
    the expected structured data from noisy OCR blocks.
    """
    # Create a mock for the genai Client and response
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    
    mock_response = MagicMock()
    # Mock the LLM returning structured JSON data
    mock_response.text = json.dumps({
        "product_name": {"value": "Gulas Jaggery Powder", "evidence": None},
        "brand_name": {"value": "Gulas", "evidence": {"source_text": "Gulas"}},
        "manufacturer": {"value": "SUNRAJA", "evidence": {"source_text": "SUNRAJA"}},
        "net_quantity": {"value": "500g", "evidence": {"source_text": "500g"}},
        "mrp": {"value": "130.00", "evidence": {"source_text": "Rs. 130.00"}},
        "manufacturing_date": {"value": "10/08/2026", "evidence": {"source_text": "MFG 10/08/2026"}},
        "expiry_date": {"value": "09/08/2027", "evidence": {"source_text": "EXP 09/08/2027"}},
        "batch_number": {"value": "C0584", "evidence": {"source_text": "BATCHNo."}},
        "country_of_origin": {"value": "India", "evidence": {"source_text": "Made in India"}},
        "ingredients": {"value": "Sugarcane Extract", "evidence": {"source_text": "INGREDIENTS:Sugarcane Extract"}},
        "license_number": {"value": "10012042000032", "evidence": {"source_text": "FSSAI Lic. No. 10012042000032"}},
        "customer_care": {"value": "18001234567", "evidence": {"source_text": "Customer Care 18001234567"}},
        "warnings": {"value": "KEEP AWAY FROM DIRECT SUNLIGHT", "evidence": {"source_text": "KEEP AWAY FROM DIRECT SUNLIGHT"}}
    })
    mock_client.models.generate_content.return_value = mock_response

    # Run extraction
    result = extract_product_info(gulas_blocks, inspection_product_name="Gulas Sugar")

    # Assert that the Gemini pathway was used and returned the expected structured data
    assert result is not None
    assert result.extraction_version == "2.0-gemini"
    assert result.product_name == "Gulas Jaggery Powder"
    assert result.brand_name == "Gulas"
    assert result.manufacturer == "SUNRAJA"
    assert result.net_quantity == "500g"
    assert result.mrp == "130.00"
    assert result.batch_number == "C0584"
    assert result.ingredients == "Sugarcane Extract"
    assert result.warnings == "KEEP AWAY FROM DIRECT SUNLIGHT"
    
    # Assert that the mapping successfully attached OCR evidence block details
    for field in result.fields:
        if field.field_name == "net_quantity":
            assert field.detection_status == "DETECTED"
            assert field.evidence is not None
            assert field.evidence.source_text == "500g"
            # It should have mapped to an actual block confidence, not the default 0.9
            assert field.evidence.confidence > 0.95
            assert field.evidence.bbox is not None


@patch.dict(os.environ, {}, clear=True)
def test_gulas_extraction_fallback(gulas_blocks):
    """
    Test that if GEMINI_API_KEY is missing, it gracefully falls back
    to the legacy regex extractors and does not crash.
    """
    # Run extraction with no API key
    result = extract_product_info(gulas_blocks, inspection_product_name="Gulas Sugar")
    
    # Assert fallback was used
    assert result is not None
    assert result.extraction_version == "1.0-fallback"
    
    # Assert deterministic logic still extracted what it could (even if limited)
    assert result.net_quantity == "500g"
    assert result.batch_number == "No" # Brittle regex logic gets "No" instead of "C0584"
    assert result.ingredients == "Sugarcane Extract"
