#!/usr/bin/env bash
# Automated Cloudflare Tunnel provisioning script for Omarchy Arch Linux
set -euo pipefail

TUNNEL_NAME="${1:-palace-tunnel}"
HOSTNAME="${2:-palace.yourdomain.com}"

echo "=== [1/4] Installing cloudflared on Omarchy ==="
sudo pacman -S --needed --noconfirm cloudflared

echo "=== [2/4] Authenticating Cloudflare Tunnel ==="
if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then
  cloudflared tunnel login
fi

echo "=== [3/4] Provisioning Tunnel '$TUNNEL_NAME' and Routing DNS '$HOSTNAME' ==="
cloudflared tunnel create "$TUNNEL_NAME" || true
cloudflared tunnel route dns "$TUNNEL_NAME" "$HOSTNAME"

echo "=== [4/4] Installing Systemd Service ==="
echo " Copy config/cloudflared-config.yml to ~/.cloudflared/config.yml with your Tunnel UUID, then run:"
echo "  sudo cloudflared service install"
echo "  sudo systemctl enable --now cloudflared"
