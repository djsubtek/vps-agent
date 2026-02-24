from __future__ import annotations

from typing import Optional

import subprocess

from guard.policy import load_policy

from backend.app.orchestrator.config import REPO_ROOT


def prepare_pr(
    title: Optional[str],
    body: Optional[str],
) -> dict:
    """
    Prepare a PR creation request.
    TODO: Wire into GitHub API client/service when available.
    """
    policy = load_policy(str(REPO_ROOT / "autonomy.yml"))
    base_branch = policy.default_branch
    head_branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return {
        "status": "skipped",
        "reason": "PR creation not configured",
        "base": base_branch,
        "head": head_branch,
        "title": title or "",
        "body": body or "",
    }


def _run_git(cmd: list[str]) -> str:
    p = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()
