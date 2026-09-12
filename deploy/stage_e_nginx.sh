#!/bin/bash
# =============================================================================
# Stage E: Nginx Reverse Proxy & Port Lockdown
# Run as: ubuntu user (uses sudo)
# =============================================================================
set -euo pipefail

echo "=============================================="
echo "  STAGE E: Nginx Reverse Proxy & Firewall"
echo "=============================================="

# ── Step 1: Install Nginx ───────────────────────────────────────────────────
echo "[E.1] Installing Nginx..."
sudo apt install -y nginx
sudo systemctl enable nginx
echo "[E.1] ✓ Nginx installed"

# ── Step 2: Configure Nginx site ────────────────────────────────────────────
echo "[E.2] Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/sih26034 > /dev/null << 'NGINX_CONF'
server {
    listen 80;
    server_name _;

    # Max upload size for high-res evidence images
    client_max_body_size 25M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout for long PaddleOCR analysis requests
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 60s;
    }
}
NGINX_CONF

# Enable site, disable default
sudo ln -sf /etc/nginx/sites-available/sih26034 /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
echo "[E.2] ✓ Nginx configured and reloaded"

# ── Step 3: Firewall lockdown ──────────────────────────────────────────────
echo "[E.3] Configuring iptables firewall..."
sudo apt install -y iptables-persistent

# Allow HTTP and HTTPS
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT

# Block direct access to port 8000 from outside
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP

# Save rules
sudo netfilter-persistent save
echo "[E.3] ✓ Firewall rules applied"
echo "  Port 80:   OPEN (HTTP)"
echo "  Port 443:  OPEN (HTTPS)"
echo "  Port 8000: BLOCKED (internal only)"

# ── Step 4: Verify ─────────────────────────────────────────────────────────
echo ""
echo "[E.4] Verification..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ Nginx → FastAPI proxy working — /api/health returned 200"
    curl -s http://localhost/api/health | python3.11 -m json.tool
else
    echo "  ⚠ Proxy health check returned HTTP $HTTP_CODE"
    echo "  Check: sudo journalctl -u nginx -n 20 --no-pager"
    echo "  Check: sudo journalctl -u sih26034 -n 20 --no-pager"
fi

echo ""
echo "=============================================="
echo "  STAGE E COMPLETE"
echo "  Backend accessible at: http://<VM_PUBLIC_IP>/api/health"
echo "=============================================="
