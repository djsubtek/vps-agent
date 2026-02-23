#!/usr/bin/env bash
set -euo pipefail

ok() {
  printf 'OK  - %s\n' "$1"
}

warn() {
  printf 'WARN- %s\n' "$1"
}

fail() {
  printf 'FAIL- %s\n' "$1"
  return 1
}

exit_code=0

if [[ -n "$(git status --porcelain)" ]]; then
  fail "repo has uncommitted changes" || exit_code=1
else
  ok "repo is clean"
fi

origin_url="$(git remote get-url origin 2>/dev/null || true)"
head_sha="$(git rev-parse HEAD)"
if command -v gh >/dev/null 2>&1 && [[ "$origin_url" == *"github.com"* ]]; then
  repo_path="$(printf '%s' "$origin_url" | sed -E 's#.*github.com[:/](.+?)(\\.git)?$#\\1#')"
  if [[ -z "$repo_path" || "$repo_path" == "$origin_url" ]]; then
    fail "unable to parse GitHub repo from origin URL" || exit_code=1
  else
    run_sha="$(gh api "repos/$repo_path/actions/workflows/smoke.yml/runs?head_sha=$head_sha&per_page=1" --jq '.workflow_runs[0].head_sha' 2>/dev/null || true)"
    run_conclusion="$(gh api "repos/$repo_path/actions/workflows/smoke.yml/runs?head_sha=$head_sha&per_page=1" --jq '.workflow_runs[0].conclusion' 2>/dev/null || true)"
    if [[ -z "$run_sha" || -z "$run_conclusion" ]]; then
      fail "smoke CI run not found for HEAD $head_sha" || exit_code=1
    elif [[ "$run_sha" != "$head_sha" ]]; then
      fail "smoke CI SHA mismatch (got $run_sha)" || exit_code=1
    elif [[ "$run_conclusion" != "success" ]]; then
      fail "smoke CI not successful (conclusion: $run_conclusion)" || exit_code=1
    else
      ok "smoke CI gate passed for $head_sha"
    fi
  fi
else
  warn "gh not available or origin not GitHub; skipping CI gate"
fi

if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  if git pull --ff-only; then
    ok "git pull --ff-only"
  else
    fail "git pull --ff-only" || exit_code=1
  fi
else
  ok "no upstream configured; skipping git pull"
fi

if bash scripts/smoke.sh; then
  ok "pre-release smoke test"
else
  fail "pre-release smoke test" || exit_code=1
fi

if docker compose up -d --build; then
  ok "docker compose up -d --build"
else
  fail "docker compose up -d --build" || exit_code=1
fi

if bash scripts/smoke.sh; then
  ok "post-release smoke test"
else
  fail "post-release smoke test" || exit_code=1
fi

if [[ $exit_code -eq 0 ]]; then
  printf 'RESULT: OK (exit 0)\n'
  exit 0
fi

printf 'RESULT: FAIL (exit 1)\n'
exit 1
