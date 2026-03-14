import os
import re
import subprocess
from typing import List, Optional, Set
from .policy import Policy
from .git_diff import DiffStats


class PolicyViolation(ValueError):
    pass


def _run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        return ""
    return p.stdout.strip()


def _matches_any(patterns: List[str], path: str) -> bool:
    for pat in patterns:
        if re.search(pat, path):
            return True
    return False


def _exists_in_base(path: str, base_branch: str) -> bool:
    out = _run(["git", "ls-tree", "-r", f"origin/{base_branch}", "--name-only"])
    return path in out.splitlines()


def check_paths(policy: Policy, files: List[str], allowed_exact_paths: Optional[Set[str]] = None) -> None:
    blocked = []
    allowed_exact_paths = allowed_exact_paths or set()

    for f in files:
        if f in allowed_exact_paths:
            continue

        # Immutable handling: allow creation if not yet in base branch
        if _matches_any(policy.immutable_files, f):
            if _exists_in_base(f, policy.default_branch):
                blocked.append(f)
            continue

        if _matches_any(policy.restricted_paths, f):
            blocked.append(f)

    if blocked:
        raise PolicyViolation(
            "Blocked by policy. Restricted/immutable files detected:\n"
            + "\n".join(f"  - {b}" for b in blocked)
        )


def check_limits(policy: Policy, stats: DiffStats) -> None:
    if policy.max_files_changed > 0 and len(stats.files) > policy.max_files_changed:
        raise PolicyViolation(f"Blocked by policy. Too many files changed: {len(stats.files)} > {policy.max_files_changed}")

    if policy.max_lines_changed > 0 and stats.total_lines_changed > policy.max_lines_changed:
        raise PolicyViolation(
            "Blocked by policy. Diff explosion:\n"
            f"  lines_changed={stats.total_lines_changed} (add={stats.total_add}, del={stats.total_del}) > {policy.max_lines_changed}"
        )


def check_budget(policy: Policy) -> None:
    v = os.environ.get("GUARD_COST_EUR")
    if not v:
        return
    try:
        cost = float(v)
    except Exception:
        raise PolicyViolation("Blocked by policy. GUARD_COST_EUR is not a float.")

    if policy.max_cost_eur > 0 and cost > policy.max_cost_eur:
        raise PolicyViolation(f"Blocked by policy. Cost exceeds max_cost_eur: {cost:.2f} > {policy.max_cost_eur:.2f}")
