import subprocess
import sys

from .policy import load_policy
from .git_diff import staged_stats, range_stats
from .checks import check_paths, check_limits, check_budget, PolicyViolation
from .github_ci import commit_status_success, CiError

EXIT_POLICY_VIOLATION = 2
EXIT_RUNTIME_ERROR = 3


def _run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def _ensure_origin_updated(default_branch: str) -> None:
    _run(["git", "fetch", "origin", default_branch])


def pre_commit() -> None:
    policy = load_policy("autonomy.yml")
    stats = staged_stats()
    if not stats.files:
        return
    check_paths(policy, stats.files)
    check_limits(policy, stats)
    check_budget(policy)


def pre_pr() -> None:
    policy = load_policy("autonomy.yml")
    _ensure_origin_updated(policy.default_branch)
    base = f"origin/{policy.default_branch}"
    stats = range_stats(base, "HEAD")
    if not stats.files:
        return
    check_paths(policy, stats.files)
    check_limits(policy, stats)
    check_budget(policy)


def pre_merge(sha: str) -> None:
    policy = load_policy("autonomy.yml")
    pre_pr()
    if policy.require_tests_pass:
        commit_status_success(policy, sha)


def main(argv):
    try:
        mode = argv[1] if len(argv) > 1 else "pre-commit"
        if mode == "pre-commit":
            pre_commit()
        elif mode == "pre-pr":
            pre_pr()
        elif mode == "pre-merge":
            if len(argv) < 3:
                raise RuntimeError("Usage: python -m guard.cli pre-merge <commit_sha>")
            pre_merge(argv[2])
        else:
            raise RuntimeError(f"Unknown mode: {mode}")

        print("GUARD OK")
        return 0

    except PolicyViolation as e:
        print(str(e), file=sys.stderr)
        return EXIT_POLICY_VIOLATION
    except (CiError, RuntimeError, Exception) as e:
        print(f"GUARD RUNTIME ERROR: {e}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
