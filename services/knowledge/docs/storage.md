# Storage

## Local Storage

Uploaded files are stored by the backend under `/storage` inside the container. Docker Compose mounts the `knowledge_storage` volume at that path so files persist across container restarts.

Files are saved as:

```text
/storage/{uuid}_{filename}
```

The database stores the resulting `file_path` and original `file_name` on the `items` row.

## File Flow

1. A client sends `POST /ingest` with `type=file`, `file_name`, `file_content_base64`, and optional `source`.
2. The backend decodes the base64 content.
3. `storage.save_file()` writes the bytes to `/storage`.
4. The backend stores metadata in PostgreSQL with `status=stored`.

## Future S3 Replacement

The storage interface is intentionally small: `save_file()` writes bytes and returns a path, while `get_file()` reads bytes by path. A later S3 implementation can keep the same interface and return object keys or URLs instead of local paths.
