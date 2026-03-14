System architecture notes & small changes (2026-03-14)

Summary of updates
- Replaced AGENTS.md with a concise, bootstrap-focused version emphasizing roles, guardrails, and a minimal subagent verification policy.
- Added deterministic verification step: main orchestrator will explicitly check child session history once and retry once after a short backoff.

Files changed
- /opt/vps-agent/AGENTS.md (backed up as /opt/vps-agent/AGENTS.md.bak.2026-03-14-1211)
- /opt/vps-agent/docs/system-architecture.md (this file)

Deterministic subagent handover (recommended minimal implementation)
1. Spawn child via sessions_spawn with runtime="subagent".
2. Immediately call sessions_history(childSessionKey, limit=50).
3. Inspect messages for a final assistant message containing the result and a status JSON (e.g., {"ok": true}).
4. If not found, sleep 1–2 seconds and call sessions_history once more.
5. If still not found, record a clear warning and wait for the auto-announce; surface the mismatch for manual inspection.

Why this is minimal
- One direct check + one retry keeps overhead tiny, removes race-related flakiness, and avoids busy polling or complex orchestration logic.

Rollback steps
- Restore previous AGENTS.md (example):
  cp /opt/vps-agent/AGENTS.md.bak.2026-03-14-1211 /opt/vps-agent/AGENTS.md

Contact
- For further changes to the bootstrap flow, coordinate with the Ops role and include a rollback path in the change commit.
