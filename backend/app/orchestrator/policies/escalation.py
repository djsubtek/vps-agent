from __future__ import annotations


def should_escalate(env: str, reason: str | None = None) -> bool:
    if env != "staging":
        return False
    if reason == "needs_codex":
        return True
    return False
