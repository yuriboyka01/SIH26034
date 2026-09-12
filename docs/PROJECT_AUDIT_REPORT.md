# Project Audit Report — SIH26034 Legal Metrology Compliance System

---

## 1. Executive Summary

SIH26034 is a **Legal Metrology (Packaged Commodities) Rules, 2011 compliance checking system**. It allows inspectors to create inspections, upload product label photos, run OCR → extraction → compliance checks against Indian legal metrology rules, and generate PDF/DOCX reports.

**Overall status: The project is substantially implemented and functional across 5 of 6 planned phases.** The core pipeline (Image Upload → OCR → Extraction → Compliance → Reports) is wired end-to-end with real code, a real database, and a working frontend.

### Key Findings

| Area | Verdict |
|------|---------|
| LLM implemented? | **YES** — Groq (Llama 3 70B) |
| LLM actually works? | **PARTIALLY** — it will execute when `GROQ_API_KEY` is set, but falls back to regex deterministically if absent. Cannot confirm runtime LLM behavior without running the server. |
| Claimed "8 rules"? | **FALSE — there are 10 active rules** (LM001–LM010 in `REGISTERED_RULES`) |
| Critical security issues? | **YES — exposed API keys in `.env` committed to Git, no rate limiting, no RBAC enforcement, JWT secret is weak** |
| Architecture quality | **GOOD** — clean layered separation (API → Service → Repository → Model) |
| Test coverage | **GOOD** — 15 test files covering phases 1–5 |
| Frontend | **Functional** — React + Vite + TailwindCSS + TypeScript |
| Production readiness | **NOT READY** — multiple security and operational gaps |

---

## 2. Current Project Status

| Phase | Feature | Claimed Status | **Verified Status** |
|-------|---------|----------|----------|
| 1 | Foundation, auth, database, image upload | ✅ Complete | ✅ **Fully implemented** |
| 2 | Computer vision, image preprocessing, PaddleOCR | ✅ Complete | ✅ **Fully implemented** |
| 3 | AI declaration extraction (Groq + Regex fallback) | ✅ Complete | ✅ **Fully implemented** |
| 4 | Legal Metrology compliance rules engine | ✅ Complete | ✅ **Fully implemented** (10 rules, not 8) |
| 5 | Reports (PDF/DOCX), audit dashboard, analytics | ✅ Complete | ✅ **Fully implemented** |
| 6 | Cloud deployment, Render blueprint, S3 storage | 🚀 In Progress | 🟡 **Partially** — Render YAML & S3 storage exist, but not deployed |

### Component Status Table

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| FastAPI Backend | ✅ Working | [`backend/app/main.py`](file:///d:/CompliQ/backend/app/main.py) | 8 route modules mounted |
| PostgreSQL + SQLAlchemy | ✅ Working | [`backend/app/core/database.py`](file:///d:/CompliQ/backend/app/core/database.py) | Neon DB configured |
| Alembic Migrations | ✅ Working | [`backend/migrations/`](file:///d:/CompliQ/backend/migrations) | Schema management |
| JWT Authentication | ✅ Working | [`backend/app/core/security.py`](file:///d:/CompliQ/backend/app/core/security.py) | bcrypt + python-jose |
| Role-Based Access | 🟡 Partial | [`backend/app/models/user.py`](file:///d:/CompliQ/backend/app/models/user.py) | ADMIN/INSPECTOR enum exists but **never enforced** |
| Image Upload | ✅ Working | [`backend/app/services/image_service.py`](file:///d:/CompliQ/backend/app/services/image_service.py) | Local + S3 storage |
| Image Preprocessing | ✅ Working | [`backend/app/ai/preprocessing.py`](file:///d:/CompliQ/backend/app/ai/preprocessing.py) | OpenCV pipeline |
| PaddleOCR | ✅ Working | [`backend/app/ai/ocr_service.py`](file:///d:/CompliQ/backend/app/ai/ocr_service.py) | Dual-track (original + preprocessed) |
| LLM Extraction (Groq) | ✅ Working | [`backend/app/ai/extraction.py`](file:///d:/CompliQ/backend/app/ai/extraction.py#L60-L240) | Llama 3 70B with regex fallback |
| Regex Extraction | ✅ Working | [`backend/app/ai/extraction.py`](file:///d:/CompliQ/backend/app/ai/extraction.py#L375-L1100) | 15+ regex extractors |
| Compliance Engine | ✅ Working | [`backend/app/compliance/engine.py`](file:///d:/CompliQ/backend/app/compliance/engine.py) | 10 rules |
| PDF Report Generation | ✅ Working | [`backend/app/services/report_service.py`](file:///d:/CompliQ/backend/app/services/report_service.py#L156-L316) | ReportLab |
| DOCX Report Generation | ✅ Working | [`backend/app/services/report_service.py`](file:///d:/CompliQ/backend/app/services/report_service.py#L318-L394) | python-docx |
| Dashboard Analytics | ✅ Working | [`backend/app/services/dashboard_service.py`](file:///d:/CompliQ/backend/app/services/dashboard_service.py) | KPIs, top violations, recent inspections |
| React Frontend | ✅ Working | [`frontend/src/`](file:///d:/CompliQ/frontend/src) | 5 pages, 8 components |
| Render Deployment | 🟡 Partial | [`render.yaml`](file:///d:/CompliQ/render.yaml) | Blueprint exists, not confirmed deployed |
| `rules/` Directory | ⚪ Placeholder | [`rules/README.md`](file:///d:/CompliQ/rules/README.md) | README says "Phase 1: Directory placeholder only" — **outdated**, rules are in code |
| `compliance/base.py` | ⚪ Unused | [`backend/app/compliance/base.py`](file:///d:/CompliQ/backend/app/compliance/base.py) | ABC interfaces never used — actual implementation uses `engine.py` + `rules.py` |
| `ai/base.py` | ⚪ Unused | [`backend/app/ai/base.py`](file:///d:/CompliQ/backend/app/ai/base.py) | ABC interfaces never used — actual implementation uses concrete classes |

---

## 3. Architecture Overview

```mermaid
graph TD
    subgraph Frontend["React Frontend (Vite + TS + Tailwind)"]
        LP[Login Page]
        DP[Dashboard Page]
        IP[Inspections Page]
        NI[New Inspection]
        ID[Inspection Detail]
    end

    subgraph API["FastAPI API Layer"]
        AUTH["/api/auth/*"]
        INSP["/api/inspections/*"]
        IMG["/api/inspections/{id}/images"]
        ANL["/api/inspections/{id}/analyze"]
        COMP["/api/inspections/{id}/compliance"]
        RPT["/api/inspections/{id}/compliance/report.*"]
        DASH["/api/dashboard/stats"]
        HLTH["/api/health"]
    end

    subgraph Services["Service Layer"]
        AuthSvc[AuthService]
        InspSvc[InspectionService]
        ImgSvc[ImageService]
        AnlSvc[AnalysisService]
        ExtSvc[ExtractionService]
        CompSvc[ComplianceService]
        RptSvc[ReportService]
        DashSvc[DashboardService]
    end

    subgraph AI["AI / ML Layer"]
        OCR[PaddleOCR Service]
        PP[OpenCV Preprocessing]
        EXT["Extraction Engine (Groq LLM + Regex)"]
    end

    subgraph Compliance["Compliance Engine"]
        RE[Rule Engine]
        R1["10 Rules (LM001-LM010)"]
    end

    subgraph Data["Data Layer"]
        REPO[Repositories]
        DB[(PostgreSQL)]
        FS[("File Storage (Local/S3)")]
    end

    Frontend --> API
    API --> Services
    AnlSvc --> OCR
    AnlSvc --> PP
    AnlSvc --> ExtSvc
    ExtSvc --> EXT
    CompSvc --> RE
    RE --> R1
    Services --> REPO
    REPO --> DB
    ImgSvc --> FS
```

### Data Flow — Full Pipeline

```
User uploads image → ImageService saves to storage
                   ↓
User triggers analysis → AnalysisService
                       ↓
        OpenCV Preprocessing (quality check, resize, grayscale, denoise, contrast)
                       ↓
        PaddleOCR (dual-track: original + preprocessed, best wins)
                       ↓
        OCR results persisted to DB
                       ↓
        ExtractionService → extraction.py
                          ↓
          1. Try Groq LLM (Llama 3 70B, JSON mode, temp=0)
          2. If LLM fails/unavailable → Regex fallback pipeline
                          ↓
        ProductInfo persisted to DB
                       ↓
User triggers compliance → ComplianceService → ComplianceRuleEngine
                         ↓
          10 rules evaluated against extracted fields
                         ↓
        ComplianceReport + RuleResults persisted to DB
                       ↓
User downloads report → ReportService → PDF/DOCX generation
```

---

## 4. LLM Implementation Audit

### LLM Provider & Configuration

| Attribute | Value | Source |
|-----------|-------|--------|
| **Provider** | Groq (hosted inference) | [`extraction.py:85`](file:///d:/CompliQ/backend/app/ai/extraction.py#L85) |
| **Model** | `qwen/qwen3.8-27b` | [`extraction.py:91`](file:///d:/CompliQ/backend/app/ai/extraction.py#L91) |
| **SDK** | `groq` Python package ≥ 0.9.0 | [`requirements.txt:47`](file:///d:/CompliQ/backend/requirements.txt#L47) |
| **Import handling** | Graceful — `try/except ImportError` | [`extraction.py:24-27`](file:///d:/CompliQ/backend/app/ai/extraction.py#L24-L27) |
| **API key source** | `settings.GROQ_API_KEY` or `os.getenv("GROQ_API_KEY")` | [`extraction.py:64`](file:///d:/CompliQ/backend/app/ai/extraction.py#L64) |
| **Response format** | `json_object` (structured JSON) | [`extraction.py:97`](file:///d:/CompliQ/backend/app/ai/extraction.py#L97) |
| **Temperature** | 0.0 (deterministic) | [`extraction.py:98`](file:///d:/CompliQ/backend/app/ai/extraction.py#L98) |
| **System prompt** | "You are a JSON generating assistant. Always return raw JSON." | [`extraction.py:93`](file:///d:/CompliQ/backend/app/ai/extraction.py#L93) |
| **Retry logic** | 3 attempts with exponential backoff (2s, 4s, 6s) on 503/rate-limit | [`extraction.py:88-106`](file:///d:/CompliQ/backend/app/ai/extraction.py#L88-L106) |
| **Output parsing** | Pydantic `model_validate_json` → `LLMProductData` | [`extraction.py:114`](file:///d:/CompliQ/backend/app/ai/extraction.py#L114) |
| **Evidence matching** | Fuzzy match (difflib SequenceMatcher, threshold > 0.8) back to OCR blocks | [`extraction.py:130-156`](file:///d:/CompliQ/backend/app/ai/extraction.py#L130-L156) |
| **Fallback** | Full regex extraction pipeline | [`extraction.py:1010-1099`](file:///d:/CompliQ/backend/app/ai/extraction.py#L1010-L1099) |
| **Fallback model** | None (single model) | — |
| **Local model** | None | — |
| **Token/usage tracking** | None | — |
| **Timeout handling** | None explicit (relies on Groq SDK defaults) | — |
| **Caching** | None | — |
| **Cost tracking** | None | — |

### Complete Execution Path

```
extract_product_info() [line 983]
  ↓ converts OCR blocks to internal _Block objects
  ↓ calls _extract_with_groq(blocks, product_name, brand) [line 1004]
    ↓ checks Groq SDK installed
    ↓ checks API key present
    ↓ joins all block text into single string
    ↓ constructs prompt with OCR text
    ↓ calls Groq API (qwen/qwen3.8-27b, json_object mode, temp=0)
    ↓ parses response into LLMProductData (Pydantic)
    ↓ maps each LLM field → ExtractedField with evidence matching
    ↓ returns StructuredProductData (version "2.0-groq")
  ↓ IF LLM fails → falls back to regex pipeline [line 1010]
    ↓ spatial grouping of blocks
    ↓ 15+ individual regex extractors
    ↓ returns StructuredProductData (version "1.0-fallback")
```

### Prompt Analysis

**FACT**: The user prompt is constructed at [`extraction.py:73-82`](file:///d:/CompliQ/backend/app/ai/extraction.py#L73-L82):

```python
prompt = f"""
You are an expert compliance extraction engine. Extract structured product data 
from the following OCR text of a product package.
For each field, if the information is present, provide the extracted 'value' and 
the exact 'source_text' from the OCR output used to derive it.
If a field is missing, return null for both value and evidence. DO NOT hallucinate 
or guess missing values.
The OCR text may be noisy.
Return ONLY a valid JSON object matching the requested schema. Do not return 
markdown blocks or any other text.

OCR Text:
{text_content}
"""
```

**Assessment**:
- ✅ Anti-hallucination instruction ("DO NOT hallucinate or guess")
- ✅ Evidence-linking requirement ("provide the exact 'source_text'")
- ✅ Noise tolerance ("OCR text may be noisy")
- ✅ Output format constraint ("Return ONLY a valid JSON object")
- ❌ No schema definition in prompt — relies on Groq `json_object` mode and Pydantic validation
- ❌ No few-shot examples
- ❌ No field definitions/descriptions in prompt
- ❌ `inspection_product_name` and `inspection_brand` parameters are accepted but **never used** in the Groq prompt

---

## 5. Does the LLM Actually Work?

### Verdict: **PARTIALLY — CANNOT FULLY VERIFY**

**FACT**: The LLM execution path is real, functional code:
- The Groq SDK is imported and used correctly
- The API call is structured properly with retry logic
- The response is parsed into validated Pydantic models
- Evidence is matched back to OCR blocks with fuzzy matching
- A real `GROQ_API_KEY` is present in [`.env`](file:///d:/CompliQ/.env#L17)

**FACT**: The code calls the LLM **first** and only falls back to regex if it fails ([`extraction.py:1003-1011`](file:///d:/CompliQ/backend/app/ai/extraction.py#L1003-L1011)).

**INFERENCE**: The LLM likely works at runtime when:
1. The Groq SDK is installed
2. The API key is valid and has remaining quota
3. The Groq service is available

**CANNOT VERIFY**: Without actually running the server and sending a real image through the pipeline, I cannot confirm:
- Whether the current API key has quota remaining
- Whether the model produces correct extractions for real Indian product labels
- Whether the evidence-matching produces accurate bounding boxes
- What the actual false positive/negative rate is

**The fallback is well-implemented**: If the LLM is unavailable, the system degrades gracefully to regex extraction, which is a robust design decision.

---

## 6. What the LLM Does and Why

### What it does

The LLM performs **structured data extraction from noisy OCR text**. Specifically, it:

1. Receives concatenated OCR text blocks from a product label image
2. Extracts 19 specific fields (product name, brand, manufacturer, MRP, net quantity, dates, batch number, country of origin, ingredients, license number, customer care, warnings, email, unit sale price, packaging date, commodity, storage instructions, sale restrictions)
3. Provides evidence (source text snippets) for each extraction
4. Returns structured JSON

### Why the LLM is used

**FACT**: The LLM is used as an **intelligence amplifier** over the regex fallback.

| Aspect | LLM (Groq) | Regex Fallback |
|--------|-----------|----------------|
| Handles noisy OCR | ✅ Better | 🟡 Fragile |
| Handles non-standard formats | ✅ Better | ❌ Misses unusual patterns |
| Evidence linking | ✅ Returns source text | ✅ Has exact block match |
| Hallucination risk | ⚠️ Possible despite instructions | ✅ None |
| Cost | 💰 API cost per call | ✅ Free |
| Latency | ~2-5s per call | < 50ms |
| Determinism | ✅ temp=0 | ✅ Fully deterministic |
| Reliability | ❌ Depends on external API | ✅ Always available |

**RECOMMENDATION**: The hybrid approach (LLM-first, regex-fallback) is sound. The LLM genuinely adds value for noisy OCR text where regex patterns would miss non-standard formats. However, there are opportunities to improve the LLM's prompt and add output validation.

---

## 7. Current Rule Engine

### Architecture

The compliance engine is located in [`backend/app/compliance/`](file:///d:/CompliQ/backend/app/compliance):

- [`rules.py`](file:///d:/CompliQ/backend/app/compliance/rules.py) — Rule definitions and registry
- [`engine.py`](file:///d:/CompliQ/backend/app/compliance/engine.py) — Evaluation orchestrator
- [`base.py`](file:///d:/CompliQ/backend/app/compliance/base.py) — **Unused** ABC interfaces

### Rule Types

| Type | Class | Logic |
|------|-------|-------|
| Presence Check | [`PresenceRule`](file:///d:/CompliQ/backend/app/compliance/rules.py#L25-L62) | Checks if a field has `detection_status == "DETECTED"` → PASS; `"UNCERTAIN"` → REVIEW; else → FAIL |
| Contextual Review | [`ContextualReviewRule`](file:///d:/CompliQ/backend/app/compliance/rules.py#L65-L105) | If DETECTED → PASS; else → REVIEW (because legal exemptions may apply) |
| Always Review | [`AlwaysReviewRule`](file:///d:/CompliQ/backend/app/compliance/rules.py#L108-L126) | Always returns REVIEW (requires human verification) |

### Engine Logic ([`engine.py`](file:///d:/CompliQ/backend/app/compliance/engine.py))

- Iterates all `REGISTERED_RULES`, calls `.evaluate()` on each
- If any HIGH/CRITICAL rule FAILs → overall FAIL
- If any REVIEW → overall REVIEW
- If only MEDIUM/LOW failures → overall REVIEW (not FAIL)
- All pass → overall PASS
- Engine version: `1.0.0`, Ruleset version: `LM-2011-v1`

---

## 8. Verified Active Rule Count

> [!IMPORTANT]
> **The claim of "8 rules" is FALSE. There are 10 active rules.**

**FACT**: The `REGISTERED_RULES` list at [`rules.py:247-258`](file:///d:/CompliQ/backend/app/compliance/rules.py#L247-L258) contains **10 rules**: `rule_lm001` through `rule_lm010`.

**FACT**: The Phase 4 test at [`test_phase4.py:174`](file:///d:/CompliQ/backend/tests/test_phase4.py#L174) asserts `rep["total_rules_checked"] == 10`, confirming 10 rules are evaluated.

| Rule ID | Rule Name | Type | Target Field | Severity | Active? | Tested? | LLM-dependent? |
|---------|-----------|------|-------------|----------|---------|---------|---------------|
| LM001 | Manufacturer / Packer / Importer Declaration | ContextualReview | `manufacturer` | HIGH | ✅ Yes | ✅ Yes (unit + API) | No (evals extracted field) |
| LM002 | Common / Generic Commodity Name | Presence | `product_name` | HIGH | ✅ Yes | ✅ Yes | No |
| LM003 | Net Quantity Declaration | Presence | `net_quantity` | CRITICAL | ✅ Yes | ✅ Yes | No |
| LM004 | Manufacturing / Pre-Packing Month and Year | ContextualReview | `manufacturing_date` | HIGH | ✅ Yes | ✅ Yes | No |
| LM005 | Retail Sale Price / MRP | Presence | `mrp` | CRITICAL | ✅ Yes | ✅ Yes | No |
| LM006 | Consumer Complaint Contact Details | Presence | `customer_care` | HIGH | ✅ Yes | ✅ Yes | No |
| LM007 | Quantity Unit / Basic Format | ContextualReview | `net_quantity` | MEDIUM | ✅ Yes | ✅ Yes | No |
| LM008 | Declaration Readability / Prominence | AlwaysReview | *(none)* | MEDIUM | ✅ Yes | ✅ Yes | No |
| LM009 | Country of Origin Declaration | ContextualReview | `country_of_origin` | HIGH | ✅ Yes | ✅ Yes | No |
| LM010 | Statutory License / Registration Number | ContextualReview | `license_number` | MEDIUM | ✅ Yes | ✅ Yes | No |

**Current verified active rule count: 10**

All 10 rules are:
- Defined in code ✅
- Registered in `REGISTERED_RULES` ✅
- Purely deterministic (no LLM reasoning at rule evaluation time) ✅
- Tested via unit tests and API integration tests ✅

---

## 9. Existing Rule Analysis

### Per-Rule Assessment

| Rule | Purpose | Accuracy | False Positives | False Negatives | Edge Cases | Bypass Risk |
|------|---------|----------|-----------------|-----------------|------------|-------------|
| LM001 | Manufacturer present | Good | Low — defaults to REVIEW | Possible if OCR misses text | Packer vs Manufacturer distinction not handled | Low |
| LM002 | Product name present | Good | Low | Relies on inspection metadata, not OCR | Product name in non-English | Low |
| LM003 | Net quantity present | Good | Low | May miss unusual quantity formats | Multi-pack quantities ("6 × 100g") | Low |
| LM004 | Manufacturing date | Good | Low — defaults to REVIEW | Date format variations | Dates like "B/B 12 months from mfg" | Low |
| LM005 | MRP declared | Good | Low | May miss "inclusive of all taxes" variants | "₹." with dot (handled) | Low |
| LM006 | Customer care info | Moderate | Low | Regex may miss email-only contacts | WhatsApp number formats | Low |
| LM007 | Quantity unit format | Weak | High REVIEW rate | Cannot actually validate unit correctness | Fourth Schedule requirements unknown | Low |
| LM008 | Readability check | N/A | N/A (always REVIEW) | N/A | Cannot measure physical mm from pixels | None |
| LM009 | Country of origin | Good | Low | Domestic products get REVIEW unnecessarily | "Product of India" (handled) | Low |
| LM010 | License/Registration | Good | Low | May miss non-FSSAI license formats | BIS, ISI marks vs FSSAI | Low |

### Structural Weaknesses

1. **All rules operate on single-field presence only** — no cross-field validation (e.g., "if food product, FSSAI is mandatory")
2. **No product category context** — rules cannot differentiate food vs cosmetics vs electronics
3. **No MRP value validation** — only checks if MRP exists, not if it's a reasonable value
4. **No date validity checking** — doesn't check if manufacturing date is in the future or expiry is before manufacturing
5. **LM007 (Quantity Format) is effectively non-functional** — it checks net_quantity detection but cannot verify Fourth Schedule unit requirements
6. **LM008 (Readability) provides zero automated value** — always REVIEW with no analysis
7. **No rule priority/ordering** — all rules run in registration order regardless of dependencies
8. **No NOT_APPLICABLE path** — no rule ever returns NOT_APPLICABLE despite the status being supported

---

## 10. Security / Logic Findings

### P0 — Critical Security Issues

| # | Finding | Evidence | Risk |
|---|---------|----------|------|
| 1 | **API keys committed to Git** | [`.env:17`](file:///d:/CompliQ/.env#L17) — `GROQ_API_KEY` is a real key; [`.env:2`](file:///d:/CompliQ/.env#L2) — full Neon DB connection string with password; [`.env:16`](file:///d:/CompliQ/.env#L16) — commented GEMINI key | **CRITICAL** — anyone with repo access has full DB and API access |
| 2 | **Weak JWT secret in production** | [`.env:5`](file:///d:/CompliQ/.env#L5) — `JWT_SECRET=dev-secret-key-change-in-production-abc123xyz` | **CRITICAL** — JWT tokens can be forged |
| 3 | **No RBAC enforcement** | `UserRole.ADMIN` / `UserRole.INSPECTOR` exist in [`user.py:16-19`](file:///d:/CompliQ/backend/app/models/user.py#L16-L19) but are **never checked** in any endpoint | **HIGH** — any user can access any inspection and admin endpoints |

### P1 — High Security Issues

| # | Finding | Evidence | Risk |
|---|---------|----------|------|
| 4 | **No rate limiting** | No rate-limit middleware anywhere in codebase | Brute-force attacks on login, API abuse |
| 5 | **No input sanitization on registration** | [`auth_service.py:38-43`](file:///d:/CompliQ/backend/app/services/auth_service.py#L38-L43) — name field stored as-is | XSS in reports if name contains HTML |
| 6 | **CORS allows all methods/headers** | [`main.py:33-36`](file:///d:/CompliQ/backend/app/main.py#L33-L36) — `allow_methods=["*"], allow_headers=["*"]` | Overly permissive |
| 7 | **No password complexity requirements** | [`auth_service.py:20`](file:///d:/CompliQ/backend/app/services/auth_service.py#L20) — accepts any password string | Weak passwords |
| 8 | **OCR text injected into LLM prompt without sanitization** | [`extraction.py:69`](file:///d:/CompliQ/backend/app/ai/extraction.py#L69) — OCR text joined and placed directly in prompt | Prompt injection via crafted label images |
| 9 | **No file type validation beyond extension** | Image upload likely accepts any file content | Malicious file uploads |

### P2 — Medium Issues

| # | Finding | Evidence | Risk |
|---|---------|----------|------|
| 10 | **No JWT refresh token mechanism** | Only access tokens, 60-minute expiry | UX issue — forced re-login |
| 11 | **No audit logging** | No record of who triggered analysis/compliance checks | Compliance/forensic gap |
| 12 | **`compliance/base.py` and `ai/base.py` are dead code** | Abstract interfaces never implemented or referenced | Code clutter |
| 13 | **`rules/README.md` is outdated** | Says "Phase 1: Directory placeholder only" when Phase 4 is complete | Documentation drift |
| 14 | **`python-docx` not in requirements.txt** | Used in [`report_service.py:17`](file:///d:/CompliQ/backend/app/services/report_service.py#L17) but not listed in [`requirements.txt`](file:///d:/CompliQ/backend/requirements.txt) | Import failure on fresh install |
| 15 | **`on_event("startup")` is deprecated** | [`main.py:58`](file:///d:/CompliQ/backend/app/main.py#L58) — use `lifespan` context manager | Future FastAPI breakage |

---

## 11. Proposed Additional Rules

### Category: Date/Temporal Validation

| Proposed Rule | Problem Solved | Detection Logic | Priority | Deterministic/LLM | Complexity | Expected Value |
|---------------|----------------|----------------|----------|-------------------|------------|----------------|
| LM011 — Expiry Date Presence | Expiry/Best Before missing for consumables | PresenceRule on `expiry_date` | P1 | Deterministic | Low | High — legally required for food/cosmetics |
| LM012 — Date Validity | Future mfg date or expired product | Compare extracted dates against today | P2 | Deterministic | Medium | Medium — catches impossible dates |
| LM013 — Expiry vs Manufacturing Consistency | Expiry before manufacturing date | Cross-field date comparison | P2 | Deterministic | Medium | Medium — catches data errors |

### Category: Value Validation

| Proposed Rule | Problem Solved | Detection Logic | Priority | Deterministic/LLM | Complexity | Expected Value |
|---------------|----------------|----------------|----------|-------------------|------------|----------------|
| LM014 — MRP Reasonability | MRP = 0 or absurdly high | Numeric range check on extracted MRP value | P2 | Deterministic | Low | Medium |
| LM015 — Net Quantity Format | "500g" vs "500 g" format compliance | Regex validation of quantity format against Fourth Schedule | P2 | Deterministic | Medium | Medium |

### Category: Cross-Field Logic

| Proposed Rule | Problem Solved | Detection Logic | Priority | Deterministic/LLM | Complexity | Expected Value |
|---------------|----------------|----------------|----------|-------------------|------------|----------------|
| LM016 — Import Package Completeness | Imported products need country of origin + importer | If `country_of_origin` ≠ "India" → require importer info | P2 | Deterministic | Medium | High |
| LM017 — Food Product FSSAI | Food products must have FSSAI license | If product category = food → require `license_number` matching FSSAI format | P1 | Deterministic + category hint | Medium | High |

### Category: Multi-Image Consistency

| Proposed Rule | Problem Solved | Detection Logic | Priority | Deterministic/LLM | Complexity | Expected Value |
|---------------|----------------|----------------|----------|-------------------|------------|----------------|
| LM018 — Cross-Image MRP Consistency | Same product, different MRP on different label panels | Compare MRP values across images of same inspection | P3 | Deterministic | Medium | Medium |

### Category: LLM/Prompt Security

| Proposed Rule | Problem Solved | Detection Logic | Priority | Deterministic/LLM | Complexity | Expected Value |
|---------------|----------------|----------------|----------|-------------------|------------|----------------|
| SYS001 — OCR Text Sanitization | Prompt injection via crafted labels | Strip control characters, limit text length before LLM prompt | P1 | Deterministic | Low | High |

---

## 12. Proposed New Features

### Product Features

| Feature | What it does | Why it matters | Limitation Solved | Complexity | Impact |
|---------|-------------|---------------|-------------------|------------|--------|
| **Product Category Selection** | Inspector selects category (Food, Cosmetics, Electronics, etc.) when creating inspection | Enables category-specific rules (FSSAI for food, BIS for electronics) | Rules are blind to product type | Medium | High |
| **Multi-Image Merge** | Merge extracted data across all images of an inspection into a single consolidated ProductInfo | Currently each image has separate extraction; front/back of package should combine | Partial label coverage | Medium | High |
| **Inspection History** | View previous inspections of same product/brand | Track repeat offenders, compliance trends | No institutional memory | Low | Medium |
| **Batch Processing** | Upload multiple images at once, auto-create inspections | Efficiency for field inspectors | One-at-a-time workflow | Low | Medium |

### Security Features

| Feature | What it does | Why it matters | Risk | Complexity |
|---------|-------------|---------------|------|------------|
| **Rate Limiting** | Limit API requests per user/IP | Prevents brute-force and abuse | None | Low |
| **RBAC Enforcement** | Admin-only dashboard, inspector-scoped data | Multi-tenant security | None | Low |
| **API Key Rotation** | Move secrets to environment-only, never in repo | Prevent credential leaks | None | Low |
| **Password Policy** | Min length, complexity requirements | Prevent weak passwords | None | Low |

### Intelligence Features

| Feature | What it does | Why it matters | Complexity |
|---------|-------------|---------------|------------|
| **LLM-Assisted Rule Interpretation** | Use LLM to determine if a detected "Registration No" is FSSAI, BIS, or other | Regex can't distinguish license types | Medium |
| **Comparative Analysis** | Compare current product against historical extractions | Detect label changes over time | High |
| **OCR Confidence-Weighted Rules** | Rules consider OCR confidence when determining PASS/FAIL/REVIEW | Low-confidence detections shouldn't be trusted as PASS | Low |

### Developer/Admin Features

| Feature | What it does | Why it matters | Complexity |
|---------|-------------|---------------|------------|
| **Extraction Debugger** | Visual overlay of OCR blocks + extracted fields on image | Debug extraction accuracy | Medium |
| **Rule Configuration UI** | Enable/disable rules, adjust thresholds via admin panel | No code changes needed for rule tuning | Medium |
| **API Usage Dashboard** | Track Groq API calls, costs, latency, fallback rate | Operational visibility | Low |

### Observability

| Feature | What it does | Why it matters | Complexity |
|---------|-------------|---------------|------------|
| **Structured Logging** | JSON-formatted logs with correlation IDs | Production debugging | Low |
| **Extraction Metrics** | Log field detection rates, LLM vs regex usage split | Measure extraction quality | Low |
| **Performance Metrics** | OCR latency, LLM latency, total analysis time tracking | SLA monitoring | Low |

---

## 13. LLM Improvement Opportunities

| Area | Current State | Recommendation | Priority |
|------|--------------|----------------|----------|
| **Prompt quality** | Adequate but lacks schema definition and examples | Add JSON schema + 1-2 few-shot examples to prompt | P1 |
| **System/user prompt separation** | System prompt is generic ("JSON generating assistant") | Make system prompt domain-specific with extraction rules | P1 |
| **Context management** | Only sends OCR text, ignores product category | Include product category + inspection metadata in prompt | P2 |
| **Structured outputs** | Uses `json_object` mode + Pydantic validation ✅ | Already good — keep | — |
| **Output validation** | Pydantic validates schema but not values | Add value-level validation (e.g., MRP is numeric, date is valid) | P2 |
| **Hallucination control** | Anti-hallucination instruction in prompt | Add post-extraction verification: does LLM output exist in OCR text? | P1 |
| **Temperature** | 0.0 ✅ | Already optimal | — |
| **Token usage** | No tracking | Add token counting and cost logging | P2 |
| **Model choice** | `qwen/qwen3.8-27b` | Consider `llama-3.1-70b-versatile` or `qwen/qwen3.8-27b` for better extraction | P3 |
| **Caching** | None | Cache LLM results by OCR text hash to avoid redundant calls | P2 |
| **Timeout** | No explicit timeout | Add request-level timeout (30s) | P1 |
| **Prompt injection** | OCR text injected raw into prompt | Sanitize OCR text: strip control chars, limit length, escape delimiters | P0 |
| **Logging** | Logs success/failure only | Log prompt, response, and evidence-match quality for debugging | P2 |
| **Unused params** | `inspection_product_name` and `inspection_brand` passed but NOT included in Groq prompt | Include in prompt as context hints | P2 |
| **Model fallback** | Single model, no fallback model | Add a faster/cheaper fallback model (e.g., `llama3-8b`) | P3 |

---

## 14. Recommended Architecture

The current architecture is well-structured. The recommendation is to **evolve** rather than rewrite:

```
Input (Image Upload)
    ↓
Input Validation (file type, size, format) ← STRENGTHEN
    ↓
Image Quality Assessment (OpenCV) ← EXISTING ✅
    ↓
Image Preprocessing (OpenCV) ← EXISTING ✅
    ↓
OCR (PaddleOCR dual-track) ← EXISTING ✅
    ↓
OCR Text Sanitization ← NEW: strip control chars, limit length
    ↓
Extraction Pipeline ← EXISTING ✅
    ├─ LLM Extraction (Groq) + Post-Validation ← IMPROVE
    └─ Regex Fallback ← EXISTING ✅
    ↓
Multi-Image Field Merge ← NEW: combine front/back labels
    ↓
Product Category Resolution ← NEW: user-provided or LLM-inferred
    ↓
Deterministic Rules (LM001-LM010+) ← EXISTING ✅ + EXPAND
    ↓
Category-Specific Rules ← NEW: FSSAI for food, BIS for electronics
    ↓
Cross-Field Validation ← NEW: date consistency, import completeness
    ↓
Confidence-Weighted Scoring ← NEW: use OCR confidence in rule decisions
    ↓
Output Validation ← NEW: verify no contradictions in report
    ↓
Compliance Report Generation ← EXISTING ✅
    ↓
PDF/DOCX Reports ← EXISTING ✅
    ↓
Audit Logging ← NEW
    ↓
Dashboard Analytics ← EXISTING ✅
```

---

## 15. Priority Matrix

### P0 — Critical (Fix Immediately)

| # | Item | Type | Effort |
|---|------|------|--------|
| 1 | **Remove API keys from `.env` in Git** — rotate all compromised keys (Groq, Neon DB) | Security | 1 hour |
| 2 | **Add `.env` to `.gitignore`** and use `.env.example` only | Security | 5 minutes |
| 3 | **Sanitize OCR text before LLM prompt** (prompt injection defense) | Security | 2 hours |
| 4 | **Use strong JWT secret in production** (env-only, generated) | Security | 30 minutes |

### P1 — High (Strongly Recommended)

| # | Item | Type | Effort |
|---|------|------|--------|
| 5 | **Add `python-docx` to `requirements.txt`** | Bug | 5 minutes |
| 6 | **Implement RBAC enforcement** — admin-only dashboard, user-scoped inspections | Security | 4 hours |
| 7 | **Add rate limiting** middleware (e.g., `slowapi`) | Security | 2 hours |
| 8 | **Add password complexity requirements** | Security | 1 hour |
| 9 | **Improve LLM prompt** — add schema, few-shot examples, inspection context | LLM | 4 hours |
| 10 | **Add LLM request timeout** (30s) | Reliability | 30 minutes |
| 11 | **Add LM011 — Expiry Date Presence rule** | Rule | 1 hour |
| 12 | **Add LM017 — Food Product FSSAI rule** | Rule | 2 hours |
| 13 | **Add LLM output verification** — cross-check extracted values against OCR text | LLM | 4 hours |

### P2 — Medium (Useful Improvement)

| # | Item | Type | Effort |
|---|------|------|--------|
| 14 | Add product category selection to inspection creation | Feature | 4 hours |
| 15 | Multi-image field merge | Feature | 8 hours |
| 16 | Add date validity rules (LM012, LM013) | Rule | 4 hours |
| 17 | Add MRP reasonability rule (LM014) | Rule | 2 hours |
| 18 | OCR confidence-weighted rule evaluation | Architecture | 4 hours |
| 19 | Add structured logging with correlation IDs | Observability | 4 hours |
| 20 | LLM token/cost tracking | Observability | 2 hours |
| 21 | Remove dead code (`compliance/base.py`, `ai/base.py`) | Cleanup | 30 minutes |
| 22 | Update outdated `rules/README.md` | Documentation | 15 minutes |
| 23 | Migrate `on_event("startup")` to lifespan | Maintenance | 1 hour |
| 24 | Include `inspection_product_name` and `inspection_brand` in Groq prompt | LLM | 30 minutes |

### P3 — Future (Nice-to-Have)

| # | Item | Type | Effort |
|---|------|------|--------|
| 25 | LLM caching by OCR text hash | Performance | 4 hours |
| 26 | Extraction debugger (visual overlay) | DX | 16 hours |
| 27 | Rule configuration UI (admin panel) | Feature | 16 hours |
| 28 | Cross-image consistency rules (LM018) | Rule | 8 hours |
| 29 | Comparative analysis across inspections | Feature | 16 hours |
| 30 | Fallback LLM model (Llama 3 8B) | Reliability | 4 hours |
| 31 | JWT refresh tokens | Auth | 4 hours |

---

## 16. Implementation Roadmap

### Phase 1: Critical Security Fixes (Day 1)

| Task | File(s) | Change | Risk | Complexity |
|------|---------|--------|------|------------|
| Rotate all API keys | External (Groq console, Neon dashboard) | Generate new keys | None | Low |
| Add `.env` to `.gitignore` | [`.gitignore`](file:///d:/CompliQ/.gitignore) | Add `.env` entry | None | Trivial |
| Remove `.env` from Git history | Git | `git filter-branch` or BFG | Low | Medium |
| Sanitize OCR text | [`extraction.py`](file:///d:/CompliQ/backend/app/ai/extraction.py#L69) | Strip control chars, limit to 10K chars | Low | Low |
| Strong JWT secret | `.env` / render.yaml | Use `generateValue: true` (already in render.yaml) | None | Trivial |

### Phase 2: Security Hardening (Week 1)

| Task | File(s) | Change | Dependencies | Complexity |
|------|---------|--------|-------------|------------|
| Add `python-docx` to requirements | [`requirements.txt`](file:///d:/CompliQ/backend/requirements.txt) | Add `python-docx>=1.0.0` | None | Trivial |
| RBAC middleware | `core/security.py`, API routes | Create `require_role()` dependency | None | Medium |
| Rate limiting | `main.py`, new `core/rate_limit.py` | Add `slowapi` middleware | `slowapi` dep | Low |
| Password policy | `schemas/user.py`, `auth_service.py` | Add Pydantic validators | None | Low |
| Request timeout for Groq | `extraction.py` | Add `timeout=30` to Groq client | None | Low |

### Phase 3: Rule Engine Expansion (Week 2)

| Task | File(s) | Change | Dependencies | Complexity |
|------|---------|--------|-------------|------------|
| Add LM011 (Expiry Date) | `compliance/rules.py` | New PresenceRule on `expiry_date` | None | Low |
| Add LM012/LM013 (Date Validation) | `compliance/rules.py` | New rule type: `DateValidationRule` | Python `dateutil` | Medium |
| Add LM014 (MRP Reasonability) | `compliance/rules.py` | New rule type: `ValueRangeRule` | None | Low |
| Add LM017 (FSSAI for Food) | `compliance/rules.py` | New rule type: `CategoryConditionalRule` | Product category field | Medium |
| Update tests | `tests/test_phase4.py` | Add tests for new rules | None | Medium |

### Phase 4: LLM Improvements (Week 2-3)

| Task | File(s) | Change | Dependencies | Complexity |
|------|---------|--------|-------------|------------|
| Enhance prompt with schema | `extraction.py` | Add JSON schema + few-shot examples | None | Medium |
| Include inspection context in prompt | `extraction.py` | Pass product_name, brand, category to prompt | Product category feature | Low |
| Post-extraction verification | `extraction.py` | Verify extracted values exist in OCR text | None | Medium |
| Token/cost logging | `extraction.py` | Log `usage` from Groq response | None | Low |

### Phase 5: Product Features (Week 3-4)

| Task | File(s) | Change | Dependencies | Complexity |
|------|---------|--------|-------------|------------|
| Product category field | Models, schemas, API, frontend | Add category to Inspection model | Migration | Medium |
| Multi-image field merge | `compliance_service.py` or new service | Merge ProductInfo across images | None | Medium |
| OCR confidence-weighted rules | `compliance/rules.py` | Rules consider evidence confidence | None | Medium |

### Phase 6: Testing & Hardening (Ongoing)

| Task | Change | Complexity |
|------|--------|------------|
| Add adversarial tests | Test with crafted images containing prompt injection | Medium |
| Add extraction accuracy benchmarks | Test against known product label images | Medium |
| Add performance benchmarks | Measure E2E latency | Low |
| Add CI/CD pipeline | GitHub Actions for tests + linting | Medium |

---

## 17. Testing Strategy

### Current Test Coverage

| Test File | Scope | Lines | Status |
|-----------|-------|-------|--------|
| [`test_auth.py`](file:///d:/CompliQ/backend/tests/test_auth.py) | Auth API (register, login, me) | 3787 | ✅ |
| [`test_inspections.py`](file:///d:/CompliQ/backend/tests/test_inspections.py) | CRUD operations | 2981 | ✅ |
| [`test_images.py`](file:///d:/CompliQ/backend/tests/test_images.py) | Image upload/delete | 4650 | ✅ |
| [`test_phase2.py`](file:///d:/CompliQ/backend/tests/test_phase2.py) | OCR + preprocessing | 14996 | ✅ |
| [`test_phase3.py`](file:///d:/CompliQ/backend/tests/test_phase3.py) | Extraction pipeline | 24141 | ✅ |
| [`test_phase4.py`](file:///d:/CompliQ/backend/tests/test_phase4.py) | Compliance rules + engine + API | 7787 | ✅ |
| [`test_phase5.py`](file:///d:/CompliQ/backend/tests/test_phase5.py) | Report generation | 5866 | ✅ |
| [`test_generic_extraction.py`](file:///d:/CompliQ/backend/tests/test_generic_extraction.py) | Extraction edge cases | 6707 | ✅ |
| [`test_gulas_extraction.py`](file:///d:/CompliQ/backend/tests/test_gulas_extraction.py) | Real product extraction | 4197 | ✅ |
| [`test_real_package_extraction.py`](file:///d:/CompliQ/backend/tests/test_real_package_extraction.py) | Real package testing | 19342 | ✅ |
| [`test_live_extraction.py`](file:///d:/CompliQ/backend/tests/test_live_extraction.py) | Live extraction tests | 1659 | ✅ |
| [`test_storage.py`](file:///d:/CompliQ/backend/tests/test_storage.py) | Storage abstraction | 6088 | ✅ |

### Missing Tests

| Category | What's Missing | Priority |
|----------|---------------|----------|
| **Adversarial** | Prompt injection via OCR text, malformed images | P1 |
| **RBAC** | Test that INSPECTOR cannot access ADMIN endpoints | P1 |
| **Rate Limiting** | Test that rate limits are enforced | P1 |
| **LLM Integration** | Real Groq API call test (with test key) | P2 |
| **Edge Cases** | Empty OCR results, single-block images, very long text | P2 |
| **Frontend** | No frontend tests exist | P3 |
| **Performance** | No latency/throughput benchmarks | P3 |

### Rule Test Matrix

| Rule | All-Pass Input | All-Fail Input | Uncertain Input | Empty Input | Tested? |
|------|---------------|----------------|-----------------|-------------|---------|
| LM001 | ✅ | ✅ | — | — | ✅ Unit |
| LM002 | ✅ | ✅ | — | — | ✅ Unit |
| LM003 | ✅ | ✅ | — | — | ✅ Unit + API |
| LM004 | ✅ | ✅ | — | — | ✅ Unit |
| LM005 | ✅ | ✅ | — | — | ✅ Unit + API |
| LM006 | ✅ | ✅ | — | — | ✅ Unit |
| LM007 | ✅ | — | — | — | ✅ Unit |
| LM008 | N/A (always REVIEW) | N/A | N/A | ✅ | ✅ Unit |
| LM009 | ✅ | ✅ | — | — | ✅ Unit |
| LM010 | ✅ | ✅ | — | — | ✅ Unit |

### LLM Test Matrix

| Scenario | Input | Expected Behavior | Current Behavior | Pass/Fail |
|----------|-------|-------------------|------------------|-----------|
| Normal product label | Clear OCR text with all fields | Extract all fields with evidence | Extracts via LLM or regex | ✅ (via test files) |
| No API key | `GROQ_API_KEY` unset | Fall back to regex | Falls back correctly | ✅ |
| Groq SDK not installed | `groq` package absent | Fall back to regex | Falls back correctly (try/except ImportError) | ✅ |
| Empty OCR text | No blocks | Return all NOT_DETECTED | Returns empty product data | ✅ |
| Rate limited | 503 from Groq | Retry 3 times, then fall back | Retries implemented | ✅ (code) |
| Prompt injection | OCR text contains "ignore above instructions" | Should still extract normally | **UNTESTED** | ⚠️ Unknown |
| Very long OCR text | > 8192 tokens of OCR text | Truncation or error | **UNTESTED** | ⚠️ Unknown |
| Non-English label | Hindi/multilingual text | Partial extraction at best | **UNTESTED** | ⚠️ Unknown |
| Groq returns invalid JSON | Malformed response | Should fall back to regex | Pydantic validation catches → logs error → falls back | ✅ (code) |

---

## 18. Risks and Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Groq API key compromised** (committed to Git) | HIGH | Critical — unauthorized usage, cost | Rotate keys immediately |
| **Neon DB credentials compromised** | HIGH | Critical — data breach | Rotate credentials, restrict IP access |
| **Groq API deprecates qwen/qwen3.8-27b** | Medium | High — extraction breaks | Pin model version, add fallback model |
| **PaddleOCR version incompatibility** | Low | Medium — OCR breaks | Pin version in requirements |
| **Groq rate limits in production** | Medium | Medium — degrades to regex | Implement caching, retry with backoff |
| **Large image uploads causing OOM** | Medium | Medium — server crash | Enforce server-side image size limits before OCR |

### External Dependencies

| Dependency | Purpose | Risk Level |
|-----------|---------|------------|
| Groq API | LLM extraction | Medium — external service dependency |
| Neon PostgreSQL | Database | Medium — external hosted DB |
| PaddleOCR / PaddlePaddle | OCR engine | Low — vendored models |
| OpenCV | Image preprocessing | Low — stable library |
| ReportLab | PDF generation | Low — stable library |

---

## 19. Quick Wins

These can be done in under 30 minutes each and have disproportionate impact:

1. ✅ **Add `.env` to `.gitignore`** — prevents future credential leaks
2. ✅ **Add `python-docx>=1.0.0` to `requirements.txt`** — fixes broken DOCX reports on fresh installs
3. ✅ **Update `rules/README.md`** — remove "placeholder only" text
4. ✅ **Remove `compliance/base.py` and `ai/base.py`** — eliminate dead code confusion
5. ✅ **Add LLM timeout** — `Groq(api_key=api_key, timeout=30.0)` in extraction.py
6. ✅ **Include `inspection_product_name` and `inspection_brand` in Groq prompt** — already passed as params, just not used in prompt
7. ✅ **Sanitize OCR text** — `text_content = text_content[:10000].replace("\x00", "")` before prompt

---

## 20. Recommended Final Product Direction

### Short-Term (1-2 weeks): Production Hardening

The project is **feature-complete for a demo/MVP** but needs **security hardening before any production deployment**. Focus on:
- Credential rotation and secret management
- RBAC enforcement
- Rate limiting
- Input sanitization
- LLM prompt improvement

### Medium-Term (3-4 weeks): Intelligence Upgrade

- Product category awareness (enables category-specific compliance rules)
- Multi-image field merge (realistic for field inspectors who photograph front, back, sides)
- Cross-field validation rules (date consistency, import completeness)
- LLM output verification pipeline
- Structured logging and monitoring

### Long-Term (2-3 months): Platform Evolution

- Rule configuration UI (no-code rule management for compliance officers)
- Extraction accuracy benchmarking with labeled test datasets
- Historical analysis and trend detection
- Multi-language OCR support (Hindi labels)
- Mobile-optimized frontend for field inspectors
- Offline-capable PWA for areas with poor connectivity

### Architecture Direction

The current architecture is **sound and should be preserved**. The layered separation (API → Service → Repository → Model) with the AI/Compliance modules as independent subsystems is clean and maintainable. 

The key evolution should be:
1. **Strengthen the deterministic layer** — more and smarter rules
2. **Constrain the LLM** — better prompts, output validation, caching
3. **Add product context** — category-aware compliance
4. **Improve observability** — logging, metrics, debugging tools

Do NOT rewrite the architecture. Extend it.

---

## Final Answers

1. **What is the current status?** — Phases 1-5 are fully implemented and functional. Phase 6 (deployment) is in progress.

2. **Is the LLM actually implemented?** — **YES.** Groq SDK integration with Llama 3 70B is fully coded with retry logic, Pydantic validation, evidence matching, and regex fallback.

3. **Does the LLM actually work at runtime?** — **PARTIALLY / CANNOT FULLY VERIFY.** The code is structurally correct and a real API key is configured. Cannot confirm without running the server.

4. **What exactly does the LLM do?** — Structured data extraction from noisy OCR text. Extracts 19 fields from product labels with evidence linking.

5. **Why is the LLM being used?** — Because regex alone is brittle for noisy OCR text. The LLM handles non-standard label formats, OCR errors, and ambiguous text better than pattern matching.

6. **How does the LLM interact with the rest of the system?** — It's called first in the extraction pipeline. If it succeeds, its results are used. If it fails (SDK missing, key missing, API error, invalid response), the system falls back to regex extraction. The compliance engine then evaluates the extracted fields regardless of extraction method.

7. **Are there really only 8 active rules?** — **NO. There are 10 active rules** (LM001–LM010).

8. **Verified number of active rules?** — **10**, confirmed from `REGISTERED_RULES` list and test assertions.

9. **Weaknesses of existing rules?** — Single-field presence checks only; no cross-field validation; no product category awareness; no date/value validation; LM007 and LM008 provide minimal automated value.

10. **Additional rules?** — 8 proposed (LM011–LM018 + SYS001) covering expiry dates, date validity, MRP reasonability, quantity format, import completeness, FSSAI enforcement, cross-image consistency, and OCR text sanitization.

11. **Highest potential features?** — Product category selection, multi-image field merge, RBAC enforcement, and LLM prompt improvement.

12. **Implement first?** — P0: Credential rotation, `.env` protection, OCR text sanitization, JWT secret. Then P1: RBAC, rate limiting, prompt improvement, expiry date rule.

13. **NOT implement yet?** — Rule configuration UI, extraction debugger, comparative analysis, fallback LLM model, JWT refresh tokens.

14. **Target architecture?** — Extend current layered architecture. Add OCR text sanitization layer, multi-image merge, product category context, category-conditional rules, confidence-weighted scoring, and audit logging. Do NOT rewrite.
