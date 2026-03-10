# OpenClaw Self-Update

## Helper

- Host helper: `/opt/vps-agent/tools/openclaw-update.sh`
- Supported operations only: `detect`, `backup`, `status`, `pull`, `restart`, `logs`
- State file: `~/.openclaw/update-state.json`
- Backup root: `/root/openclaw-backups/`

The helper does not accept arbitrary shell fragments. It exposes a fixed verb set and internally runs only the required Docker Compose flow for OpenClaw.

## Compose discovery

Discovery checks these directories in order:

1. `/opt/vps-agent`
2. `/srv/vps-agent`
3. `/home/node/vps-agent`
4. `/work/vps-agent`

Within each directory it prefers:

1. `docker-compose.yml`
2. `compose.yml`
3. `compose.yaml`

If discovery succeeds, the selected compose directory is persisted in `~/.openclaw/update-state.json` and used first on later runs.

## OpenClaw integration

OpenClaw should call the helper on the gateway host instead of invoking Docker directly:

```text
/opt/vps-agent/tools/openclaw-update.sh detect
/opt/vps-agent/tools/openclaw-update.sh backup
/opt/vps-agent/tools/openclaw-update.sh pull
/opt/vps-agent/tools/openclaw-update.sh restart
```

Optional follow-up checks:

```text
/opt/vps-agent/tools/openclaw-update.sh status
/opt/vps-agent/tools/openclaw-update.sh logs
```

Expected structured markers:

- `DISCOVERY_OK`
- `BACKUP_OK`
- `PULL_OK`
- `RESTART_OK`
- `SMOKE_OK`

## Allowlist config

The live exec allowlist entry is in [`data/openclaw/exec-approvals.json`](/opt/vps-agent/data/openclaw/exec-approvals.json).

```json
{
  "pattern": "/opt/vps-agent/tools/openclaw-update.sh"
}
```

This keeps Docker itself out of the OpenClaw allowlist. OpenClaw is allowed to execute only the helper, and the helper constrains the host-side actions.

## Example output

```text
$ /opt/vps-agent/tools/openclaw-update.sh detect
DISCOVERY_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml source=scan multiple=false

$ /opt/vps-agent/tools/openclaw-update.sh backup
BACKUP_OK backup_dir=/root/openclaw-backups/20260310T120000Z config=/opt/vps-agent/data/openclaw/openclaw.json compose_dir=/opt/vps-agent

$ /opt/vps-agent/tools/openclaw-update.sh pull
PULL_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml

$ /opt/vps-agent/tools/openclaw-update.sh restart
RESTART_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml
SMOKE_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml
```

`restart` also runs `docker compose ps` and `docker compose logs --tail 200` so the tail of recent logs is emitted before the structured success lines.

## Rollback

1. Identify the latest backup directory under `/root/openclaw-backups/`.
2. Restore the config:

```bash
cp -a /root/openclaw-backups/<timestamp>/openclaw.json /opt/vps-agent/data/openclaw/openclaw.json
```

3. Restore the compose directory:

```bash
tar -C / -xzf /root/openclaw-backups/<timestamp>/compose-dir.tgz
```

4. Restart the stack:

```bash
docker compose -f /opt/vps-agent/docker-compose.yml up -d
docker compose -f /opt/vps-agent/docker-compose.yml ps
docker compose -f /opt/vps-agent/docker-compose.yml logs --tail 200
```

If the deployed stack is under `/srv/vps-agent`, `/home/node/vps-agent`, or `/work/vps-agent`, adjust the restore target and compose file path to match the discovered directory.

# Phase 1 Completion (System Stabilization)

The following components exist and are operational on the canonical host path:

- Repository: `/opt/vps-agent`
- Compose stack: `/opt/vps-agent/docker-compose.yml`
- Update helper: `/opt/vps-agent/tools/openclaw-update.sh`
- Backup location: `/root/openclaw-backups/`
- State persistence: `~/.openclaw/update-state.json`
- Exec allowlist: `/opt/vps-agent/data/openclaw/exec-approvals.json`

## Standard update procedure

Run the helper in this order:

1. `detect`
2. `status`
3. `backup`
4. `pull`
5. `restart`
6. `logs`

Canonical command sequence:

```text
/opt/vps-agent/tools/openclaw-update.sh detect
/opt/vps-agent/tools/openclaw-update.sh status
/opt/vps-agent/tools/openclaw-update.sh backup
/opt/vps-agent/tools/openclaw-update.sh pull
/opt/vps-agent/tools/openclaw-update.sh restart
/opt/vps-agent/tools/openclaw-update.sh logs
```

Expected example output markers:

```text
$ /opt/vps-agent/tools/openclaw-update.sh detect
DISCOVERY_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml source=state multiple=false

$ /opt/vps-agent/tools/openclaw-update.sh status
SMOKE_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml

$ /opt/vps-agent/tools/openclaw-update.sh backup
BACKUP_OK backup_dir=/root/openclaw-backups/20260310T122300Z config=/opt/vps-agent/data/openclaw/openclaw.json compose_dir=/opt/vps-agent

$ /opt/vps-agent/tools/openclaw-update.sh pull
PULL_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml

$ /opt/vps-agent/tools/openclaw-update.sh restart
RESTART_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml
SMOKE_OK compose_dir=/opt/vps-agent compose_file=/opt/vps-agent/docker-compose.yml

$ /opt/vps-agent/tools/openclaw-update.sh logs
openclaw-1  | ...
```

Notes:

- `detect` confirms compose discovery and persists the selected compose path.
- `status` prints Docker and Compose status, then ends with `SMOKE_OK`.
- `backup` writes a timestamped snapshot under `/root/openclaw-backups/`.
- `pull` refreshes images for the discovered compose stack and ends with `PULL_OK`.
- `restart` runs `docker compose up -d`, prints service state and recent logs, then ends with `RESTART_OK` and `SMOKE_OK`.
- `logs` emits the recent compose log tail only. It does not print a final structured `*_OK` marker.

## Short rollback

If an update fails after `pull` or `restart`:

1. Identify the latest backup under `/root/openclaw-backups/`.
2. Restore `openclaw.json` from that backup.
3. Restore `compose-dir.tgz` to `/`.
4. Restart with `docker compose -f /opt/vps-agent/docker-compose.yml up -d`.
5. Verify with `docker compose -f /opt/vps-agent/docker-compose.yml ps` and `docker compose -f /opt/vps-agent/docker-compose.yml logs --tail 200`.

"Phase 1 (Stabilize system & persist fixes) is completed."
