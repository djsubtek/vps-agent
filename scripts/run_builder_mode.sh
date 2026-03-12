#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

runtime_config="/opt/vps-agent/data/openclaw/openclaw.json"
context_policy="$repo_root/config/context-policy.yml"
agent_policy="$repo_root/config/agent-policy.yml"
verify_only=0

usage() {
  cat <<'EOF'
Usage:
  scripts/run_builder_mode.sh --verify
  scripts/run_builder_mode.sh -- [command...]

Options:
  --runtime-config PATH
  --context-policy PATH
  --agent-policy PATH
  --verify
  --help

Behavior:
  - validates the live OpenClaw runtime config first
  - loads Builder Mode policies from YAML files outside openclaw.json
  - prints active policy values for the run
  - in --verify mode, performs a dry simulated Builder Mode activation
EOF
}

command_args=()
while (($#)); do
  case "$1" in
    --runtime-config)
      runtime_config="$2"
      shift 2
      ;;
    --context-policy)
      context_policy="$2"
      shift 2
      ;;
    --agent-policy)
      agent_policy="$2"
      shift 2
      ;;
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

"$script_dir/check-openclaw-config.sh" "$runtime_config"

export BUILDER_RUNTIME_CONFIG="$runtime_config"
export BUILDER_CONTEXT_POLICY="$context_policy"
export BUILDER_AGENT_POLICY="$agent_policy"

python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

import yaml


def fail(message):
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


runtime_config = Path(os.environ["BUILDER_RUNTIME_CONFIG"])
context_policy_path = Path(os.environ["BUILDER_CONTEXT_POLICY"])
agent_policy_path = Path(os.environ["BUILDER_AGENT_POLICY"])

for path in (runtime_config, context_policy_path, agent_policy_path):
    if not path.exists():
        fail(f"required file not found: {path}")

with runtime_config.open() as handle:
    runtime_data = json.load(handle)

with context_policy_path.open() as handle:
    context_data = yaml.safe_load(handle) or {}

with agent_policy_path.open() as handle:
    agent_data = yaml.safe_load(handle) or {}

memory_flush_after_task = bool((context_data.get("memory") or {}).get("flush_after_task"))
files_include = list((context_data.get("files") or {}).get("include") or [])
files_exclude = list((context_data.get("files") or {}).get("exclude") or [])
context_limits = dict(context_data.get("context_management") or {})
tool_output = dict(context_data.get("tool_output") or {})
stages = list(((agent_data.get("execution") or {}).get("stages")) or [])
limits = dict(agent_data.get("limits") or {})
response_format = list(((agent_data.get("responses") or {}).get("format")) or [])

summary = {
    "runtime_config": str(runtime_config),
    "runtime_model_primary": (((runtime_data.get("agents") or {}).get("defaults") or {}).get("model") or {}).get("primary"),
    "context_policy": str(context_policy_path),
    "agent_policy": str(agent_policy_path),
    "memory_flush_after_task": memory_flush_after_task,
    "diff_first": "changed_files" in files_include,
    "changed_files_only": files_include,
    "exclude_paths": files_exclude,
    "context_limits": context_limits,
    "tool_output": tool_output,
    "stages": stages,
    "limits": limits,
    "response_format": response_format,
}

expected_errors = []
if not memory_flush_after_task:
    expected_errors.append("memory.flush_after_task must be true")
if "changed_files" not in files_include:
    expected_errors.append("files.include must contain changed_files for diff-first behavior")
if stages != ["PLAN", "BUILD", "REVIEW", "DONE"]:
    expected_errors.append("execution.stages must be PLAN -> BUILD -> REVIEW -> DONE")
if limits.get("planning_rounds") != 2:
    expected_errors.append("limits.planning_rounds must be 2")
if limits.get("retries") != 2:
    expected_errors.append("limits.retries must be 2")
if limits.get("subagent_spawns") != 2:
    expected_errors.append("limits.subagent_spawns must be 2")
if response_format != ["STATUS", "RESULT", "NEXT"]:
    expected_errors.append("responses.format must be STATUS / RESULT / NEXT")

print("Builder Mode policies loaded")
print(json.dumps(summary, indent=2))

if expected_errors:
    print("Policy validation errors:", file=sys.stderr)
    for item in expected_errors:
        print(f"- {item}", file=sys.stderr)
    sys.exit(1)

print("Builder Mode policy validation: OK")
PY

export BUILDER_MODE_MEMORY_FLUSH_AFTER_TASK=true
export BUILDER_MODE_CONTEXT_MODE=diff-first
export BUILDER_MODE_STAGES="PLAN,BUILD,REVIEW,DONE"
export BUILDER_MODE_PLANNING_ROUNDS=2
export BUILDER_MODE_RETRIES=2
export BUILDER_MODE_SUBAGENT_SPAWNS=2
export BUILDER_MODE_RESPONSE_FIELDS="STATUS,RESULT,NEXT"

if [[ $verify_only -eq 1 ]]; then
  printf 'Verification mode: active\n'
  printf 'Simulated run: PLAN -> BUILD -> REVIEW -> DONE\n'
  printf 'Response format: STATUS / RESULT / NEXT\n'
  printf 'Runtime config unchanged: %s\n' "$runtime_config"
  exit 0
fi

if ((${#command_args[@]} == 0)); then
  printf 'No wrapped command supplied. Use --verify or pass a command after --.\n'
  exit 0
fi

printf 'Running Builder Mode command:'
for arg in "${command_args[@]}"; do
  printf ' %q' "$arg"
done
printf '\n'
exec "${command_args[@]}"
