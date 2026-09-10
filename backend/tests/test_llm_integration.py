import pytest
from unittest.mock import patch, MagicMock
from app.ai.extraction import extract_product_info, LLMProductData
from app.core.config import settings

@pytest.fixture
def sample_blocks():
    return [
        {"text": "Super Energy Drink", "confidence": 0.99, "bbox": [0,0,10,10]},
        {"text": "MRP Rs. 50", "confidence": 0.95, "bbox": [0,10,10,20]}
    ]

@patch("app.ai.extraction.Groq")
def test_llm_extraction_success(mock_groq, sample_blocks):
    """Test A: Successful LLM extraction via mock"""
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"product_name": {"value": "Super Energy Drink", "evidence": {"source_text": "Super Energy Drink"}}, "mrp": {"value": "50", "evidence": {"source_text": "MRP Rs. 50"}}, "brand_name": {"value": null}, "manufacturer": {"value": null}, "net_quantity": {"value": null}, "manufacturing_date": {"value": null}, "expiry_date": {"value": null}, "batch_number": {"value": null}, "country_of_origin": {"value": null}, "ingredients": {"value": null}, "license_number": {"value": null}, "customer_care": {"value": null}, "warnings": {"value": null}}'
    mock_client.chat.completions.create.return_value = mock_response

    # Force GROQ_API_KEY to trigger LLM path
    with patch.dict("os.environ", {"GROQ_API_KEY": "fake_key"}):
        settings.GROQ_API_KEY = "fake_key"
        result = extract_product_info(sample_blocks)
        
        assert result.extraction_version == "2.0-groq"
        assert result.product_name == "Super Energy Drink"
        assert result.mrp == "50"

@patch("app.ai.extraction.Groq")
def test_llm_failure_fallback(mock_groq, sample_blocks):
    """Test B: LLM failure -> regex fallback"""
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    # Simulate an unknown exception to trigger fallback
    mock_client.chat.completions.create.side_effect = Exception("Unknown Groq API Error")

    with patch.dict("os.environ", {"GROQ_API_KEY": "fake_key"}):
        settings.GROQ_API_KEY = "fake_key"
        result = extract_product_info(sample_blocks)
        
        assert result.extraction_version == "1.0-fallback"
        assert result.product_name == "Super Energy Drink"
        assert result.mrp == "50"

@patch("app.ai.extraction.Groq")
def test_model_config_used(mock_groq, sample_blocks):
    """Test C: Model config used from settings"""
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"product_name": null, "brand_name": null, "manufacturer": null, "net_quantity": null, "mrp": null, "manufacturing_date": null, "expiry_date": null, "batch_number": null, "country_of_origin": null, "ingredients": null, "license_number": null, "customer_care": null, "warnings": null}'
    mock_client.chat.completions.create.return_value = mock_response

    original_model = settings.GROQ_MODEL
    try:
        settings.GROQ_MODEL = "test/custom-model-123"
        with patch.dict("os.environ", {"GROQ_API_KEY": "fake_key"}):
            settings.GROQ_API_KEY = "fake_key"
            extract_product_info(sample_blocks)
            
            mock_client.chat.completions.create.assert_called_once()
            called_kwargs = mock_client.chat.completions.create.call_args[1]
            assert called_kwargs["model"] == "test/custom-model-123"
    finally:
        settings.GROQ_MODEL = original_model

@patch("app.ai.extraction.Groq")
def test_non_retryable_400_fails_fast(mock_groq, sample_blocks):
    """Test D: Non-retryable 400 errors fail fast and fallback"""
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    mock_client.chat.completions.create.side_effect = Exception("400 Bad Request: model_not_found")

    with patch.dict("os.environ", {"GROQ_API_KEY": "fake_key"}):
        settings.GROQ_API_KEY = "fake_key"
        result = extract_product_info(sample_blocks)
        
        assert mock_client.chat.completions.create.call_count == 1
        assert result.extraction_version == "1.0-fallback"
