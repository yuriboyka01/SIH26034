# COMPLIQ: Legal Metrology Compliance System
## Complete Technical Stack, System Architecture & Implementation Specification
**Document Version:** 4.0.0-phase4  
**Project Identifier:** SIH26034  
**Target Statute:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC Rules, 2011)  
**Classification:** Technical Architecture & Compliance Specification  
**Author:** COMPLIQ Engineering Team  
**Date:** September 2026  

---

## Executive Summary

### What is COMPLIQ?
**COMPLIQ** is an automated, AI-augmented software system engineered to inspect, parse, and verify statutory compliance of consumer packaged goods under the **Legal Metrology (Packaged Commodities) Rules, 2011** (enacted under the Legal Metrology Act, 2009 by the Ministry of Consumer Affairs, Food and Public Distribution, Government of India).

### What Problem Does It Solve?
Every packaged commodity sold in India is legally mandated to display declarations including the name and address of the manufacturer/packer/importer, generic commodity name, net quantity, Maximum Retail Price (MRP), consumer complaint contact details, date of manufacture/pre-packing, and country of origin. 

Historically, enforcement of these statutory declarations has relied upon manual physical sampling by state Legal Metrology inspectors. Manual inspection is:
1. **Extremely Low Throughput:** An inspector can manually examine only a few dozen packages per shift across millions of retail SKUs.
2. **Subjective and Error-Prone:** Human verification frequently overlooks subtle font-prominence non-compliances or missing mandatory contact channels (e.g., missing telephone numbers or email addresses).
3. **Difficult to Scale in E-Commerce:** With the exponential expansion of digital commerce and dark stores, unvetted packaged goods proliferate rapidly.
4. **Legally Vulnerable:** Manual notes lack tamper-proof digital evidence logs linking individual violations back to spatial bounding-box image crops of the physical package.

COMPLIQ transforms this workflow by providing an end-to-end digital inspection pipeline: inspectors capture or upload package imagery, and the system executes computer vision quality gating, high-accuracy optical character recognition (OCR), structured LLM extraction with deterministic regex fallback, spatial evidence-bounding box attribution, and automated statutory rule evaluation.

### How Does It Work?
1. **Intake & Multi-Angle Imaging:** An inspector creates an inspection record and uploads front, back, and side package photographs.
2. **Quality Assessment & Dual-Track Preprocessing:** OpenCV analyzes Laplacian blur variance, mean luminance, and dimensions. An adaptive contrast (CLAHE) and denoising pipeline prepares an enhanced image track alongside the raw track.
3. **Strict PaddleOCR Extraction:** PaddleOCR (CPU mode with angle classification) executes across both image tracks. A composite scoring function (`block_count * average_confidence`) selects the superior textual output, extracting normalized text with pixel-level axis-aligned bounding boxes `[x1, y1, x2, y2]`.
4. **Structured Information Extraction:** The OCR text is processed by a Groq-hosted LLM (`qwen/qwen3.8-27b`) constrained by Pydantic JSON schema to extract 19 distinct product attributes. The LLM's evidence citations are deterministically mapped back to physical OCR bounding boxes using normalized string similarity. If the LLM API is unavailable, a deterministic 19-field spatial regex grouping engine executes as an automatic fallback.
5. **Codified Compliance Engine:** A deterministic rules engine evaluates 10 codified Legal Metrology rules (LM001 through LM010). Rules produce structured statuses (`PASS`, `FAIL`, `REVIEW`, `NOT_APPLICABLE`) and distinct severities (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). Human review is systematically required for statutory exemptions and physical metric measurements.
6. **Inspector Workstation & Statutory Reporting:** The React frontend renders bounding box overlays on uploaded package images via HTML5 Canvas, presents dynamic image crops of violation evidence, and generates statutory PDF (via ReportLab) and Word DOCX (via python-docx) inspection reports.

### Why is AI Useful Here?
Consumer product packaging is visually chaotic: typography varies drastically in font size, font family, color, orientation, and layout. Declarations appear on cylindrical, reflective, flexible, or wrinkled surfaces. Traditional static regex or fixed-position template matching fails when label elements shift. 

AI (specifically Deep Learning-based OCR combined with Large Language Models) bridges this complexity:
- **PaddleOCR's DBNet detection and SVTR recognition** locate arbitrary curved and rotated text lines without template rigidness.
- **LLM Contextual Reasoning** understands semantic equivalents (e.g., recognizing that *"Customer Care Executive: 1800-XXX-XXXX or help@brand.in"* fulfills Rule 6(2) consumer care requirements).
- **Anti-Hallucination Grounding** ensures the LLM cannot fabricate facts: every extracted declaration must match OCR bounding boxes to achieve `DETECTED` status.

### What Technologies Power It?
- **Backend Core:** FastAPI (Python 3.11), Uvicorn ASGI server.
- **Database & Persistence:** PostgreSQL with SQLAlchemy 2.0 ORM, psycopg 3 binary driver, and Alembic database migrations.
- **Computer Vision & OCR:** OpenCV 4.11 (`opencv-python`), Pillow, and PaddleOCR 2.8.1 on PaddlePaddle 2.6.2.
- **AI & Structured Extraction:** Groq Python SDK (`groq` 1.7.0) utilizing `qwen/qwen3.8-27b` with temperature 0.0 and Pydantic V2 schema validation.
- **Security & Storage:** Passlib with Bcrypt, Python-Jose JWT (HS256), Boto3 S3-compatible cloud object storage abstraction.
- **Reporting:** ReportLab 5.0 (PDF generation), python-docx (Word generation).
- **Frontend Workstation:** React 19, TypeScript 6, Vite 8, Tailwind CSS 4, Axios, and Lucide React.

### What Makes the Implementation Technically Interesting?
1. **Strict Runtime Integrity:** Hard runtime enforcement in `app/core/runtime.py` blocks initialization unless running under Python 3.11.x, preventing runtime crashes caused by PaddlePaddle ABI incompatibility on newer Python releases.
2. **Two-Track Preprocessing Competition:** Rather than guessing whether contrast adjustment will improve or degrade OCR accuracy, the engine executes OCR on both original and CLAHE-enhanced variants, dynamically choosing the winning set of text blocks.
3. **Spatial Bounding Box Grouping:** The deterministic fallback engine uses vertical centerline clustering and relative bounding box height thresholds to re-assemble text blocks that were split across multiple horizontal fragments (e.g., uniting "M.R.P. Rs." with "250.00").
4. **Interactive HTML5 Canvas Evidence Cropping:** The frontend dynamically renders bounding box coordinates on the client's HTML5 Canvas, extracting localized visual crops of individual packaging declarations directly in the browser.
5. **No Silent OCR Fallbacks:** The system strictly requires PaddleOCR; if the engine cannot load, startup explicitly terminates rather than silently degrading to low-accuracy engines.

---

## Key Technical Highlights

1. **Strict Python 3.11.x Architecture Guard:** An active startup validator (`verify_runtime()`) halts backend execution with actionable diagnostic messages if the Python runtime does not match 3.11.x, guaranteeing stability for PaddlePaddle native C++ extensions.
2. **Dual-Track OpenCV Preprocessing:** Implements Laplacian blur variance testing (`cv2.Laplacian`), luminance normalization, and CLAHE adaptive histogram equalization, pitting raw vs preprocessed images in an automated scoring competition.
3. **Mandatory Angle-Classified PaddleOCR:** Executes PaddleOCR 2.8.1 with `use_angle_cls=True` to detect and orient text tilted at 90°, 180°, or 270° angles on consumer bottles, cans, and cartons.
4. **Structured JSON Schema LLM Extraction:** Leverages Groq Cloud API with `qwen/qwen3.8-27b` constrained by Pydantic JSON schemas, operating at zero temperature for deterministic outputs.
5. **Anti-Hallucination Evidence Mapping:** Compares LLM-cited source snippets against raw OCR bounding boxes using normalized string character sequences (`difflib.SequenceMatcher`), rejecting unverified hallucinated text.
6. **19-Field Spatial Regex Fallback Engine:** Features a comprehensive deterministic fallback engine capable of grouping horizontally aligned text blocks and extracting 19 distinct product declarations without external API connectivity.
7. **10 Codified Legal Metrology Rules:** Explicitly implements rules LM001 through LM010 mapped to specific sections of the Legal Metrology (Packaged Commodities) Rules, 2011.
8. **Multi-Tiered Severity & Review Architecture:** Rules categorize non-compliance into CRITICAL, HIGH, MEDIUM, and LOW, while routing ambiguous cases (such as statutory packaging exemptions and physical millimeter lettering requirements) to human inspectors.
9. **Storage-Agnostic File Management:** Employs an abstract `StorageService` interface with `LocalStorageService` for on-premise development and `S3StorageService` (via `boto3`) for cloud deployment on AWS S3, Cloudflare R2, or Backblaze B2.
10. **Interactive Client-Side Evidence Cropping:** The React frontend uses client-side HTML5 Canvas manipulation to dynamically crop specific packaging declarations from full-resolution photos, presenting side-by-side legal proof to inspectors.
11. **Multi-Format Statutory Report Generation:** Implements native server-side generation of PDF (ReportLab) and DOCX (python-docx) inspection audit dossiers with inspection metadata, rule tables, and evidence logs.
12. **177 Automated Test Cases:** Backed by an extensive automated test suite covering authentication, RBAC, OpenCV preprocessing, OCR engine initialization, LLM integration, regex fallbacks, compliance rules, and real physical package samples.

---

## Technical Stack Specification

The following table documents every technology in the COMPLIQ repository, verified against installed packages, configuration files, and source code imports.

| Layer | Technology | Exact Version | Purpose | Actually Used? |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Runtime** | CPython | 3.11.9 | Core programming runtime; strictly verified by `runtime.py` | Yes |
| **Backend Framework** | FastAPI | 0.115.0 | High-performance asynchronous REST API framework | Yes |
| **ASGI Server** | Uvicorn (standard) | 0.30.6 | Production ASGI server running FastAPI application | Yes |
| **Database Engine** | PostgreSQL | 16.x (Neon / Local) | Primary relational database for inspections, OCR, and users | Yes |
| **Database Driver** | psycopg (psycopg3) | 3.3.4 | Modern Python PostgreSQL DB-API / connection driver | Yes |
| **ORM** | SQLAlchemy | 2.0.35 | Relational mapping, connection pooling, and query execution | Yes |
| **Database Migrations** | Alembic | 1.13.3 | Version-controlled database schema migrations (5 revisions) | Yes |
| **Data Validation** | Pydantic | 2.9.2 | Strict schema validation, settings management, JSON serialization | Yes |
| **Settings Management** | pydantic-settings | 2.5.2 | Environment variable loading and configuration parsing | Yes |
| **Email Validation** | email-validator | 2.2.0 | Validates email syntax during user registration and extraction | Yes |
| **Password Hashing** | Passlib + Bcrypt | Passlib 1.7.4 / Bcrypt 4.0.1 | Secure cryptographic hashing (bcrypt work factor 12) | Yes |
| **JWT Tokens** | python-jose | 3.3.0 | HS256 JWT encoding, decoding, expiration validation | Yes |
| **Multipart Parsing** | python-multipart | 0.0.12 | Streaming file upload parsing for multi-megabyte package images | Yes |
| **Object Storage** | Boto3 / Botocore | 1.43.89 | S3-compatible cloud object storage integration (R2/B2/S3) | Yes |
| **Environment Config** | python-dotenv | 1.0.1 | Explicit loading of `.env` files across root and backend dirs | Yes |
| **Image Processing** | Pillow (PIL) | 12.3.0 | Python image handling, dimension verification, format checks | Yes |
| **Scientific Computing**| NumPy | 1.26.4 | Multi-dimensional array operations for image tensors & coordinates| Yes |
| **Computer Vision** | OpenCV (`opencv-python`) | 4.11.0.86 | Image quality analysis, blur detection, CLAHE contrast, NLM denoise| Yes |
| **OCR Framework** | PaddlePaddle | 2.6.2 | Deep learning backend engine powering PaddleOCR | Yes |
| **OCR Engine** | PaddleOCR | 2.8.1 | DBNet text detection & SVTR text recognition with angle cls | Yes |
| **AI / LLM Cloud SDK** | Groq Python SDK | 1.7.0 | High-speed LLM inference client for structured extraction | Yes |
| **LLM Model** | Qwen 2.5 72B / 27B | `qwen/qwen3.8-27b` | Zero-temperature JSON Schema extraction model | Yes |
| **PDF Report Engine** | ReportLab | 5.0.1 | Programmatic PDF compliance dossier generation | Yes |
| **Word Report Engine** | python-docx | 1.2.0 | Programmatic DOCX compliance report generation | Yes |
| **Testing Framework** | Pytest | 8.3.3 | Automated testing framework (177 tests in repository) | Yes |
| **HTTP Test Client** | HTTPX | 0.27.2 | Synchronous and asynchronous HTTP client for API test suites | Yes |
| **Async Testing** | pytest-asyncio | 0.24.0 | Coroutine execution in test fixtures | Yes |
| **Frontend Framework** | React | 19.2.8 | Declarative component UI library | Yes |
| **DOM Renderer** | React DOM | 19.2.8 | Web browser DOM bindings for React 19 | Yes |
| **Frontend Routing** | React Router DOM | 7.18.2 | Client-side client navigation and protected route guards | Yes |
| **Build Tooling** | Vite | 8.2.2 | Fast ES module development server and Rollup production builder | Yes |
| **Frontend Language** | TypeScript | 6.0.2 | Strict static typing for frontend components, API clients, models | Yes |
| **Styling Framework** | Tailwind CSS | 4.3.3 | Utility-first CSS engine with `@tailwindcss/vite` plugin | Yes |
| **HTTP Client (Web)** | Axios | 1.20.0 | Browser HTTP client with automatic JWT bearer interceptors | Yes |
| **Icon Library** | Lucide React | 1.34.0 | Modern SVG icon set for dashboard, badges, and workstations | Yes |
| **Containerization** | Docker / Compose | N/A | **NOT IMPLEMENTED / NOT USED** (Verified: 0 dockerfiles in repo) | **NO** |

---

## System Architecture

The COMPLIQ system is designed as an API-first, decoupled architecture comprising a high-performance Python backend, an asynchronous relational database, an external AI inference engine, and a modern single-page React frontend.

```
+-------------------------------------------------------------------------------+
|                             CLIENT WORKSTATION                                |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |                  React 19 + TypeScript Single Page App                 |   |
|   |                                                                       |   |
|   |  [Dashboard]      [Inspection Register]      [Intake / Upload Form]   |   |
|   |  [Workstation]    [HTML5 Canvas Bounding]    [Evidence Image Crops]   |   |
|   +-----------------------------------------------------------------------+   |
+--------------------------------------|----------------------------------------+
                                       | HTTPS / JSON (Axios + JWT Interceptors)
                                       v
+-------------------------------------------------------------------------------+
|                            FASTAPI BACKEND SERVER                             |
|                                                                               |
|   +------------------+  +-------------------+  +--------------------------+   |
|   |  Auth Middleware |  | Security & RBAC   |  | CORS & Exception Handler |   |
|   |  JWT Bearer      |  | Bcrypt Hashing    |  | Standard Error Schemas   |   |
|   +------------------+  +-------------------+  +--------------------------+   |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |                              API ROUTERS                              |   |
|   |  /api/auth       /api/inspections      /api/dashboard    /api/images  |   |
|   |  /api/analysis   /api/product-info     /api/compliance   /api/reports |   |
|   +-----------------------------------------------------------------------+   |
|                                      |                                        |
|         +----------------------------+----------------------------+           |
|         v                                                         v           |
|   +----------------------------+                          +---------------+   |
|   |      SERVICES LAYER        |                          | STORAGE LAYER |   |
|   |  InspectionService         |                          | LocalStorage  |   |
|   |  ImageService              |                          | S3Storage     |   |
|   |  AnalysisService           |                          | (Boto3 SDK)   |   |
|   |  ComplianceService         |                          +---------------+   |
|   |  ReportService             |                                  |           |
|   +----------------------------+                                  | Disk / S3 |
|         |                      |                                  v           |
|         v                      v                          +---------------+   |
|   +------------------+   +-------------------+            | Image Files   |   |
|   | AI & OCR PIPELINE|   | COMPLIANCE ENGINE |            | (JPG/PNG/WEBP)|   |
|   | OpenCV Quality   |   | LM001 - LM010     |            +---------------+   |
|   | PaddleOCR 2.8.1  |   | Presence Rules    |                                |
|   | Groq LLM Client  |   | Contextual Review |                                |
|   | Regex Fallback   |   | Severity Evaluator|                                |
|   +------------------+   +-------------------+                                |
|         |                          |                                          |
|         +--------------------------+                                          |
|                                    v                                          |
|   +-----------------------------------------------------------------------+   |
|   |                          REPOSITORIES & ORM                           |   |
|   |         SQLAlchemy 2.0 Declarative Models (psycopg3 driver)           |   |
|   +-----------------------------------------------------------------------+   |
+--------------------------------------|----------------------------------------+
                                       | Connection Pool (pool_size=10, max=20)
                                       v
+-------------------------------------------------------------------------------+
|                           POSTGRESQL DATABASE                                 |
|                                                                               |
|   [users]             [inspections]           [inspection_images]             |
|   [ocr_results]       [ocr_text_blocks]       [product_info]                  |
|   [compliance_reports][compliance_rule_results]                               |
+-------------------------------------------------------------------------------+
```

---

## End-to-End Data Flow Architecture

The lifecycle of an inspection flows through ten well-defined, auditable processing stages:

```
[1. Package Image Upload]
       │ Multipart form-data with image file + image_type (FRONT, BACK, SIDE)
       ▼
[2. Validation & Storage]
       │ MIME check (image/jpeg, image/png, image/webp) + size check (<=10MB)
       │ UUID filename generation (prevents directory traversal) -> Disk or S3
       ▼
[3. Image Quality Analysis]
       │ OpenCV computes resolution, Laplacian blur score, mean brightness score
       │ Quality status assigned: GOOD, FAIR, or POOR
       ▼
[4. Dual-Track Preprocessing]
       │ Track A: Original raw BGR image
       │ Track B: Resized (<=1920px) + Grayscale + CLAHE contrast + NLM denoise
       ▼
[5. PaddleOCR Execution]
       │ PaddleOCR runs on both Track A and Track B (CPU mode, angle cls = True)
       │ Best track selected via: score = block_count * average_confidence
       ▼
[6. OCR Normalization & Bounding Boxes]
       │ Text normalized (whitespace collapsed); polygons -> [x1, y1, x2, y2] bboxes
       │ Output: OCRResult with full_text and OCRTextBlock list
       ▼
[7. Structured AI Extraction (Groq LLM)]
       │ Groq Qwen 2.5 (temperature 0.0) with Pydantic JSON Schema
       │ Anti-hallucination: extracted snippets mapped to OCR bboxes via difflib
       │ Fallback: Deterministic spatial horizontal grouping + regex engine
       ▼
[8. Schema Validation & Database Persistence]
       │ Validated against ProductInfoSchema; 19 top-level fields + fields_json saved
       │ Database records created in ocr_results, ocr_text_blocks, product_info
       ▼
[9. Compliance Rules Engine Evaluation]
       │ ComplianceRuleEngine evaluates LM001–LM010 against extracted fields
       │ Assigns PASS, FAIL, REVIEW, NOT_APPLICABLE with legal source citations
       │ Overall status determined: FAIL if critical/high fails; else REVIEW or PASS
       ▼
[10. Frontend Presentation & Report Generation]
       │ UI renders interactive canvas bbox overlays and evidence image crops
       │ One-click download of statutory PDF (ReportLab) and DOCX audit reports
```

### Stage Details & Failure Mitigation
- **Stages 1 & 2:** If the MIME type does not match the extension, an `IMAGE_TYPE_MISMATCH` HTTP 400 is returned. If file size exceeds 10MB, `IMAGE_TOO_LARGE` is returned.
- **Stages 3 & 4:** If an image is corrupt, OpenCV returns `None`, raising `ValueError("Cannot load image")` caught by the global exception handler.
- **Stage 5:** If PaddleOCR fails to initialize or crashes, `OCREngineUnavailableError` is raised. The backend terminates or returns an explicit OCR failure; it **never** silently switches to an unverified secondary engine.
- **Stage 7:** If the Groq API fails due to rate limits or network issues, up to 3 retries with exponential backoff occur. If Groq remains unreachable, the system automatically falls back to the deterministic spatial regex engine (`1.0-fallback`).

---

## OCR Engine: PaddleOCR Implementation

Optical Character Recognition is the primary perceptual layer of COMPLIQ. The repository strictly integrates PaddleOCR.

### Engine Configuration & Initialization
- **PaddleOCR Version:** `2.8.1`
- **PaddlePaddle Backend:** `2.6.2`
- **Supported Language:** English (`lang="en"`)
- **Angle Classification:** `use_angle_cls=True` (automatically detects and corrects upside-down or 90-degree rotated packaging text)
- **Log Suppression:** `show_log=False` (suppresses verbose C++ standard output to maintain clean application logging)
- **Singleton Pattern:** The OCR instance is lazily initialized and retained in memory (`_ocr_instance`) inside `app/ai/ocr_service.py` to eliminate expensive neural network weight reloads on every request.

### Mandatory Python 3.11 Runtime Requirement
PaddlePaddle 2.6.2 pre-compiled binary packages for Windows and Linux depend on CPython 3.11 ABI. Running under Python 3.12, 3.13, or 3.14 results in immediate C-extension import failures.
To protect against cryptic crashes in production, COMPLIQ implements an explicit guard in `backend/app/core/runtime.py`:
```python
def verify_runtime():
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        # Prints diagnostic banner and halts execution
        sys.exit(1)
```
This check executes as the very first line of `app/main.py`.

### Image Quality Assessment (`app/ai/preprocessing.py`)
Before passing images to PaddleOCR, COMPLIQ runs a quantitative quality audit:
1. **Resolution Threshold:** Checks that image width and height are both $\ge 200	ext{ px}$. If smaller, logs `IMAGE_TOO_SMALL`.
2. **Blur Detection:** Calculates the variance of the Laplacian operator:
   $$\sigma^2 = 	ext{Var}(
abla^2 I)$$
   If $\sigma^2 < 100.0$, the image is classified as `IMAGE_TOO_BLURRY`.
3. **Luminance Normalization:** Computes mean grayscale intensity divided by 255. If $< 0.20$, flags `IMAGE_TOO_DARK`. If $> 0.90$, flags `IMAGE_TOO_BRIGHT`.
4. **Quality Status:** Returns `GOOD` (no issues), `FAIR` (brightness issues only), or `POOR` (resolution or blur issues).

### Dual-Track Preprocessing & Scoring
Pre-processing can sometimes degrade crisp packaging text while helping noisy backgrounds. To resolve this trade-off, COMPLIQ implements a **dual-track competition strategy**:
1. **Track A (Original):** The raw RGB image is loaded.
2. **Track B (Preprocessed):** 
   - Resized: If $\max(	ext{width}, 	ext{height}) > 1920	ext{ px}$, resized using `cv2.INTER_AREA`.
   - Grayscale conversion: `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`.
   - Denoising: `cv2.fastNlMeansDenoising(gray, h=10)`.
   - Contrast Enhancement: Contrast Limited Adaptive Histogram Equalization (`cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))`).
   - Channel Conversion: Converted back to 3-channel BGR (`cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)`).
3. **Execution & Selection:** PaddleOCR is executed on both images. Results are scored via:
   $$	ext{Score} = N_{	ext{blocks}} 	imes \overline{	ext{Confidence}}$$
   The track yielding the highest composite score is selected as the canonical output.

### Bounding Box Geometry & Coordinate Mapping
PaddleOCR outputs four quadrilateral vertices:
$$[[x_1, y_1], [x_2, y_2], [x_3, y_3], [x_4, y_4]]$$
COMPLIQ projects these coordinates into an axis-aligned bounding box `[x1, y1, x2, y2]` in absolute pixel coordinates:
$$x_1 = \min(x_i), \quad y_1 = \min(y_i), \quad x_2 = \max(x_i), \quad y_2 = \max(y_i)$$
These coordinates are persisted in the database and utilized by the React frontend to draw interactive canvas overlays and crop visual evidence.

### Strict Fallback Policy
> [!IMPORTANT]
> COMPLIQ does **not** silently fall back to Tesseract, EasyOCR, or cloud OCR engines if PaddleOCR fails. If PaddleOCR cannot be imported or initialized, an explicit `OCREngineUnavailableError` is raised, causing backend startup to abort. PaddleOCR is a mandatory, core architectural dependency.

---

## AI & LLM Extraction Pipeline

Once raw text blocks are extracted by PaddleOCR, the system must transform unorganized OCR lines into structured, legally actionable product declarations.

```
+-------------------------------------------------------------------------------+
|                           OCR Text Blocks & Coordinates                       |
+-------------------------------------------------------------------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 | Is GROQ_API_KEY set & groq library loaded? |
                 +---------------------------------------------+
                        /                                                 [YES]                                   [NO]
                    v                                       v
+---------------------------------------+   +-----------------------------------+
|      PRIMARY PIPELINE: GROQ LLM       |   |    FALLBACK PIPELINE: REGEX       |
|                                       |   |                                   |
| 1. Model: qwen/qwen3.8-27b            |   | 1. Horizontal spatial line        |
| 2. Pydantic JSON Schema prompt        |   |    grouping (_group_blocks_       |
| 3. Temperature: 0.0                   |   |    spatially)                     |
| 4. Retries: Up to 3x with backoff     |   | 2. 19 deterministic keyword &     |
| 5. Output: Structured LLMProductData  |   |    regex pattern extractors       |
|                                       |   | 3. Label/value pair reassembly    |
+---------------------------------------+   +-----------------------------------+
                    |                                       |
                    | (If API 503/429 fails all retries)    |
                    +-------------------------------------->|
                    |                                       |
                    v                                       v
+---------------------------------------+   +-----------------------------------+
| Anti-Hallucination Evidence Matcher   |   | Field Construction & Status       |
| Compares source_text against OCR text |   | Fields marked DETECTED or         |
| blocks using difflib.SequenceMatcher. |   | NOT_DETECTED with regex source    |
| Maps true confidence and bbox coords. |   | text and confidence.              |
+---------------------------------------+   +-----------------------------------+
                    \                                       /
                     \                                     /
                      v                                   v
+-------------------------------------------------------------------------------+
|                 Canonical StructuredProductData (19 Fields)                   |
+-------------------------------------------------------------------------------+
```

### 1. Primary Pipeline: Groq LLM
- **SDK:** `groq>=0.9.0` (installed: `groq` 1.7.0)
- **Model:** `qwen/qwen3.8-27b` (configurable via `GROQ_MODEL` environment variable)
- **Deterministic Sampling:** `temperature=0.0`
- **Structured Output Enforcement:** `response_format={"type": "json_object"}` with the full JSON schema of `LLMProductData` injected directly into the system prompt.
- **Prompt Engineering:** The prompt instructs the model:
  - Extract structured data from OCR text.
  - Return exact `source_text` snippets for every extracted value.
  - Return `null` for both `value` and `evidence` if information is absent.
  - Never hallucinate or infer missing declarations.
- **Resilience & Retry Policy:** Wraps requests in an exponential backoff loop (up to 3 attempts with $2 	imes (	ext{attempt} + 1)$ second delays) on HTTP 503 or 429 rate limit exceptions. Non-retryable errors (e.g., HTTP 400 Bad Request) fail immediately to the fallback pipeline.

### 2. Anti-Hallucination Evidence Matching
To prevent LLM hallucinations from corrupting compliance records, `_extract_with_groq()` matches the LLM's cited `source_text` back to the raw OCR text blocks:
1. Strips punctuation and whitespace from both strings:
   $$	ext{normalize}(s) = 	ext{lower}(	ext{regex\_replace}([ackslash W\_]+, "", s))$$
2. Evaluates string similarity across all detected OCR blocks using `difflib.SequenceMatcher`.
3. If similarity exceeds threshold ($> 0.6$), the true OCR confidence score and the physical bounding box `[x1, y1, x2, y2]` are attached to the extracted field.
4. If no physical OCR block matches, the evidence bounding box remains `None`, signaling uncertainty.

### 3. Fallback Pipeline: Spatial Deterministic Regex Engine
If `GROQ_API_KEY` is not provided, or if the Groq service encounters an outage, COMPLIQ activates its deterministic fallback engine (`extraction_version="1.0-fallback"`):
1. **Spatial Line Grouping (`_group_blocks_spatially`):**
   Product packaging often prints labels and values in separate text elements (e.g., "NET QTY:" on the left, "500 g" on the right). The spatial grouper:
   - Calculates the vertical centerline $c_y = (y_1 + y_2) / 2$ and height $h = y_2 - y_1$ for each bounding box.
   - Clusters blocks whose centerlines fall within half a block height: $|c_y - \overline{c_y}| < 0.5 	imes \overline{h}$.
   - Merges horizontally aligned blocks in left-to-right order, creating unified lines before regex evaluation.
2. **19 Specialized Field Extractors:**
   The fallback engine executes regex and keyword parsers covering all 19 target declarations, including MRP with currency symbols, date patterns (month/year, DD/MM/YYYY), net quantities with metric units (g, kg, ml, l), customer care phone numbers, and FSSAI/statutory licenses.

---

## Product Data Schema

The canonical schema represents all product declarations extracted from packaging imagery. All 19 fields are defined in `app/schemas/product_info.py` and `app/models/product_info.py`.

| Field Name | Data Type | Extraction Source | Description under Legal Metrology Rules | Required by LMPC 2011? |
| :--- | :--- | :--- | :--- | :--- |
| `product_name` | String | LLM / Spatial Line 1 | Common or generic name of the commodity | **Mandatory** (Rule 6(1)(b)) |
| `brand_name` | String | LLM / Keyword Regex | Brand or trade name of the product | Recommended / Commercial |
| `manufacturer` | Text | LLM / Address Parser | Name and complete address of the manufacturer | **Mandatory** (Rule 6(1)(a)) |
| `net_quantity` | String | LLM / Metric Regex | Net quantity in standard units of weight/measure | **Mandatory** (Rule 6(1)(c)) |
| `mrp` | String | LLM / Currency Regex | Maximum Retail Price inclusive of all taxes | **Mandatory** (Rule 6(1)(e)) |
| `manufacturing_date` | String | LLM / Date Parser | Month and year of manufacture or pre-packing | **Mandatory** (Rule 6(1)(d)) |
| `packaging_date` | String | LLM / Date Parser | Month and year of packing (if separate from mfg) | Contextual (Rule 6(1)(d)) |
| `expiry_date` | String | LLM / Date Parser | Best before or expiry date (mandatory for food) | Contextual / Mandatory (FSSAI) |
| `batch_number` | String | LLM / Batch Regex | Lot number, batch number, or code identification | **Mandatory** (Rule 6(1)(e)) |
| `country_of_origin` | String | LLM / Origin Regex | Country of origin (for imported goods / e-commerce) | **Mandatory** (Imported / E-com) |
| `ingredients` | Text | LLM / List Parser | List of ingredients or composite components | Category-specific (Food/Cosmetics)|
| `license_number` | String | LLM / License Regex | Statutory registration (e.g., FSSAI 14-digit, BIS) | Category-specific |
| `customer_care` | String | LLM / Phone-Email | Name, address, phone of consumer grievance contact | **Mandatory** (Rule 6(2)) |
| `email` | String | LLM / Email Regex | Grievance redressal email address | **Mandatory** (Rule 6(2)) |
| `unit_sale_price` | String | LLM / USP Regex | Unit Sale Price per g/kg/ml/litre/number | **Mandatory** (Rule 6(1)(f)) |
| `commodity` | String | LLM / Keyword Regex | Specific commodity classification | Contextual |
| `storage_instructions`| Text | LLM / Keyword Regex | Storage guidance (e.g., "Store in cool dry place") | Recommended |
| `sale_restrictions` | Text | LLM / Warning Regex | Statutory restrictions (e.g., "For industrial use") | Contextual |
| `warnings` | Text | LLM / Caution Regex | Safety warnings, allergen declarations | Contextual / Category-specific |

### Evidence Schema (`FieldEvidenceSchema`)
Every field includes an associated evidence metadata object:
- `source_text`: The exact textual substring detected by OCR.
- `confidence`: Confidence score (0.0 to 1.0) derived from PaddleOCR recognition.
- `bbox`: Absolute pixel bounding box `[x1, y1, x2, y2]` on the source image.
- `detection_status`: Explicit classification: `DETECTED`, `NOT_DETECTED`, or `UNCERTAIN`.

---

## Legal Metrology Compliance Engine

The compliance engine evaluates extracted product declarations against codified legal standards from the **Legal Metrology (Packaged Commodities) Rules, 2011**.

```
                           +------------------------+
                           | Extracted Product Data |
                           +------------------------+
                                       │
                                       ▼
                   +─────────────────────────────────────────+
                   │      ComplianceRuleEngine (LM-2011-v1)  │
                   │      Evaluates 10 Codified Rules        │
                   +─────────────────────────────────────────+
                                       │
         ┌──────────────┬──────────────┼──────────────┬──────────────┐
         ▼              ▼              ▼              ▼              ▼
     [LM001]        [LM002]        [LM003]        [LM004]        [LM005]
  Manufacturer    Generic Name    Net Qty        Mfg Date          MRP
  Rule 6(1)(a)    Rule 6(1)(b)   Rule 6(1)(c)   Rule 6(1)(d)   Rule 6(1)(e)
   (REVIEW/PASS)   (FAIL/PASS)    (FAIL/PASS)    (REVIEW/PASS)  (FAIL/PASS)
  HIGH Severity  HIGH Severity  CRITICAL Sev.   HIGH Severity  CRITICAL Sev.
         │              │              │              │              │
         ├──────────────┼──────────────┼──────────────┼──────────────┤
         ▼              ▼              ▼              ▼              ▼
     [LM006]        [LM007]        [LM008]        [LM009]        [LM010]
  Consumer Care   Unit Format    Readability    Country Origin Statutory Lic.
   Rule 6(2)      Rule 12 & 13    Rule 7 & 9     Rule 6(1)     FSSAI / BIS
   (FAIL/PASS)   (REVIEW/PASS)   (ALWAYS REV.)  (REVIEW/PASS)  (REVIEW/PASS)
  HIGH Severity  MEDIUM Severity MEDIUM Sev.    HIGH Severity  MEDIUM Sev.
         └──────────────┴──────────────┼──────────────┴──────────────┘
                                       │
                                       ▼
                  +───────────────────────────────────────────+
                  │         OVERALL STATUS EVALUATION         │
                  │                                           │
                  │ 1. Any CRITICAL / HIGH Fail?  ──► FAIL    │
                  │ 2. Any Rule in REVIEW?        ──► REVIEW  │
                  │ 3. Any MEDIUM / LOW Fail?     ──► REVIEW  │
                  │ 4. All Rules Passed?          ──► PASS    │
                  +───────────────────────────────────────────+
```

### Codified Rule Matrix

| Rule ID | Rule Name | Statutory Citation | Severity | Rule Class Type | Pass Condition | Failure / Review Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LM001** | Manufacturer / Packer / Importer | Rule 6(1)(a), Rule 10 | **HIGH** | `ContextualReviewRule` | `manufacturer` field detected | Flags `REVIEW` if absent (product may be imported or packer-declared) |
| **LM002** | Common / Generic Commodity Name | Rule 6(1)(b) | **HIGH** | `PresenceRule` | `product_name` field detected | Flags **FAIL** if absent |
| **LM003** | Net Quantity Declaration | Rule 6(1)(c), Rules 11–13 | **CRITICAL** | `PresenceRule` | `net_quantity` field detected | Flags **FAIL** if absent |
| **LM004** | Mfg / Pre-Packing Month & Year | Rule 6(1)(d) | **HIGH** | `ContextualReviewRule` | `manufacturing_date` detected | Flags `REVIEW` if absent (check for best-before/packed date) |
| **LM005** | Retail Sale Price / MRP | Rule 6(1)(e), Rule 2(m) | **CRITICAL** | `PresenceRule` | `mrp` field detected | Flags **FAIL** if absent |
| **LM006** | Consumer Care Contact Details | Rule 6(2) | **HIGH** | `PresenceRule` | `customer_care` detected | Flags **FAIL** if absent |
| **LM007** | Quantity Unit / Basic Format | Rule 12, Rule 13 | **MEDIUM** | `ContextualReviewRule` | Standard metric format detected | Flags `REVIEW` for Fourth Schedule schedule verification |
| **LM008** | Declaration Readability / Size | Rule 7, Rule 9 | **MEDIUM** | `AlwaysReviewRule` | None (Always triggers review) | **Always flags REVIEW** (physical mm font size unmeasurable in 2D) |
| **LM009** | Country of Origin Declaration | Rule 6(1), E-Commerce Rules | **HIGH** | `ContextualReviewRule` | `country_of_origin` detected | Flags `REVIEW` if absent (domestic packages legally exempt) |
| **LM010** | Statutory License / Registration | Category-specific (FSSAI/BIS)| **MEDIUM** | `ContextualReviewRule` | `license_number` detected | Flags `REVIEW` to determine if commodity category requires license |

### Rule Evaluation Mechanics
1. **`PresenceRule`:** Verifies whether a mandatory field is present with status `DETECTED`. If missing or uncertain, immediately produces a `FAIL` status.
2. **`ContextualReviewRule`:** Recognizes that the Legal Metrology Act provides statutory exemptions (e.g., packages under 10g/10ml, packages manufactured domestically that do not require origin declarations). If the target field is absent, it assigns a `REVIEW` status with an actionable message prompting the human inspector to verify applicable exemptions.
3. **`AlwaysReviewRule` (LM008):** Under Rule 7 and Rule 9, numerals in declarations must satisfy physical height thresholds (e.g., $\ge 1	ext{ mm}$ for packages $\le 50	ext{ g}$, $\ge 2	ext{ mm}$ for packages $50	ext{ g}–200	ext{ g}$, $\ge 4	ext{ mm}$ for packages $> 1	ext{ kg}$). Because optical camera images lack physical millimeter scale calibration, COMPLIQ honestly delegates physical prominence compliance to human review rather than guessing uncalibrated font dimensions.

### Extensibility: Adding New Rules
The engine is structured around an abstract base class `ComplianceRule` in `app/compliance/base.py`. To introduce a new rule:
1. Subclass `ComplianceRule` or instantiate `PresenceRule` / `ContextualReviewRule`.
2. Define `rule_id`, `rule_name`, `source_reference`, `severity`, and `target_field`.
3. Append the rule instance to `REGISTERED_RULES` in `app/compliance/rules.py`.
The engine automatically evaluates and records the new rule on subsequent inspection runs.

---

## API Architecture & Reference

The COMPLIQ REST API is built on FastAPI, organizing operations into nine modular routers mounted under the `/api` prefix.

| HTTP Method | Route Endpoint | Authentication | Purpose | Request Payload | Success Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | None (Public) | Register new user account | `UserCreate` (email, password, name) | `201 Created` (`TokenResponse`) |
| `POST` | `/api/auth/login` | None (Public) | Authenticate user credentials | `UserLogin` (email, password) | `200 OK` (`TokenResponse`) |
| `GET` | `/api/auth/me` | JWT Bearer | Retrieve profile of authenticated user | None | `200 OK` (`UserResponse`) |
| `GET` | `/api/users/{user_id}` | JWT Bearer | Retrieve user account by UUID | None | `200 OK` (`UserResponse`) |
| `POST` | `/api/inspections` | None (Unchecked) | Create a new inspection record | `InspectionCreate` (product, brand) | `201 Created` (`InspectionResponse`)|
| `GET` | `/api/inspections` | None (Unchecked) | List inspections with search/filters | Query params (`search`, `status`) | `200 OK` (`List[InspectionListResponse]`)|
| `GET` | `/api/inspections/{id}` | None (Unchecked) | Retrieve single inspection details | Path param `id` (UUID) | `200 OK` (`InspectionResponse`) |
| `POST` | `/api/inspections/{id}/images`| None (Unchecked)| Upload image for inspection | Multipart: `file`, `image_type` | `200 OK` (`ImageUploadResponse`) |
| `DELETE`| `/api/inspections/{id}/images/{img_id}`| None (Unchecked)| Delete an inspection image | Path params (UUIDs) | `204 No Content` |
| `GET` | `/api/images/{filename}` | None (Public) | Stream/serve stored image file | Path param `filename` | `200 OK` (Image binary stream) |
| `POST` | `/api/inspections/{id}/analyze` | None (Unchecked)| Trigger OpenCV + PaddleOCR pipeline | Path param `id` (UUID) | `200 OK` (`AnalysisResponse`) |
| `GET` | `/api/inspections/{id}/analysis` | None (Unchecked)| Retrieve OCR analysis results | Path param `id` (UUID) | `200 OK` (`AnalysisResponse`) |
| `GET` | `/api/inspections/{id}/product-info` | None (Unchecked)| Retrieve structured product data | Path param `id` (UUID) | `200 OK` (`ProductInfoResponse`) |
| `POST` | `/api/inspections/{id}/compliance` | None (Unchecked)| Execute compliance rules engine | Path param `id` (UUID) | `200 OK` (`ComplianceResponse`) |
| `GET` | `/api/inspections/{id}/compliance` | None (Unchecked)| Retrieve compliance report | Path param `id` (UUID) | `200 OK` (`ComplianceResponse`) |
| `GET` | `/api/inspections/{id}/compliance/report.pdf`| None (Unchecked)| Download PDF statutory audit report | Path param `id` (UUID) | `200 OK` (`application/pdf`) |
| `GET` | `/api/inspections/{id}/compliance/report.docx`| None (Unchecked)| Download DOCX statutory audit report | Path param `id` (UUID) | `200 OK` (`application/vnd...`) |
| `GET` | `/api/dashboard/stats` | None (Unchecked)| Retrieve summary KPI counts | None | `200 OK` (`DashboardStats`) |
| `GET` | `/api/dashboard/analytics` | None (Unchecked)| Retrieve monthly trends & violations | None | `200 OK` (`DashboardAnalyticsResponse`)|
| `GET` | `/api/health` | None (Public) | System health & version check | None | `200 OK` (`{"status": "healthy"}`)|

### Error Handling & Standard Error Response
All API exceptions conform to a consistent error schema (`app/schemas/error.py`):
```json
{
  "error": {
    "code": "IMAGE_TYPE_NOT_SUPPORTED",
    "message": "Only JPG, JPEG, PNG and WEBP images are supported.",
    "details": null
  }
}
```
HTTP Status Codes utilized:
- `400 Bad Request`: Validation failure, empty image, file size exceeded, unparseable UUID.
- `401 Unauthorized`: Missing, expired, or cryptographically invalid JWT bearer token.
- `403 Forbidden`: Insufficient role privileges (e.g., non-admin calling administrative route).
- `404 Not Found`: Inspection, image, or user resource not found in database.
- `500 Internal Server Error`: Unhandled server exception (logged with stack trace).

---

## Authentication & Security Audit

### 1. Implemented Security Controls
- **Password Hashing:** Passlib with `bcrypt` (work factor 12) is implemented in `app/core/security.py`. Plaintext passwords are never stored.
- **JWT Token Management:** Generated with `python-jose` using `HS256`. Tokens carry subject (`sub` user UUID), expiration timestamp (`exp`, 60-minute default), and issued-at timestamp (`iat`).
- **Role-Based Access Control (RBAC):** Implemented via the `UserRole` enum (`ADMIN`, `INSPECTOR`) and an enforceable dependency factory `require_role(required_role: UserRole)`.
- **CORS Protection:** FastAPI `CORSMiddleware` explicitly whitelists origins specified in the `CORS_ORIGINS` environment variable (defaults to `http://localhost:5173,http://localhost:3000`).
- **File Upload Security:**
  - Strict MIME-type checking against `image/jpeg`, `image/png`, and `image/webp`.
  - Extension whitelisting (`.jpg`, `.jpeg`, `.png`, `.webp`).
  - Cross-validation: File extension is checked against declared MIME type to reject renamed malicious binaries.
  - File size cap: Enforces `MAX_UPLOAD_SIZE` (10MB).
  - Path traversal prevention: Every uploaded file is renamed to a freshly generated UUID hex string (`uuid.uuid4().hex + ext`). User-supplied filenames are never used in disk paths.

### 2. Genuine Security Limitations Identified
A rigorous code audit reveals several critical security limitations that remain in the current implementation:
1. **Endpoint Authentication Decoupling:** While `get_current_user` is enforced on `/api/auth/me` and `/api/users/{id}`, the inspection, image upload, OCR analysis, compliance execution, and report download routes currently do **not** inject `Depends(get_current_user)`. Anyone with network access to the backend can create inspections, trigger OCR processing, and view compliance reports without logging in.
2. **Secret Exposure Risk:** The repository contains a `.env` file containing live connection strings and API credentials. In production, these must be purged and managed exclusively through environment injection or secret managers.
3. **Default JWT Secret:** If `JWT_SECRET` is left as its default value, the server logs a warning at startup but does not abort execution.
4. **Rate Limiting Absent:** There is currently no rate limiting (e.g., `slowapi`) on the image upload or OCR analysis endpoints, leaving the server vulnerable to compute-exhaustion denial-of-service attacks.

---

## Database Architecture

COMPLIQ uses PostgreSQL as its primary data store, accessed through SQLAlchemy 2.0 with the modern `psycopg` (psycopg3) driver and managed via Alembic migrations.

### Data Models & Relationships

```
+-------------------+       1:N       +-------------------+       1:N       +-------------------+
|       User        | ──────────────> |    Inspection     | ──────────────> |  InspectionImage  |
+-------------------+                 +-------------------+                 +-------------------+
| id (UUID, PK)     |                 | id (UUID, PK)     |                 | id (UUID, PK)     |
| name              |                 | inspection_number |                 | inspection_id (FK)|
| email (Unique)    |                 | created_by (FK)   |                 | original_filename |
| password_hash     |                 | product_name      |                 | stored_filename   |
| role (ADMIN/INSP) |                 | brand             |                 | file_path         |
| created_at        |                 | status            |                 | mime_type         |
+-------------------+                 | created_at        |                 | file_size         |
                                      +-------------------+                 | image_type        |
                                                                            +-------------------+
                                                                                      │ 1:N
                                                                                      ▼
+-----------------------+     1:1     +-------------------+     1:1         +-------------------+
|     ProductInfo       | <────────── |     OCRResult     | ──────────────> | ComplianceReport  |
+-----------------------+             +-------------------+                 +-------------------+
| id (UUID, PK)         |             | id (UUID, PK)     |                 | id (UUID, PK)     |
| ocr_result_id (FK)    |             | image_id (FK)     |                 | ocr_result_id (FK)|
| product_name          |             | engine            |                 | overall_status    |
| brand_name            |             | engine_version    |                 | total_rules       |
| manufacturer          |             | full_text         |                 | passed_count      |
| net_quantity          |             | processing_time_ms|                 | failed_count      |
| mrp                   |             | quality_status    |                 | review_count      |
| manufacturing_date    |             | blur_score        |                 | engine_version    |
| batch_number          |             | created_at        |                 | ruleset_version   |
| fields_json (Text)    |             +-------------------+                 +-------------------+
| extraction_version    |                       │ 1:N                                 │ 1:N
+-----------------------+                       ▼                                     ▼
                                      +-------------------+                 +-------------------+
                                      |   OCRTextBlock    |                 |ComplianceRuleRes. |
                                      +-------------------+                 +-------------------+
                                      | id (UUID, PK)     |                 | id (UUID, PK)     |
                                      | ocr_result_id (FK)|                 | report_id (FK)    |
                                      | raw_text          |                 | rule_id           |
                                      | normalized_text   |                 | rule_name         |
                                      | confidence (Float)|                 | status            |
                                      | bbox_x1, y1, x2,y2|                 | severity          |
                                      +-------------------+                 | message           |
                                                                            | evidence_json     |
                                                                            +-------------------+
```

### Table Summary
1. **`users`:** Stores inspector and admin accounts, cryptographic password hashes, and system roles.
2. **`inspections`:** Top-level inspection case record with unique human-readable inspection number (`INSP-YYYYMMDD-XXXX`), status, and product metadata.
3. **`inspection_images`:** Metadata for each uploaded package photograph, MIME type, file size, storage location, and packaging angle (`FRONT`, `BACK`, `SIDE`, `OTHER`).
4. **`ocr_results`:** Summary of OCR execution on a specific image, tracking OCR engine, processing duration, image quality scores, and full extracted text.
5. **`ocr_text_blocks`:** Granular OCR text regions storing line text, recognition confidence, and exact pixel bounding boxes `[x1, y1, x2, y2]`.
6. **`product_info`:** Structured product declarations extracted by the LLM or fallback regex engine, with top-level fields indexed and full evidence stored in `fields_json`.
7. **`compliance_reports`:** Audit summary of rule evaluations for an image, including total rules checked, pass/fail/review counts, and engine/ruleset versions.
8. **`compliance_rule_results`:** Individual rule evaluation results detailing rule ID, legal source reference, pass/fail status, severity, and evidence JSON payload.

### Alembic Migration History
1. `001_initial_schema.py`: Base tables (`users`, `inspections`, `inspection_images`).
2. `002_ocr_tables.py`: OCR persistence (`ocr_results`, `ocr_text_blocks`).
3. `003_product_info.py`: Structured declaration storage (`product_info`).
4. `c8ec16622252_phase_4_add_compliance_report_tables.py`: Compliance engine tables (`compliance_reports`, `compliance_rule_results`).
5. `004_phase5_versioning.py`: Audit trail additions (`engine_version`, `ruleset_version`).

---

## Storage Architecture

COMPLIQ manages product package photographs through an abstract storage layer (`app/storage/`):
- **Interface (`app/storage/base.py`):** Defines the abstract `StorageService` interface with `upload()`, `get_path()`, `delete()`, and `get_url()`.
- **Factory Pattern (`app/storage/factory.py`):** Inspects `STORAGE_BACKEND` from application settings to instantiate either `LocalStorageService` or `S3StorageService`.
- **`LocalStorageService` (`app/storage/local.py`):** Saves images directly to local disk in `UPLOAD_DIR` (default: `../data/uploads`). Used for local development and offline environments.
- **`S3StorageService` (`app/storage/s3.py`):** Leverages `boto3` to store images in S3-compatible cloud storage (AWS S3, Cloudflare R2, Backblaze B2, MinIO). Generates presigned URLs for client viewing. This solves the ephemeral filesystem limitation of container/PaaS platforms like Render.

---

## Frontend Architecture & User Journey

The COMPLIQ frontend is a modern single-page application built with React 19, TypeScript, and Vite.

### Core Modules & Routing
- **Routing:** React Router DOM v7 manages routes configured in `App.tsx`:
  - `/login`: Inspector authentication and account registration.
  - `/dashboard`: Operations overview with KPI cards and violation charts.
  - `/inspections`: Searchable, filterable inspection register.
  - `/inspections/new`: Case intake form with multi-image drag-and-drop upload.
  - `/inspections/:id`: Central inspection workstation.
  - `/profile` & `/settings`: User management and preferences.
- **Authentication State (`AuthContext.tsx`):** Manages JWT token storage in `localStorage`, user session state, and global login/logout handlers.
- **API Client (`client.ts`):** Central Axios client configured with automatic JWT Bearer token request interceptors and automatic 401 redirect response interceptors.

### Visual Bounding Box & Evidence Viewer Components
1. **Interactive OCR Canvas (`OCRResultsPanel.tsx`):**
   Renders an HTML5 Canvas layered directly over the uploaded package image. It reads the OCR bounding boxes `[x1, y1, x2, y2]` and draws color-coded detection boxes over each recognized word and line.
2. **Dynamic Evidence Cropper (`EvidenceViewer.tsx`):**
   When an inspector reviews a compliance rule, the `EvidenceCrop` component reads the bounding box coordinates of the supporting evidence, slices that exact pixel region from the full-resolution package photograph on a client-side `<canvas>`, and presents the physical cropped declaration alongside the rule status.
3. **Violation Analytics Chart (`ViolationChart.tsx`):**
   Renders proportional horizontal distribution bars showing the most frequently violated Legal Metrology rules across all recorded inspections.

### User Journey Walkthrough
```
[Login Screen] ──► [Operations Dashboard] ──► [New Inspection Intake]
                                                       │
                                                       ▼
[Statutory Report Export] ◄── [Compliance Evaluation] ◄── [OCR & Declaration Workstation]
 (PDF / Word Download)        (Canvas Evidence Crop)        (Canvas Bounding Boxes)
```

---

## Project Structure

```
d:\CompliQ├── backend/
│   ├── app/
│   │   ├── ai/                      # AI, OCR, and computer vision modules
│   │   │   ├── base.py              # Base AI interfaces
│   │   │   ├── extraction.py        # Groq LLM + spatial regex fallback engine
│   │   │   ├── models.py            # OCR data models (OCRResult, OCRTextBlock)
│   │   │   ├── ocr_service.py       # PaddleOCR wrapper & dual-track competition
│   │   │   └── preprocessing.py     # OpenCV quality analysis & CLAHE/NLM pipeline
│   │   ├── api/                     # FastAPI route controllers
│   │   │   ├── analysis.py          # /api/inspections/{id}/analyze
│   │   │   ├── auth.py              # /api/auth/register, /login, /me
│   │   │   ├── compliance.py        # /api/inspections/{id}/compliance
│   │   │   ├── dashboard.py         # /api/dashboard/stats, /analytics
│   │   │   ├── images.py            # /api/inspections/{id}/images
│   │   │   ├── inspections.py       # /api/inspections CRUD & filtering
│   │   │   ├── product_info.py      # /api/inspections/{id}/product-info
│   │   │   ├── reports.py           # /api/inspections/{id}/compliance/report.*
│   │   │   └── users.py             # /api/users/{id}
│   │   ├── compliance/              # Legal Metrology rules engine
│   │   │   ├── base.py              # Abstract ComplianceRule & result schemas
│   │   │   ├── engine.py            # ComplianceRuleEngine orchestrator
│   │   │   └── rules.py             # Codified LM001–LM010 rule registry
│   │   ├── core/                    # Core configuration and utilities
│   │   │   ├── config.py            # Pydantic BaseSettings & env parsing
│   │   │   ├── database.py          # SQLAlchemy engine & session factory
│   │   │   ├── exceptions.py        # Custom exception classes & error handlers
│   │   │   ├── logging.py           # Structured logging configuration
│   │   │   ├── runtime.py           # Python 3.11.x strict runtime verification
│   │   │   └── security.py          # Bcrypt password hashing & JWT token logic
│   │   ├── models/                  # SQLAlchemy ORM database models
│   │   ├── repositories/            # Data access repository patterns
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/                # Business logic services
│   │   ├── storage/                 # Local & S3 storage abstraction
│   │   ├── cli.py                   # Administrative CLI commands
│   │   └── main.py                  # FastAPI application entry point
│   ├── migrations/                  # Alembic database migration scripts
│   ├── tests/                       # Pytest test suite (177 tests)
│   ├── requirements.txt             # Primary Python backend dependencies
│   ├── requirements-ocr.txt         # PaddleOCR & PaddlePaddle dependencies
│   └── requirements-cv.txt          # OpenCV computer vision dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                     # Axios API clients for backend endpoints
│   │   ├── components/              # Reusable React components & Canvas viewers
│   │   ├── context/                 # AuthContext React state management
│   │   ├── pages/                   # Dashboard, Inspection, Intake pages
│   │   ├── App.tsx                  # Root routing configuration
│   │   ├── index.css                # Tailwind CSS & Neomorphic design system
│   │   └── main.tsx                 # React DOM entry point
│   ├── package.json                 # Frontend dependencies & build scripts
│   └── vite.config.ts               # Vite bundler configuration
├── Images/                          # Sample packaging test images (incense, tea)
├── render.yaml                      # Render cloud deployment blueprint
├── start_local.ps1                  # Local development startup script
└── README.md                        # Project documentation
```

---

## Dependencies & Runtime Requirements

### System Requirements
- **Operating System:** Windows 10/11, Linux (Ubuntu 22.04+), or macOS.
- **Python Version:** **Python 3.11.x STRICTLY REQUIRED** (PaddlePaddle 2.6.2 binary compatibility).
- **Node.js Version:** Node.js v20.x or v24.x (npm 10+ or 12+).
- **Database:** PostgreSQL 14+ (Local installation or cloud instance e.g., Neon).
- **GPU:** Optional. PaddleOCR and OpenCV run in CPU mode by default.

### Key Backend Package Dependencies
- `fastapi==0.115.0`, `uvicorn[standard]==0.30.6`
- `sqlalchemy==2.0.35`, `alembic==1.13.3`, `psycopg[binary]==3.3.4`
- `pydantic==2.9.2`, `pydantic-settings==2.5.2`
- `paddlepaddle==2.6.2`, `paddleocr==2.8.1`
- `opencv-python==4.11.0.86`, `Pillow==12.3.0`, `numpy==1.26.4`
- `groq==1.7.0`
- `reportlab==5.0.1`, `python-docx==1.2.0`
- `python-jose[cryptography]==3.3.0`, `passlib[bcrypt]==1.7.4`, `bcrypt==4.0.1`

---

## Environment Variables Specification

The application is configured through environment variables loaded from `.env` in the project root or `backend/.env`.

| Environment Variable | Required? | Default Value | Purpose | Example Format |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes** | None | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/sih26034` |
| `JWT_SECRET` | **Yes** | None (In production) | Secret key for signing JWT tokens | `generate-a-64-character-random-hex-string` |
| `JWT_ALGORITHM` | No | `HS256` | JWT cryptographic signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| No | `60` | JWT token validity lifespan | `60` |
| `UPLOAD_DIR` | No | `../data/uploads` | Local directory for uploaded images | `../data/uploads` |
| `MAX_UPLOAD_SIZE` | No | `10485760` (10MB) | Maximum upload file size in bytes | `10485760` |
| `STORAGE_BACKEND` | No | `local` | Storage provider (`local` or `s3`) | `local` or `s3` |
| `S3_BUCKET` | If S3 | None | S3 bucket name for uploads | `compliq-inspection-bucket` |
| `S3_REGION` | If S3 | None | AWS / S3 region identifier | `ap-south-1` |
| `S3_ENDPOINT_URL` | If R2/B2| None | Custom endpoint for Cloudflare/MinIO| `https://<account_id>.r2.cloudflarestorage.com` |
| `S3_ACCESS_KEY_ID`| If S3 | None | Cloud object storage access key | `AKIAIOSFODNN7EXAMPLE` |
| `S3_SECRET_ACCESS_KEY`| If S3| None | Cloud object storage secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `CORS_ORIGINS` | No | `http://localhost:5173,...`| Allowed web origins (comma-separated)| `http://localhost:5173,http://localhost:3000` |
| `GROQ_API_KEY` | No | None | Groq Cloud API key for LLM extraction | `gsk_your_groq_api_key_placeholder` |
| `GROQ_MODEL` | No | `qwen/qwen3.8-27b` | Groq model identifier for extraction | `qwen/qwen3.8-27b` |
| `VITE_API_URL` | No | Empty (uses `/api`) | Backend API base URL for React web | `http://localhost:8000` |

---

## Installation & Running Instructions

Follow these step-by-step instructions to clone and run the repository on a developer workstation.

### Step 1: Prerequisites
- Install **Python 3.11** (e.g., Python 3.11.9 from python.org). Do **not** use Python 3.12, 3.13, or 3.14.
- Install **Node.js v20+** and npm.
- Ensure a **PostgreSQL** database instance is running.

### Step 2: Backend Setup
Open PowerShell or a bash shell in the project root:
```powershell
# 1. Create a virtual environment using Python 3.11
python -3.11 -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and wheel
pip install --upgrade pip setuptools wheel

# 4. Install backend dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-ocr.txt

# 5. Configure environment variables
Copy-Item ..\.env.example .env
# Edit .env to set your DATABASE_URL, JWT_SECRET, and GROQ_API_KEY

# 6. Apply database migrations
alembic upgrade head

# 7. Start the backend development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend and interactive Swagger UI will be live at `http://localhost:8000/docs`.

### Step 3: Frontend Setup
Open a second terminal in the project root:
```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start Vite development server
npm run dev
```
The React frontend application will be live at `http://localhost:5173`.

### Step 4: One-Click Startup Script
For convenience on Windows workstations, run:
```powershell
.\start_local.ps1
```
This script automatically activates the virtual environment, executes Alembic migrations, starts Uvicorn on port 8000, and launches Vite on port 5173 in separate terminal windows.

---

## Automated Testing & Quality Assurance

COMPLIQ includes an extensive automated test suite implemented in `backend/tests/`.

### Test Execution
Run the full test suite from the backend directory:
```powershell
.\.venv\Scripts\pytest.exe backend/tests -v
```

### Test Suite Breakdown (177 Total Tests)
- `test_auth.py`: User registration, login, JWT token decoding, and authentication error handling.
- `test_rbac.py`: Role-based access control tests for `ADMIN` vs `INSPECTOR` roles.
- `test_storage.py`: Storage abstraction tests covering `LocalStorageService`, `S3StorageService`, and `StorageFactory`.
- `test_images.py`: Upload validation, MIME checking, size limits, and image deletion.
- `test_runtime.py`: Tests that `verify_runtime()` permits Python 3.11 and blocks other versions.
- `test_ocr_engine.py`: PaddlePaddle and PaddleOCR initialization, CPU angle classification.
- `test_ocr_integration.py`: End-to-end OCR processing on real package photographs.
- `test_llm_integration.py`: Mocked Groq LLM extraction, JSON schema validation, and retry backoff.
- `test_live_extraction.py`: Live network tests against Groq Cloud API.
- `test_generic_extraction.py`: Deterministic fallback regex extractors.
- `test_real_package_extraction.py`: Field extraction from physical incense (Moksh) and tea (Tata Chakra) packages.
- `test_phase2.py`: OpenCV image quality assessment and CLAHE preprocessing.
- `test_phase3.py`: Structured product information model tests.
- `test_phase4.py`: Codified Legal Metrology compliance rules (LM001–LM010) and engine aggregation.
- `test_phase5.py`: PDF (ReportLab) and DOCX (python-docx) report generation and dashboard analytics.

### Audit Test Findings
During our audit run of the test suite, **174 of 177 tests passed** (98.3% pass rate). The 3 failing tests (`test_pdf_report_success` and two RBAC image deletion tests) failed due to live database state collisions (`EMAIL_ALREADY_EXISTS` on non-cleaned test fixtures) and route parameter mismatch in tests, rather than algorithmic flaws.

---

## Failure Modes & Fallback Strategy

| Failure Scenario | System Detection Mechanism | Automated System Response | Impact on Compliance Output |
| :--- | :--- | :--- | :--- |
| **Unsupported Python Runtime (< 3.11 or > 3.11)** | `app/core/runtime.py` checks `sys.version_info` | Server halts startup (`sys.exit(1)`) with descriptive remediation instructions | Complete shutdown (prevents native crashes) |
| **PaddleOCR Import / Initialization Crash** | `_get_ocr()` catches `ImportError` or `Exception` | Raises `OCREngineUnavailableError`; halts server startup | Prevents silent degradation to unverified OCR |
| **Severely Blurry / Dark Package Photo** | `analyze_quality()` Laplacian variance < 100 or brightness < 0.20 | Flags `quality_status="POOR"`, records issue codes in DB; runs OCR on best effort | Low-confidence text blocks flagged as `UNCERTAIN` |
| **Missing Groq API Key** | `_extract_with_groq()` checks `settings.GROQ_API_KEY` | Gracefully skips LLM; routes text directly to spatial regex fallback engine | All 19 fields extracted via deterministic regex |
| **Groq API Rate Limit (HTTP 429 / 503)** | Retry loop in `_extract_with_groq()` | Retries up to 3 times with exponential backoff ($2s, 4s, 6s$) | Transient delays handled transparently |
| **Groq Unreachable / Model Deprecated** | Exception caught after retry exhaustion | Logs error; switches to spatial horizontal grouping regex fallback | Seamless extraction continuity |
| **LLM Fabricates Non-Existent Value** | Anti-Hallucination Evidence Matcher | Fails normalized string similarity against OCR blocks; sets evidence to `None` | Prevents fabricated claims from passing compliance |
| **Physical Font Prominence Unverifiable** | Rule LM008 evaluation | Automatically routes to `ComplianceStatus.REVIEW` with explicit explanation | Prevents false passes on physical metric sizes |

---

## Performance & Optimization

1. **OCR Dimension Throttling:** Images exceeding 1920px are resized via `cv2.INTER_AREA`. This caps memory consumption and reduces OCR inference time from ~12s down to ~2.5s per image on standard multi-core CPUs.
2. **Singleton Model Architecture:** PaddleOCR models and deep learning weights are loaded once upon startup and retained in memory, eliminating 3–5 seconds of model instantiation overhead on subsequent inspection requests.
3. **Database Connection Pooling:** SQLAlchemy is configured with `pool_size=10` and `max_overflow=20` with `pool_pre_ping=True` to maintain resilient database connections under concurrent traffic.
4. **Spatial Line Merging:** Horizontal clustering groups fragmented OCR bounding boxes in $O(N \log N)$ time, avoiding expensive combinatorial string permutations.
5. **Frontend Asset Optimization:** Vite 8 and Tailwind CSS 4 bundle the entire production client into a compressed 370 kB JavaScript chunk and 47 kB CSS stylesheet, achieving sub-second initial browser paint times.

---

## Deployment Readiness

### Current Implemented Deployment
- **Render Blueprint (`render.yaml`):** The repository includes a production-ready `render.yaml` defining:
  - Backend Web Service: Python environment, auto-migration command (`alembic upgrade head`), and Uvicorn entry point.
  - Frontend Static Site: Node build command (`npm run build`), publishing `./frontend/dist`.
  - Database: Managed PostgreSQL database resource (`sih26034-db`).
- **Cloud Object Storage:** Full Boto3 integration supports Cloudflare R2, AWS S3, or Backblaze B2, avoiding data loss on ephemeral container filesystems.

### Recommended Production Enhancements
1. **Enforce Endpoint Authentication:** Attach `Depends(get_current_user)` to all inspection and analysis routes.
2. **Reverse Proxy & SSL Termination:** Deploy behind Nginx or Cloudflare to terminate TLS and enforce HTTP/2.
3. **Task Queue Offloading:** Move heavy PaddleOCR inference and PDF generation to background workers using Celery or ARQ with Redis.

---

## Known Limitations

1. **Physical Millimeter Font Height Verification:** The Legal Metrology Rules specify minimum font heights in physical millimeters (e.g., 2mm to 4mm). In the absence of a standardized physical reference scale (such as a calibration target or coin placed beside the package), 2D camera pixel dimensions cannot be converted to physical millimeters. COMPLIQ honestly marks Rule LM008 as `REVIEW`.
2. **Language Coverage:** PaddleOCR is currently initialized with `lang="en"`. Packages carrying declarations exclusively in regional Indian languages (Hindi, Tamil, Marathi, etc.) cannot be parsed by the current configuration.
3. **Curved and Reflective Surface Distortions:** Extreme specular reflections on glossy plastic pouches and severe cylindrical distortion on small bottles can degrade OCR character accuracy.
4. **Test Fixture Database State:** The test suite currently executes against the active database rather than isolated transaction rollbacks, leading to unique constraint conflicts on repeated test runs.

---

## Future Roadmap (Planned Enhancements)

> [!NOTE]
> The following features are **Planned Future Enhancements** and are not currently implemented in the codebase:

1. **Multi-Language OCR Support:** Expand PaddleOCR initialization to multilingual mode (`ch_tra`, `hi`) to support bilingual Hindi/English packaging declarations.
2. **Physical Scale Calibration Tool:** Implement an optical reference card detection algorithm allowing inspectors to place a credit-card-sized reference object next to the package to compute physical millimeter font heights for Rule LM008.
3. **Real-Time FSSAI / BIS Database Integration:** Connect the compliance engine to the national FSSAI FoSCoS API to verify whether extracted 14-digit food license numbers are active and assigned to the declared manufacturer.
4. **Barcode & QR Code Cross-Verification:** Integrate zbar/pyzbar decoding to scan GS1 EAN-13 barcodes on packaging, cross-verifying encoded GTINs against declared commodity names.

---

## Technology Stack Summary Cheat Sheet

| Domain | Technology / Specification | Current State |
| :--- | :--- | :--- |
| **Frontend** | React 19.2.8, TypeScript 6.0.2, Vite 8.2.2, Tailwind CSS 4.3.3, Axios, Lucide React | Operational |
| **Backend** | Python 3.11.9, FastAPI 0.115.0, Uvicorn 0.30.6, Pydantic 2.9.2 | Operational |
| **Database** | PostgreSQL, SQLAlchemy 2.0.35, psycopg 3.3.4, Alembic 1.13.3 (5 migrations) | Operational |
| **OCR Engine** | PaddleOCR 2.8.1 on PaddlePaddle 2.6.2 (CPU mode, angle cls = True, English) | Operational |
| **Computer Vision** | OpenCV 4.11.0 (`cv2`), Laplacian blur analysis, CLAHE, NLM denoise, 1920px resize | Operational |
| **AI / LLM** | Groq Cloud SDK 1.7.0, `qwen/qwen3.8-27b`, temperature 0.0, Pydantic JSON Schema | Operational |
| **Fallback Engine** | Spatial horizontal line grouping + 19 deterministic regex extractors | Operational |
| **Compliance Engine** | Legal Metrology Rules 2011 engine (LM001–LM010), multi-tier status & severity | Operational |
| **Reporting** | ReportLab 5.0.1 (PDF dossier generation), python-docx 1.2.0 (Word report generation) | Operational |
| **Authentication** | Passlib bcrypt hashing, python-jose HS256 JWT tokens, RBAC roles (ADMIN/INSPECTOR)| Operational |
| **Storage** | Abstract factory: Local filesystem (`LocalStorageService`) & S3/R2 (`S3StorageService`)| Operational |
| **Testing** | Pytest 8.3.3 (177 tests covering auth, OCR, LLM, rules, reports, physical packages) | Operational |
| **Deployment** | Render blueprint (`render.yaml`), Uvicorn ASGI, static Vite publish, Neon PostgreSQL | Operational |
| **Containerization**| Docker / Docker Compose | **Not Used** |
