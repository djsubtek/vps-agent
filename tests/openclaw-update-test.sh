#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT="/opt/vps-agent/tools/openclaw-update.sh"
TEST_TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TEST_TMPDIR"' EXIT

pass_count=0

fail_test() {
  printf 'FAIL %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    printf 'ASSERT FAILED [%s]\nexpected to find: %s\nin: %s\n' "$label" "$needle" "$haystack" >&2
    exit 1
  fi
}

assert_file_exists() {
  local path="$1"
  local label="$2"
  [[ -e "$path" ]] || fail_test "${label}: missing ${path}"
}

new_env() {
  local name="$1"
  local root="${TEST_TMPDIR}/${name}"
  mkdir -p "${root}/home/.openclaw" "${root}/backups" "${root}/bin"
  printf '%s\n' "$root"
}

write_fake_docker() {
  local root="$1"
  cat > "${root}/bin/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${DOCKER_LOG:?}"
case "${1:-}" in
  version)
    printf 'Client: fake\n'
    ;;
  ps)
    printf 'CONTAINER ID   IMAGE   STATUS\n'
    ;;
  compose)
    shift
    if [[ "${1:-}" == "-f" ]]; then
      shift 2
    fi
    case "${1:-}" in
      ps)
        printf 'NAME        STATUS\nopenclaw    running\n'
        ;;
      pull)
        printf 'Pulled images\n'
        ;;
      up)
        printf 'Started services\n'
        ;;
      logs)
        printf 'openclaw  | ready\n'
        ;;
      *)
        printf 'unexpected compose subcommand: %s\n' "${1:-}" >&2
        exit 1
        ;;
    esac
    ;;
  *)
    printf 'unexpected docker subcommand: %s\n' "${1:-}" >&2
    exit 1
    ;;
esac
EOF
  chmod 0755 "${root}/bin/docker"
}

run_script() {
  local root="$1"
  local op="$2"
  local with_docker="${3:-yes}"
  local search_roots="${4:-}"
  local output=""
  local status=0

  if [[ "$with_docker" == "yes" ]]; then
    write_fake_docker "$root"
  fi

  export HOME="${root}/home"
  export OPENCLAW_UPDATE_HOME="${root}/home/.openclaw"
  export OPENCLAW_UPDATE_BACKUP_ROOT="${root}/backups"
  export OPENCLAW_UPDATE_SEARCH_ROOTS="${search_roots}"
  export DOCKER_LOG="${root}/docker.log"
  : > "$DOCKER_LOG"

  set +e
  output="$(
    PATH="${root}/bin:/usr/bin:/bin" \
    "$SCRIPT" "$op" 2>&1
  )"
  status=$?
  set -e

  printf '%s\n%s' "$status" "$output"
}

test_detect_opt_path() {
  local root env_output status output
  root="$(new_env detect_opt)"
  mkdir -p "${root}/opt/vps-agent"
  printf 'services: {}\n' > "${root}/opt/vps-agent/docker-compose.yml"

  env_output="$(run_script "$root" detect yes "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"

  [[ "$status" == "0" ]] || fail_test "detect_opt_path: expected success"
  assert_contains "$output" "DISCOVERY_OK" "detect_opt_path result"
  assert_contains "$output" "compose_dir=${root}/opt/vps-agent" "detect_opt_path compose_dir"
  assert_file_exists "${root}/home/.openclaw/update-state.json" "detect_opt_path state"
  pass_count=$((pass_count + 1))
}

test_detect_work_path() {
  local root env_output status output
  root="$(new_env detect_work)"
  mkdir -p "${root}/work/vps-agent"
  printf 'services: {}\n' > "${root}/work/vps-agent/compose.yaml"

  env_output="$(run_script "$root" detect yes "${root}/opt/vps-agent:${root}/work/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"

  [[ "$status" == "0" ]] || fail_test "detect_work_path: expected success"
  assert_contains "$output" "compose_dir=${root}/work/vps-agent" "detect_work_path compose_dir"
  assert_contains "$output" "compose_file=${root}/work/vps-agent/compose.yaml" "detect_work_path compose_file"
  pass_count=$((pass_count + 1))
}

test_multiple_compose_files() {
  local root env_output status output
  root="$(new_env detect_multiple)"
  mkdir -p "${root}/opt/vps-agent"
  printf 'services: {}\n' > "${root}/opt/vps-agent/docker-compose.yml"
  printf 'services: {}\n' > "${root}/opt/vps-agent/compose.yaml"

  env_output="$(run_script "$root" detect yes "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"

  [[ "$status" == "0" ]] || fail_test "multiple_compose_files: expected success"
  assert_contains "$output" "compose_file=${root}/opt/vps-agent/docker-compose.yml" "multiple_compose_files priority"
  assert_contains "$output" "multiple=true" "multiple_compose_files multiple flag"
  pass_count=$((pass_count + 1))
}

test_compose_not_found() {
  local root env_output status output
  root="$(new_env no_compose)"
  mkdir -p "${root}/opt/vps-agent"

  env_output="$(run_script "$root" detect yes "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"

  [[ "$status" != "0" ]] || fail_test "compose_not_found: expected failure"
  assert_contains "$output" "DISCOVERY_FAIL" "compose_not_found result"
  pass_count=$((pass_count + 1))
}

test_worker_without_docker() {
  local root env_output status output
  root="$(new_env no_docker)"
  mkdir -p "${root}/opt/vps-agent"
  printf 'services: {}\n' > "${root}/opt/vps-agent/docker-compose.yml"

  env_output="$(run_script "$root" status no "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"

  [[ "$status" != "0" ]] || fail_test "worker_without_docker: expected failure"
  assert_contains "$output" "DOCKER_UNAVAILABLE" "worker_without_docker result"
  pass_count=$((pass_count + 1))
}

test_backup_pull_restart_logs() {
  local root env_output status output
  root="$(new_env flow)"
  mkdir -p "${root}/opt/vps-agent/data/openclaw"
  printf 'services: {}\n' > "${root}/opt/vps-agent/docker-compose.yml"
  printf '{"ok":true}\n' > "${root}/opt/vps-agent/data/openclaw/openclaw.json"

  env_output="$(run_script "$root" backup yes "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"
  [[ "$status" == "0" ]] || fail_test "backup_pull_restart_logs: backup failed"
  assert_contains "$output" "BACKUP_OK" "backup_pull_restart_logs backup"

  env_output="$(run_script "$root" pull yes "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"
  [[ "$status" == "0" ]] || fail_test "backup_pull_restart_logs: pull failed"
  assert_contains "$output" "PULL_OK" "backup_pull_restart_logs pull"

  env_output="$(run_script "$root" restart yes "${root}/opt/vps-agent")"
  status="${env_output%%$'\n'*}"
  output="${env_output#*$'\n'}"
  [[ "$status" == "0" ]] || fail_test "backup_pull_restart_logs: restart failed"
  assert_contains "$output" "RESTART_OK" "backup_pull_restart_logs restart"
  assert_contains "$output" "SMOKE_OK" "backup_pull_restart_logs smoke"
  assert_contains "$(cat "${root}/docker.log")" "compose -f ${root}/opt/vps-agent/docker-compose.yml logs --tail 200" "backup_pull_restart_logs docker logs"
  pass_count=$((pass_count + 1))
}

test_detect_opt_path
test_detect_work_path
test_multiple_compose_files
test_compose_not_found
test_worker_without_docker
test_backup_pull_restart_logs

printf 'PASS %s tests\n' "$pass_count"
