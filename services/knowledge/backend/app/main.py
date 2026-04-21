from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import models
from app.db import SessionLocal, ensure_database

ensure_database()

app = FastAPI(title="Knowledge Service")


class IngestRequest(BaseModel):
    type: str = Field(..., min_length=1)
    content: str | None = None
    source: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(payload: IngestRequest):
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
