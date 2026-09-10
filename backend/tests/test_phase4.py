"""
Phase 4 tests — compliance rules engine, evaluation, and API.
"""

import io
import pytest

from app.schemas.compliance import ComplianceStatus, RuleSeverity
from app.compliance.rules import PresenceRule, ContextualReviewRule, AlwaysReviewRule
from app.compliance.engine import ComplianceRuleEngine


# ── Unit: Individual Rules ───────────────────────────────────────────────────

class TestComplianceRules:
    
    def test_presence_rule_pass(self):
        rule = PresenceRule("R1", "Test", "Src", RuleSeverity.HIGH, "Expected", "mrp")
        fields = [{"field_name": "mrp", "value": "100", "detection_status": "DETECTED"}]
        res = rule.evaluate(fields)
        assert res.status == ComplianceStatus.PASS
        assert res.actual == "100"

    def test_presence_rule_fail(self):
        rule = PresenceRule("R1", "Test", "Src", RuleSeverity.HIGH, "Expected", "mrp")
        fields = [{"field_name": "mrp", "value": None, "detection_status": "NOT_DETECTED"}]
        res = rule.evaluate(fields)
        assert res.status == ComplianceStatus.FAIL

    def test_presence_rule_uncertain(self):
        rule = PresenceRule("R1", "Test", "Src", RuleSeverity.HIGH, "Expected", "mrp")
        fields = [{"field_name": "mrp", "value": "100", "detection_status": "UNCERTAIN"}]
        res = rule.evaluate(fields)
        assert res.status == ComplianceStatus.REVIEW

    def test_contextual_review_rule_pass(self):
        rule = ContextualReviewRule("R2", "Test", "Src", RuleSeverity.MEDIUM, "Expected", "mfg_date", "Review")
        fields = [{"field_name": "mfg_date", "value": "Jan", "detection_status": "DETECTED"}]
        res = rule.evaluate(fields)
        assert res.status == ComplianceStatus.PASS
        
    def test_contextual_review_rule_missing(self):
        rule = ContextualReviewRule("R2", "Test", "Src", RuleSeverity.MEDIUM, "Expected", "mfg_date", "Review")
        fields = [{"field_name": "mfg_date", "value": None, "detection_status": "NOT_DETECTED"}]
        res = rule.evaluate(fields)
        # Should be REVIEW, not FAIL
        assert res.status == ComplianceStatus.REVIEW

    def test_always_review_rule(self):
        rule = AlwaysReviewRule("R3", "Test", "Src", RuleSeverity.LOW, "Expected", "Review")
        res = rule.evaluate([])
        assert res.status == ComplianceStatus.REVIEW


# ── Unit: Compliance Engine ──────────────────────────────────────────────────

class TestComplianceEngine:

    def test_engine_all_pass(self):
        engine = ComplianceRuleEngine()
        # Mock rules
        engine.rules = [
            PresenceRule("R1", "Test", "Src", RuleSeverity.HIGH, "Expected", "f1"),
            PresenceRule("R2", "Test", "Src", RuleSeverity.MEDIUM, "Expected", "f2"),
        ]
        
        fields = [
            {"field_name": "f1", "value": "v1", "detection_status": "DETECTED"},
            {"field_name": "f2", "value": "v2", "detection_status": "DETECTED"},
        ]
        
        report = engine.evaluate("insp1", "img1", fields)
        
        assert report.overall_status == ComplianceStatus.PASS
        assert report.total_rules_checked == 2
        assert report.passed_count == 2
        assert report.failed_count == 0

    def test_engine_critical_fail(self):
        engine = ComplianceRuleEngine()
        engine.rules = [
            PresenceRule("R1", "Test", "Src", RuleSeverity.CRITICAL, "Expected", "f1"),
        ]
        fields = [{"field_name": "f1", "value": None, "detection_status": "NOT_DETECTED"}]
        
        report = engine.evaluate("insp1", "img1", fields)
        assert report.overall_status == ComplianceStatus.FAIL
        assert report.failed_count == 1

    def test_engine_review(self):
        engine = ComplianceRuleEngine()
        engine.rules = [
            AlwaysReviewRule("R1", "Test", "Src", RuleSeverity.MEDIUM, "Expected", "Rev"),
        ]
        
        report = engine.evaluate("insp1", "img1", [])
        assert report.overall_status == ComplianceStatus.REVIEW
        assert report.review_count == 1


# ── API Tests ────────────────────────────────────────────────────────────────

class TestComplianceAPI:
    
    def _make_real_jpeg(self) -> bytes:
        import numpy as np
        import cv2
        img = np.full((100, 100, 3), 200, dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()

    def test_compliance_unauthenticated(self, client):
        import uuid
        response = client.get(f"/api/inspections/{uuid.uuid4()}/compliance")
        assert response.status_code in (401, 403)

    def test_compliance_not_found(self, client, auth_headers):
        import uuid
        response = client.get(f"/api/inspections/{uuid.uuid4()}/compliance", headers=auth_headers)
        assert response.status_code == 404

    def test_compliance_flow(self, client, auth_headers, monkeypatch):
        # 1. Create inspection
        create_resp = client.post(
            "/api/inspections",
            json={"product_name": "Test", "brand": "Brand"},
            headers=auth_headers,
        )
        insp_id = create_resp.json()["id"]

        # 2. Upload image
        client.post(
            f"/api/inspections/{insp_id}/images",
            files={"file": ("label.jpg", io.BytesIO(self._make_real_jpeg()), "image/jpeg")},
            headers=auth_headers,
        )

        # 3. Mock OCR
        from app.ai import ocr_service
        from app.ai.models import OCRResult, OCRTextBlock, ImageQuality

        def mock_extract(image_path: str) -> OCRResult:
            return OCRResult(
                image_path=image_path, engine="paddleocr", engine_version="mock",
                blocks=[
                    OCRTextBlock("MRP Rs 50", "MRP Rs 50", 0.95, [0, 0, 100, 20]),
                    OCRTextBlock("Net Weight: 200 g", "Net Weight: 200 g", 0.9, [0, 20, 100, 40]),
                    OCRTextBlock("Brand XYZ", "Brand XYZ", 0.9, [0, 40, 100, 60]), # Will extract product_name
                ],
                full_text="MRP Rs 50\\nNet Weight: 200 g\\nBrand XYZ",
                processing_time_ms=50, preprocessing_applied=[],
                quality=ImageQuality("GOOD", 200.0, 0.5, []),
            )

        monkeypatch.setattr(ocr_service, "extract", mock_extract)

        # 4. Analyze (triggers OCR + Phase 3 Extraction)
        analyze_resp = client.post(f"/api/inspections/{insp_id}/analyze", headers=auth_headers)
        assert analyze_resp.status_code == 200

        # 5. Run compliance
        comp_resp = client.post(f"/api/inspections/{insp_id}/compliance", headers=auth_headers)
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        
        assert comp_data["inspection_id"] == insp_id
        # We expect REVIEW or FAIL depending on what was missing (e.g. customer care is missing -> FAIL)
        assert comp_data["overall_status"] in ["FAIL", "REVIEW"]
        
        reports = comp_data["reports"]
        assert len(reports) == 1
        rep = reports[0]
        
        assert rep["total_rules_checked"] == 10
        
        # 6. Retrieve compliance reports
        get_comp_resp = client.get(f"/api/inspections/{insp_id}/compliance", headers=auth_headers)
        assert get_comp_resp.status_code == 200
        get_comp_data = get_comp_resp.json()
        
        assert len(get_comp_data["reports"]) == 1
        assert get_comp_data["overall_status"] == comp_data["overall_status"]
