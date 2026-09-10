Write-Host "Starting Local Development Environment for SIH26034..."

# Start the backend in a new PowerShell window
Write-Host "Starting Backend..."
$VenvActivate = if (Test-Path ".\backend\venv\Scripts\activate.ps1") { ".\backend\venv\Scripts\activate.ps1" } elseif (Test-Path ".\.venv\Scripts\activate.ps1") { ".\.venv\Scripts\activate.ps1" } else { "venv\Scripts\activate" }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$VenvActivate; cd backend; alembic upgrade head; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start the frontend in a new PowerShell window
Write-Host "Starting Frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm install; npm run dev"

Write-Host "✅ Backend and Frontend are starting in separate windows!"
Write-Host "Make sure your local PostgreSQL database is running with the credentials in your .env file."
