# Knowledge Service Architecture

## Components

### FastAPI

The backend exposes the HTTP API for the knowledge service. It provides `GET /health`, `POST /ingest`, and initializes the database schema with SQLAlchemy.

### PostgreSQL

PostgreSQL stores ingestion metadata. The `items` table keeps source metadata, content type, raw content, extracted text, summary, category, tags, file path, file name, status, and creation timestamp fields.

### Storage

The backend stores uploaded file bytes in a Docker volume mounted at `/storage`. Database rows keep the local `file_path` and original `file_name`.

### Extraction

After file storage, the backend extracts readable text synchronously. PDFs are processed with `pdfplumber`; supported image files are processed with Tesseract OCR through `pytesseract`.

### Policies

The backend loads human-readable rules from `/policies/rules.txt` during ingestion. The first matching rule can set `category` and add `tags` without AI.

### AI Classification

After policies run, the backend can call OpenAI when `OPENAI_API_KEY` is set. AI enrichment only fills missing fields: it can set `category` if empty, merge additional `tags`, and set `summary` if empty.

### Docker Compose

Docker Compose runs the FastAPI backend and PostgreSQL database together. The backend image includes Tesseract system packages, is exposed on host port `8010`, and waits for PostgreSQL to pass its healthcheck before starting.

## Data Flow

Clients call the FastAPI backend over HTTP. The backend reads `DATABASE_URL` from `.env`, connects to PostgreSQL through SQLAlchemy, stores ingestion records in the `items` table, writes uploaded file bytes to `/storage`, stores extracted text when available, applies matching policies, then runs guarded AI enrichment before committing rows.

## Ingest Flow

Clients send `POST /ingest` with a JSON body. For text ingestion, the backend maps `content` into `raw_content`, sets `status` to `new`, commits the row to PostgreSQL, and returns the new item UUID.

For file ingestion, clients send `type=file`, `file_name`, `file_content_base64`, and optional `source`. The backend decodes the file, saves it under `/storage`, extracts text for supported PDFs and images, stores `file_path`, `file_name`, and `extracted_text` in PostgreSQL, sets `status` to `processed`, and returns the item UUID.
