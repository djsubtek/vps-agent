import base64
import html
import logging
from binascii import Error as Base64Error

from fastapi import FastAPI, Query
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import Text, cast, func, or_

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
CATEGORIES = ["restaurant", "idea", "document", "other"]


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
        counts = get_category_counts(session)

    return render_dashboard([format_search_result(item) for item in items], counts)


@app.get("/category/{name}", response_class=HTMLResponse)
def category_view(name: str):
    if name not in CATEGORIES:
        raise HTTPException(status_code=404, detail="category not found")

    with SessionLocal() as session:
        query = session.query(models.Item)
        if name == "other":
            query = query.filter(or_(models.Item.category.is_(None), models.Item.category == "other"))
        else:
            query = query.filter(models.Item.category == name)
        items = query.order_by(models.Item.created_at.desc()).limit(50).all()

    return render_items_page(f"{name.title()} Items", "", [format_search_result(item) for item in items])


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


def render_dashboard(items, counts):
    rows = "\n".join(render_item(item) for item in items) or "<p>No items found.</p>"
    tiles = "\n".join(render_category_tile(category, counts[category]) for category in CATEGORIES)
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Knowledge Dashboard</title>
    <style>
      body {{ font-family: sans-serif; max-width: 1000px; margin: 32px auto; padding: 0 16px; }}
      form {{ margin-bottom: 24px; }}
      input, button, textarea {{ padding: 8px; }}
      textarea {{ width: 100%; min-height: 80px; box-sizing: border-box; }}
      .search {{ display: flex; gap: 8px; }}
      .search input {{ flex: 1; }}
      .tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 24px 0; }}
      .tile {{ border: 1px solid #ddd; padding: 16px; text-decoration: none; color: #111; }}
      .count {{ font-size: 28px; font-weight: bold; }}
      article {{ border-bottom: 1px solid #ddd; padding: 16px 0; }}
      .meta {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
      .tags {{ color: #444; font-size: 14px; }}
      .preview {{ white-space: pre-wrap; }}
    </style>
  </head>
  <body>
    <h1>Knowledge Dashboard</h1>
    <form class="search" action="/search" method="get">
      <input name="q" placeholder="Search stored items">
      <button type="submit">Search</button>
    </form>
    <form action="/ingest" method="post" enctype="multipart/form-data">
      <h2>Add Item</h2>
      <p><textarea name="text" placeholder="Text to store"></textarea></p>
      <p><input type="file" name="file"></p>
      <input type="hidden" name="source" value="web">
      <button type="submit">Upload</button>
    </form>
    <h2>Categories</h2>
    <div class="tiles">{tiles}</div>
    <h2>Latest Items</h2>
    {rows}
  </body>
</html>"""


def render_category_tile(category, count):
    return f"""<a class="tile" href="/category/{html.escape(category)}">
  <div>{html.escape(category.title())}</div>
  <div class="count">{count}</div>
</a>"""


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


def get_category_counts(session):
    counts = dict.fromkeys(CATEGORIES, 0)
    grouped = session.query(models.Item.category, func.count(models.Item.id)).group_by(models.Item.category).all()
    for category, count in grouped:
        if category in counts:
            counts[category] += count
        else:
            counts["other"] += count
    return counts


@app.post("/ingest")
async def ingest(request: Request):
    payload = await parse_ingest_request(request)
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
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        return RedirectResponse("/", status_code=303)
    return format_ingest_response(item)


async def parse_ingest_request(request):
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        file_name = None
        file_content_base64 = None

        if upload is not None and getattr(upload, "filename", ""):
            file_bytes = await upload.read()
            file_name = upload.filename
            file_content_base64 = base64.b64encode(file_bytes).decode()

        return IngestRequest(
            text=form.get("text") or None,
            source=form.get("source") or "web",
            file_name=file_name,
            file_content_base64=file_content_base64,
        )

    return IngestRequest.model_validate(await request.json())


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
