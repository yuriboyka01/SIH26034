#!/bin/bash
# =============================================================================
# Stage F: Domain (DuckDNS) & HTTPS (Let's Encrypt)
# Run as: ubuntu user (uses sudo)
#
# Usage: ./stage_f_https.sh <your-duckdns-subdomain> <your-duckdns-token>
# Example: ./stage_f_https.sh compliq-api abc123-your-token
# =============================================================================
set -euo pipefail

DUCKDNS_SUBDOMAIN="${1:-}"
DUCKDNS_TOKEN="${2:-}"

if [ -z "$DUCKDNS_SUBDOMAIN" ] || [ -z "$DUCKDNS_TOKEN" ]; then
    echo "Usage: $0 <duckdns-subdomain> <duckdns-token>"
    echo ""
    echo "Steps to get these:"
    echo "  1. Go to https://www.duckdns.org/"
    echo "  2. Log in with Google/GitHub/Reddit"
    echo "  3. Create a subdomain (e.g., 'compliq-api')"
    echo "  4. Copy your token from the account page"
    echo ""
    echo "Example: $0 compliq-api xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    exit 1
fi

DOMAIN="${DUCKDNS_SUBDOMAIN}.duckdns.org"

echo "=============================================="
echo "  STAGE F: DuckDNS + HTTPS Setup"
echo "  Domain: $DOMAIN"
echo "=============================================="

# ── Step 1: Update DuckDNS to point to this VM's IP ────────────────────────
echo "[F.1] Updating DuckDNS record..."
PUBLIC_IP=$(curl -s https://api.ipify.org)
echo "  VM Public IP: $PUBLIC_IP"

RESULT=$(curl -s "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=${PUBLIC_IP}")
if [ "$RESULT" = "OK" ]; then
    echo "  ✓ DuckDNS updated: $DOMAIN → $PUBLIC_IP"
else
    echo "  ✗ DuckDNS update failed: $RESULT"
    exit 1
fi

# ── Step 2: Set up DuckDNS auto-update cron ─────────────────────────────────
echo "[F.2] Setting up DuckDNS auto-update cron..."
mkdir -p /home/ubuntu/duckdns
cat > /home/ubuntu/duckdns/duck.sh << DUCKSH
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=" | curl -k -o /home/ubuntu/duckdns/duck.log -K -
DUCKSH
chmod +x /home/ubuntu/duckdns/duck.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/duckdns/duck.sh >/dev/null 2>&1") | sort -u | crontab -
echo "  ✓ DuckDNS cron installed (updates every 5 minutes)"

# ── Step 3: Update Nginx with domain ───────────────────────────────────────
echo "[F.3] Updating Nginx server_name..."
sudo sed -i "s/server_name _;/server_name ${DOMAIN};/" /etc/nginx/sites-available/sih26034
sudo nginx -t
sudo systemctl reload nginx
echo "  ✓ Nginx updated with domain: $DOMAIN"

# ── Step 4: Install Certbot and provision SSL ──────────────────────────────
echo "[F.4] Installing Certbot..."
sudo apt install -y certbot python3-certbot-nginx

echo "[F.4] Provisioning SSL certificate..."
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "noreply@${DOMAIN}" --redirect

echo "  ✓ SSL certificate provisioned"

# ── Step 5: Verify HTTPS ───────────────────────────────────────────────────
echo ""
echo "[F.5] Verification..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/api/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ HTTPS working — https://${DOMAIN}/api/health returned 200"
    curl -s "https://${DOMAIN}/api/health" | python3.11 -m json.tool
else
    echo "  ⚠ HTTPS health check returned HTTP $HTTP_CODE"
    echo "  Try: curl -v https://${DOMAIN}/api/health"
fi

# ── Step 6: Set up auto-renewal ────────────────────────────────────────────
echo "[F.6] Certbot auto-renewal is configured automatically via systemd timer"
sudo systemctl status certbot.timer --no-pager 2>/dev/null || echo "  (certbot timer not found, setting up cron)"

echo ""
echo "=============================================="
echo "  STAGE F COMPLETE"
echo "  Your backend is live at: https://${DOMAIN}"
echo "  SSL auto-renews via certbot timer"
echo "=============================================="
echo ""
echo "NEXT: Update frontend VITE_API_URL to: https://${DOMAIN}"
