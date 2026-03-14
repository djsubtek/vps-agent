# Builder Mode Default Path

Builder Mode is the default execution path for autonomous OpenClaw task runs in this repository.

Default task wrapper:
- `/opt/vps-agent/scripts/openclaw-task.sh`

Current default launcher:
- `/opt/vps-agent/run-codex.sh`
- This now starts `codex` through `scripts/openclaw-task.sh` instead of calling it directly

Execution flow:
1. `scripts/openclaw-task.sh` runs `scripts/check-openclaw-config.sh`
2. If runtime config validation passes, it runs `scripts/run_builder_mode.sh --verify`
3. If verification passes, it runs the requested task through `scripts/run_builder_mode.sh`
4. If validation or verification fails, execution aborts before the task starts

Policy handling:
- Policies are loaded externally from:
  - `/opt/vps-agent/config/context-policy.yml`
  - `/opt/vps-agent/config/agent-policy.yml`
- Policies are not merged into `/opt/vps-agent/data/openclaw/openclaw.json`
- Runtime config therefore remains schema-safe for the current OpenClaw version

Logging:
- Each wrapper run appends to `/opt/vps-agent/logs/builder-mode-runs.log`
- Logged fields include:
  - timestamp
  - task start
  - policy files loaded
  - runtime config validation result
  - Builder Mode verify result

Safe verification:
- `scripts/openclaw-task.sh --verify`
- This confirms the Builder Mode wrapper is active without modifying runtime config
