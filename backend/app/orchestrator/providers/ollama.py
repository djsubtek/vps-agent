from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        url = f"{self.base_url.rstrip('/')}/api/generate"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
        data = json.loads(body)
        return {
            "provider": "ollama",
            "model": self.model,
            "response": data.get("response", ""),
        }
