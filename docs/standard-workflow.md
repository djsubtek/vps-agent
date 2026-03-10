# Standard Workflow

This is the canonical workflow for future OpenClaw and Codex tasks.

## Operating Roles

OpenClaw and Codex
- write only to the workspace
- validate in the workspace
- propose promotion
- do not directly edit `/opt/vps-agent` except through the approved promotion path

Ops
- runs promotion with approval
- verifies runtime state
- performs runtime-only system actions when needed

## Canonical Flow

1. Task assigned
2. Work performed in workspace
3. QA checks workspace result
4. Promote dry-run
5. Approval
6. Promote
7. Verify runtime
8. Optional restart or reload if required
9. Log outcome

## Standard Commands

Dry-run
```bash
/opt/vps-agent/tools/promote-workspace.sh dry-run
```

Promote
```bash
sudo /opt/vps-agent/tools/promote-workspace.sh promote
```

Verify promotion state
```bash
/opt/vps-agent/tools/promote-workspace.sh verify
/opt/vps-agent/tools/verify-runtime-state.sh
```

Rollback information
```bash
/opt/vps-agent/tools/promote-workspace.sh rollback-info
```

Tailnet access restore when needed
```bash
/opt/vps-agent/tools/restore-tailnet-access.sh
```

## Approval Points

- Any promotion into `/opt/vps-agent`
- Any change that affects runtime helpers or runtime data
- Any restart, reload, or network-facing runtime action
- Any allowlist expansion
