#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly DEFAULT_SEARCH_ROOTS="/opt/vps-agent:/srv/vps-agent:/home/node/vps-agent:/work/vps-agent"
readonly STATE_HOME="${OPENCLAW_UPDATE_HOME:-${HOME:-/root}/.openclaw}"
readonly STATE_FILE="${STATE_HOME}/update-state.json"
readonly BACKUP_ROOT="${OPENCLAW_UPDATE_BACKUP_ROOT:-/root/openclaw-backups}"
readonly DOCKER_BIN="${OPENCLAW_UPDATE_DOCKER_BIN:-docker}"

COMPOSE_DIR=""
COMPOSE_FILE=""
DISCOVERY_SOURCE=""
DISCOVERY_MULTIPLE="false"
DISCOVERY_NOTES=""
COMPOSE_CANDIDATE=""

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} <detect|backup|status|pull|restart|logs>
EOF
}

say() {
  printf '%s\n' "$*"
}

fail() {
  local code="$1"
  shift
  say "${code} $*"
  exit 1
}

timestamp_utc() {
  date -u +"%Y%m%dT%H%M%SZ"
}

allowed_root() {
  local target="$1"
  local roots_string="${OPENCLAW_UPDATE_SEARCH_ROOTS:-$DEFAULT_SEARCH_ROOTS}"
  local root
  IFS=':' read -r -a root_array <<< "$roots_string"
  for root in "${root_array[@]}"; do
    [[ -n "$root" ]] || continue
    if [[ "$target" == "$root" ]]; then
      return 0
    fi
  done
  return 1
}

load_state_dir() {
  local file_path="$1"
  [[ -f "$file_path" ]] || return 1
  sed -n 's/.*"compose_dir"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$file_path" | head -n 1
}

compose_file_in_dir() {
  local dir="$1"
  local selected=""
  local found=()
  local name
  COMPOSE_CANDIDATE=""
  for name in docker-compose.yml compose.yml compose.yaml; do
    if [[ -f "$dir/$name" ]]; then
      found+=("$name")
      if [[ -z "$selected" ]]; then
        selected="$dir/$name"
      fi
    fi
  done
  if [[ "${#found[@]}" -eq 0 ]]; then
    return 1
  fi
  if [[ "${#found[@]}" -gt 1 ]]; then
    DISCOVERY_MULTIPLE="true"
    DISCOVERY_NOTES="candidates=$(IFS=,; printf '%s' "${found[*]}")"
  fi
  COMPOSE_CANDIDATE="$selected"
  return 0
}

persist_state() {
  mkdir -p "$STATE_HOME"
  cat > "$STATE_FILE" <<EOF
{"compose_dir":"$COMPOSE_DIR","compose_file":"$COMPOSE_FILE","discovered_at":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","source":"$DISCOVERY_SOURCE"}
EOF
}

discover_compose() {
  local state_dir=""
  local compose_candidate=""
  local root=""
  local roots_string="${OPENCLAW_UPDATE_SEARCH_ROOTS:-$DEFAULT_SEARCH_ROOTS}"

  DISCOVERY_MULTIPLE="false"
  DISCOVERY_NOTES=""

  state_dir="$(load_state_dir "$STATE_FILE" || true)"
  if [[ -n "$state_dir" ]] && allowed_root "$state_dir"; then
    if compose_file_in_dir "$state_dir"; then
      COMPOSE_DIR="$state_dir"
      COMPOSE_FILE="$COMPOSE_CANDIDATE"
      DISCOVERY_SOURCE="state"
      persist_state
      return 0
    fi
  fi

  IFS=':' read -r -a root_array <<< "$roots_string"
  for root in "${root_array[@]}"; do
    [[ -d "$root" ]] || continue
    if compose_file_in_dir "$root"; then
      COMPOSE_DIR="$root"
      COMPOSE_FILE="$COMPOSE_CANDIDATE"
      DISCOVERY_SOURCE="scan"
      persist_state
      return 0
    fi
  done

  fail "DISCOVERY_FAIL" "reason=compose_not_found searched=${roots_string}"
}

config_path() {
  local primary="${STATE_HOME}/openclaw.json"
  local fallback="${COMPOSE_DIR}/data/openclaw/openclaw.json"
  if [[ -f "$primary" ]]; then
    printf '%s\n' "$primary"
    return 0
  fi
  if [[ -f "$fallback" ]]; then
    printf '%s\n' "$fallback"
    return 0
  fi
  return 1
}

ensure_docker() {
  if ! command -v "$DOCKER_BIN" >/dev/null 2>&1; then
    fail "DOCKER_UNAVAILABLE" "reason=binary_not_found bin=${DOCKER_BIN}"
  fi
  if ! "$DOCKER_BIN" version; then
    fail "DOCKER_UNAVAILABLE" "reason=docker_version_failed"
  fi
}

run_compose() {
  "$DOCKER_BIN" compose -f "$COMPOSE_FILE" "$@"
}

do_detect() {
  discover_compose
  say "DISCOVERY_OK compose_dir=${COMPOSE_DIR} compose_file=${COMPOSE_FILE} source=${DISCOVERY_SOURCE} multiple=${DISCOVERY_MULTIPLE}${DISCOVERY_NOTES:+ ${DISCOVERY_NOTES}}"
}

do_backup() {
  local ts=""
  local backup_dir=""
  local source_config=""

  discover_compose
  source_config="$(config_path || true)"
  if [[ -z "$source_config" ]]; then
    fail "BACKUP_FAIL" "reason=config_not_found checked=${STATE_HOME}/openclaw.json fallback=${COMPOSE_DIR}/data/openclaw/openclaw.json"
  fi

  ts="$(timestamp_utc)"
  backup_dir="${BACKUP_ROOT}/${ts}"
  mkdir -p "$backup_dir"
  cp -a "$source_config" "${backup_dir}/openclaw.json"
  tar -C "$(dirname "$COMPOSE_DIR")" -czf "${backup_dir}/compose-dir.tgz" "$(basename "$COMPOSE_DIR")"
  say "BACKUP_OK backup_dir=${backup_dir} config=${source_config} compose_dir=${COMPOSE_DIR}"
}

do_status() {
  discover_compose
  ensure_docker
  "$DOCKER_BIN" ps
  run_compose ps
  say "SMOKE_OK compose_dir=${COMPOSE_DIR} compose_file=${COMPOSE_FILE}"
}

do_pull() {
  discover_compose
  ensure_docker
  run_compose pull
  say "PULL_OK compose_dir=${COMPOSE_DIR} compose_file=${COMPOSE_FILE}"
}

do_restart() {
  discover_compose
  ensure_docker
  run_compose up -d
  run_compose ps
  run_compose logs --tail 200
  say "RESTART_OK compose_dir=${COMPOSE_DIR} compose_file=${COMPOSE_FILE}"
  say "SMOKE_OK compose_dir=${COMPOSE_DIR} compose_file=${COMPOSE_FILE}"
}

do_logs() {
  discover_compose
  ensure_docker
  run_compose logs --tail 200
}

main() {
  if [[ "$#" -ne 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    detect)
      do_detect
      ;;
    backup)
      do_backup
      ;;
    status)
      do_status
      ;;
    pull)
      do_pull
      ;;
    restart)
      do_restart
      ;;
    logs)
      do_logs
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
