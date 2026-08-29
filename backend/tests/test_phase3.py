"""
Phase 3 tests — extraction engine, evidence linking, API endpoint, persistence.

All tests run without PaddleOCR (OCR is mocked where needed).
Target: 0 failures.

NOTE: These tests exercise the deterministic regex-fallback extraction path on
purpose (fast, offline, reproducible). The autouse fixture below forces
app.ai.extraction.genai to None for every test in this file, so a real
GEMINI_API_KEY in the environment doesn't route these through the live
Gemini API (slow + non-deterministic + costs quota). Live/LLM extraction is
covered separately in test_live_extraction.py and test_gulas_extraction.py.
"""

import io
import json
import pytest

import app.ai.extraction as extraction_module
from app.ai.extraction import (
    extract_product_info,
    _extract_date,
    _extract_mrp,
    _extract_net_quantity,
    _extract_dates,
    _extract_batch,
    _extract_country_of_origin,
    _clean,
    _Block,
    StructuredProductData,
    ExtractedField,
)


@pytest.fixture(autouse=True)
def _force_regex_fallback(monkeypatch):
    """Keep this file's extraction tests fast/offline regardless of a real API key."""
    monkeypatch.setattr(extraction_module, "genai", None)



# ── Helpers ───────────────────────────────────────────────────────────────────

def blocks_from_texts(*texts: str, confidence: float = 0.92) -> list:
    """Create OCR block dicts from plain strings."""
    return [{"text": t, "confidence": confidence, "bbox": [0, 0, 100, 20]} for t in texts]


def _make_real_jpeg() -> bytes:
    """Create a minimal real JPEG for upload tests."""
    import numpy as np
    import cv2
    img = np.full((400, 600, 3), 200, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ── Unit: Text Cleaning ───────────────────────────────────────────────────────

class TestTextCleaning:
    def test_clean_strips(self):
        assert _clean("  MRP Rs 50  ") == "MRP Rs 50"

    def test_clean_collapses_spaces(self):
        assert _clean("Net  Qty  500  g") == "Net Qty 500 g"

    def test_clean_replaces_rupee_symbol(self):
        result = _clean("MRP ₹420")
        assert "Rs" in result or "420" in result

    def test_clean_replaces_rs_dot(self):
        result = _clean("MRP Rs. 420")
        # Rs. → Rs
        assert "Rs" in result


# ── Unit: Date Extraction ────────────────────────────────────────────────────

class TestDateExtraction:
    def test_ddmmyyyy_slash(self):
        assert _extract_date("Mfg: 10/08/2026") == "10/08/2026"

    def test_ddmmyyyy_dash(self):
        assert _extract_date("Exp: 10-08-2027") == "10-08-2027"

    def test_mmyyyy(self):
        result = _extract_date("Best Before: 08/2027")
        assert result is not None
        assert "2027" in result

    def test_month_year(self):
        result = _extract_date("Exp: Aug 2027")
        assert result is not None
        assert "Aug" in result or "2027" in result

    def test_no_date(self):
        assert _extract_date("Brand: ABC Foods") is None

    def test_yyyymmdd(self):
        result = _extract_date("DOM: 2026/08/10")
        assert result is not None
        assert "2026" in result


# ── Unit: MRP Extraction ─────────────────────────────────────────────────────

class TestMRPExtraction:
    def test_mrp_keyword_with_rs(self):
        blocks = [_Block("MRP Rs 120", 0.95, [0, 0, 100, 20])]
        field = _extract_mrp(blocks)
        assert field.value == "120"
        assert field.detection_status == "DETECTED"

    def test_mrp_keyword_with_inr(self):
        blocks = [_Block("MRP INR 250.00", 0.91, None)]
        field = _extract_mrp(blocks)
        assert field.value == "250.00"

    def test_mrp_rupee_symbol(self):
        blocks = [_Block("MRP ₹ 420", 0.88, None)]
        field = _extract_mrp(blocks)
        assert field.value == "420"
        assert field.detection_status == "DETECTED"

    def test_mrp_fallback_price(self):
        blocks = [_Block("Rs 75", 0.80, None)]
        field = _extract_mrp(blocks)
        assert field.value == "75"
        assert field.detection_status == "UNCERTAIN"

    def test_mrp_not_found(self):
        blocks = [_Block("Net Weight 500 g", 0.9, None)]
        field = _extract_mrp(blocks)
        assert field.value is None
        assert field.detection_status == "NOT_DETECTED"

    def test_mrp_with_comma(self):
        blocks = [_Block("MRP Rs 1,200", 0.90, None)]
        field = _extract_mrp(blocks)
        assert field.value == "1200"

    def test_mrp_evidence_preserved(self):
        blocks = [_Block("MRP Rs 99", 0.95, [10.0, 20.0, 200.0, 40.0])]
        field = _extract_mrp(blocks)
        assert field.evidence is not None
        assert field.evidence.source_text == "MRP Rs 99"
        assert field.evidence.confidence == 0.95
        assert field.evidence.bbox == [10.0, 20.0, 200.0, 40.0]


# ── Unit: Net Quantity Extraction ────────────────────────────────────────────

class TestNetQuantityExtraction:
    def test_net_weight_grams(self):
        blocks = [_Block("Net Weight: 500 g", 0.92, None)]
        field = _extract_net_quantity(blocks)
        assert "500" in field.value
        assert "g" in field.value.lower()
        assert field.detection_status == "DETECTED"

    def test_net_weight_kg(self):
        blocks = [_Block("Net Weight: 1 kg", 0.90, None)]
        field = _extract_net_quantity(blocks)
        assert "1" in field.value
        assert "kg" in field.value.lower()

    def test_net_qty_ml(self):
        blocks = [_Block("Net Volume: 200 ml", 0.88, None)]
        field = _extract_net_quantity(blocks)
        assert "200" in field.value

    def test_qty_only_fallback(self):
        blocks = [_Block("500g", 0.75, None)]
        field = _extract_net_quantity(blocks)
        assert field.value is not None
        assert field.detection_status == "UNCERTAIN"

    def test_qty_not_found(self):
        blocks = [_Block("Brand ABC", 0.9, None)]
        field = _extract_net_quantity(blocks)
        assert field.value is None
        assert field.detection_status == "NOT_DETECTED"


# ── Unit: Batch Number Extraction ────────────────────────────────────────────

class TestBatchExtraction:
    def test_batch_no(self):
        blocks = [_Block("Batch No: A123", 0.93, None)]
        field = _extract_batch(blocks)
        assert field.value == "A123"
        assert field.detection_status == "DETECTED"

    def test_lot_no(self):
        blocks = [_Block("LOT: X99Z", 0.88, None)]
        field = _extract_batch(blocks)
        assert field.value == "X99Z"

    def test_batch_not_found(self):
        blocks = [_Block("MRP Rs 50", 0.9, None)]
        field = _extract_batch(blocks)
        assert field.value is None


# ── Unit: Country of Origin ──────────────────────────────────────────────────

class TestCountryExtraction:
    def test_made_in_india(self):
        blocks = [_Block("Made in India", 0.95, None)]
        field = _extract_country_of_origin(blocks)
        assert field.value is not None
        assert "India" in field.value

    def test_country_of_origin(self):
        blocks = [_Block("Country of Origin: India", 0.92, None)]
        field = _extract_country_of_origin(blocks)
        assert "India" in field.value

    def test_not_found(self):
        blocks = [_Block("Net Weight 500 g", 0.9, None)]
        field = _extract_country_of_origin(blocks)
        assert field.value is None


# ── Unit: Date Fields ────────────────────────────────────────────────────────

class TestDateFields:
    def test_mfg_and_exp(self):
        blocks = [
            _Block("Mfg: 10/08/2026", 0.92, None),
            _Block("Best Before: 10/08/2027", 0.90, None),
        ]
        result = _extract_dates(blocks)
        assert result["manufacturing_date"].value is not None
        assert "2026" in result["manufacturing_date"].value
        assert result["expiry_date"].value is not None
        assert "2027" in result["expiry_date"].value

    def test_mfg_only(self):
        blocks = [_Block("Mfg: 01/01/2026", 0.91, None)]
        result = _extract_dates(blocks)
        assert result["manufacturing_date"].value is not None
        assert result["expiry_date"].value is None

    def test_no_dates(self):
        blocks = [_Block("Brand ABC Foods", 0.9, None)]
        result = _extract_dates(blocks)
        assert result["manufacturing_date"].value is None
        assert result["expiry_date"].value is None


# ── Unit: Full Extraction Pipeline ───────────────────────────────────────────

class TestFullExtractionPipeline:
    def test_typical_product_label(self):
        """Simulate a typical product label with all major fields."""
        ocr_blocks = blocks_from_texts(
            "ABC Foods Premium Basmati Rice",
            "Brand: ABC Foods",
            "Net Weight: 5 kg",
            "MRP Rs 420",
            "Mfg: 10/08/2026",
            "Best Before: 10/08/2027",
            "Batch No: B2026-08",
            "Made in India",
            "Manufactured by: ABC Foods Pvt Ltd, Delhi",
            "FSSAI Lic No: 12345678901234",
        )
        result = extract_product_info(
            ocr_blocks,
            inspection_product_name="Basmati Rice",
            inspection_brand="ABC Foods",
        )
        assert isinstance(result, StructuredProductData)
        assert result.mrp == "420"
        assert result.net_quantity is not None
        assert "5" in result.net_quantity
        assert result.manufacturing_date is not None
        assert result.expiry_date is not None
        assert result.batch_number == "B2026-08"
        assert result.country_of_origin is not None
        assert result.manufacturer is not None
        assert result.license_number is not None

    def test_empty_blocks_returns_none_fields(self):
        """No OCR blocks → all fields must be None, not invented values."""
        result = extract_product_info([])
        assert result.mrp is None
        assert result.net_quantity is None
        assert result.manufacturing_date is None
        assert result.expiry_date is None
        assert result.batch_number is None
        assert result.country_of_origin is None
        assert result.total_blocks_processed == 0

    def test_noisy_ocr_still_extracts(self):
        """OCR with noise and extra spaces still extracts fields."""
        ocr_blocks = blocks_from_texts(
            "M R P   Rs   99",
            "Net   Wt   250  g",
            "Batch  No:  X 001",
        )
        result = extract_product_info(ocr_blocks)
        # MRP may come from fallback pattern
        assert result.mrp is not None or result.net_quantity is not None

    def test_inspection_metadata_fallback(self):
        """Product name and brand from inspection metadata when not in OCR."""
        result = extract_product_info(
            [],
            inspection_product_name="Test Product",
            inspection_brand="Test Brand",
        )
        assert result.product_name == "Test Product"
        assert result.brand_name == "Test Brand"

    def test_evidence_linked_fields(self):
        """All detected fields must carry evidence."""
        ocr_blocks = blocks_from_texts("MRP Rs 50", "Net Weight: 100 g")
        result = extract_product_info(ocr_blocks)
        mrp_field = next((f for f in result.fields if f.field_name == "mrp"), None)
        assert mrp_field is not None
        if mrp_field.detection_status == "DETECTED":
            assert mrp_field.evidence is not None
            assert mrp_field.evidence.source_text != ""

    def test_to_dict_serializable(self):
        """to_dict() must return a JSON-serializable dict."""
        result = extract_product_info(blocks_from_texts("MRP Rs 99", "Net Wt 100 g"))
        d = result.to_dict()
        assert isinstance(d, dict)
        # Must be JSON serializable
        json_str = json.dumps(d)
        assert len(json_str) > 0

    def test_detection_statuses_valid(self):
        """All fields must have a valid detection_status."""
        valid_statuses = {"DETECTED", "NOT_DETECTED", "UNCERTAIN"}
        result = extract_product_info(blocks_from_texts("MRP Rs 100"))
        for f in result.fields:
            assert f.detection_status in valid_statuses, f"Bad status: {f.field_name}={f.detection_status}"

    def test_total_blocks_count(self):
        texts = ["line one", "line two", "line three"]
        result = extract_product_info(blocks_from_texts(*texts))
        assert result.total_blocks_processed == 3


# ── API Tests: product-info endpoint ─────────────────────────────────────────

class TestProductInfoAPI:

    def test_get_product_info_unauthenticated(self, client):
        """Product info without auth should fail with 403."""
        import uuid
        response = client.get(f"/api/inspections/{uuid.uuid4()}/product-info")
        assert response.status_code == 403

    def test_get_product_info_not_found(self, client, auth_headers):
        """Product info for non-existent inspection should 404."""
        import uuid
        response = client.get(
            f"/api/inspections/{uuid.uuid4()}/product-info",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_product_info_empty_before_analysis(self, client, auth_headers, upload_dir):
        """Product info for an inspection with no analysis should return empty list."""
        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "Rice", "brand": "Brand A"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]

        response = client.get(
            f"/api/inspections/{insp_id}/product-info",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inspection_id"] == insp_id
        assert data["product_info_list"] == []

    def test_product_info_populated_after_analysis(self, client, auth_headers, upload_dir, monkeypatch):
        """After analysis with mocked OCR, product_info should be populated."""
        from app.ai import ocr_service
        from app.ai.models import OCRResult, OCRTextBlock, ImageQuality

        def mock_extract(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path,
                engine="paddleocr",
                engine_version="mock",
                blocks=[
                    OCRTextBlock(
                        raw_text="MRP Rs 420",
                        normalized_text="MRP Rs 420",
                        confidence=0.95,
                        bbox=[10.0, 20.0, 200.0, 50.0],
                    ),
                    OCRTextBlock(
                        raw_text="Net Weight: 5 kg",
                        normalized_text="Net Weight: 5 kg",
                        confidence=0.93,
                        bbox=[10.0, 60.0, 200.0, 90.0],
                    ),
                    OCRTextBlock(
                        raw_text="Mfg: 10/08/2026",
                        normalized_text="Mfg: 10/08/2026",
                        confidence=0.91,
                        bbox=[10.0, 100.0, 200.0, 120.0],
                    ),
                    OCRTextBlock(
                        raw_text="Batch No: B001",
                        normalized_text="Batch No: B001",
                        confidence=0.90,
                        bbox=[10.0, 130.0, 200.0, 150.0],
                    ),
                ],
                full_text="MRP Rs 420\nNet Weight: 5 kg\nMfg: 10/08/2026\nBatch No: B001",
                processing_time_ms=100,
                preprocessing_applied=[],
                quality=ImageQuality(
                    status="GOOD",
                    blur_score=300.0,
                    brightness_score=0.6,
                    issues=[],
                ),
            )

        monkeypatch.setattr(ocr_service, "extract", mock_extract)

        # Create inspection
        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "Basmati Rice", "brand": "Kohinoor"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        insp_id = create_resp.json()["id"]

        # Upload image
        upload_resp = client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("label.jpg", io.BytesIO(_make_real_jpeg()), "image/jpeg")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 201

        # Run analysis
        analyze_resp = client.post(
            f"/api/inspections/{insp_id}/analyze",
            headers=auth_headers,
        )
        assert analyze_resp.status_code == 200
        analyze_data = analyze_resp.json()

        # product_info should be embedded in the analysis response
        img_result = analyze_data["images"][0]
        assert img_result["status"] == "OK"
        assert img_result["product_info"] is not None
        pi = img_result["product_info"]
        assert pi["mrp"] == "420"
        assert pi["net_quantity"] is not None
        assert "5" in pi["net_quantity"]
        assert pi["manufacturing_date"] is not None
        assert pi["batch_number"] == "B001"

        # Verify dedicated endpoint also returns data
        info_resp = client.get(
            f"/api/inspections/{insp_id}/product-info",
            headers=auth_headers,
        )
        assert info_resp.status_code == 200
        info_data = info_resp.json()
        assert len(info_data["product_info_list"]) == 1
        pi2 = info_data["product_info_list"][0]
        assert pi2["mrp"] == "420"
        assert pi2["total_blocks_processed"] == 4

    def test_analysis_response_backward_compatible(self, client, auth_headers, upload_dir, monkeypatch):
        """
        Existing analysis endpoint response must still have all Phase 2 fields.
        product_info is an addition, not a replacement.
        """
        from app.ai import ocr_service
        from app.ai.models import OCRResult, OCRTextBlock, ImageQuality

        def mock_extract(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path,
                engine="paddleocr",
                engine_version="mock",
                blocks=[
                    OCRTextBlock("text", "text", 0.9, [0, 0, 100, 20]),
                ],
                full_text="text",
                processing_time_ms=50,
                preprocessing_applied=[],
                quality=ImageQuality("GOOD", 200.0, 0.5, []),
            )

        monkeypatch.setattr(ocr_service, "extract", mock_extract)

        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "P", "brand": "B"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]

        client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("t.jpg", io.BytesIO(_make_real_jpeg()), "image/jpeg")},
            headers=auth_headers,
        )

        resp = client.post(f"/api/inspections/{insp_id}/analyze", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        # Phase 2 fields still present
        assert "inspection_id" in data
        assert "status" in data
        assert "images" in data
        img = data["images"][0]
        assert "image_id" in img
        assert "status" in img
        assert "quality" in img
        assert "ocr" in img
        assert img["ocr"]["engine"] == "paddleocr"
        assert len(img["ocr"]["blocks"]) == 1
        # Phase 3 field added
        assert "product_info" in img

    def test_fields_list_has_detection_statuses(self, client, auth_headers, upload_dir, monkeypatch):
        """
        The fields list in product_info must have valid detection_status values.
        """
        from app.ai import ocr_service
        from app.ai.models import OCRResult, OCRTextBlock, ImageQuality

        def mock_extract(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path, engine="paddleocr", engine_version="mock",
                blocks=[OCRTextBlock("MRP Rs 50", "MRP Rs 50", 0.95, [0, 0, 100, 20])],
                full_text="MRP Rs 50",
                processing_time_ms=30, preprocessing_applied=[],
                quality=ImageQuality("GOOD", 200.0, 0.5, []),
            )

        monkeypatch.setattr(ocr_service, "extract", mock_extract)

        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "P", "brand": "B"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]
        client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("t.jpg", io.BytesIO(_make_real_jpeg()), "image/jpeg")},
            headers=auth_headers,
        )
        resp = client.post(f"/api/inspections/{insp_id}/analyze", headers=auth_headers)
        assert resp.status_code == 200

        pi = resp.json()["images"][0]["product_info"]
        assert pi is not None
        valid_statuses = {"DETECTED", "NOT_DETECTED", "UNCERTAIN"}
        for f in pi["fields"]:
            assert f["detection_status"] in valid_statuses

    def test_get_analysis_still_includes_product_info(self, client, auth_headers, upload_dir, monkeypatch):
        """GET /analysis should also return product_info after analysis is done."""
        from app.ai import ocr_service
        from app.ai.models import OCRResult, OCRTextBlock, ImageQuality

        def mock_extract(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path, engine="paddleocr", engine_version="mock",
                blocks=[OCRTextBlock("Net Weight: 200 g", "Net Weight: 200 g", 0.90, [0, 0, 100, 20])],
                full_text="Net Weight: 200 g",
                processing_time_ms=40, preprocessing_applied=[],
                quality=ImageQuality("GOOD", 250.0, 0.6, []),
            )

        monkeypatch.setattr(ocr_service, "extract", mock_extract)

        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "Biscuits", "brand": "Good Day"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]
        client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("t.jpg", io.BytesIO(_make_real_jpeg()), "image/jpeg")},
            headers=auth_headers,
        )
        # Run analysis
        client.post(f"/api/inspections/{insp_id}/analyze", headers=auth_headers)

        # GET analysis — should include product_info
        resp = client.get(f"/api/inspections/{insp_id}/analysis", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        img = data["images"][0]
        assert "product_info" in img
        # net_quantity should be detected
        pi = img["product_info"]
        if pi:
            assert pi["net_quantity"] is not None
            assert "200" in pi["net_quantity"]
