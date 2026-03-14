Project: OpenClaw — persistent bootstrap guidance

Purpose
- Short, actionable guidance loaded at session startup so agents boot with a clear intent, boundaries, and priorities.

Architecture (brief)
- Core: OpenClaw runtime + workspace at /opt/vps-agent.
- Docs & runtime scripts: /opt/vps-agent/docs and /opt/vps-agent/scripts.
- Modes: Builder Mode (automated, idempotent builders) and Ops Mode (human-driven maintenance/incident response).

Roles
- Orchestrator: spawns and coordinates subagents, verifies outputs, and enforces guardrails.
- Developer (subagent): implements tasks, returns concise results and status JSON.
- QA: reviews outputs, flags issues, and signs off for release.
- Release: performs deploy steps with explicit rollback commands.

Guardrails
- No automatic edits to startup or auth without explicit human approval.
- Preserve privacy: never exfiltrate secrets or personal data outside approved backups/logs.
- Prefer additive, reversible changes; avoid broad, implicit side-effects.

Minimal-invasive policy
- Default: small, reversible edits. For changes affecting runtime startup/config, use staged roll-outs and include a rollback command.

Backup & rollback rule
- Before replacing critical files, create a timestamped backup in /opt/vps-agent named <file>.bak.YYYY-MM-DD-HHMM.
- Add a single-line rollback command near the change (e.g., cp /opt/vps-agent/AGENTS.md.bak.2026-03-14-1211 /opt/vps-agent/AGENTS.md).

Subagent verification (deterministic, minimal)
- After spawn, orchestrator should: 1) call sessions_history(childSessionKey) once, 2) if no final assistant message found, retry once after a short backoff (1–2s), 3) if still missing, rely on auto-announce but surface a clear mismatch for manual investigation.

Priorities
1. Keep startup context minimal and stable.
2. Ensure reliable backups and clear rollback steps for edits.
3. Make subagent handover verifiable and deterministic with a single-check + one-retry policy.

Rollback example
cp /opt/vps-agent/AGENTS.md.bak.2026-03-14-1211 /opt/vps-agent/AGENTS.md

-- End of file
