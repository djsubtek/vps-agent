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

## Ingest File

```bash
curl -X POST http://localhost:8010/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "type":"file",
    "file_name":"test.txt",
    "file_content_base64":"SGVsbG8gd29ybGQ=",
    "source":"telegram"
  }'
```

For supported files, the service stores the upload under `/storage`, extracts readable text automatically, saves it in `extracted_text`, and marks the item as `processed`.

## Policies

Rules in `policies/rules.txt` control simple category and tag assignment without code changes. Edit the file, then send new ingests; rules are loaded during ingestion.

Example rule:

```text
RULE: Restaurant Idea

WHEN:
- text contains "Restaurant" or "Essen"

THEN:
- set category = restaurant
- add tags = food
```

## Architecture

Docker Compose runs a FastAPI backend and PostgreSQL database. The backend reads `DATABASE_URL` from `.env`, initializes the `items` table at startup, stores incoming text payloads through `POST /ingest`, persists uploaded files under `/storage`, extracts text from supported PDFs and images, and applies human-readable policies from `policies/rules.txt`.
