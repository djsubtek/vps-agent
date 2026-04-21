# Knowledge Service Architecture

## Components

### FastAPI

The backend exposes the HTTP API for the knowledge service. It provides `GET /health`, `POST /ingest`, and initializes the database schema with SQLAlchemy.

### PostgreSQL

PostgreSQL stores ingestion metadata. The `items` table keeps source metadata, content type, raw content, extracted text, summary, category, tags, file path, file name, status, and creation timestamp fields.

### Storage

The backend stores uploaded file bytes in a Docker volume mounted at `/storage`. Database rows keep the local `file_path` and original `file_name`.

### Docker Compose

Docker Compose runs the FastAPI backend and PostgreSQL database together. The backend is exposed on host port `8010` and waits for PostgreSQL to pass its healthcheck before starting.

## Data Flow

Clients call the FastAPI backend over HTTP. The backend reads `DATABASE_URL` from `.env`, connects to PostgreSQL through SQLAlchemy, stores ingestion records in the `items` table, and writes uploaded file bytes to `/storage`.

## Ingest Flow

Clients send `POST /ingest` with a JSON body. For text ingestion, the backend maps `content` into `raw_content`, sets `status` to `new`, commits the row to PostgreSQL, and returns the new item UUID.

For file ingestion, clients send `type=file`, `file_name`, `file_content_base64`, and optional `source`. The backend decodes the file, saves it under `/storage`, stores `file_path` and `file_name` in PostgreSQL, sets `status` to `stored`, and returns the item UUID.
