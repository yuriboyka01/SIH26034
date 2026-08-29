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

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 16+

### 1. Clone & Configure

```bash
git clone <repository-url>
cd sih26034
cp .env.example .env
```
Open the `.env` file and configure your environment:
- **Database**: Update PostgreSQL credentials if needed.
- **LLM Extraction (Optional)**: To use the AI extraction features, generate an API key at [Groq Console](https://console.groq.com/keys) and set `GROQ_API_KEY=your_key_here`. If omitted, the system safely falls back to regex-based extraction.

### 2. Start PostgreSQL

Ensure PostgreSQL is running locally and the database `sih26034` exists. Update `.env` with your PostgreSQL credentials.

### 3. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
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

## 📌 Current Phase: Phase 1

Phase 1 delivers the foundation. Future phases will add:

| Phase | Feature |
|-------|---------|
| 2 | OCR & image preprocessing |
| 3 | Declaration extraction |
| 4 | Legal Metrology compliance rules |
| 5 | Reports, dashboards, analytics |
| 6 | Cloud deployment & integration |
