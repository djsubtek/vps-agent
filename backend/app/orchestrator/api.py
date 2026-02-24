from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.orchestrator import iteration_runner, service
from app.orchestrator import write_flow
from app.orchestrator.guard_runner import GuardError

router = APIRouter()


class IdeaCreate(BaseModel):
    title: str
    detail: Optional[str] = None


class RunRequest(BaseModel):
    env: str = "staging"


class WriteRequest(BaseModel):
    patch: str
    commit_message: str
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None


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


@router.post("/orchestrator/write")
def write_changes(payload: WriteRequest) -> dict:
    try:
        result = write_flow.apply_patch_and_commit(
            patch=payload.patch,
            commit_message=payload.commit_message,
            pr_title=payload.pr_title,
            pr_body=payload.pr_body,
        )
    except GuardError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except write_flow.WriteError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"commit": result.commit_sha, "pr": result.pr}


@router.get("/health")
def health() -> dict:
    status = service.healthcheck()
    if not status.get("db"):
        raise HTTPException(status_code=503, detail="DB unavailable")
    return status
