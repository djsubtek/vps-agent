# operations

## Backup Procedure

Standard command for future backups:

Codex / Ops should execute the backup workflow that:

1. archives /opt/vps-agent
2. archives OpenClaw data
3. archives workspace
4. captures docker state
5. captures tailscale configuration
6. records runtime verification

Backups stored in:

/root/openclaw-backups/system/<timestamp>
