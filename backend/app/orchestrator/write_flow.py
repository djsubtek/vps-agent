from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.orchestrator.config import REPO_ROOT
from app.orchestrator.guard_runner import GuardError, run_pre_commit, run_pre_pr
from app.orchestrator import pr_gateway


@dataclass(frozen=True)
class WriteResult:
    commit_sha: str
    pr: dict


class WriteError(RuntimeError):
    pass


_ALLOWED_GIT_SUBCOMMANDS = {"apply", "add", "commit", "rev-parse"}
_PATCH_LIMIT_BYTES = 200_000


def _audit_log(
    command: str,
    returncode: int,
    commit_sha: Optional[str] = None,
    guard_stage: Optional[str] = None,
) -> None:
    log_dir = REPO_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "orchestrator_audit.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    line = (
        f"{timestamp} command={command} returncode={returncode}"
        f" commit_sha={commit_sha or ''} guard_stage={guard_stage or ''}\n"
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _validate_git_cmd(cmd: list[str]) -> None:
    if not cmd or cmd[0] != "git":
        raise WriteError("Git subcommand not allowed")
    subcommand = cmd[1] if len(cmd) > 1 else ""
    if subcommand not in _ALLOWED_GIT_SUBCOMMANDS:
        raise WriteError("Git subcommand not allowed")


def run_git(cmd: list[str], input_text: Optional[str] = None) -> str:
    _validate_git_cmd(cmd)
    try:
        p = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        _audit_log(" ".join(cmd), -1)
        raise WriteError("Git command timed out") from exc
    _audit_log(" ".join(cmd), p.returncode)
    if p.returncode != 0:
        raise WriteError(f"Git command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def apply_patch_and_commit(
    patch: str,
    commit_message: str,
    pr_title: Optional[str] = None,
    pr_body: Optional[str] = None,
) -> WriteResult:
    if len(patch.encode("utf-8")) > _PATCH_LIMIT_BYTES:
        raise WriteError("Patch too large")

    dry_run = os.getenv("ORCHESTRATOR_DRY_RUN", "").lower() == "true"

    run_git(["git", "apply", "--whitespace=nowarn", "-"], input_text=patch)
    run_git(["git", "add", "-A"])

    try:
        run_pre_commit()
    except GuardError as exc:
        _audit_log("guard pre-commit", exc.exit_code, guard_stage="pre-commit")
        raise
    _audit_log("guard pre-commit", 0, guard_stage="pre-commit")

    if dry_run:
        _audit_log("dry-run", 0, commit_sha="DRY_RUN")
        return WriteResult(
            commit_sha="DRY_RUN",
            pr={"status": "skipped", "reason": "dry-run"},
        )

    run_git(["git", "commit", "-m", commit_message])
    commit_sha = run_git(["git", "rev-parse", "HEAD"])
    _audit_log("git rev-parse HEAD", 0, commit_sha=commit_sha)

    try:
        run_pre_pr()
    except GuardError as exc:
        _audit_log("guard pre-pr", exc.exit_code, guard_stage="pre-pr")
        raise
    _audit_log("guard pre-pr", 0, guard_stage="pre-pr")

    pr_result = pr_gateway.prepare_pr(pr_title, pr_body)
    return WriteResult(commit_sha=commit_sha, pr=pr_result)
