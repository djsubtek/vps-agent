# Knowledge Data Model

## Items Table

- `id`: UUID primary key for each stored item.
- `source`: Optional origin of the item, such as `telegram`.
- `content_type`: Required content type from the ingest request, such as `text`.
- `title`: Optional human-readable title.
- `raw_content`: Optional original payload content.
- `extracted_text`: Optional readable text extracted from uploaded PDFs or images.
- `summary`: Optional generated summary for later AI processing.
- `category`: Optional classification label.
- `tags`: Optional JSON array for labels or keywords.
- `file_path`: Optional local storage path for uploaded files.
- `file_name`: Optional original uploaded file name.
- `status`: Required processing status, defaulting to `new`.
- `created_at`: Timestamp set when the row is created.

## Ingestion Flow

1. A client sends `POST /ingest` with `type`, optional `content`, and optional `source`.
2. The backend maps `type` to `content_type`, `content` to `raw_content`, and `source` to `source`.
3. The backend stores a new `items` row with `status` set to `new`.
4. The response returns the stored item UUID.

For file ingestion, the client sends `type=file`, `file_name`, `file_content_base64`, and optional `source`. The backend stores the file locally, records `file_path` and `file_name`, extracts readable text into `extracted_text` when supported, and sets `status` to `processed`.

This phase supports text ingestion, local file ingestion, PDF text extraction, and basic image OCR. Summarization, tagging, categorization, and remote object storage are reserved for later phases.
