# SIH26034 Backend

FastAPI backend for the Legal Metrology Compliance System.

> **Note:** COMPLIQ strictly requires **Python 3.11.x** for full compatibility with PaddleOCR and C-extensions.

### Installation

Use the provided setup script to automatically detect Python 3.11, create the virtual environment, and install all dependencies including PaddleOCR.

```powershell
# Open a PowerShell terminal and run:
.\setup_environment.ps1
```

If the script fails to find Python 3.11, please install it from [python.org](https://www.python.org/downloads/windows/).

### Running the Server

```powershell
# Activate the environment
.\venv\Scripts\Activate.ps1

# Run database migrations (if not already done)
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
pytest tests/ -v
```
