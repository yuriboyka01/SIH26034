<#
.SYNOPSIS
Sets up the COMPLIQ backend environment securely and reproducibly.

.DESCRIPTION
This script verifies the Python 3.11 requirement, creates a dedicated
virtual environment, upgrades pip/setuptools, installs all dependencies,
and performs a health check for the PaddleOCR engine.
#>

$ErrorActionPreference = "Stop"
$InformationPreference = "Continue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "COMPLIQ Backend Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Detect Python 3.11
Write-Host "`n[1/7] Detecting Python 3.11..."
$PythonExe = ""
$PotentialPaths = @(
    "py",
    "python",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "C:\Python311\python.exe"
)

foreach ($path in $PotentialPaths) {
    try {
        $versionInfo = ""
        if ($path -eq "py") {
            $versionInfo = & $path -3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($versionInfo -eq "3.11") {
                $PythonExe = "py -3.11"
                break
            }
        } else {
            $versionInfo = & $path -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($versionInfo -eq "3.11") {
                $PythonExe = $path
                break
            }
        }
    } catch {
        # Ignore errors and try the next path
    }
}

if (-not $PythonExe) {
    Write-Host "`nERROR: Python 3.11.x is required but could not be found." -ForegroundColor Red
    Write-Host "Please install Python 3.11 from https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Python 3.11 at: $PythonExe" -ForegroundColor Green

# 2. Check existing venv
Write-Host "`n[2/7] Checking virtual environment..."
$VenvPath = "venv"
if (Test-Path "$VenvPath\Scripts\python.exe") {
    $VenvVersion = & "$VenvPath\Scripts\python.exe" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ($VenvVersion -ne "3.11") {
        Write-Host "Existing venv uses unsupported Python version ($VenvVersion). Recreating..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    } else {
        Write-Host "Existing venv uses Python 3.11. Keeping it." -ForegroundColor Green
    }
}

# 3. Create venv
if (-not (Test-Path $VenvPath)) {
    Write-Host "`n[3/7] Creating virtual environment with Python 3.11..."
    if ($PythonExe -eq "py -3.11") {
        py -3.11 -m venv $VenvPath
    } else {
        & $PythonExe -m venv $VenvPath
    }
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "`n[3/7] Virtual environment already exists."
}

# 4. Upgrade packaging tools
Write-Host "`n[4/7] Upgrading pip, setuptools, and wheel..."
& "$VenvPath\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel | Out-Null
Write-Host "Packaging tools upgraded." -ForegroundColor Green

# 5. Install requirements
Write-Host "`n[5/7] Installing backend dependencies..."
& "$VenvPath\Scripts\python.exe" -m pip install -r requirements.txt
Write-Host "Core dependencies installed." -ForegroundColor Green

# 6. Install Paddle OCR requirements
Write-Host "`n[6/7] Installing PaddleOCR dependencies..."
& "$VenvPath\Scripts\python.exe" -m pip install -r requirements-ocr.txt
Write-Host "PaddleOCR dependencies installed." -ForegroundColor Green

# 7. Run Health Check
Write-Host "`n[7/7] Running OCR Initialization Check..."
$CheckScript = @"
import sys
try:
    from app.ai.ocr_service import _get_ocr
    instance, version, engine = _get_ocr()
    print(f'SUCCESS: {engine} version {version} initialized successfully.')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
$CheckResult = & "$VenvPath\Scripts\python.exe" -c $CheckScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nOCR Health Check FAILED!" -ForegroundColor Red
    Write-Host $CheckResult -ForegroundColor Red
    exit 1
}

Write-Host $CheckResult -ForegroundColor Green

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "ENVIRONMENT READY" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Activate it with:"
Write-Host "    .\venv\Scripts\Activate.ps1"
Write-Host "Start the server with:"
Write-Host "    .\venv\Scripts\uvicorn.exe app.main:app --reload"
