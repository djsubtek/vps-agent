from __future__ import annotations

import hmac
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.board.router import router as board_router
from backend.app.orchestrator.api import router as orchestrator_router

INTERNAL_AGENT_API_KEY = os.getenv("INTERNAL_AGENT_API_KEY")


class AgentRunRequest(BaseModel):
    prompt: str


app = FastAPI()
app.include_router(orchestrator_router)
app.include_router(board_router)
app.mount(
    "/board/assets",
    StaticFiles(directory=Path(__file__).resolve().parent / "board" / "static"),
    name="board-assets",
)


@app.post("/agent/run")
def run_agent(
    payload: AgentRunRequest, authorization: str | None = Header(default=None)
) -> dict[str, str]:
    if not INTERNAL_AGENT_API_KEY:
        raise HTTPException(status_code=503, detail="Internal agent runner is not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.removeprefix("Bearer ").strip()
    if not token or not hmac.compare_digest(token, INTERNAL_AGENT_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"status": "ok", "received_prompt": payload.prompt}
