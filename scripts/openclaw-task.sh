#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
runtime_config="/opt/vps-agent/data/openclaw/openclaw.json"
context_policy="$repo_root/config/context-policy.yml"
agent_policy="$repo_root/config/agent-policy.yml"
log_file="$repo_root/logs/builder-mode-runs.log"

mkdir -p "$(dirname "$log_file")"

timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

log_line() {
  printf '[%s] %s\n' "$(timestamp)" "$*" >>"$log_file"
}

usage() {
  cat <<'EOF'
Usage:
  scripts/openclaw-task.sh --verify
  scripts/openclaw-task.sh -- [command...]

Behavior:
  - validates the runtime config first
  - runs Builder Mode verification before task execution
  - aborts immediately if validation or verification fails
  - logs each run to logs/builder-mode-runs.log
EOF
}

verify_only=0
command_args=()

while (($#)); do
  case "$1" in
    --verify)
      verify_only=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      command_args=("$@")
      break
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ $verify_only -eq 0 && ${#command_args[@]} -eq 0 ]]; then
  verify_only=1
fi

task_desc="verify"
if [[ ${#command_args[@]} -gt 0 ]]; then
  printf -v task_desc '%q ' "${command_args[@]}"
  task_desc="${task_desc% }"
fi

log_line "task start: $task_desc"
log_line "policy files loaded: $context_policy $agent_policy"

if ! validation_output="$("$script_dir/check-openclaw-config.sh" "$runtime_config" 2>&1)"; then
  log_line "runtime config validation: FAIL"
  while IFS= read -r line; do
    log_line "validation output: $line"
  done <<<"$validation_output"
  printf '%s\n' "$validation_output" >&2
  exit 1
fi

log_line "runtime config validation: OK"
while IFS= read -r line; do
  log_line "validation output: $line"
done <<<"$validation_output"

if ! verify_output="$("$script_dir/run_builder_mode.sh" --verify 2>&1)"; then
  log_line "verify result: FAIL"
  while IFS= read -r line; do
    log_line "verify output: $line"
  done <<<"$verify_output"
  printf '%s\n' "$verify_output" >&2
  exit 1
fi

log_line "verify result: OK"
while IFS= read -r line; do
  log_line "verify output: $line"
done <<<"$verify_output"

if [[ $verify_only -eq 1 ]]; then
  printf '%s\n' "$verify_output"
  exit 0
fi

log_line "execution path: scripts/run_builder_mode.sh -- $task_desc"
"$script_dir/run_builder_mode.sh" -- "${command_args[@]}"
run_status=$?
log_line "task end: exit=$run_status"
exit "$run_status"
