#!/usr/bin/env bash
set -euo pipefail

readonly RUNTIME_DIR="${PROMOTION_TEST_RUNTIME_DIR:-/opt/vps-agent}"
readonly TEST_WORKSPACE_ROOT="${PROMOTION_TEST_WORKSPACE_DIR:-$(mktemp -d)}"
readonly TEST_RELATIVE_PATH="docs/promotion-test.md"
readonly TEST_SOURCE="${TEST_WORKSPACE_ROOT}/${TEST_RELATIVE_PATH}"
readonly TEST_TARGET="${RUNTIME_DIR}/${TEST_RELATIVE_PATH}"

fail() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

cleanup() {
  if [[ -z "${PROMOTION_TEST_WORKSPACE_DIR:-}" ]]; then
    rm -rf "${TEST_WORKSPACE_ROOT}"
  fi
}

trap cleanup EXIT

mkdir -p "${TEST_WORKSPACE_ROOT}/docs"
cat > "${TEST_SOURCE}" <<'EOF'
# Promotion Test

This file validates the standard workspace to runtime promotion path.
EOF

PROMOTION_WORKSPACE_DIR="${TEST_WORKSPACE_ROOT}" \
  "${RUNTIME_DIR}/tools/promote-workspace.sh" dry-run >/tmp/promotion-dry-run.out
sudo env PROMOTION_WORKSPACE_DIR="${TEST_WORKSPACE_ROOT}" \
  "${RUNTIME_DIR}/tools/promote-workspace.sh" promote >/tmp/promotion-promote.out
PROMOTION_WORKSPACE_DIR="${TEST_WORKSPACE_ROOT}" \
  "${RUNTIME_DIR}/tools/promote-workspace.sh" verify >/tmp/promotion-verify.out
"${RUNTIME_DIR}/tools/verify-runtime-state.sh" >/tmp/verify-runtime-state.out

[[ -f "${TEST_TARGET}" ]] || fail "runtime file missing: ${TEST_TARGET}"
grep -q 'Promotion Test' "${TEST_TARGET}" || fail "runtime file content mismatch"

latest_log="$(ls -1t "${RUNTIME_DIR}/logs/promotions"/*.log 2>/dev/null | head -n 1 || true)"
latest_backup="$(cat "${RUNTIME_DIR}/logs/promotions/latest-backup.txt" 2>/dev/null || true)"

[[ -n "${latest_log}" ]] || fail "promotion log missing"
[[ -n "${latest_backup}" ]] || fail "backup path record missing"
[[ -d "${latest_backup}" ]] || fail "backup directory missing: ${latest_backup}"

printf 'PASS test_file=%s runtime_file=%s log=%s backup=%s\n' \
  "${TEST_SOURCE}" \
  "${TEST_TARGET}" \
  "${latest_log}" \
  "${latest_backup}"
