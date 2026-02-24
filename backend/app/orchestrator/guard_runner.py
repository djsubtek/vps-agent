from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Optional

from app.orchestrator.config import REPO_ROOT


@dataclass(frozen=True)
class GuardError(Exception):
    mode: str
    exit_code: int
    stdout: str
    stderr: str

    def __str__(self) -> str:
        msg = self.stderr.strip() or self.stdout.strip()
        if msg:
            return f"Guard {self.mode} failed (exit={self.exit_code}): {msg}"
        return f"Guard {self.mode} failed (exit={self.exit_code})"


def _run_guard(mode: str, sha: Optional[str] = None) -> None:
    cmd = ["python3", "-m", "guard.cli", mode]
    if mode == "pre-merge":
        if not sha:
            raise ValueError("pre-merge requires a commit sha")
        cmd.append(sha)
    p = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        raise GuardError(mode=mode, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)


def run_pre_commit() -> None:
    _run_guard("pre-commit")


def run_pre_pr() -> None:
    _run_guard("pre-pr")


def run_pre_merge(sha: str) -> None:
    _run_guard("pre-merge", sha=sha)
