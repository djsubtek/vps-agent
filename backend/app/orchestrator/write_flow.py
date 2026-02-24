from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional

from backend.app.orchestrator.config import REPO_ROOT
from backend.app.orchestrator.guard_runner import run_pre_commit, run_pre_pr
from backend.app.orchestrator import pr_gateway


@dataclass(frozen=True)
class WriteResult:
    commit_sha: str
    pr: dict


class WriteError(RuntimeError):
    pass


def run_git(cmd: list[str], input_text: Optional[str] = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        raise WriteError(f"Git command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def apply_patch_and_commit(
    patch: str,
    commit_message: str,
    pr_title: Optional[str] = None,
    pr_body: Optional[str] = None,
) -> WriteResult:
    run_git(["git", "apply", "--whitespace=nowarn", "-"], input_text=patch)
    run_git(["git", "add", "-A"])

    run_pre_commit()

    run_git(["git", "commit", "-m", commit_message])
    commit_sha = run_git(["git", "rev-parse", "HEAD"])

    run_pre_pr()

    pr_result = pr_gateway.prepare_pr(pr_title, pr_body)
    return WriteResult(commit_sha=commit_sha, pr=pr_result)

