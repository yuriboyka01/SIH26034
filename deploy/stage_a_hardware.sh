#!/bin/bash
# =============================================================================
# Stage A (partial): Swap Setup + Initial Hardening
# Run FIRST after SSH-ing into the VM for the first time
# =============================================================================
set -euo pipefail

echo "=============================================="
echo "  STAGE A: Hardware Audit & Swap Setup"
echo "=============================================="

# ── Architecture verification ───────────────────────────────────────────────
ARCH=$(uname -m)
echo "[A.1] Architecture: $ARCH"
if [ "$ARCH" != "x86_64" ]; then
    echo "✗ FATAL: Expected x86_64 but got $ARCH"
    echo "  PaddlePaddle 2.6.2 ONLY supports x86_64."
    echo "  Delete this VM and create a new one with AMD shape (VM.Standard.E2.1.Micro)."
    exit 1
fi
echo "  ✓ x86_64 confirmed"

# ── System info ─────────────────────────────────────────────────────────────
echo ""
echo "[A.2] System information:"
echo "  OS:    $(lsb_release -d -s 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"
echo "  CPUs:  $(nproc)"
echo "  RAM:   $(free -h | awk '/^Mem:/{print $2}')"
echo "  Disk:  $(df -h / | awk 'NR==2{print $4}') available"
echo ""

# ── Swap setup ──────────────────────────────────────────────────────────────
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
echo "[A.3] Total RAM: ${TOTAL_RAM_MB}MB"

if [ "$TOTAL_RAM_MB" -lt 1500 ]; then
    echo "  RAM is under 1.5GB — setting up 2GB swap..."
    
    if [ -f /swapfile ]; then
        echo "  Swapfile already exists:"
        swapon --show
    else
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        
        # Make persistent
        if ! grep -q '/swapfile' /etc/fstab; then
            echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        fi
        echo "  ✓ 2GB swap created and enabled"
    fi
else
    echo "  RAM is ${TOTAL_RAM_MB}MB — sufficient, skipping swap."
fi

echo ""
echo "--- Final Memory Status ---"
free -h
echo ""

# ── System updates ──────────────────────────────────────────────────────────
echo "[A.4] Running system updates..."
sudo apt update -y && sudo apt upgrade -y
echo "  ✓ System updated"

echo ""
echo "=============================================="
echo "  STAGE A COMPLETE"
echo "  ✓ Architecture: x86_64"
echo "  ✓ Swap configured (if needed)"
echo "  ✓ System updated"
echo "=============================================="
echo ""
echo "NEXT: Run stage_b_setup.sh"
