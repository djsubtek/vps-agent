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

## Web UI

Open the minimal browser UI:

```text
http://localhost:8010
```

## Ingest Text

```bash
curl -X POST http://localhost:8010/ingest \
  -H "Content-Type: application/json" \
  -d '{"type":"text","content":"Test idea restaurant Cologne","source":"telegram"}'
```

Expected response:

```json
{"status":"stored","item_id":"<uuid>","category":"restaurant","tags":["food"]}
```

## OpenClaw Ingest

OpenClaw can forward plain text without setting `type`; the service auto-detects text ingestion:

```bash
curl -X POST http://localhost:8010/ingest \
  -H "Content-Type: application/json" \
  -d '{"text":"Restaurant in Köln testen","source":"telegram"}'
```

If `file_name` is present, the service auto-detects file ingestion:

```bash
curl -X POST http://localhost:8010/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_name":"note.txt","file_content_base64":"SGVsbG8gd29ybGQ=","source":"telegram"}'
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

## AI Classification

Set `OPENAI_API_KEY` in the environment before starting the service to enable AI enrichment:

```bash
OPENAI_API_KEY=... docker compose up -d
```

Ingestion applies rules first, then AI. AI can fill a missing `category`, merge additional `tags`, and set `summary`; it never overwrites a rule-set category or removes existing tags.

## Search

Search stored content, extracted text, summaries, and tags:

```bash
curl "http://localhost:8010/search?q=restaurant"
```

Filter by category:

```bash
curl "http://localhost:8010/search?q=restaurant&category=restaurant"
```

## Architecture

Docker Compose runs a FastAPI backend and PostgreSQL database. The backend reads `DATABASE_URL` from `.env`, initializes the `items` table at startup, accepts flexible OpenClaw-friendly payloads through `POST /ingest`, persists uploaded files under `/storage`, extracts text from supported PDFs and images, applies human-readable policies from `policies/rules.txt`, optionally enriches items with AI when `OPENAI_API_KEY` is set, and exposes PostgreSQL-backed search through `GET /search`.
