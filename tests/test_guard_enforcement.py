from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from guard import cli
from guard.git_diff import DiffStats
from guard.policy import load_policy


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_restricted_paths_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Test User"], cwd=repo)

    root = Path(__file__).resolve().parents[1]
    shutil.copy(root / "autonomy.yml", repo / "autonomy.yml")

    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "blocked.yml").write_text("name: test\n", encoding="utf-8")
    _run(["git", "add", ".github/workflows/blocked.yml"], cwd=repo)

    monkeypatch.chdir(repo)
    with pytest.raises(cli.PolicyViolation):
        cli.pre_commit()


def test_limits_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[1]
    policy = load_policy(str(root / "autonomy.yml"))

    def _load_policy(_path: str = "autonomy.yml"):
        return policy

    monkeypatch.setattr(cli, "load_policy", _load_policy)
    monkeypatch.setattr(
        cli,
        "staged_stats",
        lambda: DiffStats(
            files=[f"f{i}.txt" for i in range(policy.max_files_changed + 1)],
            total_add=1,
            total_del=0,
        ),
    )

    with pytest.raises(cli.PolicyViolation):
        cli.pre_commit()

    monkeypatch.setattr(cli, "_ensure_origin_updated", lambda _branch: None)
    monkeypatch.setattr(
        cli,
        "range_stats",
        lambda _base, _head: DiffStats(
            files=["a.txt"],
            total_add=policy.max_lines_changed + 1,
            total_del=0,
        ),
    )

    with pytest.raises(cli.PolicyViolation):
        cli.pre_pr()
