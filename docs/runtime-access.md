# Runtime Access Architecture

## Primary Access

OpenClaw UI is exposed through Tailscale Serve.

URL:
https://srv1401539.tail1429d2.ts.net

Verified mapping:

tailscale serve --bg --https=443 http://127.0.0.1:18789

## Local Service Layout

OpenClaw UI
127.0.0.1:18789

OpenClaw update host API
127.0.0.1:18790

Containers

openclaw
vps-agent-backend
vps-agent-control
openclaw-update-host

## Network Model

openclaw runs with:

network_mode: host

This allows the OpenClaw gateway to bind directly on port 18789 on the host.

## Important Rule

Port 443 must NOT be taken by Caddy or other reverse proxies when Tailscale Serve is used for the tailnet hostname.

If port 443 is occupied, the Tailscale hostname will not reach OpenClaw even when the Serve mapping is correct.
