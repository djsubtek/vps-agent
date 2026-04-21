import base64
from binascii import Error as Base64Error

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app import models
from app.db import SessionLocal, ensure_database
from app.storage import save_file

ensure_database()

app = FastAPI(title="Knowledge Service")


class IngestRequest(BaseModel):
    type: str = Field(..., min_length=1)
    content: str | None = None
    source: str | None = None
    file_name: str | None = None
    file_content_base64: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(payload: IngestRequest):
    if payload.type == "file":
        if not payload.file_content_base64:
            raise HTTPException(status_code=422, detail="file_content_base64 is required for file ingestion")

        try:
            file_bytes = base64.b64decode(payload.file_content_base64, validate=True)
        except Base64Error as exc:
            raise HTTPException(status_code=422, detail="file_content_base64 must be valid base64") from exc

        file_path = save_file(file_bytes, payload.file_name or "upload.bin")

        with SessionLocal() as session:
            item = models.Item(
                source=payload.source,
                content_type="file",
                file_path=file_path,
                file_name=payload.file_name,
                status="stored",
            )
            session.add(item)
            session.commit()
            session.refresh(item)

        return {"status": "stored", "item_id": str(item.id)}

    with SessionLocal() as session:
        item = models.Item(
            source=payload.source,
            content_type=payload.type,
            raw_content=payload.content,
            status="new",
        )
        session.add(item)
        session.commit()
        session.refresh(item)

    return {"status": "stored", "item_id": str(item.id)}
