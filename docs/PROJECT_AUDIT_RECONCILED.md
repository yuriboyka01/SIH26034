# PROJECT AUDIT RECONCILED (PHASE 2)

## Confirmed Findings
* **Core Pipeline**: Exists end-to-end. API routes trigger OCR -> Extraction -> Compliance.
* **FastAPI Backend**: Operational and correctly structured.
* **PostgreSQL/SQLAlchemy**: Integrated successfully (Neon DB connection string is present in `.env`).
* **OCR Pipeline**: PaddleOCR integration is present in `app/ai/ocr_service.py`.
* **Groq LLM Integration**: Implemented in `app/ai/extraction.py` via `_extract_with_groq`.
* **Regex Fallback**: Exists and is robust, handling 19 different fields as a fallback pipeline.
* **Compliance Engine**: Operates deterministically over the extracted fields.
* **Security Status**: Critical vulnerabilities exist. Database passwords and Groq API keys are hardcoded in the `.env` file, which is actively tracked in the repository.

## Incorrect Findings
* **Rule Count**: The previous claim of "8 rules" is **FALSE**. There are exactly **10 registered rules** (LM001–LM010).
* **LLM Runtime Status**: While the LLM integration code is technically sound and the API key is valid, **the LLM pipeline is currently BROKEN at runtime**. The model specified (`qwen/qwen3.8-27b`) has been decommissioned by Groq. All runtime extraction currently falls back to regex.
* **Rule Quality**: While 10 rules exist, they do not perform deep validation. They are purely "presence checks". LM007 claims to check quantity format but actually only checks presence (redundantly with LM003).

## Unverified Findings
* **Frontend Integration**: Assumed functional based on previous audit, but not dynamically tested during this verification.
* **Report Generation**: PDF/DOCX generation exists in `report_service.py` but hasn't been stress-tested for visual layout breaks.

## Corrected Rule Count
**VERIFIED RULE COUNT: 10**

| Rule ID | Name | Type | Input | Logic | Output | Meaningful Validation? |
| ------- | ---- | ---- | ----- | ----- | ------ | ---------------------- |
| LM001 | Manufacturer/Packer | Contextual | `manufacturer` | Presence check | PASS/REVIEW | Weak (Presence only) |
| LM002 | Product Name | Presence | `product_name` | Presence check | PASS/FAIL | Weak (Presence only) |
| LM003 | Net Quantity | Presence | `net_quantity` | Presence check | PASS/FAIL | Weak (Presence only) |
| LM004 | Mfg Date | Contextual | `manufacturing_date` | Presence check | PASS/REVIEW | Weak (Presence only) |
| LM005 | MRP | Presence | `mrp` | Presence check | PASS/FAIL | Weak (Presence only) |
| LM006 | Consumer Care | Presence | `customer_care` | Presence check | PASS/FAIL | Weak (Presence only) |
| LM007 | Quantity Format | Contextual | `net_quantity` | Presence check | PASS/REVIEW | **NO** (Redundant with LM003) |
| LM008 | Readability | AlwaysReview | None | Hardcoded | REVIEW | **NO** (Placeholder only) |
| LM009 | Country of Origin | Contextual | `country_of_origin`| Presence check | PASS/REVIEW | Weak (Presence only) |
| LM010 | Statutory License | Contextual | `license_number` | Presence check | PASS/REVIEW | Weak (Presence only) |

## Corrected LLM Status
**BROKEN (At Runtime)**
* **Is the LLM actually called?** Yes, it is the primary extraction method.
* **Conditions to skip:** Missing `groq` module or missing API key.
* **When does regex fallback occur?** When the Groq API throws an error. Currently, this happens 100% of the time because the model `qwen/qwen3.8-27b` is decommissioned, returning a 400 Bad Request.
* **Evidence Matching:** The LLM architecture is excellent at evidence matching. It extracts a value and `source_text`, which is deterministically fuzzy-matched back to the OCR bounding boxes to prevent hallucinations.
* **Hallucination Risks:** Mitigated by the diff-based evidence matcher. If the LLM invents a value, it won't map to a bounding box, resulting in an `UNCERTAIN` detection status.

## Corrected Security Status
**COMPROMISED**
The `.env` file contains production secrets and is visible in the workspace.
* `DATABASE_URL` (Neon PostgreSQL) is exposed.
* `GROQ_API_KEY` is exposed.
* JWT Secret is a dummy value `dev-secret-key-change-in-production-abc123xyz`.
* Rotation is required immediately.
