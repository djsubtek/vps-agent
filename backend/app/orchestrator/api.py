from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.orchestrator import iteration_runner, service

router = APIRouter()


class IdeaCreate(BaseModel):
    title: str
    detail: Optional[str] = None


class RunRequest(BaseModel):
    env: str = "staging"


@router.post("/orchestrator/ideas")
def create_idea(payload: IdeaCreate) -> dict:
    conn = service.get_db()
    try:
        service.ensure_schema(conn)
        idea_id = service.create_idea(conn, payload.title, payload.detail)
    finally:
        conn.close()
    return {"id": idea_id}


@router.post("/orchestrator/run")
def run_once(payload: RunRequest) -> dict:
    if payload.env != "staging":
        raise HTTPException(status_code=403, detail="Run is staging-only")
    return iteration_runner.run_once(env=payload.env)


@router.get("/health")
def health() -> dict:
    status = service.healthcheck()
    if not status.get("db"):
        raise HTTPException(status_code=503, detail="DB unavailable")
    return status
