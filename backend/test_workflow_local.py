"""
Step 2 Workflow Test: Login → Create Inspection → Upload Image → Analyze
Tests the complete COMPLIQ pipeline against the local backend.
"""
import sys
import os
import json
import time
import requests

BASE_URL = "http://localhost:8000"
IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Images", "GOLD_front.jpeg")

# --- Use a unique test user for isolation
TEST_EMAIL = "demo.compliq.sih2026@gmail.com"
TEST_PASSWORD = "DemoTest@123!"
TEST_NAME = "Demo Test User"

def print_step(n, title):
    print(f"\n{'='*55}")
    print(f"  STEP {n}: {title}")
    print(f"{'='*55}")

def fail(msg):
    print(f"  [FAIL] {msg}")
    sys.exit(1)

def ok(msg):
    print(f"  [OK] {msg}")


print("\n" + "="*55)
print("  COMPLIQ Full Workflow Test (Local Backend)")
print(f"  Backend: {BASE_URL}")
print(f"  Image:   {os.path.basename(IMAGE_PATH)}")
print("="*55)

# --- Step 1: Health check
print_step(1, "Health Check")
r = requests.get(f"{BASE_URL}/api/health", timeout=10)
assert r.status_code == 200, f"Health check failed: {r.status_code}"
ok(f"Health OK: {r.json()}")

# --- Step 2: Register user (ignore if already exists)
print_step(2, "Register / Login")
reg = requests.post(f"{BASE_URL}/api/auth/register", json={
    "name": TEST_NAME,
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}, timeout=10)
if reg.status_code in (200, 201):
    ok(f"Registered new user: {TEST_EMAIL}")
elif reg.status_code == 400:
    ok(f"User already exists (OK): {TEST_EMAIL}")
else:
    print(f"  Registration response: {reg.status_code} — {reg.text[:200]}")

# --- Step 3: Login
print_step(3, "Login")
login = requests.post(f"{BASE_URL}/api/auth/login",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    timeout=10
)
assert login.status_code == 200, f"Login failed: {login.status_code} --- {login.text}"
token = login.json()["access_token"]
ok(f"Login OK -- JWT obtained")

headers = {"Authorization": f"Bearer {token}"}

# --- Step 4: Create inspection
print_step(4, "Create Inspection")
create = requests.post(f"{BASE_URL}/api/inspections", json={
    "product_name": "Gold Refined Sunflower Oil (Test)",
    "brand": "Gold SWinner"
}, headers=headers, timeout=10)
assert create.status_code in (200, 201), f"Create inspection failed: {create.status_code} — {create.text}"
inspection = create.json()
inspection_id = inspection["id"]
ok(f"Inspection created: {inspection_id}")

# --- Step 5: Upload image
print_step(5, "Upload Image")
assert os.path.exists(IMAGE_PATH), f"Image not found: {IMAGE_PATH}"
with open(IMAGE_PATH, "rb") as f:
    upload = requests.post(
        f"{BASE_URL}/api/inspections/{inspection_id}/images",
        files={"file": (os.path.basename(IMAGE_PATH), f, "image/jpeg")},
        headers=headers,
        timeout=30
    )
assert upload.status_code in (200, 201), f"Upload failed: {upload.status_code} — {upload.text}"
image_data = upload.json()
image_id = image_data["id"]
ok(f"Image uploaded: {image_id}")

# --- Step 6: Analyze (triggers PaddleOCR)
print_step(6, "Analyze — PaddleOCR + Extraction + Compliance Engine")
print("  (This may take 15–60s for first PaddleOCR initialization...)")
t0 = time.time()
analyze = requests.post(
    f"{BASE_URL}/api/inspections/{inspection_id}/analyze",
    headers=headers,
    timeout=120
)
elapsed = time.time() - t0
assert analyze.status_code in (200, 201), f"Analyze failed: {analyze.status_code} — {analyze.text[:500]}"
analysis_result = analyze.json()
ok(f"Analysis complete in {elapsed:.1f}s")

# --- Step 7: Inspect analysis results
print_step(7, "Inspect Results")
results = analysis_result if isinstance(analysis_result, list) else [analysis_result]
for r in results:
    ocr_text = r.get("ocr_result", {}).get("full_text", "")
    engine = r.get("ocr_result", {}).get("engine", "unknown")
    blocks = len(r.get("ocr_result", {}).get("blocks", []))
    print(f"  OCR Engine:  {engine}")
    print(f"  OCR Blocks:  {blocks}")
    print(f"  OCR Text (first 200 chars): {ocr_text[:200]!r}")
    
    if engine != "paddle":
        print(f"  [WARN] OCR engine is '{engine}', expected 'paddle'")
    else:
        ok("PaddleOCR was invoked")
    
    # Compliance check
    compliance = r.get("compliance_result", {})
    if compliance:
        violations = compliance.get("violations", [])
        score = compliance.get("compliance_score", "N/A")
        ok(f"Compliance engine ran: score={score}, violations={len(violations)}")
    else:
        print("  [WARN] No compliance result in response")

# --- Step 8: Fetch inspection detail (final report)
print_step(8, "Final Report / Inspection Detail")
detail = requests.get(f"{BASE_URL}/api/inspections/{inspection_id}", headers=headers, timeout=10)
assert detail.status_code == 200, f"Detail fetch failed: {detail.status_code}"
ok("Inspection detail fetched OK")

print("\n" + "="*55)
print("  [PASS] ALL STEPS PASSED - Local workflow verified")
print("="*55 + "\n")
