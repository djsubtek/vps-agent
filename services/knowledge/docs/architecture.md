# Knowledge Service Architecture

## Components

### FastAPI

The backend exposes the HTTP API for the knowledge service. It provides `GET /health`, `POST /ingest`, and initializes the database schema with SQLAlchemy.

### PostgreSQL

PostgreSQL stores ingestion data. The `items` table keeps source metadata, content type, raw content, extracted text, summary, category, tags, status, and creation timestamp fields.

### Docker Compose

Docker Compose runs the FastAPI backend and PostgreSQL database together. The backend is exposed on host port `8010` and waits for PostgreSQL to pass its healthcheck before starting.

## Data Flow

Clients call the FastAPI backend over HTTP. The backend reads `DATABASE_URL` from `.env`, connects to PostgreSQL through SQLAlchemy, and stores future ingestion records in the `items` table.

## Ingest Flow

Clients send `POST /ingest` with a JSON body containing `type`, optional `content`, and optional `source`. The backend maps the request into a new `items` row, sets `status` to `new`, commits the row to PostgreSQL, and returns the new item UUID.
