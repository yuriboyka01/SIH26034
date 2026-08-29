# Development Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- Git

## Local Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd sih26034
```

### 2. Environment Variables

```bash
cp .env.example .env
```

Default values work for local development. For production, change:
- `JWT_SECRET` to a long random string
- `DATABASE_URL` to your production database
- `CORS_ORIGINS` to your frontend domain

### 3. Start PostgreSQL

Ensure PostgreSQL is running locally and the database `sih26034` exists.

### 4. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### 5. Frontend

```bash
cd frontend

npm install
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://sih26034:... | PostgreSQL connection string |
| JWT_SECRET | (see .env.example) | Secret key for JWT signing |
| JWT_ALGORITHM | HS256 | JWT signing algorithm |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | Token expiry in minutes |
| UPLOAD_DIR | ../data/uploads | File upload directory |
| MAX_UPLOAD_SIZE | 10485760 | Max upload size in bytes (10MB) |
| CORS_ORIGINS | http://localhost:5173 | Comma-separated allowed origins |

## Database Migrations

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Tests use SQLite in-memory, so no database setup is needed.

## Project Structure

### Backend Layers

```
API Route → Service → Repository → Database
```

- **Routes** (`app/api/`): HTTP handlers, request parsing, response formatting
- **Services** (`app/services/`): Business logic, validation, orchestration
- **Repositories** (`app/repositories/`): Database queries, CRUD operations
- **Models** (`app/models/`): SQLAlchemy ORM models
- **Schemas** (`app/schemas/`): Pydantic request/response validation

### Frontend Structure

```
src/
├── api/          # Typed API client functions
├── components/   # Reusable UI components
├── context/      # React contexts (auth)
└── pages/        # Route page components
```

## Branch Workflow

```
main
  └── develop
        ├── feature/auth
        ├── feature/inspections
        ├── feature/image-upload
        └── fix/bug-name
```

1. Branch from `develop`
2. Name: `feature/description` or `fix/description`
3. Open PR against `develop`
4. Merge to `main` for releases

## Commit Convention

```
feat: add inspection creation API
fix: handle duplicate email registration
docs: update API documentation
test: add image upload tests
chore: update dependencies
refactor: extract storage interface
```
