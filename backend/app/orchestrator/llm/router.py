from __future__ import annotations

from typing import Any, Dict

from backend.app.orchestrator.policies.escalation import should_escalate
from backend.app.orchestrator.providers.ollama import OllamaClient
from backend.app.orchestrator.providers.openai_codex import CodexClient


class LLMRouter:
    def __init__(self) -> None:
        self.ollama = OllamaClient()
        self.codex = CodexClient()

    def generate(self, prompt: str, env: str, policy_reason: str | None = None) -> Dict[str, Any]:
        if should_escalate(env, policy_reason):
            return self.codex.generate(prompt)
        return self.ollama.generate(prompt)
