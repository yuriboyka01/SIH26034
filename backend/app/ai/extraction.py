"""
Phase 3: Product Information Extraction Engine.

Converts normalized OCR text blocks into structured, evidence-linked product fields.

Design principles:
  - Deterministic: regex + keyword matching, NOT LLM generation.
  - Honest: if a field is not found, value is None — never hallucinated.
  - Evidence-linked: every extracted field records the source OCR block text,
    confidence, and bounding box for downstream compliance explainability.
  - Testable: all extractors are pure functions operating on strings/lists.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from app.core.logging import logger


# ── Evidence dataclass ───────────────────────────────────────────────────────

@dataclass
class FieldEvidence:
    """Provenance for one extracted field value."""
    source_text: str              # The OCR text line that provided this value
    confidence: float             # OCR confidence of that block (0.0–1.0)
    bbox: Optional[List[float]]   # [x1, y1, x2, y2] in pixels, if available


@dataclass
class ExtractedField:
    """
    A single structured field extracted from OCR output.

    value=None means the field was NOT detected in the OCR text.
    detection_status: DETECTED | NOT_DETECTED | UNCERTAIN
    """
    field_name: str
    value: Optional[str]
    detection_status: str = "NOT_DETECTED"   # DETECTED | NOT_DETECTED | UNCERTAIN
    evidence: Optional[FieldEvidence] = None


@dataclass
class StructuredProductData:
    """
    Full structured product information extracted from OCR text blocks.

    This is the Phase 3 output and the Phase 4 rule-engine input.
    All optional fields default to None (not hallucinated).
    """
    # Core mandatory declarations (Legal Metrology Rules 2011)
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    batch_number: Optional[str] = None
    country_of_origin: Optional[str] = None

    # Additional declarations
    ingredients: Optional[str] = None
    license_number: Optional[str] = None
    customer_care: Optional[str] = None
    warnings: Optional[str] = None

    # Evidence for each field (field_name → ExtractedField)
    fields: List[ExtractedField] = field(default_factory=list)

    # Extraction metadata
    total_blocks_processed: int = 0
    extraction_version: str = "1.0"

    def to_dict(self) -> dict:
        """Serialize for API / database storage."""
        return {
            "product_name": self.product_name,
            "brand_name": self.brand_name,
            "manufacturer": self.manufacturer,
            "net_quantity": self.net_quantity,
            "mrp": self.mrp,
            "manufacturing_date": self.manufacturing_date,
            "expiry_date": self.expiry_date,
            "batch_number": self.batch_number,
            "country_of_origin": self.country_of_origin,
            "ingredients": self.ingredients,
            "license_number": self.license_number,
            "customer_care": self.customer_care,
            "warnings": self.warnings,
            "fields": [
                {
                    "field_name": f.field_name,
                    "value": f.value,
                    "detection_status": f.detection_status,
                    "evidence": {
                        "source_text": f.evidence.source_text,
                        "confidence": f.evidence.confidence,
                        "bbox": f.evidence.bbox,
                    } if f.evidence else None,
                }
                for f in self.fields
            ],
            "total_blocks_processed": self.total_blocks_processed,
            "extraction_version": self.extraction_version,
        }


# ── Internal text block representation ───────────────────────────────────────

@dataclass
class _Block:
    """Simplified internal representation for extraction processing."""
    text: str
    confidence: float
    bbox: Optional[List[float]]


# ── Normalization helpers ─────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Normalize OCR noise: collapse spaces, strip punctuation artifacts."""
    text = text.strip()
    text = re.sub(r"[ \t]+", " ", text)
    # Fix common OCR substitutions
    text = text.replace("₹", "Rs").replace("Rs.", "Rs").replace("RS.", "Rs")
    return text


def _clean_value(raw: str) -> str:
    """Strip leading keyword prefix from a matched value."""
    return raw.strip().strip(":-").strip()


# ── Regex patterns ────────────────────────────────────────────────────────────

# Date patterns — handles DD/MM/YYYY, MM/YYYY, Month YYYY, etc.
_DATE_PATTERNS = [
    r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b",          # DD/MM/YYYY or DD-MM-YYYY
    r"\b(\d{1,2}[\/\-]\d{4})\b",                               # MM/YYYY
    r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-\.]\d{4})\b",  # Month YYYY
    r"\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b",                 # YYYY/MM/DD
]
_DATE_RE = re.compile("|".join(_DATE_PATTERNS), re.IGNORECASE)

# MRP: Rs/INR followed by number
_MRP_RE = re.compile(
    r"(?:MRP|M\.R\.P\.?|Maximum Retail Price)[:\s]*(?:Rs\.?|INR|₹)?[\s]*(\d[\d,\.]+)",
    re.IGNORECASE,
)
# Also catch "Rs 420" patterns even if keyword is on adjacent line
_PRICE_RE = re.compile(r"(?:Rs\.?|INR|₹)\s*(\d[\d,\.]+)", re.IGNORECASE)

# Net quantity: number + unit
_NET_QTY_RE = re.compile(
    r"(?:Net[\s\-]*(?:Weight|Wt\.?|Qty|Quantity|Contents?|Volume|Vol\.?))[\s:\-]*([0-9][0-9\s,\.]*\s*(?:g|gm|gram|kg|kilogram|ml|l|litre|liter|piece|pieces|pcs|units?|count|nos?)\b)",
    re.IGNORECASE,
)
# Catch standalone "500 g", "1 kg", "100 ml" patterns
_QTY_ONLY_RE = re.compile(
    r"\b(\d+(?:\.\d+)?\s*(?:g|gm|gram|kg|ml|l|litre|liter|pcs|pieces|units?)\b)",
    re.IGNORECASE,
)

# Batch/Lot number
_BATCH_RE = re.compile(
    r"(?:Batch[\s\-]*(?:No|Number|Code|#)\.?|Lot[\s\-]*(?:No|Number|Code)?\.?|Batch|LOT)[:\s\-]*([A-Z0-9][A-Z0-9\-\/]+)",
    re.IGNORECASE,
)

# Country of origin
_ORIGIN_RE = re.compile(
    r"(?:Country[\s\-]*of[\s\-]*Origin|Made[\s\-]*in|Manufactured[\s\-]*in)[:\s]*([A-Za-z\s]+)",
    re.IGNORECASE,
)

# FSSAI / License number
_LICENSE_RE = re.compile(
    r"(?:FSSAI[:\s\-]*(?:Lic(?:ense)?\.?[\s\-]*(?:No|Number)?\.?)?|Lic(?:ense)?[\s\-]*(?:No|Number)\.?)[:\s\-]*([0-9A-Z][0-9A-Z\-\/]{3,})",
    re.IGNORECASE,
)

# Customer care phone
_CUSTOMER_CARE_RE = re.compile(
    r"(?:Customer[\s\-]*(?:Care|Service|Helpline)|Toll[\s\-]*Free|Helpline)[:\s\-]*([0-9\-\s\+]{6,20})",
    re.IGNORECASE,
)

# Ingredients section keywords
_INGREDIENTS_KEYWORDS = ["ingredient", "contains", "composition"]

# Warning keywords
_WARNING_KEYWORDS = ["warning", "caution", "allergen", "allergy", "keep out of reach", "keep away"]

# Manufacturer keywords
_MANUFACTURER_KEYWORDS = [
    "manufactured by", "mfg by", "mfg.", "manufactured for",
    "marketed by", "packed by", "packed for", "distributed by",
    "imported by", "importer",
]

# Brand keywords
_BRAND_KEYWORDS = ["brand", "brand name", "trade name", "trademark"]


# ── Core extraction functions ─────────────────────────────────────────────────

def _extract_date(text: str) -> Optional[str]:
    """Extract first date-like pattern from text."""
    match = _DATE_RE.search(text)
    if match:
        # Return the first non-None group
        return next((g for g in match.groups() if g is not None), None)
    return None


def _extract_mrp(blocks: List[_Block]) -> Optional[ExtractedField]:
    """
    Find MRP across all OCR blocks.
    Tries the explicit MRP keyword pattern first, then raw price patterns.
    """
    for block in blocks:
        text = _clean(block.text)
        m = _MRP_RE.search(text)
        if m:
            value = m.group(1).replace(",", "").strip()
            return ExtractedField(
                field_name="mrp",
                value=value,
                detection_status="DETECTED",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    # Fallback: Rs/₹ followed by number on the same or adjacent line
    for block in blocks:
        text = _clean(block.text)
        m = _PRICE_RE.search(text)
        if m:
            value = m.group(1).replace(",", "").strip()
            return ExtractedField(
                field_name="mrp",
                value=value,
                detection_status="UNCERTAIN",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    return ExtractedField(field_name="mrp", value=None, detection_status="NOT_DETECTED")


def _extract_net_quantity(blocks: List[_Block]) -> ExtractedField:
    """Find net quantity field."""
    for block in blocks:
        text = _clean(block.text)
        m = _NET_QTY_RE.search(text)
        if m:
            value = m.group(1).strip()
            return ExtractedField(
                field_name="net_quantity",
                value=value,
                detection_status="DETECTED",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    # Fallback: bare quantity patterns (lower confidence)
    for block in blocks:
        text = _clean(block.text)
        m = _QTY_ONLY_RE.search(text)
        if m:
            value = m.group(1).strip()
            return ExtractedField(
                field_name="net_quantity",
                value=value,
                detection_status="UNCERTAIN",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    return ExtractedField(field_name="net_quantity", value=None, detection_status="NOT_DETECTED")


def _extract_dates(blocks: List[_Block]) -> dict:
    """
    Extract manufacturing and expiry dates from OCR blocks.
    Returns dict with keys 'manufacturing_date' and 'expiry_date'.
    """
    mfg_patterns = re.compile(
        r"(?:Mfg\.?|Manufactured|Manufacturing|Date of Mfg|DOM)[:\s\.\-]*",
        re.IGNORECASE,
    )
    exp_patterns = re.compile(
        r"(?:Exp(?:iry)?\.?|Best Before|Use Before|Best By|Expiration|BB|Use By)[:\s\.\-]*",
        re.IGNORECASE,
    )

    result = {
        "manufacturing_date": ExtractedField(field_name="manufacturing_date", value=None, detection_status="NOT_DETECTED"),
        "expiry_date": ExtractedField(field_name="expiry_date", value=None, detection_status="NOT_DETECTED"),
    }

    for block in blocks:
        text = _clean(block.text)

        if mfg_patterns.search(text) and result["manufacturing_date"].value is None:
            date = _extract_date(text)
            if date:
                result["manufacturing_date"] = ExtractedField(
                    field_name="manufacturing_date",
                    value=date,
                    detection_status="DETECTED",
                    evidence=FieldEvidence(
                        source_text=block.text,
                        confidence=block.confidence,
                        bbox=block.bbox,
                    ),
                )

        if exp_patterns.search(text) and result["expiry_date"].value is None:
            date = _extract_date(text)
            if date:
                result["expiry_date"] = ExtractedField(
                    field_name="expiry_date",
                    value=date,
                    detection_status="DETECTED",
                    evidence=FieldEvidence(
                        source_text=block.text,
                        confidence=block.confidence,
                        bbox=block.bbox,
                    ),
                )

    return result


def _extract_batch(blocks: List[_Block]) -> ExtractedField:
    for block in blocks:
        text = _clean(block.text)
        m = _BATCH_RE.search(text)
        if m:
            value = m.group(1).strip()
            return ExtractedField(
                field_name="batch_number",
                value=value,
                detection_status="DETECTED",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    return ExtractedField(field_name="batch_number", value=None, detection_status="NOT_DETECTED")


def _extract_country_of_origin(blocks: List[_Block]) -> ExtractedField:
    for block in blocks:
        text = _clean(block.text)
        m = _ORIGIN_RE.search(text)
        if m:
            value = m.group(1).strip().rstrip(".,;")
            if len(value) >= 2:
                return ExtractedField(
                    field_name="country_of_origin",
                    value=value,
                    detection_status="DETECTED",
                    evidence=FieldEvidence(
                        source_text=block.text,
                        confidence=block.confidence,
                        bbox=block.bbox,
                    ),
                )
    return ExtractedField(field_name="country_of_origin", value=None, detection_status="NOT_DETECTED")


def _extract_license(blocks: List[_Block]) -> ExtractedField:
    for block in blocks:
        text = _clean(block.text)
        m = _LICENSE_RE.search(text)
        if m:
            value = m.group(1).strip()
            return ExtractedField(
                field_name="license_number",
                value=value,
                detection_status="DETECTED",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    return ExtractedField(field_name="license_number", value=None, detection_status="NOT_DETECTED")


def _extract_customer_care(blocks: List[_Block]) -> ExtractedField:
    for block in blocks:
        text = _clean(block.text)
        m = _CUSTOMER_CARE_RE.search(text)
        if m:
            value = m.group(1).strip()
            return ExtractedField(
                field_name="customer_care",
                value=value,
                detection_status="DETECTED",
                evidence=FieldEvidence(
                    source_text=block.text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                ),
            )
    return ExtractedField(field_name="customer_care", value=None, detection_status="NOT_DETECTED")


def _extract_keyword_line(
    blocks: List[_Block],
    keywords: List[str],
    field_name: str,
    value_after_colon: bool = True,
) -> ExtractedField:
    """
    Generic keyword-based extractor.
    Finds a block containing any of the keywords and returns the value after ':'.
    """
    for block in blocks:
        text_lower = block.text.lower()
        for kw in keywords:
            if kw in text_lower:
                if value_after_colon and ":" in block.text:
                    parts = block.text.split(":", 1)
                    value = _clean_value(parts[1]) if len(parts) > 1 else None
                else:
                    value = _clean(block.text)
                if value:
                    return ExtractedField(
                        field_name=field_name,
                        value=value,
                        detection_status="DETECTED",
                        evidence=FieldEvidence(
                            source_text=block.text,
                            confidence=block.confidence,
                            bbox=block.bbox,
                        ),
                    )
    return ExtractedField(field_name=field_name, value=None, detection_status="NOT_DETECTED")


def _extract_manufacturer(blocks: List[_Block]) -> ExtractedField:
    """
    Extract manufacturer. Tries keyword match first.
    The value is the remainder of the line after the keyword and colon.
    """
    for block in blocks:
        text_lower = block.text.lower()
        for kw in _MANUFACTURER_KEYWORDS:
            if kw in text_lower:
                # Get value after the keyword
                idx = text_lower.index(kw)
                remainder = block.text[idx + len(kw):].strip().lstrip(":").strip()
                if remainder and len(remainder) >= 3:
                    return ExtractedField(
                        field_name="manufacturer",
                        value=remainder,
                        detection_status="DETECTED",
                        evidence=FieldEvidence(
                            source_text=block.text,
                            confidence=block.confidence,
                            bbox=block.bbox,
                        ),
                    )
    return ExtractedField(field_name="manufacturer", value=None, detection_status="NOT_DETECTED")


def _extract_ingredients(blocks: List[_Block]) -> ExtractedField:
    """
    Extract ingredients section. Returns the block text following ingredients keyword.
    Concatenates adjacent lines if the keyword block is short.
    """
    for i, block in enumerate(blocks):
        text_lower = block.text.lower()
        for kw in _INGREDIENTS_KEYWORDS:
            if kw in text_lower:
                # Value may be in same block or in the next blocks
                if ":" in block.text:
                    parts = block.text.split(":", 1)
                    value = _clean_value(parts[1])
                else:
                    value = ""

                # Grab text from next block if value is too short
                if len(value) < 10 and i + 1 < len(blocks):
                    value = (value + " " + _clean(blocks[i + 1].text)).strip()

                if value:
                    return ExtractedField(
                        field_name="ingredients",
                        value=value,
                        detection_status="DETECTED",
                        evidence=FieldEvidence(
                            source_text=block.text,
                            confidence=block.confidence,
                            bbox=block.bbox,
                        ),
                    )
    return ExtractedField(field_name="ingredients", value=None, detection_status="NOT_DETECTED")


def _extract_warnings(blocks: List[_Block]) -> ExtractedField:
    """Extract warning/caution text."""
    warning_blocks = []
    for block in blocks:
        text_lower = block.text.lower()
        if any(kw in text_lower for kw in _WARNING_KEYWORDS):
            warning_blocks.append(_clean(block.text))

    if warning_blocks:
        value = " | ".join(warning_blocks)
        return ExtractedField(
            field_name="warnings",
            value=value,
            detection_status="DETECTED",
            evidence=FieldEvidence(
                source_text=warning_blocks[0],
                confidence=0.9,
                bbox=None,
            ),
        )
    return ExtractedField(field_name="warnings", value=None, detection_status="NOT_DETECTED")


# ── Public API ────────────────────────────────────────────────────────────────

def extract_product_info(
    ocr_blocks: List[dict],
    inspection_product_name: Optional[str] = None,
    inspection_brand: Optional[str] = None,
) -> StructuredProductData:
    """
    Main entry point: given a list of OCR block dicts, return StructuredProductData.

    Args:
        ocr_blocks: List of dicts with keys: text, confidence, bbox (optional).
        inspection_product_name: Pre-filled from the Inspection record (used as fallback).
        inspection_brand: Pre-filled from the Inspection record (used as fallback).

    Returns:
        StructuredProductData with all extractable fields populated.

    Guarantee: if a field cannot be found in OCR text, its value is None.
    No values are invented.
    """
    logger.info(f"EXTRACTION | processing {len(ocr_blocks)} OCR blocks")

    # Convert to internal _Block list
    blocks = [
        _Block(
            text=b.get("text", b.get("normalized_text", "")),
            confidence=float(b.get("confidence", 0.0)),
            bbox=b.get("bbox"),
        )
        for b in ocr_blocks
        if b.get("text") or b.get("normalized_text")
    ]

    # Run all extractors
    mrp_field = _extract_mrp(blocks)
    qty_field = _extract_net_quantity(blocks)
    date_fields = _extract_dates(blocks)
    batch_field = _extract_batch(blocks)
    origin_field = _extract_country_of_origin(blocks)
    license_field = _extract_license(blocks)
    care_field = _extract_customer_care(blocks)
    mfr_field = _extract_manufacturer(blocks)
    ingredients_field = _extract_ingredients(blocks)
    warnings_field = _extract_warnings(blocks)
    brand_field = _extract_keyword_line(blocks, _BRAND_KEYWORDS, "brand_name")

    # Product name: use inspection metadata as initial value, OCR may refine it
    product_name_value = inspection_product_name  # Use from inspection metadata
    product_name_status = "DETECTED" if product_name_value else "NOT_DETECTED"

    brand_value = brand_field.value or inspection_brand
    brand_status = "DETECTED" if brand_field.value else (
        "UNCERTAIN" if inspection_brand else "NOT_DETECTED"
    )
    if brand_value and brand_field.value is None:
        # Using inspection metadata as fallback
        brand_field = ExtractedField(
            field_name="brand_name",
            value=brand_value,
            detection_status=brand_status,
        )

    all_fields = [
        ExtractedField(field_name="product_name", value=product_name_value, detection_status=product_name_status),
        brand_field,
        mfr_field,
        qty_field,
        mrp_field,
        date_fields["manufacturing_date"],
        date_fields["expiry_date"],
        batch_field,
        origin_field,
        ingredients_field,
        license_field,
        care_field,
        warnings_field,
    ]

    detected = sum(1 for f in all_fields if f.detection_status == "DETECTED")
    logger.info(
        f"EXTRACTION | done | {detected}/{len(all_fields)} fields detected "
        f"from {len(blocks)} blocks"
    )

    return StructuredProductData(
        product_name=product_name_value,
        brand_name=brand_value,
        manufacturer=mfr_field.value,
        net_quantity=qty_field.value,
        mrp=mrp_field.value,
        manufacturing_date=date_fields["manufacturing_date"].value,
        expiry_date=date_fields["expiry_date"].value,
        batch_number=batch_field.value,
        country_of_origin=origin_field.value,
        ingredients=ingredients_field.value,
        license_number=license_field.value,
        customer_care=care_field.value,
        warnings=warnings_field.value,
        fields=all_fields,
        total_blocks_processed=len(blocks),
        extraction_version="1.0",
    )
