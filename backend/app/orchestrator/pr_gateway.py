from __future__ import annotations

from typing import Optional
import os
import time

import subprocess
import requests
from datetime import datetime, timezone

from guard.policy import load_policy

from backend.app.orchestrator.config import REPO_ROOT


def prepare_pr(
    title: Optional[str],
    body: Optional[str],
) -> dict:
    policy = load_policy(str(REPO_ROOT / "autonomy.yml"))
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    base_branch = policy.default_branch
    head_branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    commit_sha = _run_git(["git", "rev-parse", "HEAD"])

    _run_git(["git", "push", "origin", "HEAD"])

    pr = _create_pr(
        token=token,
        owner=policy.owner,
        repo=policy.repo,
        title=title or "",
        body=body or "",
        head=head_branch,
        base=base_branch,
    )
    pr_number = pr.get("number")
    if not pr_number:
        raise RuntimeError("GitHub PR creation failed: missing PR number")

    merge_result = None
    try:
        ci_state = _poll_ci_status(
            token=token,
            owner=policy.owner,
            repo=policy.repo,
            sha=commit_sha,
        )
        if policy.require_ci_success:
            merge_result = _merge_pr(
                token=token,
                owner=policy.owner,
                repo=policy.repo,
                number=int(pr_number),
            )
        _audit_log(pr_number, ci_state, merge_result)
    except Exception as exc:
        _audit_log(pr_number, "error", merge_result)
        raise RuntimeError(str(exc)) from exc

    return {
        "status": "created",
        "pr": pr,
        "ci_status": ci_state,
        "merge": merge_result,
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


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }


def _create_pr(
    token: str,
    owner: str,
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str,
) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {"title": title, "body": body, "head": head, "base": base}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code != 201:
        raise RuntimeError(f"GitHub PR create failed: {r.status_code} {r.text}")
    return r.json()


def _poll_ci_status(
    token: str,
    owner: str,
    repo: str,
    sha: str,
) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/status"
    start = time.time()
    while time.time() - start < 120:
        r = requests.get(url, headers=_headers(token), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"GitHub CI status failed: {r.status_code} {r.text}")
        state = (r.json() or {}).get("state")
        if state == "success":
            return "success"
        if state in {"failure", "error"}:
            raise RuntimeError(f"CI status {state}")
        time.sleep(5)
    raise RuntimeError("CI status timeout")


def _merge_pr(
    token: str,
    owner: str,
    repo: str,
    number: int,
) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge"
    payload = {"merge_method": "squash"}
    r = requests.put(url, headers=_headers(token), json=payload, timeout=30)
    if r.status_code not in {200, 201}:
        raise RuntimeError(f"GitHub merge failed: {r.status_code} {r.text}")
    return r.json()


def _audit_log(pr_number: int, ci_status: str, merge_result: Optional[dict]) -> None:
    log_dir = REPO_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "orchestrator_audit.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    merge_state = ""
    if merge_result is not None:
        merge_state = str(merge_result.get("merged", ""))
    line = (
        f"{timestamp} pr_number={pr_number} ci_status={ci_status}"
        f" merge_result={merge_state}\n"
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
