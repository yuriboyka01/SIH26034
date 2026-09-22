Write-Host "Starting Local Development Environment for SIH26034..."

# Resolve paths relative to THIS script's own location, not the shell's current
# directory. The previous version used a relative path ("./backend/venv/...")
# which only worked if the new PowerShell window happened to inherit this
# folder as its working directory. When it didn't, "if (Test-Path ...)" and
# the activation both silently failed, and uvicorn fell through to whatever
# Python was on the global PATH instead of the project venv -- which is how
# a stale, wrong-interpreter backend ended up holding port 8000 while the
# correct venv-based one failed to bind and sat there doing nothing.
$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$VenvActivate = if (Test-Path (Join-Path $BackendDir "venv\Scripts\activate.ps1")) { Join-Path $BackendDir "venv\Scripts\activate.ps1" } elseif (Test-Path (Join-Path $RootDir ".venv\Scripts\activate.ps1")) { Join-Path $RootDir ".venv\Scripts\activate.ps1" } else { $null }

if (-not $VenvActivate) {
    Write-Host "⚠️  Could not find a backend venv (backend\venv or .venv). Aborting so we don't silently fall back to the global Python." -ForegroundColor Yellow
    exit 1
}

# Start the backend in a new PowerShell window, with an explicit working
# directory so the activation path always resolves correctly regardless of
# how this script itself was launched.
Write-Host "Starting Backend..."
Start-Process powershell -WorkingDirectory $BackendDir -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", "& '$VenvActivate'; alembic upgrade head; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start the frontend in a new PowerShell window
Write-Host "Starting Frontend..."
Start-Process powershell -WorkingDirectory (Join-Path $RootDir "frontend") -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", "npm run dev"

Write-Host "✅ Backend and Frontend are starting in separate windows!"
Write-Host "Make sure your local PostgreSQL database is running with the credentials in your .env file."

