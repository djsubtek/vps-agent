# OpenClaw Runtime Config Rules

Purpose:
Keep the OpenClaw gateway stable by limiting `openclaw.json` to the runtime keys the current deployment actually supports.

Runtime file:
- `/opt/vps-agent/data/openclaw/openclaw.json`

Allowed root keys in the current baseline:
- `meta`
- `agents`
- `messages`
- `commands`
- `channels`
- `gateway`

Do not place policy data in `openclaw.json`:
- `policies` is not a supported root key for the current OpenClaw runtime.
- Merging builder policy or orchestration policy blocks into `openclaw.json` can make the gateway reject the config and restart with an invalid state.

Where policy files should live instead:
- Repository policy files belong under `/opt/vps-agent/config/`
- Current examples:
  - `/opt/vps-agent/config/context-policy.yml`
  - `/opt/vps-agent/config/agent-policy.yml`
- Builder tool/session permissions belong in:
  - `/opt/vps-agent/data/openclaw/workspace/.openclaw/config.yaml`
- Exec approvals belong in:
  - `/opt/vps-agent/data/openclaw/exec-approvals.json`

Safe workflow before runtime changes:
1. Edit the candidate config outside the running container.
2. Run `scripts/validate_openclaw_config.sh /path/to/openclaw.json`.
3. Only replace the live runtime file after the validator passes.
4. Restart only `openclaw` if the change requires a restart.

Validation rule of thumb:
- If a change adds a new root key, treat it as invalid until it is confirmed against the running OpenClaw schema.
- If a change is about policies, approvals, or builder behavior, prefer the dedicated policy files over `openclaw.json`.
