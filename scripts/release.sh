#!/usr/bin/env bash
set -euo pipefail

ok() {
  printf 'OK  - %s\n' "$1"
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
