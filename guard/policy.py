import os
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml


@dataclass(frozen=True)
class Policy:
    require_pr: bool
    require_tests_pass: bool

    max_files_changed: int
    max_lines_changed: int
    max_cost_eur: float

    restricted_paths: List[str]
    immutable_files: List[str]

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
    merge_gates = data.get("merge_gates", {})
    gh = data.get("github", {})

    return Policy(
        require_pr=bool(policy.get("require_pr", True)),
        require_tests_pass=bool(policy.get("require_tests_pass", True)),

        max_files_changed=int(limits.get("max_files_changed", 0)),
        max_lines_changed=int(limits.get("max_lines_changed", 0)),
        max_cost_eur=float(limits.get("max_cost_eur", 0.0)),

        restricted_paths=list(restrictions.get("restricted_paths", [])),
        immutable_files=list(restrictions.get("immutable_files", [])),

        require_guard_ok=bool(merge_gates.get("require_guard_ok", True)),
        require_ci_success=bool(merge_gates.get("require_ci_success", True)),

        owner=str(_must(gh, "owner")),
        repo=str(_must(gh, "repo")),
        default_branch=str(gh.get("default_branch", "main")),
    )
