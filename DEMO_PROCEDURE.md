# COMPLIQ — SIH Demo Procedure

> **CRITICAL WARNING**: Your local PC must remain powered ON and connected to the internet
> for the entire duration of the demo. Disable sleep/hibernate before the demo.

---

## Architecture

```
  Browser (Judges)
        |
        v
  Render Frontend (always on)
  https://sih26034-frontend-aygy.onrender.com
        |
        | HTTPS (via Cloudflare)
        v
  https://<random>.trycloudflare.com
        |
        v
  Local FastAPI (your PC, port 8000)
        |-- PaddleOCR 2.8.1
        |-- Groq LLM Extraction
        `-- Compliance Engine
```

---

## Every Demo Day: Required Startup (2 terminals)

### Terminal 1 - Start the Backend

    cd d:\CompliQ\backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Wait for: `INFO: Uvicorn running on http://0.0.0.0:8000`

### Terminal 2 - Start the Cloudflare Tunnel

    d:\CompliQ\cloudflared.exe tunnel --url http://localhost:8000

Wait for:
    Your quick Tunnel has been created! Visit it at:
    https://<NEW-RANDOM-SUBDOMAIN>.trycloudflare.com

IMPORTANT: The tunnel URL is DIFFERENT every time you restart cloudflared.
You MUST update the Render frontend with the new URL each session.

---

## After Getting the Tunnel URL: Update the Frontend

### Method A: Render Dashboard (FASTER - no rebuild needed)
1. Go to https://dashboard.render.com
2. Click sih26034-frontend -> Environment
3. Edit VITE_API_URL -> set to new tunnel URL
4. Click "Save Changes" -> then "Manual Deploy"

### Method B: render.yaml + GitHub push
1. Open d:\CompliQ\render.yaml
2. Update the VITE_API_URL value to the new tunnel URL
3. Run:
    git add render.yaml
    git commit -m "Update tunnel URL"
    git push origin main
4. Wait ~3 minutes for Render to auto-redeploy.

---

## Verify the Tunnel is Working

    curl https://<YOUR-SUBDOMAIN>.trycloudflare.com/api/health

Expected: {"status": "healthy", "version": "4.0.0-phase4"}

---

## Full End-to-End Demo Workflow

Open: https://sih26034-frontend-aygy.onrender.com

1. Login (or register a new account)
2. Click "New Inspection"
3. Fill in product name + brand -> Submit
4. Upload a real image from d:\CompliQ\Images\ (e.g. GOLD_front.jpeg)
5. Click "Analyze" -> Wait 15-30 seconds
   (First analysis takes longer - PaddleOCR model loads on first call)
6. View OCR Results - real text detected from the label
7. View Extracted Fields - MRP, Net Weight, Manufacturer, etc.
8. View Compliance Report - violations under Legal Metrology Rules 2011
9. Download PDF/DOCX Report

---

## Current Tunnel URL (active this session)

    https://providing-reserve-sao-demonstrate.trycloudflare.com

This URL is valid until cloudflared is restarted.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Frontend shows "Connection Error" | Check both terminals running; verify tunnel URL in Render |
| Analyze button spins >60s | First PaddleOCR load takes 15-30s; wait or check Terminal 1 |
| 502 Bad Gateway | Backend crashed - check Terminal 1, restart it |
| Tunnel URL changed | Update VITE_API_URL in Render dashboard and redeploy |
| CORS error in browser console | Restart backend; confirm CORS_ORIGINS has Render URL |
