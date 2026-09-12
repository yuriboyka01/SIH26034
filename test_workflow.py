import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

print("--- API Workflow Test ---")

# 1. Login
response = requests.post(f"{BASE_URL}/auth/login", json={"email": "testuser_aygy2@example.com", "password": "password123"})
response.raise_for_status()
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("1. Logged in successfully.")

# 2. Create Inspection
response = requests.post(f"{BASE_URL}/inspections", headers=headers, json={
    "product_name": "API Test Agarbatti",
    "brand": "Cycle"
})
response.raise_for_status()
inspection_id = response.json()["id"]
print(f"2. Created inspection: {inspection_id}")

# 3. Upload Image
image_path = Path(__file__).parent / "Images" / "Agarbatti_front.jpeg"
with open(image_path, "rb") as f:
    files = {"file": ("Agarbatti_front.jpeg", f, "image/jpeg")}
    data = {"image_type": "OTHER"}
    response = requests.post(f"{BASE_URL}/inspections/{inspection_id}/images", headers=headers, files=files, data=data)
    response.raise_for_status()
    print("3. Uploaded image successfully.")

# 4. Analyze Inspection
print("4. Starting analysis (this may take 10-30 seconds)...")
response = requests.post(f"{BASE_URL}/inspections/{inspection_id}/analyze", headers=headers)
response.raise_for_status()
print("Analysis complete.")

# 5. Run Compliance
print("5. Running compliance...")
response = requests.post(f"{BASE_URL}/inspections/{inspection_id}/compliance", headers=headers)
response.raise_for_status()
compliance_data = response.json()
print(f"Compliance overall status: {compliance_data.get('overall_status')}")

# 6. Get Report
print("6. Getting PDF report...")
response = requests.get(f"{BASE_URL}/inspections/{inspection_id}/compliance/report.pdf", headers=headers)
response.raise_for_status()
print(f"Report downloaded successfully, size: {len(response.content)} bytes.")

print("--- API Workflow Test Complete ---")
