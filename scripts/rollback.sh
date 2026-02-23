#!/usr/bin/env bash
set -euo pipefail

ok() {
  printf 'OK  - %s\n' "$1"
}

fail() {
  printf 'FAIL- %s\n' "$1"
  return 1
}

if [[ $# -ne 1 ]]; then
  printf 'Usage: bash scripts/rollback.sh <sha>\n'
  exit 1
fi

sha="$1"
exit_code=0

if [[ -n "$(git status --porcelain)" ]]; then
  fail "repo has uncommitted changes" || exit_code=1
else
  ok "repo is clean"
fi

if git checkout --detach "$sha"; then
  ok "checked out $sha (detached)"
else
  fail "git checkout --detach $sha" || exit_code=1
fi

if docker compose up -d --build; then
  ok "docker compose up -d --build"
else
  fail "docker compose up -d --build" || exit_code=1
fi

if bash scripts/smoke.sh; then
  ok "rollback smoke test"
else
  fail "rollback smoke test" || exit_code=1
fi

if [[ $exit_code -eq 0 ]]; then
  printf 'RESULT: OK (exit 0)\n'
  exit 0
fi

printf 'RESULT: FAIL (exit 1)\n'
exit 1
