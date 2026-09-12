#!/bin/bash
# =============================================================================
# Stage D: systemd Service Configuration
# Run as: ubuntu user (uses sudo)
# =============================================================================
set -euo pipefail

echo "=============================================="
echo "  STAGE D: systemd Service Setup"
echo "=============================================="

# ── Step 1: Create systemd unit file ────────────────────────────────────────
echo "[D.1] Creating systemd service file..."
sudo tee /etc/systemd/system/sih26034.service > /dev/null << 'EOF'
[Unit]
Description=COMPLIQ FastAPI Backend (SIH26034)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/SIH26034/backend
Environment="PATH=/home/ubuntu/SIH26034/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/ubuntu/SIH26034/backend/.env
ExecStart=/home/ubuntu/SIH26034/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Memory guard: restart if memory exceeds 800MB (leave headroom on 1GB VM)
MemoryMax=800M

[Install]
WantedBy=multi-user.target
EOF

echo "[D.1] ✓ Service file created"

# ── Step 2: Reload, enable, start ───────────────────────────────────────────
echo "[D.2] Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable sih26034
sudo systemctl start sih26034

sleep 5

echo "[D.2] Service status:"
sudo systemctl status sih26034 --no-pager

# ── Step 3: Verify health ──────────────────────────────────────────────────
echo ""
echo "[D.3] Health check via systemd..."
sleep 10
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ Backend running under systemd — /api/health returned 200"
else
    echo "  ⚠ Backend health check returned $HTTP_CODE"
    echo "  Check logs: sudo journalctl -u sih26034 -n 50 --no-pager"
fi

echo ""
echo "=============================================="
echo "  STAGE D COMPLETE"
echo "  To check logs:   sudo journalctl -u sih26034 -f"
echo "  To restart:      sudo systemctl restart sih26034"
echo "=============================================="
echo ""
echo "NEXT: Reboot the VM to verify auto-start:"
echo "  sudo reboot"
echo "  (reconnect via SSH after ~60s)"
echo "  sudo systemctl status sih26034"
