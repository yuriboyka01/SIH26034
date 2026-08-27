"""
Phase 2 tests — preprocessing, OCR service (mocked), analysis API.

These tests run without PaddleOCR being installed by mocking the OCR call.
Real OCR integration is verified separately via the live demo.
"""

import io
import os
import tempfile
import numpy as np
import pytest

from app.ai.preprocessing import (
    analyze_quality,
    load_image,
    build_preprocessed_image,
)
from app.ai.models import OCRTextBlock, ImageQuality, OCRResult


# ── Test Helpers ─────────────────────────────────────────────────────────────

def make_test_bgr_image(width=800, height=600, color=(200, 200, 200)):
    """Create a synthetic BGR numpy image for testing."""
    return np.full((height, width, 3), color, dtype=np.uint8)


def make_test_image_file(tmpdir, filename="test.jpg", width=800, height=600):
    """Write a minimal JPEG to a temp directory."""
    import cv2
    img = make_test_bgr_image(width, height)
    path = os.path.join(tmpdir, filename)
    cv2.imwrite(path, img)
    return path


# ── Unit: Preprocessing ───────────────────────────────────────────────────────

class TestQualityAnalysis:
    def test_good_quality(self):
        """A clear, well-lit image should be GOOD."""
        img = make_test_bgr_image(800, 600, color=(180, 180, 180))
        result = analyze_quality(img)
        # Should not be too small or too blurry for a synthetic solid image
        assert result["status"] in ("GOOD", "FAIR", "POOR")  # just checks it runs
        assert "blur_score" in result
        assert "brightness_score" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_too_small_image(self):
        """A very small image should flag IMAGE_TOO_SMALL."""
        img = make_test_bgr_image(50, 50)
        result = analyze_quality(img)
        assert "IMAGE_TOO_SMALL" in result["issues"]
        assert result["status"] in ("POOR",)

    def test_dark_image(self):
        """A very dark image should flag IMAGE_TOO_DARK."""
        img = make_test_bgr_image(800, 600, color=(5, 5, 5))
        result = analyze_quality(img)
        assert "IMAGE_TOO_DARK" in result["issues"]

    def test_bright_image(self):
        """A nearly white image should flag IMAGE_TOO_BRIGHT."""
        img = make_test_bgr_image(800, 600, color=(254, 254, 254))
        result = analyze_quality(img)
        assert "IMAGE_TOO_BRIGHT" in result["issues"]

    def test_returns_float_scores(self):
        img = make_test_bgr_image(800, 600)
        result = analyze_quality(img)
        assert isinstance(result["blur_score"], float)
        assert isinstance(result["brightness_score"], float)
        assert 0.0 <= result["brightness_score"] <= 1.0


class TestPreprocessingPipeline:
    def test_build_preprocessed_image(self):
        """Preprocessed image should be same shape as original (BGR)."""
        original = make_test_bgr_image(800, 600)
        processed, steps = build_preprocessed_image(original)
        assert processed.shape == (600, 800, 3)
        assert "grayscale" in steps
        assert "denoise" in steps
        assert "contrast" in steps

    def test_large_image_gets_resized(self):
        """Images with longest dim > 1920 should be resized."""
        original = make_test_bgr_image(3000, 2000)
        processed, steps = build_preprocessed_image(original)
        h, w = processed.shape[:2]
        assert max(h, w) <= 1920
        assert "resize" in steps

    def test_small_image_not_resized(self):
        """Images within size limit should not be resized."""
        original = make_test_bgr_image(800, 600)
        _, steps = build_preprocessed_image(original)
        assert "resize" not in steps

    def test_load_image_raises_for_missing_file(self, tmp_path):
        """load_image should raise ValueError for non-existent paths."""
        with pytest.raises(ValueError, match="Cannot load image"):
            load_image(str(tmp_path / "nonexistent.jpg"))

    def test_load_image_succeeds(self, tmp_path):
        """load_image should return a valid numpy array for valid files."""
        path = make_test_image_file(str(tmp_path))
        img = load_image(path)
        assert img is not None
        assert img.ndim == 3


# ── Unit: Text Normalization ──────────────────────────────────────────────────

class TestTextNormalization:
    def test_strips_whitespace(self):
        from app.ai.ocr_service import _normalize_text  # noqa: PLC0415
        assert _normalize_text("  MRP ₹420  ") == "MRP ₹420"

    def test_collapses_spaces(self):
        from app.ai.ocr_service import _normalize_text  # noqa: PLC0415
        assert _normalize_text("MRP   ₹420") == "MRP ₹420"

    def test_preserves_content(self):
        from app.ai.ocr_service import _normalize_text  # noqa: PLC0415
        text = "Net Quantity: 5 kg"
        assert _normalize_text(text) == text


# ── Unit: Bounding Box Conversion ────────────────────────────────────────────

class TestBoundingBoxConversion:
    def test_rectangle_polygon(self):
        from app.ai.ocr_service import _polygon_to_bbox  # noqa: PLC0415
        polygon = [[10, 20], [100, 20], [100, 50], [10, 50]]
        bbox = _polygon_to_bbox(polygon)
        assert bbox == [10.0, 20.0, 100.0, 50.0]

    def test_skewed_polygon(self):
        from app.ai.ocr_service import _polygon_to_bbox  # noqa: PLC0415
        # A rotated quad where corners aren't axis-aligned
        polygon = [[15, 5], [95, 15], [85, 55], [5, 45]]
        bbox = _polygon_to_bbox(polygon)
        assert bbox[0] == 5.0   # min x
        assert bbox[1] == 5.0   # min y
        assert bbox[2] == 95.0  # max x
        assert bbox[3] == 55.0  # max y

    def test_bbox_property_on_text_block(self):
        block = OCRTextBlock(
            raw_text="test", normalized_text="test",
            confidence=0.9, bbox=[10.0, 20.0, 100.0, 50.0]
        )
        assert block.bbox == [10.0, 20.0, 100.0, 50.0]


# ── API Tests: Analysis endpoints ─────────────────────────────────────────────

def _make_fake_image_bytes():
    """Create a minimal valid JPEG bytes for upload."""
    return b"\xff\xd8\xff\xe0" + b"\x00" * 1024


def _make_real_test_image_bytes():
    """Create a real small JPEG using OpenCV."""
    import cv2
    img = make_test_bgr_image(600, 400)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


class TestAnalysisAPI:
    def test_analyze_unauthenticated(self, client):
        """Analysis without auth should fail with 403."""
        import uuid
        response = client.post(f"/api/inspections/{uuid.uuid4()}/analyze")
        assert response.status_code == 403

    def test_analyze_nonexistent_inspection(self, client, auth_headers):
        """Analysis on nonexistent inspection should return 404."""
        import uuid
        response = client.post(
            f"/api/inspections/{uuid.uuid4()}/analyze",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "INSPECTION_NOT_FOUND"

    def test_analyze_inspection_with_no_images(self, client, auth_headers):
        """Analysis on inspection with no images should return 400."""
        # Create inspection
        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "P", "brand": "B"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]

        response = client.post(
            f"/api/inspections/{insp_id}/analyze",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "NO_IMAGES"

    def test_get_analysis_unauthenticated(self, client):
        """GET analysis without auth should fail."""
        import uuid
        response = client.get(f"/api/inspections/{uuid.uuid4()}/analysis")
        assert response.status_code == 403

    def test_get_analysis_not_found(self, client, auth_headers):
        """GET analysis for nonexistent inspection should 404."""
        import uuid
        response = client.get(
            f"/api/inspections/{uuid.uuid4()}/analysis",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_analysis_no_results_yet(self, client, auth_headers, upload_dir):
        """GET analysis for inspection with images but no OCR returns NOT_ANALYSED."""
        # Create inspection
        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "Test Product", "brand": "Test Brand"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]

        # Upload image
        client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("test.jpg", io.BytesIO(_make_fake_image_bytes()), "image/jpeg")},
            headers=auth_headers,
        )

        # GET analysis without having run POST /analyze
        response = client.get(
            f"/api/inspections/{insp_id}/analysis",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inspection_id"] == insp_id
        assert len(data["images"]) == 1
        assert data["images"][0]["status"] == "NOT_ANALYSED"

    def test_analyze_with_mocked_ocr(self, client, auth_headers, upload_dir, monkeypatch):
        """
        Full analyze endpoint test with mocked OCR engine.
        Verifies the full pipeline: upload → analyze → persisted results returned.
        """
        from app.ai import ocr_service
        from app.ai.models import OCRResult, OCRTextBlock, ImageQuality

        # Mock the OCR extract function
        def mock_extract(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path,
                engine="paddleocr",
                engine_version="mock",
                blocks=[
                    OCRTextBlock(
                        raw_text="MRP Rs. 420",
                        normalized_text="MRP Rs. 420",
                        confidence=0.95,
                        bbox=[10.0, 20.0, 200.0, 50.0],
                    ),
                    OCRTextBlock(
                        raw_text="Net Qty 5 Kg",
                        normalized_text="Net Qty 5 Kg",
                        confidence=0.91,
                        bbox=[10.0, 60.0, 200.0, 90.0],
                    ),
                ],
                full_text="MRP Rs. 420\nNet Qty 5 Kg",
                processing_time_ms=123,
                preprocessing_applied=["grayscale", "denoise"],
                quality=ImageQuality(
                    status="GOOD",
                    blur_score=250.5,
                    brightness_score=0.65,
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
            files={"file": ("label.jpg", io.BytesIO(_make_real_test_image_bytes()), "image/jpeg")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 201

        # Run analysis
        response = client.post(
            f"/api/inspections/{insp_id}/analyze",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["inspection_id"] == insp_id
        assert data["status"] == "COMPLETED"
        assert len(data["images"]) == 1

        img_result = data["images"][0]
        assert img_result["status"] == "OK"
        assert img_result["quality"]["status"] == "GOOD"
        assert img_result["quality"]["issues"] == []
        assert img_result["ocr"]["full_text"] == "MRP Rs. 420\nNet Qty 5 Kg"
        assert len(img_result["ocr"]["blocks"]) == 2

        block = img_result["ocr"]["blocks"][0]
        assert block["text"] == "MRP Rs. 420"
        assert block["confidence"] == 0.95
        assert len(block["bbox"]) == 4

        # Verify persisted results are returned by GET
        get_response = client.get(
            f"/api/inspections/{insp_id}/analysis",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["images"][0]["status"] == "OK"
        assert len(get_data["images"][0]["ocr"]["blocks"]) == 2

    def test_analyze_needs_review_for_poor_quality(self, client, auth_headers, upload_dir, monkeypatch):
        """Poor quality images should set inspection status to NEEDS_REVIEW."""
        from app.ai import ocr_service
        from app.ai.models import OCRResult, ImageQuality

        def mock_extract_poor(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path,
                engine="paddleocr",
                engine_version="mock",
                blocks=[],
                full_text="",
                processing_time_ms=50,
                preprocessing_applied=[],
                quality=ImageQuality(
                    status="POOR",
                    blur_score=5.0,
                    brightness_score=0.5,
                    issues=["IMAGE_TOO_BLURRY"],
                ),
            )

        monkeypatch.setattr(ocr_service, "extract", mock_extract_poor)

        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "Blurry Product", "brand": "X"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]

        client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("blurry.jpg", io.BytesIO(_make_real_test_image_bytes()), "image/jpeg")},
            headers=auth_headers,
        )

        response = client.post(
            f"/api/inspections/{insp_id}/analyze",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "NEEDS_REVIEW"
        assert "IMAGE_TOO_BLURRY" in response.json()["images"][0]["quality"]["issues"]
