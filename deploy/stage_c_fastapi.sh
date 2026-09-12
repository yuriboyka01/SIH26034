#!/bin/bash
# =============================================================================
# Stage C: FastAPI Launch & Memory Monitoring
# Run as: ubuntu user on Oracle Cloud VM
# =============================================================================
set -euo pipefail

REPO_DIR="/home/ubuntu/SIH26034"
VENV_DIR="$REPO_DIR/backend/venv"
ENV_FILE="$REPO_DIR/backend/.env"

echo "=============================================="
echo "  STAGE C: FastAPI Launch & Memory Monitoring"
echo "=============================================="

# ── Step 1: Verify .env exists ──────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    echo "✗ ERROR: $ENV_FILE not found!"
    echo "  Create it with: DATABASE_URL, JWT_SECRET, GROQ_API_KEY, CORS_ORIGINS"
    exit 1
fi
echo "[C.1] ✓ .env file found"

# ── Step 2: Run Alembic migrations ──────────────────────────────────────────
echo "[C.2] Running database migrations..."
cd "$REPO_DIR/backend"
source "$VENV_DIR/bin/activate"
alembic upgrade head
echo "[C.2] ✓ Migrations complete"

# ── Step 3: Start FastAPI in background for testing ─────────────────────────
echo "[C.3] Starting FastAPI (uvicorn) on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
echo "  PID: $UVICORN_PID"

# Wait for startup
echo "  Waiting for server to start..."
sleep 10

# ── Step 4: Health check ────────────────────────────────────────────────────
echo "[C.4] Health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ /api/health returned 200 OK"
    curl -s http://localhost:8000/api/health | python3.11 -m json.tool
else
    echo "  ✗ /api/health returned HTTP $HTTP_CODE"
    echo "  Check logs: journalctl -u sih26034 -n 50"
fi

# ── Step 5: Memory snapshot ─────────────────────────────────────────────────
echo ""
echo "[C.5] Memory snapshot after FastAPI startup:"
free -h
echo ""
echo "Top processes by memory:"
ps aux --sort=-%mem | head -n 10
echo ""

# ── Step 6: Keep running for manual testing ─────────────────────────────────
echo "=============================================="
echo "  FastAPI is running on port 8000 (PID: $UVICORN_PID)"
echo "  Test from outside: curl http://<VM_IP>:8000/api/health"
echo "  To stop: kill $UVICORN_PID"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop the server..."
wait $UVICORN_PID
