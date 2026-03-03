# OpenClaw Gateway Runbook (Caddy + WebSocket + Pairing)

Ziel: Stabiler produktiver Betrieb des OpenClaw Gateways hinter Caddy mit WebSocket-Support und Pairing-Recovery. Keine externen APIs, nur lokales Ollama. Domain: `ai.pagesmaker.com`.

## Architektur und Ports

Services und Ports:
- `openclaw`: `18789`
- `ollama`: `11434`
- `backend`: `8000` (extern `8001`)
- `control`: `8000` (extern `8000`)
- `caddy`: `80/443`

Caddy Routing-Logik:
- `/` zeigt OpenClaw UI (Gateway)
- `/ws*` an `openclaw:18789` (WebSocket)
- `/control/*` optional an `control:8000`

Hinweis: Wenn `/` auf `backend` geroutet wird, kann `404 {"detail":"Not Found"}` erscheinen.

## Health und Status

```bash
docker compose ps
```

```bash
docker compose logs --tail=200 openclaw caddy
```

Optional gezielt:
```bash
docker compose logs --tail=200 backend control
```

## WebSocket Test

HTTP/1.1 Upgrade Test (muss `101 Switching Protocols` liefern):
```bash
curl -i --http1.1 \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: ai.pagesmaker.com" \
  https://ai.pagesmaker.com/ws
```

Wichtig: Ein HTTP/2-Test kann stattdessen `200 text/html` liefern. Das ist kein echter WS-Upgrade und deutet nicht zwingend auf einen Fehler hin.

## Pairing (ohne openclaw CLI)

Pairing-Dateien liegen im Container unter:
`/home/node/.openclaw/devices/`

- `pending.json`: neue, nicht genehmigte Geraete
- `paired.json`: genehmigte Geraete

### Manuelle Approve-Prozedur

1) `pending.json` aus Container holen:
```bash
docker cp openclaw:/home/node/.openclaw/devices/pending.json /tmp/pending.json
```

2) `paired.json` aus Container holen:
```bash
docker cp openclaw:/home/node/.openclaw/devices/paired.json /tmp/paired.json
```

3) Auf dem Host mergen und genehmigen (`approved=true`, `approvedAt=ts`):
```bash
python3 - <<'PY'
import json, time
from pathlib import Path

pending = json.loads(Path('/tmp/pending.json').read_text() or '[]')
paired = json.loads(Path('/tmp/paired.json').read_text() or '[]')

now = int(time.time())
seen = {d.get('id') for d in paired if isinstance(d, dict)}

for d in pending:
    if not isinstance(d, dict):
        continue
    d['approved'] = True
    d['approvedAt'] = now
    if d.get('id') not in seen:
        paired.append(d)
        seen.add(d.get('id'))

Path('/tmp/paired.json').write_text(json.dumps(paired, indent=2, sort_keys=True))
PY
```

4) `paired.json` in Container zurueckkopieren:
```bash
docker cp /tmp/paired.json openclaw:/home/node/.openclaw/devices/paired.json
```

5) `pending.json` im Container leeren:
```bash
docker exec openclaw sh -lc 'printf "[]" > /home/node/.openclaw/devices/pending.json'
```

6) OpenClaw neu starten:
```bash
docker compose restart openclaw
```

## Typische Fehlerbilder

- UI zeigt `disconnected (1008) pairing required`
- `/ws` liefert `200 text/html` (meist HTTP/2 Test oder falsches Routing)
- `502` waehrend Restarts
- `/` liefert `404 {"detail":"Not Found"}` wenn Default-Route auf `backend` geht

## Recovery Checklist: Wenn UI nicht erreichbar

1) Direktes HTTPS pruefen:
```bash
curl -i https://ai.pagesmaker.com/
```

2) WebSocket Upgrade pruefen:
```bash
curl -i --http1.1 \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: ai.pagesmaker.com" \
  https://ai.pagesmaker.com/ws
```

3) Container-Status pruefen:
```bash
docker compose ps
```

4) Caddy Logs pruefen:
```bash
docker compose logs --tail=200 caddy
```

5) OpenClaw Logs pruefen:
```bash
docker compose logs --tail=200 openclaw
```

6) Falls Pairing-Fehler: Manuelle Approve-Prozedur ausfuehren

## Troubleshooting Kurz

- `200 text/html` auf `/ws`: HTTP/2 Test oder Routing falsch; Caddy Route fuer `/ws*` verifizieren.
- `502` nach Restart: kurz warten, dann erneut pruefen.
- `404 {"detail":"Not Found"}` auf `/`: Default-Route zeigt auf `backend` statt OpenClaw UI.

## OPS: Token + Model Stabilisierung

### Persistenter Config-Pfad

OpenClaw-Config liegt persistent auf dem Host unter:
`/opt/vps-agent/data/openclaw/openclaw.json`

Compose-Mount:
- `./data/openclaw:/home/node/.openclaw`

### Gateway Token auslesen

```bash
python3 -c 'import json;print(json.load(open("/opt/vps-agent/data/openclaw/openclaw.json"))["gateway"]["auth"]["token"])'
```

### Gateway Token rotieren (serverseitig)

```bash
docker exec openclaw sh -lc 'TOKEN=$(openssl rand -hex 32); node /app/openclaw.mjs config set gateway.auth.token "$TOKEN" >/dev/null; echo "$TOKEN"'
docker compose up -d --force-recreate
```

UI-Anweisung:
- Paste `gateway.auth.token` into Control UI settings, then click Connect once.
- Nicht mehrfach auf Connect klicken, solange ein `token_mismatch` aktiv ist.

### Agent Model festsetzen (kein Claude-Rueckfall)

```bash
docker exec openclaw sh -lc 'node /app/openclaw.mjs config set agents.defaults.model.primary ollama/qwen2.5:3b'
docker restart openclaw
```

Verifikation:
```bash
docker exec openclaw sh -lc 'tail -n 200 /tmp/openclaw/openclaw-$(date +%F).log | grep -i "agent model" -n'
```

### Auth Rate-Limit Hinweise

Konfigurationspfad:
- `gateway.auth.rateLimit`

Relevante Felder:
- `maxAttempts`
- `windowMs`
- `lockoutMs`
- `exemptLoopback`

Referenz:
- `/app/docs/gateway/configuration-reference.md` (Abschnitt "Gateway" / `auth.rateLimit`)

## Rollback

1) Compose/Env zuruecksetzen:
```bash
cp -a /opt/vps-agent/docker-compose.yml.bak.<TIMESTAMP> /opt/vps-agent/docker-compose.yml
cp -a /opt/vps-agent/.env.bak.<TIMESTAMP> /opt/vps-agent/.env
```

2) OpenClaw Config optional zuruecksetzen:
```bash
cp -a /opt/vps-agent/data/openclaw/openclaw.json.bak.<TIMESTAMP> /opt/vps-agent/data/openclaw/openclaw.json
```

3) Neustart:
```bash
docker compose up -d --force-recreate
```
