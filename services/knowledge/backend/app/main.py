import base64
import logging
from binascii import Error as Base64Error

from fastapi import FastAPI, Query
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Text, cast, or_

from app import models
from app.classifier import classify_text
from app.db import SessionLocal, ensure_database
from app.extraction import extract_text_from_file
from app.policy_engine import apply_actions, load_rules, match_rule
from app.storage import save_file

ensure_database()

app = FastAPI(title="Knowledge Service")
logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    type: str = Field(..., min_length=1)
    content: str | None = None
    source: str | None = None
    file_name: str | None = None
    file_content_base64: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search")
def search(q: str = Query(..., min_length=1), category: str | None = None):
    pattern = f"%{q}%"

    with SessionLocal() as session:
        query = session.query(models.Item).filter(
            or_(
                models.Item.raw_content.ilike(pattern),
                models.Item.extracted_text.ilike(pattern),
                models.Item.summary.ilike(pattern),
                cast(models.Item.tags, Text).ilike(pattern),
            )
        )

        if category:
            query = query.filter(models.Item.category == category)

        items = query.order_by(models.Item.created_at.desc()).limit(20).all()

    return [format_search_result(item) for item in items]


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
        extracted_text = None

        try:
            extracted_text = extract_text_from_file(file_path)
        except Exception:
            logger.exception("file text extraction failed for %s", file_path)

        with SessionLocal() as session:
            item = models.Item(
                source=payload.source,
                content_type="file",
                file_path=file_path,
                file_name=payload.file_name,
                extracted_text=extracted_text,
                status="processed",
            )
            apply_first_matching_policy(item)
            enrich_with_ai(item)
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
        apply_first_matching_policy(item)
        enrich_with_ai(item)
        session.add(item)
        session.commit()
        session.refresh(item)

    return {"status": "stored", "item_id": str(item.id)}


def apply_first_matching_policy(item):
    try:
        for rule in load_rules():
            if match_rule(item, rule):
                apply_actions(item, rule)
                return
    except Exception:
        logger.exception("policy application failed")


def enrich_with_ai(item):
    text = item.extracted_text or item.raw_content
    if not text:
        return

    try:
        result = classify_text(text)
    except Exception:
        logger.exception("AI classification failed")
        return

    if not result:
        return

    if not item.category:
        item.category = result.get("category")

    existing_tags = item.tags or []
    new_tags = result.get("tags") or []
    item.tags = list(dict.fromkeys(existing_tags + new_tags))

    if not item.summary:
        item.summary = result.get("summary")


def format_search_result(item):
    return {
        "id": str(item.id),
        "category": item.category,
        "tags": item.tags or [],
        "summary": item.summary,
        "content_preview": build_content_preview(item),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def build_content_preview(item):
    text = item.raw_content or item.extracted_text or ""
    text = " ".join(text.split())
    if len(text) <= 160:
        return text
    return f"{text[:157]}..."
