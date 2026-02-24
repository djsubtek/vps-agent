from __future__ import annotations

from fastapi import FastAPI

from app.orchestrator.api import router as orchestrator_router

app = FastAPI()
app.include_router(orchestrator_router)
