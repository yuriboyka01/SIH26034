"""
Phase 4: Compliance SQLAlchemy models.

Stores the compliance evaluation results for each image.
"""

import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComplianceReport(Base):
    """
    Persisted compliance report for an inspection image.
    Linked 1:1 with OCRResult (which implies 1 per image).
    """
    __tablename__ = "compliance_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocr_result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ocr_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    overall_status = Column(String(50), nullable=False)  # PASS, FAIL, REVIEW
    
    total_rules_checked = Column(Integer, nullable=False, default=0)
    passed_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    review_count = Column(Integer, nullable=False, default=0)
    not_applicable_count = Column(Integer, nullable=False, default=0)
    
    # Phase 5: Report auditability — version tracking
    engine_version = Column(String(50), nullable=True)
    ruleset_version = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    ocr_result = relationship("OCRResult", back_populates="compliance_report")
    rule_results = relationship("ComplianceRuleResult", back_populates="report", cascade="all, delete-orphan")


class ComplianceRuleResult(Base):
    """
    Individual rule evaluation result.
    """
    __tablename__ = "compliance_rule_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    rule_id = Column(String(50), nullable=False)
    rule_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # PASS, FAIL, REVIEW, NOT_APPLICABLE
    severity = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    field = Column(String(100), nullable=True)
    expected = Column(Text, nullable=False)
    actual = Column(Text, nullable=True)
    source_reference = Column(String(255), nullable=False)
    
    # Evidence JSON payload
    evidence_json = Column(Text, nullable=True)
    
    # Relationships
    report = relationship("ComplianceReport", back_populates="rule_results")

    def get_evidence(self) -> dict:
        if self.evidence_json:
            try:
                return json.loads(self.evidence_json)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def set_evidence(self, evidence: dict) -> None:
        if evidence:
            self.evidence_json = json.dumps(evidence, ensure_ascii=False)
        else:
            self.evidence_json = None
