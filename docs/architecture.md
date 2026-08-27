# Architecture

## System Overview

SIH26034 is a monorepo application for checking compliance of packaged commodities under the Legal Metrology (Packaged Commodities) Rules, 2011.

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         React + Vite + TypeScript                │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ API Layer│ │ Auth Ctx  │ │ React Router     │ │
│  └────┬─────┘ └──────────┘ └──────────────────┘ │
└───────┼──────────────────────────────────────────┘
        │ REST / JSON
        ▼
┌─────────────────────────────────────────────────┐
│                   Backend                        │
│              FastAPI + Python                    │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │              API Routes                   │   │
│  │  auth.py  inspections.py  images.py       │   │
│  └──────────────────┬───────────────────────┘   │
│                     ▼                            │
│  ┌──────────────────────────────────────────┐   │
│  │            Services Layer                 │   │
│  │  AuthService  InspectionService           │   │
│  │  ImageService                             │   │
│  └──────────────────┬───────────────────────┘   │
│           ┌─────────┼─────────┐                  │
│           ▼         ▼         ▼                  │
│  ┌─────────────┐ ┌─────┐ ┌──────────────────┐  │
│  │ Repositories│ │Store│ │ Future AI/Comply  │  │
│  └──────┬──────┘ └──┬──┘ └──────────────────┘  │
│         │           │                            │
└─────────┼───────────┼────────────────────────────┘
          ▼           ▼
    ┌──────────┐ ┌──────────┐
    │PostgreSQL│ │   Local   │
    │          │ │Filesystem │
    └──────────┘ └──────────┘
```

## Component Details

### Frontend
- **Technology**: React 18, Vite, TypeScript, Tailwind CSS
- **API Client**: Centralized Axios instance with JWT interceptor
- **State**: React Context for authentication
- **Routing**: React Router v6 with protected routes

### Backend
- **Framework**: FastAPI (async Python)
- **ORM**: SQLAlchemy 2.0 with declarative models
- **Validation**: Pydantic v2 schemas
- **Architecture**: Route → Service → Repository → Database

### Database
- **Engine**: PostgreSQL 16
- **Migrations**: Alembic
- **Tables**: users, inspections, inspection_images

### Storage
- **Phase 1**: Local filesystem (`data/uploads/`)
- **Interface**: Abstract `StorageService` with `upload()`, `delete()`, `get()`
- **Future**: Implement S3StorageService, GCSStorageService, MinIOStorageService

### Future AI Modules
- `ImagePreprocessingService` → Phase 2
- `OCRService` → Phase 2
- `DeclarationExtractionService` → Phase 3
- `ComplianceService` → Phase 4
- `ReportService` → Phase 5

## Data Flow

```
User → Login → JWT Token
User → Create Inspection → DB record (status: CREATED)
User → Upload Image → Validate → Store file → DB record → Status: IMAGES_UPLOADED

Future:
Image → Preprocess → OCR → Extract Declarations → Check Compliance → Generate Report
```

## Security

- Passwords hashed with bcrypt
- JWT tokens for API authentication
- Input validation via Pydantic
- MIME type + extension validation for uploads
- Generated storage filenames (no user-controlled paths)
- CORS configured
- No secrets in version control
