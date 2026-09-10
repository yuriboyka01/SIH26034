# SIH26034 — Legal Metrology Compliance System

Software system to check compliance of Packaged Commodities under **Legal Metrology (Packaged Commodities) Rules, 2011** by scanning products, images and labels.

## 🏗️ Architecture

```
┌──────────────────┐
│   React Frontend │  (Vite + TypeScript + Tailwind CSS)
└────────┬─────────┘
         │  REST API
         ▼
┌──────────────────┐
│     FastAPI       │  (Python + Pydantic + SQLAlchemy)
└────────┬─────────┘
         │
    ┌────┼────┐
    ▼    ▼    ▼
  Auth  Insp. Storage
  Svc   Svc   Svc
    └────┼────┘
         ▼
    PostgreSQL
```

## 📂 Repository Structure

```
sih26034/
├── frontend/          # React + Vite + TypeScript + Tailwind
├── backend/           # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Config, security, database, logging
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   ├── repositories/  # Data access layer
│   │   ├── storage/   # File storage abstraction
│   │   ├── ai/        # Future AI interfaces
│   │   ├── compliance/  # Future compliance interfaces
│   │   └── main.py    # App entry point
│   ├── migrations/    # Alembic migrations
│   └── tests/         # pytest tests
├── data/uploads/      # Local file storage
├── docs/              # Project documentation
├── rules/             # Future legal metrology rules
├── .env.example       # Environment template
└── README.md
```

## 🛠️ Tech Stack

| Layer     | Technology |
|-----------|------------|
| Frontend  | React, Vite, TypeScript, Tailwind CSS, Axios |
| Backend   | Python, FastAPI, Pydantic, SQLAlchemy |
| Database  | PostgreSQL 16 |
| Auth      | JWT + bcrypt |
| Migrations| Alembic |
| Testing   | pytest, TestClient |

## 🚀 Quick Start

### Prerequisites

- **Python** 3.10+ (3.12 recommended for full OCR support)
- **Node.js** 18+
- **PostgreSQL** 16+

> **⚠️ Python Version Note:** PaddlePaddle (used for OCR) only supports Python ≤ 3.12. If you use Python 3.13+, the app works perfectly — OCR features are simply unavailable and the system uses AI extraction (Groq) instead. All other features (API, auth, inspections, compliance, reports) work on any Python 3.10+.

### 1. Clone & Configure

```bash
git clone <repository-url>
cd sih26034
cp .env.example .env
```
Open the `.env` file and configure your environment:
- **Database**: Update PostgreSQL credentials if needed.
- **LLM Extraction (Optional)**: To use the AI extraction features, generate an API key at [Groq Console](https://console.groq.com/keys) and set `GROQ_API_KEY=your_key_here`. If omitted, the system safely falls back to regex-based extraction.
- **Storage Backend (Optional)**: Defaults to `STORAGE_BACKEND=local` for local development. For production (e.g. on Render), set `STORAGE_BACKEND=s3` and configure your S3 bucket credentials (`S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`).

### 2. Start PostgreSQL

Ensure PostgreSQL is running locally and the database `sih26034` exists. Update `.env` with your PostgreSQL credentials.

### 3. Project Setup

**Option A — One-command full-stack setup (recommended):**
```bash
# Run from the project root:
python setup.py --full       # Sets up both Backend (Python 3.11, OCR, DB migrations) and Frontend (npm install)
# OR for lightweight setup without OCR:
python setup.py
```

*Flags available:*
- `python setup.py --full` — Full backend (CV + PaddleOCR) + frontend
- `python setup.py --backend` — Backend only
- `python setup.py --frontend` — Frontend only

**Option B — Manual setup:**
```bash
# Backend
cd backend
py -3.11 -m venv venv
venv\Scripts\activate        # Windows (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
pip install -r requirements-cv.txt
pip install -r requirements-ocr.txt
alembic upgrade head

# Frontend
cd ../frontend
npm install
```

### 4. Run Application

**Option A — One-click launcher (Windows):**
```powershell
.\start_local.ps1
```

**Option B — Run separately in two terminals:**
```bash
# Terminal 1 (Backend):
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 (Frontend):
cd frontend
npm run dev
```

### 5. Open Application

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/auth/register` | Register new user |
| POST   | `/api/auth/login` | Login |
| GET    | `/api/auth/me` | Current user profile |
| POST   | `/api/inspections` | Create inspection |
| GET    | `/api/inspections` | List inspections |
| GET    | `/api/inspections/{id}` | Get inspection detail |
| POST   | `/api/inspections/{id}/images` | Upload image |
| DELETE | `/api/inspections/{id}/images/{image_id}` | Delete image |
| GET    | `/api/dashboard/stats` | Dashboard statistics |
| GET    | `/api/health` | Health check |

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

## 📄 Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Database Schema](docs/database.md)
- [Development Guide](docs/development.md)

## 🚀 Deployment (Render)

The project includes an Infrastructure-as-Code blueprint in [`render.yaml`](render.yaml) for zero-config deployment to [Render](https://render.com).

### 1. Hardware & Plan Requirements
- **CPU & Memory**: The backend runs PaddlePaddle + PaddleOCR and OpenCV for text detection and image preprocessing. These models require **more than the 512MB RAM** provided on Render's free tier.
- **Recommended Plan**: Deploy the backend service on **Starter (1 GB RAM / 0.5 CPU)** or higher to prevent Out-Of-Memory (OOM) crashes during OCR processing.

### 2. Persistent Storage (S3 / Cloudflare R2 / Backblaze B2)
Render web service containers feature an **ephemeral disk** — files stored on the local filesystem disappear when the service restarts, redeploys, or scales.

To ensure uploaded images persist reliably in production:
1. Create an S3 bucket on **AWS S3**, **Cloudflare R2**, or **Backblaze B2**.
2. In the Render Dashboard under backend **Environment**, set:
   - `STORAGE_BACKEND=s3`
   - `S3_BUCKET=<your-bucket-name>`
   - `S3_REGION=<your-region>` (e.g., `us-east-1` or `auto` for Cloudflare R2)
   - `S3_ENDPOINT_URL=<custom-endpoint-url>` (only required for R2/B2/MinIO; leave blank for AWS S3)
   - `S3_ACCESS_KEY_ID=<your-access-key>`
   - `S3_SECRET_ACCESS_KEY=<your-secret-key>`

### 3. CORS Pairing
After your frontend service deploys:
1. Copy the frontend service URL from the Render Dashboard (e.g. `https://sih26034-frontend.onrender.com`).
2. Verify or update `CORS_ORIGINS` in your backend service environment variables so browser requests are permitted.

## 📌 Current Phase: Phase 6 (Cloud Deployment)

Phases 1 through 5 are complete. Phase 6 (Cloud Deployment & Render Integration) is underway.

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Foundation, auth, database, image upload | ✅ Complete |
| 2 | Computer vision, image preprocessing, PaddleOCR | ✅ Complete |
| 3 | AI declaration extraction (Groq + Regex fallback) | ✅ Complete |
| 4 | Legal Metrology compliance rules engine | ✅ Complete |
| 5 | Reports (PDF/DOCX), audit dashboard, analytics | ✅ Complete |
| 6 | Cloud deployment, Render blueprint, S3 storage abstraction | 🚀 In Progress |
