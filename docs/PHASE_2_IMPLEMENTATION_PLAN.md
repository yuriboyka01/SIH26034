# Phase 2 Implementation Plan

## 1. Current Verified Architecture
The system utilizes a FastAPI backend and a React frontend. The analysis pipeline correctly flows from Image Upload -> PaddleOCR -> Extraction (LLM + Regex) -> Compliance Engine. 

## 2. Current Verified LLM Behavior
The LLM integration is structurally sound and effectively uses Pydantic JSON mode alongside a deterministic evidence-matcher to prevent hallucinations. However, **it is broken at runtime** because it targets `qwen/qwen3.8-27b`, which has been decommissioned by Groq. It currently silently fails and relies entirely on the regex fallback.

## 3. Current Verified Rule Engine
There are exactly **10 rules**. They are exclusively built on presence checks (`PresenceRule`, `ContextualReviewRule`). There is zero semantic, cross-field, or format validation currently implemented. Rule LM007 (Quantity Format) is currently redundant with LM003 (Quantity Presence). Rule LM008 (Readability) is a static placeholder returning REVIEW.

## 4. Problems That Must Be Fixed (Phase A & B)
* **Security [CRITICAL]**: API keys and DB strings are in `.env`. Needs immediate rotation and `.gitignore` enforcement.
* **LLM Model**: Update the Groq model string to an active model (e.g., `llama-3.1-70b-versatile` or `qwen/qwen3.8-27b`).
* **Rule Engine Redundancy**: LM007 must be upgraded to actually perform Regex format validation on the `net_quantity` string (e.g., ensuring standard units like 'g', 'kg', 'ml' are used properly), rather than just checking if the field exists.

## 5. Problems That Should NOT Be Fixed Yet
* **Multi-Image Intelligence**: Merging OCR boxes across multiple images is complex and should be deferred until the single-image category/rule architecture is solidified.
* **Frontend Overhaul**: The UI works for the current pipeline. Defer major UI changes until the new backend rule model is stable.

## 6. Rule Engine Redesign
Evolve the Rule classes into a capability-driven model:
* `FormatValidationRule`: Validates that a detected string matches legal formats (e.g., MRP must be numeric, quantity must have legal units).
* `DateValidationRule`: Ensures Expiry > Mfg Date, and that dates are not in the future (for Mfg) or past (for Expiry).
* `CategoryConditionalRule`: Rules that only execute if the `ProductInfo` matches a specific category.

## 7. Proposed New Rules
| Rule | Requirement | Detection | Priority | Value |
| ---- | ----------- | --------- | -------- | ----- |
| **LM011** | Date Logic | `expiry_date` > `manufacturing_date` | High | Prevents logical contradictions in OCR/LLM. |
| **LM012** | MRP Format | `mrp` is numeric and > 0 | High | Ensures price isn't a junk string. |
| **LM013** | Qty Format | `net_quantity` uses standard SI units | High | Overhauls LM007 into a true format check. |

## 8. Product Category Architecture
Introduce a `ProductCategory` enum (e.g., `FOOD`, `COSMETICS`, `ELECTRONICS`, `GENERIC`). 
* Update the extraction prompt to instruct the LLM to classify the `ProductCategory` based on the OCR text.
* Update `ComplianceRule` base class with `applicable_categories: List[ProductCategory]`.
* Update the engine to filter out rules that do not apply to the extracted category.

## 9. LLM Improvements
* Change model to `qwen/qwen3.8-27b`.
* Inject the `ProductCategory` classification requirement into the prompt.
* Provide the LLM with a brief legal metrology context in the system prompt to improve extraction of edge-case formats.

## 10. Evidence and Confidence Architecture
Modify the engine to aggressively flag `UNCERTAIN` extractions:
* If a field is required (e.g., MRP) but `detection_status == "UNCERTAIN"`, the rule should return `REVIEW` instead of `PASS`, explicitly notifying the user that the OCR evidence was weak.

## 11. Security Hardening
* Delete `.env` from git tracking.
* Provide a script to rotate the JWT secret.
* Enforce RBAC on API endpoints using the existing `UserRole` enum in the database.

## 12. Implementation Order
1. **Phase A (Security)**: Rotate keys, secure `.env`, add RBAC.
2. **Phase B (LLM Reliability)**: Update Groq model, verify LLM runs without fallback, add category classification to prompt.
3. **Phase C (Rule Engine Upgrade)**: Implement `FormatValidationRule`, `DateValidationRule`, overhaul LM007, and add LM011/LM012.
4. **Phase D (Categories)**: Implement category-specific rule filtering based on LLM classification.

> [!WARNING]
> **User Review Required**
> Do you approve this Implementation Plan? Once approved, we will begin execution starting with Phase A (Security) and Phase B (LLM Reliability).
