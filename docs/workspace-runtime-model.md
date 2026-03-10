# Workspace Runtime Model

## 1. Purpose

This project uses one operating model:

workspace change -> review and validation -> controlled promotion -> runtime verification

The goal is to keep normal agent work in the workspace, keep runtime stable, and make production changes auditable and reversible.

## 2. Directory Roles

Workspace
- Container path: `/home/node/.openclaw/workspace/vps-agent`
- Host-mounted equivalent: `/opt/vps-agent/data/openclaw/workspace/vps-agent`
- Used for implementation, drafts, tests, reviews, prompts, role edits, and other non-runtime work

Runtime
- Path: `/opt/vps-agent`
- This is the source of truth for anything operational
- Runtime services, helper scripts, role files, and docs are loaded from here only

Never treat the workspace as runtime
- Services do not load directly from the workspace
- Manual `mv` or `cp` fixes are not the standard deployment path

## 3. Promotion Model

Promotion is handled only through:

`/opt/vps-agent/tools/promote-workspace.sh`

The promotion script:
- reads a manifest-driven allowlist and denylist
- resolves the approved workspace path
- supports `dry-run`, `promote`, `verify`, and `rollback-info`
- backs up overwritten runtime files before changing them
- writes a timestamped log for each run
- syncs only allowlisted paths
- does not delete runtime files automatically

Current approved workspace input:
- `/home/node/.openclaw/workspace/vps-agent`
- host-mounted equivalent `/opt/vps-agent/data/openclaw/workspace/vps-agent`

Current runtime target:
- `/opt/vps-agent`

## 4. Approval Model

Developer and OpenClaw work in the workspace without runtime privileges.

Promotion requires an explicit Ops action:
- review workspace output
- run `promote-workspace.sh dry-run`
- obtain approval for runtime change
- run `sudo /opt/vps-agent/tools/promote-workspace.sh promote`
- run runtime verification

This keeps OpenClaw away from broad root shells while still allowing a narrow, reviewable deployment path.

## 5. Rollback Model

Every promotion stores backups under:
- `/root/openclaw-backups/promotions/<timestamp>/`

Every promotion also writes logs under:
- `/opt/vps-agent/logs/promotions/`

Rollback approach:
1. Inspect the latest backup path with `promote-workspace.sh rollback-info`
2. Identify the backed up runtime files in the backup manifest
3. Restore only the affected files from the backup directory
4. Run `/opt/vps-agent/tools/verify-runtime-state.sh`
5. Restart or reload runtime services only if the promoted change required it

## 6. Examples

Role update
1. Edit `roles/orchestrator.md` in the workspace
2. Validate content in the workspace
3. Run `promote-workspace.sh dry-run`
4. Approve and promote
5. Verify `/opt/vps-agent/roles/orchestrator.md`

Docs update
1. Edit `docs/...` in the workspace
2. QA reviews the workspace content
3. Ops promotes only the allowlisted docs path

Tooling update
1. Update a safe project script under `tools/` in the workspace
2. Review carefully because tooling affects runtime operations
3. Promote through the standard script

## 7. Rules For Future Tasks

- Developer writes only in the workspace
- QA validates workspace outputs before runtime changes
- Ops promotes to `/opt/vps-agent` and verifies runtime state
- Runtime files are not edited directly unless there is a documented emergency fix
- If an emergency runtime fix is needed, it must be copied back into the workspace and reconciled immediately after
- New promotable paths must be added to the allowlist deliberately
- Dangerous paths stay blocked by default unless separately approved
