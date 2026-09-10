"""
Phase 4: Compliance rules definitions and registry.
Contains deterministic logic for checking fields against Legal Metrology Rules 2011.
"""

from typing import List, Optional, Dict, Any
from app.schemas.compliance import ComplianceStatus, RuleSeverity, RuleResultSchema

# We will pass the dictionary version of ProductInfo.fields to these rules
# e.g., [{"field_name": "mrp", "value": "120", "detection_status": "DETECTED", "evidence": {...}}]

class ComplianceRule:
    """Base class for compliance rules."""
    def __init__(self, rule_id: str, rule_name: str, source_reference: str, severity: RuleSeverity, expected: str):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.source_reference = source_reference
        self.severity = severity
        self.expected = expected

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        raise NotImplementedError


class PresenceRule(ComplianceRule):
    """Checks if a field is explicitly detected."""
    def __init__(self, rule_id: str, rule_name: str, source_reference: str, severity: RuleSeverity, expected: str, target_field: str):
        super().__init__(rule_id, rule_name, source_reference, severity, expected)
        self.target_field = target_field

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        # Find the target field
        field_data = next((f for f in extracted_fields if f.get("field_name") == self.target_field), None)
        
        if not field_data:
            # Field completely missing from extracted list (shouldn't happen with full ProductInfo, but safe fallback)
            return self._build_result(ComplianceStatus.FAIL, "Field not found in extraction data.", None, None)

        status = field_data.get("detection_status", "NOT_DETECTED")
        value = field_data.get("value")
        evidence = field_data.get("evidence")

        if status == "DETECTED":
            return self._build_result(ComplianceStatus.PASS, "Required declaration detected.", value, evidence)
        elif status == "UNCERTAIN":
            return self._build_result(ComplianceStatus.REVIEW, "Declaration may be present but certainty is low.", value, evidence)
        else:
            return self._build_result(ComplianceStatus.FAIL, "Required declaration not detected.", value, evidence)

    def _build_result(self, status: ComplianceStatus, message: str, actual: Optional[str], evidence: Optional[Any]) -> RuleResultSchema:
        return RuleResultSchema(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=status,
            severity=self.severity,
            message=message,
            field=self.target_field,
            expected=self.expected,
            actual=actual,
            evidence=evidence,
            source_reference=self.source_reference
        )


class ContextualReviewRule(ComplianceRule):
    """Rule that defaults to REVIEW because automated context (e.g. exemptions) is unknown."""
    def __init__(self, rule_id: str, rule_name: str, source_reference: str, severity: RuleSeverity, expected: str, target_field: str, review_message: str):
        super().__init__(rule_id, rule_name, source_reference, severity, expected)
        self.target_field = target_field
        self.review_message = review_message

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        field_data = next((f for f in extracted_fields if f.get("field_name") == self.target_field), None)
        
        status = field_data.get("detection_status", "NOT_DETECTED") if field_data else "NOT_DETECTED"
        value = field_data.get("value") if field_data else None
        evidence = field_data.get("evidence") if field_data else None

        if status == "DETECTED":
             return RuleResultSchema(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=ComplianceStatus.PASS,
                severity=self.severity,
                message="Declaration detected.",
                field=self.target_field,
                expected=self.expected,
                actual=value,
                evidence=evidence,
                source_reference=self.source_reference
            )
        
        # If not definitively detected, we mark for REVIEW instead of FAIL because of potential exemptions
        return RuleResultSchema(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=ComplianceStatus.REVIEW,
            severity=self.severity,
            message=self.review_message,
            field=self.target_field,
            expected=self.expected,
            actual=value,
            evidence=evidence,
            source_reference=self.source_reference
        )


class AlwaysReviewRule(ComplianceRule):
    """Rule that always returns REVIEW (e.g., visual readability checks requiring human)."""
    def __init__(self, rule_id: str, rule_name: str, source_reference: str, severity: RuleSeverity, expected: str, review_message: str):
        super().__init__(rule_id, rule_name, source_reference, severity, expected)
        self.review_message = review_message

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        return RuleResultSchema(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=ComplianceStatus.REVIEW,
            severity=self.severity,
            message=self.review_message,
            field=None,
            expected=self.expected,
            actual=None,
            evidence=None,
            source_reference=self.source_reference
        )


# --- Rule Registry ---

# LM001: Manufacturer/Packer/Importer
# Not all packages need all three, but they usually need at least manufacturer or packer. 
# We'll use ContextualReviewRule on 'manufacturer'.
rule_lm001 = ContextualReviewRule(
    rule_id="LM001",
    rule_name="Manufacturer / Packer / Importer Declaration",
    source_reference="Rule 6(1)(a), Rule 10",
    severity=RuleSeverity.HIGH,
    expected="Applicable package must carry the relevant identity/address declaration.",
    target_field="manufacturer",
    review_message="Not definitively detected. Review required to check if packer/importer details are present or if exempt."
)

# LM002: Product Name
rule_lm002 = PresenceRule(
    rule_id="LM002",
    rule_name="Common / Generic Commodity Name",
    source_reference="Rule 6(1)(b)",
    severity=RuleSeverity.HIGH,
    expected="Common or generic name of commodity must be declared.",
    target_field="product_name"
)

# LM003: Net Quantity
rule_lm003 = PresenceRule(
    rule_id="LM003",
    rule_name="Net Quantity Declaration",
    source_reference="Rule 6(1)(c), Rules 11, 12, 13",
    severity=RuleSeverity.CRITICAL,
    expected="Applicable package must declare net quantity.",
    target_field="net_quantity"
)

# LM004: Mfg Date
rule_lm004 = ContextualReviewRule(
    rule_id="LM004",
    rule_name="Manufacturing / Pre-Packing Month and Year",
    source_reference="Rule 6(1)(d)",
    severity=RuleSeverity.HIGH,
    expected="Applicable month/year information must be present.",
    target_field="manufacturing_date",
    review_message="Mfg date not detected. Review if product is exempt or if packed/imported date is used."
)

# LM005: MRP
rule_lm005 = PresenceRule(
    rule_id="LM005",
    rule_name="Retail Sale Price / MRP",
    source_reference="Rule 6(1)(e), Rule 2(m)",
    severity=RuleSeverity.CRITICAL,
    expected="Applicable package must declare retail sale price / MRP.",
    target_field="mrp"
)

# LM006: Consumer Care
rule_lm006 = PresenceRule(
    rule_id="LM006",
    rule_name="Consumer Complaint Contact Details",
    source_reference="Rule 6(2)",
    severity=RuleSeverity.HIGH,
    expected="Package must carry consumer complaint contact information.",
    target_field="customer_care"
)

# LM007: Quantity Unit Format
rule_lm007 = ContextualReviewRule(
    rule_id="LM007",
    rule_name="Quantity Unit / Basic Format",
    source_reference="Rule 12, Rule 13",
    severity=RuleSeverity.MEDIUM,
    expected="Quantity declaration should use the applicable unit conventions.",
    target_field="net_quantity",
    review_message="Net quantity might be missing or format cannot be automatically verified against Fourth Schedule."
)

# LM008: Readability
rule_lm008 = AlwaysReviewRule(
    rule_id="LM008",
    rule_name="Declaration Readability / Prominence",
    source_reference="Rule 7, Rule 9",
    severity=RuleSeverity.MEDIUM,
    expected="Declarations must meet requirements for legibility, prominence, size (mm).",
    review_message="Automated pixel-based bounding boxes cannot verify physical millimetre requirements. Human review required."
)

# LM009: Country of Origin
# Mandatory for imported packages (Rule 6) and for e-commerce listings under the
# Consumer Protection (E-Commerce) Rules, 2020. Not every domestically-made,
# non-e-commerce package needs this, so we default to REVIEW rather than FAIL
# when absent — same pattern as LM001/LM004 for fields with legal exemptions.
rule_lm009 = ContextualReviewRule(
    rule_id="LM009",
    rule_name="Country of Origin Declaration",
    source_reference="Rule 6(1), Consumer Protection (E-Commerce) Rules 2020",
    severity=RuleSeverity.HIGH,
    expected="Imported packages / e-commerce listings must declare country of origin.",
    target_field="country_of_origin",
    review_message="Country of origin not detected. Review if this package is domestically manufactured (exempt) or imported/e-commerce (required)."
)

# LM010: License / Registration Number
# Covers FSSAI/BIS/other statutory license numbers commonly printed alongside
# Legal Metrology declarations. Requirement source varies by commodity category
# (FSS Act 2006 for food, BIS Act for ISI-marked goods) rather than the Legal
# Metrology Rules 2011 directly — flagged for REVIEW so a human confirms which
# statute applies to this specific product category before treating it as FAIL.
rule_lm010 = ContextualReviewRule(
    rule_id="LM010",
    rule_name="Statutory License / Registration Number",
    source_reference="Category-specific (e.g. FSSAI under FSS Act 2006, BIS Act) — verify applicable statute",
    severity=RuleSeverity.MEDIUM,
    expected="Applicable license/registration number (e.g. FSSAI, BIS) must be declared if the commodity category requires one.",
    target_field="license_number",
    review_message="License number not detected. Review whether this commodity category requires a statutory license number."
)

REGISTERED_RULES = [
    rule_lm001,
    rule_lm002,
    rule_lm003,
    rule_lm004,
    rule_lm005,
    rule_lm006,
    rule_lm007,
    rule_lm008,
    rule_lm009,
    rule_lm010,
]
