"""
Phase 4 + Rule Engine v2: Compliance rules definitions and registry.

Contains deterministic logic for checking fields against Legal Metrology
(Packaged Commodities) Rules, 2011.

Design principles (see project brief for the full rationale):
  - Only evaluate what can honestly be checked from OCR + extracted fields.
  - Never turn "we don't know" into FAIL. Missing/ambiguous evidence is
    REVIEW; a genuinely inapplicable rule is NOT_APPLICABLE.
  - Commodity-specific rules only fire when the commodity category can be
    reasonably inferred from the extracted text — otherwise NOT_APPLICABLE.
  - Physical/instrument-based requirements (weighing, sampling, dimension
    measurement) are always REVIEW with an honest explanation; the engine
    never pretends to have verified them from a package photo.
"""

import re
from typing import List, Optional, Dict, Any, Tuple

from app.schemas.compliance import (
    ComplianceStatus,
    RuleSeverity,
    RuleCategory,
    RuleResultSchema,
)

# We will pass the dictionary version of ProductInfo.fields to these rules
# e.g., [{"field_name": "mrp", "value": "120", "detection_status": "DETECTED", "evidence": {...}}]


# ── Field access helpers ──────────────────────────────────────────────────────

def _get_field(extracted_fields: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    return next((f for f in extracted_fields if f.get("field_name") == name), None)


def _field_value(extracted_fields: List[Dict[str, Any]], name: str) -> Optional[str]:
    f = _get_field(extracted_fields, name)
    return f.get("value") if f else None


def _field_status(extracted_fields: List[Dict[str, Any]], name: str) -> str:
    f = _get_field(extracted_fields, name)
    return f.get("detection_status", "NOT_DETECTED") if f else "NOT_DETECTED"


def _field_evidence(extracted_fields: List[Dict[str, Any]], name: str) -> Optional[Any]:
    f = _get_field(extracted_fields, name)
    return f.get("evidence") if f else None


def _commodity_text(extracted_fields: List[Dict[str, Any]]) -> str:
    """Concatenated, lowercased text used for lightweight commodity classification."""
    parts = [
        _field_value(extracted_fields, "commodity"),
        _field_value(extracted_fields, "product_name"),
        _field_value(extracted_fields, "brand_name"),
    ]
    return " ".join(p for p in parts if p).lower()


# ── Quantity parsing ──────────────────────────────────────────────────────────

_UNIT_ALIASES = [
    (r"kilograms?|kgs?", "kg"),
    (r"grams?|gms?", "g"),
    (r"millilitres?|milliliters?|mls?", "ml"),
    (r"litres?|liters?|ltrs?|\bl\b", "l"),
    (r"millimet(?:re|er)s?|mms?", "mm"),
    (r"centimet(?:re|er)s?|cms?", "cm"),
    (r"met(?:re|er)s?|\bm\b", "m"),
    (r"square\s*met(?:re|er)s?|sq\.?\s?m\.?", "sqm"),
    (r"pieces?|pcs?|units?|nos?\.?|\bn\b|\bu\b", "count"),
]
_VALID_SI_UNITS = {"kg", "g", "ml", "l", "mm", "cm", "m", "sqm", "count"}

_QUANTITY_VALUE_RE = re.compile(r"([\d]+(?:[.,]\d+)?)")


def parse_quantity(value: Optional[str]) -> Optional[Tuple[float, str]]:
    """
    Parse a declared quantity string like "500 g", "1.5 kg", "2 pcs" into
    (numeric_value, normalized_unit). Returns None if it cannot be parsed
    with reasonable confidence — callers must treat that as "unknown", not FAIL.
    """
    if not value:
        return None
    text = value.strip().lower()
    num_match = _QUANTITY_VALUE_RE.search(text)
    if not num_match:
        return None
    try:
        num = float(num_match.group(1).replace(",", ""))
    except ValueError:
        return None

    for pattern, normalized in _UNIT_ALIASES:
        if re.search(pattern, text):
            return num, normalized
    return None


def small_package_exemption_band(extracted_fields: List[Dict[str, Any]]) -> str:
    """
    Rule 26(a): packages of 10 g/ml or less are fully exempt from Chapter II
    declarations; packages of 10-20 g/ml are exempt from everything except MRP
    and net quantity. Returns 'FULL', 'PARTIAL', or 'NONE' (NONE also covers
    "cannot tell" — we never guess our way into an exemption).
    """
    raw = _field_value(extracted_fields, "net_quantity")
    parsed = parse_quantity(raw)
    if not parsed:
        return "NONE"
    num, unit = parsed
    if unit == "g" or unit == "ml":
        grams_or_ml = num
    elif unit == "kg" or unit == "l":
        grams_or_ml = num * 1000
    else:
        return "NONE"  # exemption only concerns weight/measure, not length/number
    if grams_or_ml <= 10:
        return "FULL"
    if grams_or_ml <= 20:
        return "PARTIAL"
    return "NONE"


# ── Lightweight commodity classification (Second / Fourth Schedule + Rule 14/16) ──
# Deliberately conservative keyword matching. When nothing matches, callers must
# return NOT_APPLICABLE rather than guessing a category.

_SECOND_SCHEDULE_CATEGORIES: List[Tuple[str, List[str], str]] = [
    ("baby_food", [r"baby food", r"infant food", r"weaning food"],
     "100g/200g/300g steps up to 1kg, then 2kg, 5kg, 10kg (Second Schedule, item 1)"),
    ("biscuits", [r"biscuit"],
     "25g/50g/75g/100g/150g/200g/250g/300g, then multiples of 100g up to 1kg (Second Schedule, item 2)"),
    ("bread", [r"\bbread\b"],
     "100g and thereafter in multiples of 100g (Second Schedule, item 3)"),
    ("cereals_pulses", [r"cereal", r"\bpulses\b", r"\bdal\b"],
     "100g/200g/500g/1kg/2kg/5kg, then multiples of 5kg (Second Schedule, item 6)"),
    ("coffee", [r"\bcoffee\b"],
     "25g/50g/100g/200g/250g/500g/1kg, then multiples of 1kg (Second Schedule, item 7)"),
    ("tea", [r"\btea\b"],
     "25g/50g/100g/125g/250g/500g/1kg, then multiples of 1kg (Second Schedule, item 8)"),
    ("edible_oil", [r"edible oil", r"vanaspati", r"\bghee\b", r"cooking oil", r"sunflower oil", r"mustard oil", r"groundnut oil"],
     "50g-5kg steps (or equivalent ml/l) per Second Schedule, item 10"),
    ("milk_powder", [r"milk powder"],
     "50g/100g/200g/500g/1kg, then multiples of 500g (Second Schedule, item 11)"),
    ("detergent_powder", [r"detergent powder", r"washing powder"],
     "50g-2kg steps, then multiples of 1kg (Second Schedule, item 12)"),
    ("rice_flour", [r"\batta\b", r"\brawa\b", r"\bsuji\b", r"wheat flour", r"rice flour", r"\bflour\b"],
     "100g/200g/500g/1kg/2kg/5kg, then multiples of 5kg (Second Schedule, item 13)"),
    ("salt", [r"\bsalt\b"],
     "Below 50g in multiples of 10g; 50g-5kg steps; then multiples of 5kg (Second Schedule, item 14)"),
    ("soap", [r"\bsoap\b", r"detergent cake", r"detergent bar"],
     "25g-300g steps depending on soap type (Second Schedule, item 15)"),
    ("aerated_drinks", [r"aerated", r"soft drink", r"\bcola\b", r"carbonated"],
     "65ml-5 litre standard sizes (Second Schedule, item 16)"),
    ("mineral_water", [r"mineral water", r"drinking water", r"packaged water"],
     "100ml-5 litre standard sizes (Second Schedule, item 17)"),
    ("cement", [r"\bcement\b"],
     "1/2/5/10/20/25/40(white cement only)/50 kg bags (Second Schedule, item 18)"),
    ("paint", [r"\bpaint\b", r"\bvarnish\b", r"\benamel\b"],
     "50ml-5 litre or 500g-7kg depending on paint type (Second Schedule, item 19)"),
]

_FOURTH_SCHEDULE_UNIT_TYPES: List[Tuple[str, List[str], set, str]] = [
    ("ready_made_garments", [r"garment", r"\bshirt\b", r"\btrouser", r"\bkurta\b", r"\bt-shirt\b", r"\btshirt\b"],
     {"count"}, "Number"),
    ("curd", [r"\bcurd\b", r"\byog[hu]rt\b"], {"g", "kg"}, "Weight"),
    ("ice_cream", [r"ice[\s-]?cream"], {"g", "kg"}, "Weight (amended wef 01.07.2012 from Volume to Weight)"),
    ("aerosol", [r"\baerosol\b"], {"g", "kg"}, "Weight"),
    ("tyres_tubes", [r"\btyre\b", r"\btube\b"], {"count"}, "Number"),
    ("cosmetics", [r"\bcosmetic", r"\bshampoo\b", r"\bperfume\b", r"\blotion\b", r"\bcream\b"],
     {"g", "kg", "ml", "l"}, "Weight or Volume"),
]

_SIZED_TEXTILE_KEYWORDS = [
    r"bed[\s-]?sheet", r"\bsaree\b", r"\bsari\b", r"\btowel\b", r"\bnapkin\b",
    r"pillow[\s-]?cover", r"pillow[\s-]?case", r"table[\s-]?cloth", r"\bdhoti\b",
]

_SHEET_COMMODITY_KEYWORDS = [
    r"\btissue\b", r"toilet paper", r"toilet roll", r"aluminium foil", r"aluminum foil", r"waxed paper",
]


def _match_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def classify_second_schedule(text: str) -> Optional[Tuple[str, str]]:
    for key, patterns, sizes in _SECOND_SCHEDULE_CATEGORIES:
        if _match_any(text, patterns):
            return key, sizes
    return None


def classify_fourth_schedule(text: str) -> Optional[Tuple[str, set, str]]:
    for key, patterns, units, label in _FOURTH_SCHEDULE_UNIT_TYPES:
        if _match_any(text, patterns):
            return key, units, label
    return None


# ── Base rule classes ─────────────────────────────────────────────────────────

class ComplianceRule:
    """Base class for compliance rules."""
    def __init__(self, rule_id: str, rule_name: str, source_reference: str,
                 severity: RuleSeverity, category: RuleCategory, expected: str):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.source_reference = source_reference
        self.severity = severity
        self.category = category
        self.expected = expected

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        raise NotImplementedError

    def _result(self, status: ComplianceStatus, message: str, *, field: Optional[str] = None,
                actual: Optional[str] = None, evidence: Optional[Any] = None,
                confidence: Optional[float] = None, remediation: Optional[str] = None,
                source_reference: Optional[str] = None) -> RuleResultSchema:
        return RuleResultSchema(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=status,
            severity=self.severity,
            category=self.category,
            message=message,
            field=field,
            expected=self.expected,
            actual=actual,
            evidence=evidence,
            source_reference=source_reference or self.source_reference,
            confidence=confidence,
            remediation=remediation if status in (ComplianceStatus.FAIL, ComplianceStatus.REVIEW) else None,
        )


class PresenceRule(ComplianceRule):
    """Checks if a field is explicitly detected. FAIL means the declaration was legally
    required and is genuinely absent from the extraction — not merely low-confidence."""
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected,
                 target_field: str, remediation: Optional[str] = None):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)
        self.target_field = target_field
        self.remediation = remediation or f"Add a clear, legible declaration for {target_field.replace('_', ' ')} on the principal display panel."

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        field_data = _get_field(extracted_fields, self.target_field)
        if not field_data:
            return self._result(ComplianceStatus.FAIL, "Field not found in extraction data.",
                                 field=self.target_field, confidence=0.7, remediation=self.remediation)

        status = field_data.get("detection_status", "NOT_DETECTED")
        value = field_data.get("value")
        evidence = field_data.get("evidence")

        if status == "DETECTED":
            return self._result(ComplianceStatus.PASS, "Required declaration detected.",
                                 field=self.target_field, actual=value, evidence=evidence, confidence=0.95)
        elif status == "UNCERTAIN":
            return self._result(ComplianceStatus.REVIEW, "Declaration may be present but certainty is low.",
                                 field=self.target_field, actual=value, evidence=evidence, confidence=0.5,
                                 remediation="Confirm this declaration manually against the package image; OCR/AI confidence was low.")
        else:
            return self._result(ComplianceStatus.FAIL, "Required declaration not detected.",
                                 field=self.target_field, actual=value, evidence=evidence, confidence=0.85,
                                 remediation=self.remediation)


class ContextualReviewRule(ComplianceRule):
    """Rule that defaults to REVIEW (not FAIL) when absent, because automated context
    (e.g. legal exemptions) cannot be confirmed from OCR alone."""
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected,
                 target_field: str, review_message: str, remediation: Optional[str] = None):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)
        self.target_field = target_field
        self.review_message = review_message
        self.remediation = remediation

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        field_data = _get_field(extracted_fields, self.target_field)
        status = field_data.get("detection_status", "NOT_DETECTED") if field_data else "NOT_DETECTED"
        value = field_data.get("value") if field_data else None
        evidence = field_data.get("evidence") if field_data else None

        if status == "DETECTED":
            return self._result(ComplianceStatus.PASS, "Declaration detected.",
                                 field=self.target_field, actual=value, evidence=evidence, confidence=0.9)

        return self._result(ComplianceStatus.REVIEW, self.review_message,
                             field=self.target_field, actual=value, evidence=evidence, confidence=0.4,
                             remediation=self.remediation or "Manually confirm whether this declaration is required for this specific package, then add it if so.")


class AlwaysReviewRule(ComplianceRule):
    """Rule that always returns REVIEW — used for physical/instrument-based or
    layout requirements that cannot be verified from OCR text alone."""
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected,
                 review_message: str, remediation: Optional[str] = None):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)
        self.review_message = review_message
        self.remediation = remediation

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        return self._result(ComplianceStatus.REVIEW, self.review_message, confidence=0.2,
                             remediation=self.remediation or "Requires manual/physical inspection; cannot be automated from a package photo.")


class PatternRule(ComplianceRule):
    """
    Runs a caller-supplied evaluator function against extracted_fields and expects
    it to return (status, message, actual, remediation). Used for the small set of
    rules that need genuine text-pattern logic (unit checks, prohibited wording, etc.)
    without writing a bespoke class for each one.
    """
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected,
                 evaluator):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)
        self.evaluator = evaluator

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        status, message, field, actual, confidence, remediation = self.evaluator(extracted_fields)
        evidence = _field_evidence(extracted_fields, field) if field else None
        return self._result(status, message, field=field, actual=actual, evidence=evidence,
                             confidence=confidence, remediation=remediation)


class SmallPackageExemptionRule:
    """
    Wraps another rule with the Rule 26(a) small-package exemption.
    - net quantity <= 10 g/ml: wrapped rule is fully exempt (NOT_APPLICABLE).
    - net quantity 10-20 g/ml: wrapped rule is exempt UNLESS `keep_in_partial_band`
      is True (used for the MRP / net-quantity rules the proviso keeps mandatory).
    - otherwise: defers to the wrapped rule unchanged.
    """
    def __init__(self, inner_rule: ComplianceRule, keep_in_partial_band: bool = False):
        self.inner_rule = inner_rule
        self.keep_in_partial_band = keep_in_partial_band
        self.rule_id = inner_rule.rule_id
        self.rule_name = inner_rule.rule_name
        self.source_reference = inner_rule.source_reference
        self.severity = inner_rule.severity
        self.category = inner_rule.category

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        band = small_package_exemption_band(extracted_fields)
        exempt = band == "FULL" or (band == "PARTIAL" and not self.keep_in_partial_band)
        if exempt:
            note = (
                "Declared net quantity is 10 g/ml or less; Rule 26(a) exempts this package from this "
                "declaration requirement entirely."
                if band == "FULL" else
                "Declared net quantity is between 10-20 g/ml; Rule 26(a)'s proviso exempts this declaration "
                "(only MRP and net quantity remain mandatory in this band)."
            )
            return RuleResultSchema(
                rule_id=self.inner_rule.rule_id,
                rule_name=self.inner_rule.rule_name,
                status=ComplianceStatus.NOT_APPLICABLE,
                severity=self.inner_rule.severity,
                category=self.category,
                message=note,
                field=getattr(self.inner_rule, "target_field", None),
                expected=self.inner_rule.expected,
                actual=None,
                evidence=None,
                source_reference="Rule 26(a)",
                confidence=0.6,
                remediation=None,
            )
        return self.inner_rule.evaluate(extracted_fields)


class ConditionalKeywordReviewRule(ComplianceRule):
    """
    Flags REVIEW only when specific keywords appear in a target field's value
    (indicating a special legal condition, e.g. an export marking). Otherwise
    NOT_APPLICABLE — the condition simply doesn't apply to this package.
    """
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected,
                 target_field: str, keywords: List[str], review_message: str,
                 remediation: Optional[str] = None):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)
        self.target_field = target_field
        self.keywords = keywords
        self.review_message = review_message
        self.remediation = remediation

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        value = _field_value(extracted_fields, self.target_field)
        if value and any(kw in value.lower() for kw in self.keywords):
            return self._result(ComplianceStatus.REVIEW, self.review_message,
                                 field=self.target_field, actual=value,
                                 evidence=_field_evidence(extracted_fields, self.target_field),
                                 confidence=0.4, remediation=self.remediation)
        return self._result(ComplianceStatus.NOT_APPLICABLE,
                             "No indication this condition applies to this package.",
                             field=self.target_field, confidence=0.5)


class CommoditySpecificReviewRule(ComplianceRule):
    """
    Second-Schedule standard-package-size awareness check. Only fires when the
    commodity category can be inferred from extracted text; otherwise NOT_APPLICABLE.
    Always REVIEW (not FAIL/PASS) because confirming exact compliance with the
    schedule's stepped sizes — including the "non-standard size" labelling escape
    hatch — needs a human to compare the declared quantity against the schedule.
    """
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        text = _commodity_text(extracted_fields)
        match = classify_second_schedule(text)
        if not match:
            return self._result(ComplianceStatus.NOT_APPLICABLE,
                                 "Product category could not be reliably determined from extracted text; "
                                 "Second Schedule standard-size requirement not evaluated.", confidence=0.5)
        category_key, sizes_text = match
        qty = _field_value(extracted_fields, "net_quantity")
        if not qty:
            return self._result(ComplianceStatus.NOT_APPLICABLE,
                                 f"Detected category '{category_key.replace('_', ' ')}', but net quantity was not "
                                 "extracted — see the Net Quantity Declaration finding instead.", confidence=0.5)
        return self._result(
            ComplianceStatus.REVIEW,
            f"Detected category '{category_key.replace('_', ' ')}'. Standard package sizes: {sizes_text}. "
            f"Verify the declared quantity ({qty}) matches one of these, or that the package carries a "
            "'Not a standard pack size' declaration.",
            field="net_quantity", actual=qty,
            evidence=_field_evidence(extracted_fields, "net_quantity"), confidence=0.45,
            remediation="Confirm the declared quantity is a Second Schedule standard size, or add the "
                        "'Not a standard pack size under the Legal Metrology (Packaged Commodities) Rules, 2011' label.",
        )


class FourthScheduleUnitTypeRule(ComplianceRule):
    """
    Checks that certain Fourth-Schedule commodities (garments by number, curd by
    weight, etc.) use the unit type the schedule mandates. Only fires when both
    the commodity category and a parseable quantity unit are available.
    """
    def __init__(self, rule_id, rule_name, source_reference, severity, category, expected):
        super().__init__(rule_id, rule_name, source_reference, severity, category, expected)

    def evaluate(self, extracted_fields: List[Dict[str, Any]]) -> RuleResultSchema:
        text = _commodity_text(extracted_fields)
        match = classify_fourth_schedule(text)
        if not match:
            return self._result(ComplianceStatus.NOT_APPLICABLE,
                                 "Commodity does not match a known Fourth Schedule exception category.",
                                 confidence=0.5)
        category_key, allowed_units, label = match
        qty_raw = _field_value(extracted_fields, "net_quantity")
        parsed = parse_quantity(qty_raw)
        if not parsed:
            return self._result(ComplianceStatus.REVIEW,
                                 f"Detected category '{category_key.replace('_', ' ')}' (Fourth Schedule requires "
                                 f"declaration by {label}), but the declared unit could not be parsed from "
                                 f"'{qty_raw or 'no value'}'.",
                                 field="net_quantity", actual=qty_raw, confidence=0.4,
                                 remediation=f"Confirm the quantity is declared by {label} as required for this commodity.")
        _, unit = parsed
        if unit in allowed_units:
            return self._result(ComplianceStatus.PASS,
                                 f"Unit matches the Fourth Schedule requirement ({label}) for '{category_key.replace('_', ' ')}'.",
                                 field="net_quantity", actual=qty_raw, confidence=0.75)
        return self._result(ComplianceStatus.FAIL,
                             f"Category '{category_key.replace('_', ' ')}' must be declared by {label} per the "
                             f"Fourth Schedule; detected unit does not match.",
                             field="net_quantity", actual=qty_raw, confidence=0.65,
                             remediation=f"Re-declare the net quantity by {label} as required for this commodity category.")


# ── Pattern-rule evaluators (LM012-LM015) ─────────────────────────────────────

_MISLEADING_WORDS = [r"\bminimum\b", r"not less than", r"\baverage\b", r"\babout\b", r"approx(?:imately)?\.?"]
_NONSTANDARD_COUNT_WORDS = [r"\bdozen\b", r"\bscore\b", r"\bgross\b", r"\bgreat gross\b"]


def _eval_si_unit(fields):
    raw = _field_value(fields, "net_quantity")
    if not raw:
        return ComplianceStatus.NOT_APPLICABLE, "Net quantity not detected; see the Net Quantity Declaration finding.", "net_quantity", None, None, None
    parsed = parse_quantity(raw)
    if not parsed:
        return (ComplianceStatus.REVIEW,
                f"Could not confidently parse a recognized unit from '{raw}'.",
                "net_quantity", raw, 0.35,
                "Confirm the quantity is expressed in a standard SI unit (g, kg, ml, l, cm, m) or N/U for count.")
    _, unit = parsed
    if unit in _VALID_SI_UNITS:
        return ComplianceStatus.PASS, f"Unit '{unit}' is a valid SI/standard unit.", "net_quantity", raw, 0.8, None
    return (ComplianceStatus.FAIL, f"Unit detected in '{raw}' is not a permitted SI unit.",
            "net_quantity", raw, 0.7, "Re-declare the net quantity using SI units (g/kg, ml/l, cm/m) or N/U for count.")


def _eval_misleading_wording(fields):
    raw = _field_value(fields, "net_quantity")
    if not raw:
        return ComplianceStatus.NOT_APPLICABLE, "Net quantity not detected; nothing to check for misleading wording.", "net_quantity", None, None, None
    if any(re.search(p, raw.lower()) for p in _MISLEADING_WORDS):
        return (ComplianceStatus.FAIL, f"Quantity declaration '{raw}' contains a qualifying word that may create a "
                "misleading or inadequate impression of quantity.", "net_quantity", raw, 0.7,
                "Remove qualifying words like 'minimum', 'about', 'approximately' or 'average' from the quantity declaration.")
    return ComplianceStatus.PASS, "No misleading quantity qualifiers detected.", "net_quantity", raw, 0.8, None


def _eval_nonstandard_counts(fields):
    raw = _field_value(fields, "net_quantity")
    if not raw:
        return ComplianceStatus.NOT_APPLICABLE, "Net quantity not detected; nothing to check.", "net_quantity", None, None, None
    if any(re.search(p, raw.lower()) for p in _NONSTANDARD_COUNT_WORDS):
        return (ComplianceStatus.FAIL, f"Quantity declaration '{raw}' uses a prohibited counting unit "
                "(dozen/score/gross).", "net_quantity", raw, 0.75,
                "Replace 'dozen'/'score'/'gross' with the actual number of items (e.g. N/U count).")
    return ComplianceStatus.PASS, "No prohibited counting units (dozen/score/gross) detected.", "net_quantity", raw, 0.8, None


def _eval_when_packed(fields):
    raw = _field_value(fields, "net_quantity")
    if not raw or "when packed" not in raw.lower():
        return ComplianceStatus.NOT_APPLICABLE, "The 'when packed' qualifier is not present; nothing to check.", "net_quantity", raw, None, None
    text = _commodity_text(fields)
    permitted = _match_any(text, [r"\bsoap\b", r"\blotion\b", r"\bcream\b"])
    if permitted:
        return (ComplianceStatus.PASS, "'When packed' qualifier is used on a Third Schedule commodity "
                "(soap/lotion/cream) where it is permitted.", "net_quantity", raw, 0.7, None)
    return (ComplianceStatus.FAIL, "'When packed' qualifier is used, but the commodity does not appear to be "
            "one of the Third Schedule categories (soap, lotion, cream) permitted to use it.",
            "net_quantity", raw, 0.5,
            "Remove the 'when packed' qualifier unless this commodity is a soap, lotion, or cream covered by the Third Schedule.")


# ── Rule Registry ──────────────────────────────────────────────────────────────

# LM001: Manufacturer/Packer/Importer
rule_lm001 = ContextualReviewRule(
    rule_id="LM001",
    rule_name="Manufacturer / Packer / Importer Declaration",
    source_reference="Rule 6(1)(a), Rule 10",
    severity=RuleSeverity.HIGH,
    category=RuleCategory.MANDATORY_DECLARATIONS,
    expected="Applicable package must carry the relevant identity/address declaration.",
    target_field="manufacturer",
    review_message="Not definitively detected. Review required to check if packer/importer details are present or if exempt.",
)

# LM002: Product Name
rule_lm002 = PresenceRule(
    rule_id="LM002",
    rule_name="Common / Generic Commodity Name",
    source_reference="Rule 6(1)(b)",
    severity=RuleSeverity.HIGH,
    category=RuleCategory.MANDATORY_DECLARATIONS,
    expected="Common or generic name of commodity must be declared.",
    target_field="product_name",
)

# LM003: Net Quantity
rule_lm003 = PresenceRule(
    rule_id="LM003",
    rule_name="Net Quantity Declaration",
    source_reference="Rule 6(1)(c), Rules 11, 12, 13",
    severity=RuleSeverity.CRITICAL,
    category=RuleCategory.QUANTITY_UNITS,
    expected="Applicable package must declare net quantity.",
    target_field="net_quantity",
)

# LM004: Mfg Date
rule_lm004 = ContextualReviewRule(
    rule_id="LM004",
    rule_name="Manufacturing / Pre-Packing Month and Year",
    source_reference="Rule 6(1)(d)",
    severity=RuleSeverity.HIGH,
    category=RuleCategory.MANDATORY_DECLARATIONS,
    expected="Applicable month/year information must be present.",
    target_field="manufacturing_date",
    review_message="Mfg date not detected. Review if product is exempt or if packed/imported date is used.",
)

# LM005: MRP
rule_lm005 = PresenceRule(
    rule_id="LM005",
    rule_name="Retail Sale Price / MRP",
    source_reference="Rule 6(1)(e), Rule 2(m)",
    severity=RuleSeverity.CRITICAL,
    category=RuleCategory.PRICING_MRP,
    expected="Applicable package must declare retail sale price / MRP.",
    target_field="mrp",
)

# LM006: Consumer Care
rule_lm006 = PresenceRule(
    rule_id="LM006",
    rule_name="Consumer Complaint Contact Details",
    source_reference="Rule 6(2)",
    severity=RuleSeverity.HIGH,
    category=RuleCategory.MANDATORY_DECLARATIONS,
    expected="Package must carry consumer complaint contact information.",
    target_field="customer_care",
)

# LM007: Quantity Unit Format (legacy, broad-brush — LM012 does the actual pattern check)
rule_lm007 = ContextualReviewRule(
    rule_id="LM007",
    rule_name="Quantity Unit / Basic Format",
    source_reference="Rule 12, Rule 13",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.QUANTITY_UNITS,
    expected="Quantity declaration should use the applicable unit conventions.",
    target_field="net_quantity",
    review_message="Net quantity might be missing or format cannot be automatically verified against Fourth Schedule.",
)

# LM008: Readability
rule_lm008 = AlwaysReviewRule(
    rule_id="LM008",
    rule_name="Declaration Readability / Prominence",
    source_reference="Rule 7, Rule 9",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.PRESENTATION_LABEL,
    expected="Declarations must meet requirements for legibility, prominence, size (mm).",
    review_message="Automated pixel-based bounding boxes cannot verify physical millimetre requirements. Human review required.",
)

# LM009: Country of Origin
rule_lm009 = ContextualReviewRule(
    rule_id="LM009",
    rule_name="Country of Origin Declaration",
    source_reference="Rule 6(1), Consumer Protection (E-Commerce) Rules 2020",
    severity=RuleSeverity.HIGH,
    category=RuleCategory.MANDATORY_DECLARATIONS,
    expected="Imported packages / e-commerce listings must declare country of origin.",
    target_field="country_of_origin",
    review_message="Country of origin not detected. Review if this package is domestically manufactured (exempt) or imported/e-commerce (required).",
)

# LM010: License / Registration Number
rule_lm010 = ContextualReviewRule(
    rule_id="LM010",
    rule_name="Statutory License / Registration Number",
    source_reference="Category-specific (e.g. FSSAI under FSS Act 2006, BIS Act) — verify applicable statute",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.PRODUCT_SPECIFIC,
    expected="Applicable license/registration number (e.g. FSSAI, BIS) must be declared if the commodity category requires one.",
    target_field="license_number",
    review_message="License number not detected. Review whether this commodity category requires a statutory license number.",
)

# LM011: Dimensions for sized commodities (bedsheets, towels, sarees, etc.)
class DimensionDeclarationRule(ComplianceRule):
    def evaluate(self, extracted_fields):
        text = _commodity_text(extracted_fields)
        if not _match_any(text, _SIZED_TEXTILE_KEYWORDS):
            return self._result(ComplianceStatus.NOT_APPLICABLE,
                                 "Commodity does not appear to be a sized textile item (bedsheet, towel, saree, "
                                 "napkin, pillow cover, table cloth, dhoti) covered by Rule 14.", confidence=0.5)
        return self._result(ComplianceStatus.REVIEW,
                             "Commodity appears to be a sized textile item. Rule 14 requires the number and "
                             "finished-size dimensions to be declared; this cannot be verified from extracted "
                             "text fields alone.",
                             confidence=0.3,
                             remediation="Manually confirm the package declares the number of pieces and finished dimensions.")

rule_lm011 = DimensionDeclarationRule(
    rule_id="LM011",
    rule_name="Dimensions Declaration for Sized Commodities",
    source_reference="Rule 6(1)(f), Rule 14",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.PRODUCT_SPECIFIC,
    expected="Number and finished-size dimensions must be declared for bedsheets, towels, sarees, and similar items.",
)

# LM012: SI unit compliance
rule_lm012 = PatternRule(
    rule_id="LM012",
    rule_name="Net Quantity Unit Compliance (SI Units)",
    source_reference="Rule 12(2), Rule 13",
    severity=RuleSeverity.HIGH,
    category=RuleCategory.QUANTITY_UNITS,
    expected="Net quantity must be declared using SI units (g/kg, ml/l, cm/m) or N/U for count.",
    evaluator=_eval_si_unit,
)

# LM013: Misleading quantity wording
rule_lm013 = PatternRule(
    rule_id="LM013",
    rule_name="Misleading Quantity Wording",
    source_reference="Rule 12(6)",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.QUANTITY_UNITS,
    expected="Quantity declaration must not use words like 'minimum', 'about', 'approximately', or 'average'.",
    evaluator=_eval_misleading_wording,
)

# LM014: Non-standard counting units
rule_lm014 = PatternRule(
    rule_id="LM014",
    rule_name="Non-Standard Counting Units Prohibited",
    source_reference="Rule 13(4)",
    severity=RuleSeverity.LOW,
    category=RuleCategory.QUANTITY_UNITS,
    expected="Quantity must not be expressed as dozen, score, gross, or great gross.",
    evaluator=_eval_nonstandard_counts,
)

# LM015: 'When packed' qualifier restriction
rule_lm015 = PatternRule(
    rule_id="LM015",
    rule_name="'When Packed' Qualifier Restriction",
    source_reference="Rule 11(4), Third Schedule",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.QUANTITY_UNITS,
    expected="The 'when packed' qualifier may only be used for soaps, lotions, and creams (Third Schedule).",
    evaluator=_eval_when_packed,
)

# LM016: Declaration language
rule_lm016 = AlwaysReviewRule(
    rule_id="LM016",
    rule_name="Declaration Language (Hindi/English)",
    source_reference="Rule 9(4)",
    severity=RuleSeverity.LOW,
    category=RuleCategory.PRESENTATION_LABEL,
    expected="Declarations must be in Hindi (Devnagri) or English.",
    review_message="Script/language of the printed declarations cannot be reliably determined from structured "
                   "field extraction alone. Human review required.",
)

# LM017: Declaration placement & clear space
rule_lm017 = AlwaysReviewRule(
    rule_id="LM017",
    rule_name="Declaration Placement & Clear Space",
    source_reference="Rule 8",
    severity=RuleSeverity.LOW,
    category=RuleCategory.PRESENTATION_LABEL,
    expected="Quantity declaration must sit on the principal display panel with mandated clear space around it.",
    review_message="Verifying clear-space margins around the quantity declaration requires precise physical "
                   "layout measurement, not just OCR bounding boxes. Human review required.",
)

# LM018: Sticker alteration
rule_lm018 = AlwaysReviewRule(
    rule_id="LM018",
    rule_name="No Unauthorized Sticker Alteration",
    source_reference="Rule 6(3), Rule 6(4)",
    severity=RuleSeverity.LOW,
    category=RuleCategory.CONDITIONAL_ADDITIONAL,
    expected="Declarations may not be altered by stickers, except a compliant MRP-reduction sticker.",
    review_message="Detecting an overlaid sticker (versus the original printed label) requires physical package "
                   "inspection; a single photo cannot confirm this.",
)

# LM019: Maximum permissible error (physical verification)
rule_lm019 = AlwaysReviewRule(
    rule_id="LM019",
    rule_name="Maximum Permissible Error / Net Content Verification",
    source_reference="Rule 22, First Schedule, Sixth Schedule",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.CONDITIONAL_ADDITIONAL,
    expected="Actual package content must fall within the First Schedule's maximum permissible error.",
    review_message="Requires physical weighing/measurement of contents with calibrated instruments per the "
                   "Sixth Schedule procedure. Cannot be verified from a package photo or OCR text.",
)

# LM020: Deceptive package
rule_lm020 = AlwaysReviewRule(
    rule_id="LM020",
    rule_name="Deceptive Package Assessment",
    source_reference="Rule 23",
    severity=RuleSeverity.LOW,
    category=RuleCategory.CONDITIONAL_ADDITIONAL,
    expected="Package dimensions must not create an exaggerated or misleading impression of quantity.",
    review_message="Assessing package/content ratio for deceptive sizing requires physical inspection of the "
                   "actual package, not a 2D label image.",
)

# LM021: Export package sold in India
rule_lm021 = ConditionalKeywordReviewRule(
    rule_id="LM021",
    rule_name="Export Package Domestic Sale Restriction",
    source_reference="Rule 25",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.CONDITIONAL_ADDITIONAL,
    expected="Export packages sold in India must first be re-packed/re-labeled per Chapter II.",
    target_field="sale_restrictions",
    keywords=["export", "not for sale in india", "for sale outside india"],
    review_message="Package text references export/sale restrictions. Confirm this is not an export package "
                   "being sold in India without required re-labeling.",
    remediation="If this is an export package, verify it has been re-packed/re-labeled per Chapter II before domestic sale.",
)

# LM022: Second Schedule standard package size
rule_lm022 = CommoditySpecificReviewRule(
    rule_id="LM022",
    rule_name="Second Schedule Standard Package Quantity",
    source_reference="Rule 5, Second Schedule",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.PRODUCT_SPECIFIC,
    expected="Commodities listed in the Second Schedule must be packed in the specified standard quantities.",
)

# LM023: Fourth Schedule unit-type exceptions
rule_lm023 = FourthScheduleUnitTypeRule(
    rule_id="LM023",
    rule_name="Fourth Schedule Unit-Type Exception",
    source_reference="Rule 12(2), Fourth Schedule",
    severity=RuleSeverity.MEDIUM,
    category=RuleCategory.PRODUCT_SPECIFIC,
    expected="Certain commodities (e.g. garments by number, curd/ice cream by weight) must use the schedule's mandated unit type.",
)

# LM024: Consumer contact completeness (email in addition to phone)
rule_lm024 = ContextualReviewRule(
    rule_id="LM024",
    rule_name="Consumer Contact Completeness (Email)",
    source_reference="Rule 6(2)",
    severity=RuleSeverity.LOW,
    category=RuleCategory.MANDATORY_DECLARATIONS,
    expected="Consumer complaint contact should include an email address, if available.",
    target_field="email",
    review_message="No email address detected alongside the consumer complaint contact. Rule 6(2) only requires "
                   "an email 'if available', so this is informational rather than a hard failure.",
    remediation="If the manufacturer has an email address for consumer complaints, consider adding it.",
)

# ── Rule 26(a) small-package exemption wiring ─────────────────────────────────
# Chapter II (and therefore most of the above declarations) does not apply to
# packages of 10 g/ml or less; only MRP and net quantity survive in the 10-20 g/ml band.
rule_lm001 = SmallPackageExemptionRule(rule_lm001, keep_in_partial_band=False)
rule_lm002 = SmallPackageExemptionRule(rule_lm002, keep_in_partial_band=False)
rule_lm004 = SmallPackageExemptionRule(rule_lm004, keep_in_partial_band=False)
rule_lm006 = SmallPackageExemptionRule(rule_lm006, keep_in_partial_band=False)
rule_lm009 = SmallPackageExemptionRule(rule_lm009, keep_in_partial_band=False)
rule_lm010 = SmallPackageExemptionRule(rule_lm010, keep_in_partial_band=False)
rule_lm003 = SmallPackageExemptionRule(rule_lm003, keep_in_partial_band=True)   # net quantity — stays required 10-20g/ml
rule_lm005 = SmallPackageExemptionRule(rule_lm005, keep_in_partial_band=True)   # MRP — stays required 10-20g/ml


REGISTERED_RULES = [
    rule_lm001, rule_lm002, rule_lm003, rule_lm004, rule_lm005,
    rule_lm006, rule_lm007, rule_lm008, rule_lm009, rule_lm010,
    rule_lm011, rule_lm012, rule_lm013, rule_lm014, rule_lm015,
    rule_lm016, rule_lm017, rule_lm018, rule_lm019, rule_lm020,
    rule_lm021, rule_lm022, rule_lm023, rule_lm024,
]
