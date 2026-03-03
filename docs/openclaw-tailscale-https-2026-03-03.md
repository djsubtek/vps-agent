# OpenClaw Control UI over Tailscale HTTPS (2026-03-03)

## Goal
Make OpenClaw Control UI work reliably only over Tailscale HTTPS (no Cloudflare/public exposure), with stable networking, persistent state, correct WebSocket proxying, and trusted proxy handling.

## Changes Made
1) **Compose stack (Caddy + OpenClaw)**
- OpenClaw runs only inside the compose network, not exposed on host ports.
- Persistent state via named volume.
- Trusted proxy CIDR set to the compose network.
- Control UI allowed origins set to the Tailscale DNS name.

2) **Caddy reverse proxy**
- Caddy terminates TLS for `srv1401539.tail1429d2.ts.net`.
- Reverse proxy targets `openclaw:18789` (service name, not container IP).
- HTTP/1.1 enforced for WebSocket upgrade.

3) **OpenClaw config (persisted)**
- `gateway.bind = "lan"` to allow Caddy access on the compose network.
- `gateway.trustedProxies = ["172.21.0.0/16", "127.0.0.1/32"]`
- `gateway.controlUi.allowedOrigins = ["https://srv1401539.tail1429d2.ts.net"]`

4) **State persistence**
- Migrated state from the orphan container into the compose volume.
- Fixed volume ownership to UID 1000 so OpenClaw can write `openclaw.json`.

## Final Files
- `/opt/vps-agent/docker-compose.yml`
- `/opt/vps-agent/Caddyfile`
- OpenClaw state persisted in volume: `vps-agent_openclaw_state` (contains `openclaw.json`).

## Verification Commands (and Results)
1) **Inside Caddy container → OpenClaw**
```
docker exec caddy sh -lc 'apk add --no-cache curl >/dev/null 2>&1 || true; curl -i http://openclaw:18789/ | head -n 20'
```
Result: `HTTP/1.1 200 OK` (OpenClaw Control UI HTML).

2) **Host → Tailscale HTTPS**
```
curl -i https://srv1401539.tail1429d2.ts.net/ | head -n 20
```
Result: `HTTP/2 200` (OpenClaw Control UI HTML).

3) **WebSocket upgrade**
```
curl --max-time 5 -sS -D - -o /dev/null --http1.1 \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: srv1401539.tail1429d2.ts.net" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 13" \
  https://srv1401539.tail1429d2.ts.net/ws
```
Result: `HTTP/1.1 101 Switching Protocols`.

## Notes
- Docker network subnet set to `172.21.0.0/16` to avoid overlap with existing networks.
- Orphan containers detected: `vps-agent-backend`, `vps-agent-control`, and the previous standalone `openclaw` (removed). Keeping backend/control running for now.

## Rollback
- Compose:
```
cp /opt/vps-agent/docker-compose.yml.bak.2026-03-03_122901 /opt/vps-agent/docker-compose.yml
```
- Caddyfile:
```
cp /opt/vps-agent/Caddyfile.bak.2026-03-03_122059 /opt/vps-agent/Caddyfile
```
- OpenClaw config inside volume (example):
```
docker run --rm -v vps-agent_openclaw_state:/data alpine:3.19 \
  sh -lc 'cp /data/openclaw.json.bak.2026-03-03_123425 /data/openclaw.json'
```
- Full volume restore (example):
```
docker run --rm -v vps-agent_openclaw_state:/data -v /opt/vps-agent/backups:/backup alpine:3.19 \
  sh -lc 'rm -rf /data/* && tar -C /data -xf /backup/openclaw_state.vpsagent.2026-03-03_123133.tar'
```
