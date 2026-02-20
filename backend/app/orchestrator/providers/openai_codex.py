from __future__ import annotations

import os
from typing import Any, Dict


class CodexClient:
    def __init__(self) -> None:
        self._profile = os.getenv("CODEX_PROFILE", "default")

    def generate(self, prompt: str) -> Dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        return {
            "provider": "codex",
            "profile": self._profile,
            "auth_present": bool(api_key),
            "response": "Codex client stub - implement call path",
            "prompt_preview": prompt[:120],
        }
