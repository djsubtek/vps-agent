import base64
import html
import logging
from binascii import Error as Base64Error

from fastapi import FastAPI, Query
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import Text, cast, or_

from app import models
from app.classifier import classify_text
from app.db import SessionLocal, ensure_database
from app.extraction import extract_text_from_file
from app.policy_engine import apply_actions, load_rules, match_rule
from app.storage import save_file

logging.basicConfig(level=logging.INFO)
ensure_database()

app = FastAPI(title="Knowledge Service")
logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    type: str | None = Field(default=None, min_length=1)
    content: str | None = None
    text: str | None = None
    source: str | None = None
    file_name: str | None = None
    file_content_base64: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "knowledge"}


@app.get("/", response_class=HTMLResponse)
def index():
    with SessionLocal() as session:
        items = session.query(models.Item).order_by(models.Item.created_at.desc()).limit(50).all()

    return render_items_page("Knowledge Items", "", [format_search_result(item) for item in items])


@app.get("/search")
def search(request: Request, q: str = Query(..., min_length=1), category: str | None = None):
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

        items = query.order_by(models.Item.created_at.desc()).limit(50).all()

    results = [format_search_result(item) for item in items]
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(render_items_page("Search Results", q, results))
    return results


def render_items_page(title, query, items):
    rows = "\n".join(render_item(item) for item in items) or "<p>No items found.</p>"
    safe_title = html.escape(title)
    safe_query = html.escape(query or "")
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{safe_title}</title>
    <style>
      body {{ font-family: sans-serif; max-width: 900px; margin: 32px auto; padding: 0 16px; }}
      form {{ display: flex; gap: 8px; margin-bottom: 24px; }}
      input {{ flex: 1; padding: 8px; }}
      button {{ padding: 8px 12px; }}
      article {{ border-bottom: 1px solid #ddd; padding: 16px 0; }}
      .meta {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
      .tags {{ color: #444; font-size: 14px; }}
      .preview {{ white-space: pre-wrap; }}
    </style>
  </head>
  <body>
    <h1>{safe_title}</h1>
    <form action="/search" method="get">
      <input name="q" value="{safe_query}" placeholder="Search stored items">
      <button type="submit">Search</button>
    </form>
    <p><a href="/">Latest items</a></p>
    {rows}
  </body>
</html>"""


def render_item(item):
    tags = ", ".join(item["tags"])
    return f"""<article>
  <div class="meta">{html.escape(item["created_at"] or "")} | category: {html.escape(item["category"] or "-")}</div>
  <div class="tags">tags: {html.escape(tags or "-")}</div>
  <p><strong>summary:</strong> {html.escape(item["summary"] or "-")}</p>
  <p class="preview">{html.escape(item["content_preview"] or "")}</p>
  {render_file_name(item)}
</article>"""


def render_file_name(item):
    if not item.get("file_name"):
        return ""
    return f'<p class="meta">file: {html.escape(item["file_name"])}</p>'


@app.post("/ingest")
def ingest(payload: IngestRequest):
    ingest_type = detect_ingest_type(payload)
    content = payload.content if payload.content is not None else payload.text
    logger.info("ingest received type=%s source=%s", ingest_type, payload.source)

    try:
        if ingest_type == "file":
            item = ingest_file(payload)
        else:
            item = ingest_text(payload, ingest_type, content)
    except HTTPException:
        logger.exception("ingest failed type=%s source=%s", ingest_type, payload.source)
        raise
    except Exception as exc:
        logger.exception("ingest failed type=%s source=%s", ingest_type, payload.source)
        raise HTTPException(status_code=500, detail="ingest failed") from exc

    logger.info("ingest stored type=%s source=%s item_id=%s", ingest_type, payload.source, item["id"])
    return format_ingest_response(item)


def detect_ingest_type(payload):
    if payload.type:
        return payload.type
    if payload.file_name:
        return "file"
    return "text"


def ingest_file(payload):
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
        return detach_item(item)


def ingest_text(payload, ingest_type, content):
    with SessionLocal() as session:
        item = models.Item(
            source=payload.source,
            content_type=ingest_type,
            raw_content=content,
            status="new",
        )
        apply_first_matching_policy(item)
        enrich_with_ai(item)
        session.add(item)
        session.commit()
        session.refresh(item)
        return detach_item(item)


def detach_item(item):
    return {
        "id": item.id,
        "category": item.category,
        "tags": item.tags or [],
        "summary": item.summary,
    }


def format_ingest_response(item):
    return {
        "status": "stored",
        "item_id": str(item["id"]),
        "category": item["category"],
        "tags": item["tags"],
    }


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
        "file_name": item.file_name,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def build_content_preview(item):
    text = item.raw_content or item.extracted_text or ""
    text = " ".join(text.split())
    if len(text) <= 160:
        return text
    return f"{text[:157]}..."
