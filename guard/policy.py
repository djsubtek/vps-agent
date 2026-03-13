import os
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml


@dataclass(frozen=True)
class PreCommitOverride:
    id: str
    allowed_exact_paths: List[str]
    max_files_changed: int
    max_lines_changed: int


@dataclass(frozen=True)
class Policy:
    require_pr: bool
    require_tests_pass: bool

    max_files_changed: int
    max_lines_changed: int
    max_cost_eur: float

    restricted_paths: List[str]
    immutable_files: List[str]
    pre_commit_overrides: List[PreCommitOverride]

    require_guard_ok: bool
    require_ci_success: bool

    owner: str
    repo: str
    default_branch: str


def _must(d: Dict[str, Any], key: str):
    if key not in d:
        raise ValueError(f"Missing required key in autonomy.yml: {key}")
    return d[key]


def load_policy(path: str = "autonomy.yml") -> Policy:
    if not os.path.exists(path):
        raise ValueError(f"Missing policy file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if data.get("version") != 1:
        raise ValueError(f"Unsupported autonomy.yml version: {data.get('version')}")

    policy = data.get("policy", {})
    limits = data.get("limits", {})
    restrictions = data.get("restrictions", {})
    overrides = data.get("overrides", {})
    merge_gates = data.get("merge_gates", {})
    gh = data.get("github", {})

    pre_commit_overrides = []
    for item in overrides.get("pre_commit", []):
        pre_commit_overrides.append(
            PreCommitOverride(
                id=str(_must(item, "id")),
                allowed_exact_paths=list(item.get("allowed_exact_paths", [])),
                max_files_changed=int(item.get("max_files_changed", limits.get("max_files_changed", 0))),
                max_lines_changed=int(item.get("max_lines_changed", limits.get("max_lines_changed", 0))),
            )
        )

    return Policy(
        require_pr=bool(policy.get("require_pr", True)),
        require_tests_pass=bool(policy.get("require_tests_pass", True)),

        max_files_changed=int(limits.get("max_files_changed", 0)),
        max_lines_changed=int(limits.get("max_lines_changed", 0)),
        max_cost_eur=float(limits.get("max_cost_eur", 0.0)),

        restricted_paths=list(restrictions.get("restricted_paths", [])),
        immutable_files=list(restrictions.get("immutable_files", [])),
        pre_commit_overrides=pre_commit_overrides,

        require_guard_ok=bool(merge_gates.get("require_guard_ok", True)),
        require_ci_success=bool(merge_gates.get("require_ci_success", True)),

        owner=str(_must(gh, "owner")),
        repo=str(_must(gh, "repo")),
        default_branch=str(gh.get("default_branch", "main")),
    )
