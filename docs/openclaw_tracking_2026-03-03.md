# OpenClaw Stabilisierung - Nachverfolgung

Datum: 2026-03-03
Repo: /opt/vps-agent

## Ziel
- OpenClaw stabil ohne Ollama
- Nur OpenAI als Provider/Modell
- Remote-Zugriff via Tailscale Serve (loopback-first)

## Aktueller Ist-Stand
- Persistente Config:
  - Host: `/opt/vps-agent/data/openclaw/openclaw.json`
  - Container: `/home/node/.openclaw/openclaw.json`
- Gateway Bind: `loopback`
- Gateway Auth: `token`, `allowTailscale=true`
- Primary Model: `openai/gpt-5-mini`
- OpenClaw Netzwerk: `network_mode: host`
- Tailscale Serve:
  - `https://srv1401539.tail1429d2.ts.net/`
  - Proxy auf `http://127.0.0.1:18789`

## Durchgeführte Schritte
1. Baseline und Snapshots erstellt (`ops/snapshots/2026-03-03_144223`).
2. Persistenzpfad geprüft und bestätigt (Bind-Mount aktiv).
3. `gateway.bind` auf `loopback` gesetzt und neu gestartet.
4. Gateway-Token rotiert; Dateirechteproblem (`EACCES`) korrigiert.
5. Modell auf OpenAI gesetzt: `openai/gpt-5-mini`.
6. Compose um OpenAI-Key erweitert; Anthropic leer gesetzt.
7. Caddy für diesen Pfad gestoppt; Tailscale Serve direkt auf Loopback gesetzt.
8. OpenClaw auf Host-Netzwerk umgestellt, damit Loopback für Serve erreichbar ist.

## Verifikation
- `curl -i http://127.0.0.1:18789/` -> `HTTP/1.1 200 OK`
- `curl -i https://srv1401539.tail1429d2.ts.net/` -> `HTTP/2 200`
- Gateway-Log zeigt:
  - `listening on ws://127.0.0.1:18789`
  - `agent model: openai/gpt-5-mini`
- Keine `rate_limited` Treffer in aktueller Logdatei.

## Offener Punkt
- Es laufen weiter `token_mismatch` Events von einem bestehenden Browser-Client mit altem Token (stale localStorage).
- Erwartetes Vorgehen im UI:
  - aktuellen Token einmal einfügen
  - `Connect` genau 1x klicken

## Rollback
- Config:
  - `cp -a /opt/vps-agent/data/openclaw/openclaw.json.bak.<TIMESTAMP> /opt/vps-agent/data/openclaw/openclaw.json`
  - `docker compose -f /opt/vps-agent/docker-compose.yml restart openclaw`
- Compose:
  - `cp -a /opt/vps-agent/docker-compose.yml.bak.<TIMESTAMP> /opt/vps-agent/docker-compose.yml`
  - `docker compose -f /opt/vps-agent/docker-compose.yml up -d --force-recreate openclaw`
