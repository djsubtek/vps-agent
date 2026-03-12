# Builder Mode Activation

Purpose:
Activate Builder Mode policies without writing unsupported keys into the OpenClaw runtime config.

Runtime safety rule:
- Do not merge Builder Mode policy blocks into `/opt/vps-agent/data/openclaw/openclaw.json`
- `openclaw.json` remains runtime-only and must stay within the current supported schema

External policy sources:
- `/opt/vps-agent/config/context-policy.yml`
- `/opt/vps-agent/config/agent-policy.yml`

Runtime config guard:
- `scripts/check-openclaw-config.sh`
- This must pass before a Builder Mode run starts
- If the runtime config is invalid, Builder Mode activation aborts immediately

Activation entrypoint:
- `scripts/run_builder_mode.sh`

What the wrapper enforces for each Builder Mode run:
- memory flush after completed tasks
- diff-first / changed-files-first context handling
- stage flow: `PLAN -> BUILD -> REVIEW -> DONE`
- run limits:
  - `planning_rounds: 2`
  - `retries: 2`
  - `subagent_spawns: 2`
- response format:
  - `STATUS`
  - `RESULT`
  - `NEXT`

How the wrapper applies policy safely:
- validates `/opt/vps-agent/data/openclaw/openclaw.json` first
- loads YAML policy files externally
- prints the active policy values for the run
- exports Builder Mode environment variables for wrapped commands
- never injects policy data into `openclaw.json`

Verification mode:
- `scripts/run_builder_mode.sh --verify`
- safe dry run
- confirms the policy files load
- confirms required limits and response format are active
- does not modify runtime config

Wrapped run example:
- `scripts/run_builder_mode.sh -- bash -lc 'printf "STATUS\n\nRESULT\n\nNEXT\n"'`

Policy source of truth:
- The operational limits come from the YAML policy files in `config/`
- Documentation such as `docs/cost-control-policy.md` is descriptive and should not be treated as a runtime schema extension
