#!/bin/bash
# =============================================================================
# Stage B: Python 3.11 + PaddleOCR Setup & Standalone Validation
# Run as: ubuntu user on Oracle Cloud VM
# =============================================================================
set -euo pipefail

echo "=============================================="
echo "  STAGE B: Python Environment & OCR Setup"
echo "=============================================="

# ── Step 1: System packages ──────────────────────────────────────────────────
echo "[B.1] Installing system dependencies..."
sudo apt update -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update -y
sudo apt install -y \
  python3.11 python3.11-venv python3.11-dev \
  libgl1 libglib2.0-0 \
  git curl wget

echo "[B.1] ✓ System packages installed"
python3.11 --version

# ── Step 2: Clone repository ────────────────────────────────────────────────
echo "[B.2] Setting up repository..."
REPO_DIR="/home/ubuntu/SIH26034"
if [ -d "$REPO_DIR" ]; then
    echo "  Repository already exists at $REPO_DIR, pulling latest..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "  Cloning repository..."
    git clone https://github.com/yuriboyka01/SIH26034.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ── Step 3: Virtual environment ─────────────────────────────────────────────
echo "[B.3] Creating Python 3.11 virtual environment..."
VENV_DIR="$REPO_DIR/backend/venv"
if [ -d "$VENV_DIR" ]; then
    echo "  venv already exists, reusing..."
else
    python3.11 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# ── Step 4: Install core dependencies ───────────────────────────────────────
echo "[B.4] Installing backend dependencies (requirements.txt)..."
cd "$REPO_DIR/backend"
pip install -r requirements.txt

echo "[B.4] Installing PaddleOCR dependencies (requirements-ocr.txt)..."
pip install -r requirements-ocr.txt

pip install psutil
echo "[B.4] ✓ All dependencies installed"
echo "  paddlepaddle: $(pip show paddlepaddle 2>/dev/null | grep Version)"
echo "  paddleocr:    $(pip show paddleocr 2>/dev/null | grep Version)"

# ── Step 5: Standalone PaddleOCR Test ───────────────────────────────────────
echo "=============================================="
echo "[B.5] Running standalone PaddleOCR test..."
echo "=============================================="

# Check for test images
if ls "$REPO_DIR/Images/"*.jpeg 1>/dev/null 2>&1 || ls "$REPO_DIR/Images/"*.jpg 1>/dev/null 2>&1 || ls "$REPO_DIR/Images/"*.png 1>/dev/null 2>&1; then
    TEST_IMAGE=$(ls "$REPO_DIR/Images/"*.jpeg "$REPO_DIR/Images/"*.jpg "$REPO_DIR/Images/"*.png 2>/dev/null | head -1)
    echo "  Using test image: $TEST_IMAGE"
else
    echo "  ⚠ No test images found in Images/ — creating a synthetic test"
    TEST_IMAGE="$REPO_DIR/backend/test_synthetic.jpg"
    python3.11 -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (400, 200), 'white')
draw = ImageDraw.Draw(img)
draw.text((20, 50), 'NET WEIGHT: 500g', fill='black')
draw.text((20, 100), 'MFG: 01/2026', fill='black')
draw.text((20, 150), 'MRP: Rs. 150', fill='black')
img.save('$TEST_IMAGE')
print('Created synthetic test image')
"
fi

# Memory before OCR
echo ""
echo "--- Memory BEFORE PaddleOCR ---"
free -h
echo ""

# Run OCR
python3.11 -c "
import time, os, psutil

print('Loading PaddleOCR...')
t0 = time.time()
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
print(f'PaddleOCR loaded in {time.time()-t0:.1f}s')

proc = psutil.Process(os.getpid())
print(f'Memory after load: {proc.memory_info().rss / 1024 / 1024:.0f} MB')

test_image = '$TEST_IMAGE'
print(f'Running OCR on: {test_image}')
t1 = time.time()
result = ocr.ocr(test_image, cls=True)
elapsed = time.time() - t1

if result and result[0]:
    print(f'✓ OCR SUCCESS: {len(result[0])} text regions detected in {elapsed:.1f}s')
    for line in result[0][:5]:
        text = line[1][0]
        conf = line[1][1]
        print(f'  [{conf:.2f}] {text}')
else:
    print('✗ OCR returned no results')

print(f'Memory after OCR: {proc.memory_info().rss / 1024 / 1024:.0f} MB')
"

# Memory after OCR
echo ""
echo "--- Memory AFTER PaddleOCR ---"
free -h
echo ""

echo "=============================================="
echo "  STAGE B COMPLETE"
echo "=============================================="
