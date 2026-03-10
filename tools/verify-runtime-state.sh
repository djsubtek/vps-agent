#!/usr/bin/env bash
set -euo pipefail

readonly RUNTIME_DIR="${VERIFY_RUNTIME_DIR:-/opt/vps-agent}"

failures=0
passes=0

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    printf 'PASS file=%s\n' "${path}"
    passes=$((passes + 1))
  else
    printf 'FAIL missing_file=%s\n' "${path}"
    failures=$((failures + 1))
  fi
}

check_dir() {
  local path="$1"
  if [[ -d "${path}" ]]; then
    printf 'PASS dir=%s\n' "${path}"
    passes=$((passes + 1))
  else
    printf 'FAIL missing_dir=%s\n' "${path}"
    failures=$((failures + 1))
  fi
}

check_dir "${RUNTIME_DIR}/roles"
check_dir "${RUNTIME_DIR}/tools"
check_dir "${RUNTIME_DIR}/docs"
check_dir "${RUNTIME_DIR}/config"
check_dir "${RUNTIME_DIR}/logs/promotions"

check_file "${RUNTIME_DIR}/roles/orchestrator.md"
check_file "${RUNTIME_DIR}/roles/developer.md"
check_file "${RUNTIME_DIR}/roles/qa.md"
check_file "${RUNTIME_DIR}/roles/ops.md"
check_file "${RUNTIME_DIR}/tools/openclaw-update.sh"
check_file "${RUNTIME_DIR}/tools/restore-tailnet-access.sh"
check_file "${RUNTIME_DIR}/tools/print-approve-last.sh"
check_file "${RUNTIME_DIR}/tools/promote-workspace.sh"
check_file "${RUNTIME_DIR}/tools/verify-runtime-state.sh"
check_file "${RUNTIME_DIR}/docs/runtime-access.md"
check_file "${RUNTIME_DIR}/docs/workspace-runtime-model.md"
check_file "${RUNTIME_DIR}/docs/standard-workflow.md"
check_file "${RUNTIME_DIR}/config/promotion-allowlist.txt"
check_file "${RUNTIME_DIR}/config/promotion-denylist.txt"

printf 'SUMMARY status=%s passes=%s failures=%s runtime=%s\n' \
  "$([[ "${failures}" -eq 0 ]] && printf 'PASS' || printf 'FAIL')" \
  "${passes}" \
  "${failures}" \
  "${RUNTIME_DIR}"

[[ "${failures}" -eq 0 ]]
