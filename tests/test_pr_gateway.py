from __future__ import annotations

import os

import pytest

from guard.policy import Policy
from backend.app.orchestrator import pr_gateway


class _Resp:
    def __init__(self, status_code: int, data: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._data = data or {}
        self.text = text

    def json(self) -> dict:
        return self._data


def _policy(require_ci_success: bool = True) -> Policy:
    return Policy(
        require_pr=True,
        require_tests_pass=True,
        max_files_changed=10,
        max_lines_changed=300,
        max_cost_eur=3.0,
        restricted_paths=[],
        immutable_files=[],
        require_guard_ok=True,
        require_ci_success=require_ci_success,
        owner="owner",
        repo="repo",
        default_branch="main",
    )


def test_missing_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(pr_gateway, "load_policy", lambda _path: _policy())
    monkeypatch.setattr(pr_gateway, "_run_git", lambda _cmd: "main")
    with pytest.raises(RuntimeError):
        pr_gateway.prepare_pr("t", "b")


def test_ci_failure_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(pr_gateway, "load_policy", lambda _path: _policy())

    def _run_git(cmd: list[str]) -> str:
        if cmd[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            return "feature"
        if cmd[:2] == ["git", "rev-parse"]:
            return "deadbeef"
        return ""

    monkeypatch.setattr(pr_gateway, "_run_git", _run_git)

    monkeypatch.setattr(pr_gateway.requests, "post", lambda *a, **k: _Resp(201, {"number": 1}))
    monkeypatch.setattr(pr_gateway.requests, "get", lambda *a, **k: _Resp(200, {"state": "failure"}))
    monkeypatch.setattr(pr_gateway.requests, "put", lambda *a, **k: _Resp(500, {}, "no"))

    with pytest.raises(RuntimeError):
        pr_gateway.prepare_pr("t", "b")


def test_success_triggers_merge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(pr_gateway, "load_policy", lambda _path: _policy())

    def _run_git(cmd: list[str]) -> str:
        if cmd[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            return "feature"
        if cmd[:2] == ["git", "rev-parse"]:
            return "deadbeef"
        return ""

    monkeypatch.setattr(pr_gateway, "_run_git", _run_git)

    merge_called = {"count": 0}

    monkeypatch.setattr(pr_gateway.requests, "post", lambda *a, **k: _Resp(201, {"number": 2}))
    monkeypatch.setattr(pr_gateway.requests, "get", lambda *a, **k: _Resp(200, {"state": "success"}))

    def _merge(*_a, **_k):
        merge_called["count"] += 1
        return _Resp(200, {"merged": True})

    monkeypatch.setattr(pr_gateway.requests, "put", _merge)

    result = pr_gateway.prepare_pr("t", "b")
    assert merge_called["count"] == 1
    assert result["merge"]["merged"] is True
