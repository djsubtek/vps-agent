# Knowledge Service

Minimal FastAPI and PostgreSQL service for phase-1 text ingestion.

## Run

```bash
docker compose up -d
```

## Health Check

```bash
curl http://localhost:8010/health
```

## Ingest Text

```bash
curl -X POST http://localhost:8010/ingest \
  -H "Content-Type: application/json" \
  -d '{"type":"text","content":"Test idea restaurant Cologne","source":"telegram"}'
```

Expected response:

```json
{"status":"stored","item_id":"<uuid>"}
```

## Architecture

Docker Compose runs a FastAPI backend and PostgreSQL database. The backend reads `DATABASE_URL` from `.env`, initializes the `items` table at startup, and stores incoming text payloads through `POST /ingest`.
