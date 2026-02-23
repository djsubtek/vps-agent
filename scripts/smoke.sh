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

if ! docker compose ps --status running --services 2>/dev/null | grep -qx "control"; then
  fail "control is not running (docker compose ps)" || exit_code=1
else
  ok "control is running"
fi

health_status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' control 2>/dev/null || true)"
if [[ -z "$health_status" ]]; then
  ok "control health not configured"
else
  start_ts=$(date +%s)
  while true; do
    health_status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' control 2>/dev/null || true)"
    if [[ "$health_status" == "healthy" ]]; then
      ok "control is healthy"
      break
    fi
    now_ts=$(date +%s)
    if (( now_ts - start_ts >= 60 )); then
      fail "control health check timed out" || exit_code=1
      break
    fi
    sleep 2
  done
fi

start_ts=$(date +%s)
while true; do
  if curl -fss http://localhost:8001/healthz >/dev/null; then
    ok "healthz endpoint"
    break
  fi
  now_ts=$(date +%s)
  if (( now_ts - start_ts >= 60 )); then
    fail "healthz endpoint" || exit_code=1
    break
  fi
  sleep 2
done

start_ts=$(date +%s)
while true; do
  if curl -fss http://localhost:8001/readyz >/dev/null; then
    ok "readyz endpoint"
    break
  fi
  now_ts=$(date +%s)
  if (( now_ts - start_ts >= 60 )); then
    fail "readyz endpoint" || exit_code=1
    break
  fi
  sleep 2
done

logs="$(docker logs --tail 200 control 2>/dev/null || true)"
if command -v rg >/dev/null 2>&1; then
  if echo "$logs" | rg -qi "Unhandled exception|Traceback"; then
    fail "logs contain unhandled exception or traceback" || exit_code=1
  else
    ok "logs clean (last 200 lines)"
  fi
else
  if echo "$logs" | grep -Eq "Unhandled exception|Traceback"; then
    fail "logs contain unhandled exception or traceback" || exit_code=1
  else
    ok "logs clean (last 200 lines)"
  fi
fi

if [[ $exit_code -eq 0 ]]; then
  printf 'RESULT: OK (exit 0)\n'
  exit 0
fi

printf 'RESULT: FAIL (exit 1)\n'
exit 1
