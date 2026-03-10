#!/bin/bash

set -euo pipefail

echo "Restoring OpenClaw tailnet access"

sudo tailscale serve reset
sudo tailscale serve --bg --https=443 http://127.0.0.1:18789

tailscale serve status
