#!/usr/bin/env bash
set -euo pipefail
shopt -s dotglob globstar nullglob

readonly SCRIPT_NAME="${0##*/}"
readonly RUNTIME_DIR="${PROMOTION_RUNTIME_DIR:-/opt/vps-agent}"
readonly LOG_ROOT="${PROMOTION_LOG_ROOT:-${RUNTIME_DIR}/logs/promotions}"
readonly BACKUP_ROOT="${PROMOTION_BACKUP_ROOT:-/root/openclaw-backups/promotions}"
readonly ALLOWLIST_FILE="${PROMOTION_ALLOWLIST_FILE:-${RUNTIME_DIR}/config/promotion-allowlist.txt}"
readonly DENYLIST_FILE="${PROMOTION_DENYLIST_FILE:-${RUNTIME_DIR}/config/promotion-denylist.txt}"
readonly LATEST_BACKUP_INFO="${LOG_ROOT}/latest-backup.txt"
readonly LATEST_SUMMARY_INFO="${LOG_ROOT}/latest-summary.txt"

WORKSPACE_DIR=""
LOG_FILE=""
BACKUP_DIR=""
TIMESTAMP=""
RUNTIME_OWNER=""
COMMAND=""

declare -a ALLOW_PATTERNS=() DENY_PATTERNS=() MATCHED_FILES=() MATCHED_DIRS=() DENIED_PATHS=()

usage() { printf 'Usage: %s <dry-run|promote|verify|rollback-info>\n' "${SCRIPT_NAME}"; }
say() { printf '%s\n' "$*"; }
fail() { local code="$1"; shift; say "${code} $*" >&2; exit 1; }
log() { [[ -n "${LOG_FILE}" ]] && printf '%s\n' "$*" | tee -a "${LOG_FILE}" || printf '%s\n' "$*"; }
timestamp_utc() { date -u +"%Y%m%dT%H%M%SZ"; }

resolve_workspace() {
  local candidate=""
  local -a candidates=("${PROMOTION_WORKSPACE_DIR:-}" "/home/node/.openclaw/workspace/vps-agent" "${RUNTIME_DIR}/data/openclaw/workspace/vps-agent")
  for candidate in "${candidates[@]}"; do
    [[ -n "${candidate}" && -d "${candidate}" ]] || continue
    WORKSPACE_DIR="${candidate}"
    return 0
  done
  fail "WORKSPACE_MISSING" "checked=${candidates[*]}"
}

require_runtime() {
  [[ -d "${RUNTIME_DIR}" ]] || fail "RUNTIME_MISSING" "path=${RUNTIME_DIR}"
  [[ -f "${ALLOWLIST_FILE}" ]] || fail "ALLOWLIST_MISSING" "path=${ALLOWLIST_FILE}"
  [[ -f "${DENYLIST_FILE}" ]] || fail "DENYLIST_MISSING" "path=${DENYLIST_FILE}"
  RUNTIME_OWNER="$(stat -c '%u:%g' "${RUNTIME_DIR}")"
}

setup_log() {
  mkdir -p "${LOG_ROOT}"
  TIMESTAMP="$(timestamp_utc)"
  LOG_FILE="${LOG_ROOT}/${TIMESTAMP}-${COMMAND}.log"
  : > "${LOG_FILE}"
}

read_patterns() {
  local file_path="$1"
  local -n out="$2"
  mapfile -t out < <(sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "${file_path}" | awk 'NF && $1 !~ /^#/')
}

denied_path() {
  local rel="$1" pattern=""
  for pattern in "${DENY_PATTERNS[@]}"; do
    [[ "${rel}" == ${pattern} ]] && return 0
  done
  return 1
}

collect_paths() {
  local pattern="" candidate="" rel=""
  local -A files=() dirs=() denied=()
  MATCHED_FILES=()
  MATCHED_DIRS=()
  DENIED_PATHS=()

  for pattern in "${ALLOW_PATTERNS[@]}"; do
    for candidate in "${WORKSPACE_DIR}"/${pattern}; do
      [[ -e "${candidate}" ]] || continue
      rel="${candidate#${WORKSPACE_DIR}/}"
      [[ "${rel}" != "${candidate}" && -n "${rel}" ]] || continue
      rel="${rel#/}"
      if denied_path "${rel}"; then
        denied["${rel}"]=1
        continue
      fi
      if [[ -d "${candidate}" ]]; then
        dirs["${rel}"]=1
      else
        files["${rel}"]=1
        while [[ "${rel}" == */* ]]; do
          rel="${rel%/*}"
          dirs["${rel}"]=1
        done
      fi
    done
  done

  [[ "${#dirs[@]}" -gt 0 ]] && mapfile -t MATCHED_DIRS < <(printf '%s\n' "${!dirs[@]}" | sort)
  [[ "${#files[@]}" -gt 0 ]] && mapfile -t MATCHED_FILES < <(printf '%s\n' "${!files[@]}" | sort)
  [[ "${#denied[@]}" -gt 0 ]] && mapfile -t DENIED_PATHS < <(printf '%s\n' "${!denied[@]}" | sort)
}

same_content() {
  [[ -f "$2" ]] || return 1
  cmp -s "$1" "$2"
}

write_summary() {
  local summary="$1"
  printf '%s\n' "${summary}" > "${LATEST_SUMMARY_INFO}"
  [[ -n "${BACKUP_DIR}" ]] && printf '%s\n' "${BACKUP_DIR}" > "${LATEST_BACKUP_INFO}"
}

list_changes() {
  local rel="" src="" dst=""
  for rel in "${MATCHED_FILES[@]}"; do
    src="${WORKSPACE_DIR}/${rel}"
    dst="${RUNTIME_DIR}/${rel}"
    if same_content "${src}" "${dst}"; then
      log "UNCHANGED path=${rel}"
    elif [[ -e "${dst}" ]]; then
      log "PLAN action=overwrite path=${rel}"
    else
      log "PLAN action=create path=${rel}"
    fi
  done
}

backup_existing() {
  local rel="$1" dst="${RUNTIME_DIR}/$1" backup="${BACKUP_DIR}/$1"
  [[ -e "${dst}" ]] || return 1
  install -d -m 0755 "$(dirname "${backup}")"
  cp -a "${dst}" "${backup}"
  log "BACKUP path=${rel} backup=${backup}"
  printf '%s\n' "${rel}" >> "${BACKUP_DIR}/manifest.txt"
  return 0
}

apply_permissions() {
  local src="$1" dst="$2"
  chown "${RUNTIME_OWNER}" "${dst}"
  [[ -x "${src}" ]] && chmod 0755 "${dst}" || chmod 0644 "${dst}"
}

promote_paths() {
  local rel="" src="" dst="" changed=0 backups=0 created=0
  [[ "${EUID}" -eq 0 ]] || fail "PROMOTE_REQUIRES_SUDO" "message=\"run with sudo for backup and ownership changes\""
  mkdir -p "${BACKUP_ROOT}"
  BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
  mkdir -p "${BACKUP_DIR}"
  : > "${BACKUP_DIR}/manifest.txt"

  for rel in "${MATCHED_DIRS[@]}"; do
    install -d -m 0755 "${RUNTIME_DIR}/${rel}"
    chown "${RUNTIME_OWNER}" "${RUNTIME_DIR}/${rel}"
  done

  for rel in "${MATCHED_FILES[@]}"; do
    src="${WORKSPACE_DIR}/${rel}"
    dst="${RUNTIME_DIR}/${rel}"
    if same_content "${src}" "${dst}"; then
      log "SKIP path=${rel} reason=unchanged"
      continue
    fi
    if backup_existing "${rel}"; then
      backups=$((backups + 1))
    else
      created=$((created + 1))
    fi
    install -d -m 0755 "$(dirname "${dst}")"
    cp -a "${src}" "${dst}"
    apply_permissions "${src}" "${dst}"
    log "PROMOTE path=${rel} target=${dst}"
    changed=$((changed + 1))
  done

  local summary="SUMMARY command=promote workspace=${WORKSPACE_DIR} runtime=${RUNTIME_DIR} changed=${changed} backups=${backups} created=${created} denied=${#DENIED_PATHS[@]} log=${LOG_FILE} backup_dir=${BACKUP_DIR}"
  log "${summary}"
  write_summary "${summary}"
}

verify_model() {
  local rel="" src="" dst="" synced=0 drift=0 missing=0
  for rel in "${MATCHED_FILES[@]}"; do
    src="${WORKSPACE_DIR}/${rel}"
    dst="${RUNTIME_DIR}/${rel}"
    if [[ ! -e "${dst}" ]]; then
      log "VERIFY missing path=${rel}"
      missing=$((missing + 1))
    elif same_content "${src}" "${dst}"; then
      synced=$((synced + 1))
    else
      log "VERIFY drift path=${rel}"
      drift=$((drift + 1))
    fi
  done
  local summary="SUMMARY command=verify workspace=${WORKSPACE_DIR} runtime=${RUNTIME_DIR} candidate_files=${#MATCHED_FILES[@]} synced=${synced} drift=${drift} missing=${missing} denied=${#DENIED_PATHS[@]} log=${LOG_FILE}"
  log "${summary}"
  write_summary "${summary}"
  [[ "${drift}" -eq 0 && "${missing}" -eq 0 ]]
}

rollback_info() {
  setup_log
  if [[ -f "${LATEST_BACKUP_INFO}" ]]; then
    local latest_backup
    latest_backup="$(cat "${LATEST_BACKUP_INFO}")"
    log "ROLLBACK latest_backup=${latest_backup}"
    [[ -f "${latest_backup}/manifest.txt" ]] && { log "ROLLBACK manifest=${latest_backup}/manifest.txt"; cat "${latest_backup}/manifest.txt" | tee -a "${LOG_FILE}"; }
  else
    log "ROLLBACK none-recorded"
  fi
}

main() {
  [[ "$#" -eq 1 ]] || { usage; exit 1; }
  COMMAND="$1"
  case "${COMMAND}" in
    dry-run|promote|verify|rollback-info) ;;
    *) usage; exit 1 ;;
  esac
  [[ "${COMMAND}" == "rollback-info" ]] && { rollback_info; exit 0; }

  resolve_workspace
  require_runtime
  setup_log
  read_patterns "${ALLOWLIST_FILE}" ALLOW_PATTERNS
  read_patterns "${DENYLIST_FILE}" DENY_PATTERNS
  collect_paths

  log "INFO command=${COMMAND} workspace=${WORKSPACE_DIR} runtime=${RUNTIME_DIR} allowlist=${ALLOWLIST_FILE} denylist=${DENYLIST_FILE}"
  for rel in "${DENIED_PATHS[@]}"; do log "DENY path=${rel}"; done

  case "${COMMAND}" in
    dry-run)
      list_changes
      write_summary "SUMMARY command=dry-run workspace=${WORKSPACE_DIR} runtime=${RUNTIME_DIR} candidate_files=${#MATCHED_FILES[@]} denied=${#DENIED_PATHS[@]} log=${LOG_FILE}"
      log "$(cat "${LATEST_SUMMARY_INFO}")"
      ;;
    promote) promote_paths ;;
    verify) verify_model ;;
  esac
}

main "$@"
