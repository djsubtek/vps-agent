from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.app.board import service

router = APIRouter()

INDEX_PATH = Path(__file__).resolve().parent / "templates" / "index.html"


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    summary: str = Field(min_length=3, max_length=280)
    detail: str | None = Field(default=None, max_length=2000)
    assigned_agent: str = Field(default="unassigned", max_length=60)
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    status: Literal["backlog", "todo", "running", "review", "done"] = "backlog"
    latest_activity: str | None = Field(default=None, max_length=280)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    summary: str | None = Field(default=None, min_length=3, max_length=280)
    detail: str | None = Field(default=None, max_length=2000)
    assigned_agent: str | None = Field(default=None, max_length=60)
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    status: Literal["backlog", "todo", "running", "review", "done"] | None = None
    latest_activity: str | None = Field(default=None, max_length=280)


@router.api_route("/board", methods=["GET", "HEAD"], response_class=HTMLResponse)
@router.api_route("/board/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def board_index() -> HTMLResponse:
    return HTMLResponse(INDEX_PATH.read_text(encoding="utf-8"))


@router.get("/board/api/tasks")
def board_tasks() -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        return service.list_tasks(conn)
    finally:
        conn.close()


@router.post("/board/api/tasks")
def board_create_task(payload: TaskCreate) -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        task = service.create_task(conn, payload.model_dump())
        return {"item": task}
    finally:
        conn.close()


@router.patch("/board/api/tasks/{task_id}")
def board_update_task(task_id: int, payload: TaskUpdate) -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        task = service.update_task(conn, task_id, payload.model_dump(exclude_none=True))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"item": task}
    finally:
        conn.close()


@router.get("/board/api/agents")
def board_agents() -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        return service.list_agents(conn)
    finally:
        conn.close()


@router.get("/board/api/summaries")
def board_summaries() -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        return service.list_summaries(conn)
    finally:
        conn.close()


@router.get("/board/api/approvals")
def board_approvals() -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        return service.list_approvals(conn)
    finally:
        conn.close()


@router.get("/board/api/recurring")
def board_recurring() -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        return service.list_recurring(conn)
    finally:
        conn.close()


@router.api_route("/board/api/system", methods=["GET", "HEAD"])
def board_system() -> dict:
    conn = service.get_db()
    try:
        service.ensure_ready(conn)
        return service.list_system(conn)
    finally:
        conn.close()


@router.get("/board/api/health")
def board_health() -> dict:
    return service.health_snapshot()


@router.get("/board/api/version")
def board_version() -> dict:
    return service.health_snapshot()
