import os
import requests
from .policy import Policy


class CiError(RuntimeError):
    pass


def _token() -> str:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not t:
        raise CiError("Missing GITHUB_TOKEN or GH_TOKEN environment variable.")
    return t


def commit_status_success(policy: Policy, sha: str) -> None:
    url = f"https://api.github.com/repos/{policy.owner}/{policy.repo}/commits/{sha}/status"
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        raise CiError(f"GitHub API error {r.status_code}: {r.text}")

    state = (r.json() or {}).get("state")
    if state != "success":
        raise CiError(f"CI not successful for {sha}. state={state}")
