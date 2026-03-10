#!/usr/bin/env python3
import glob
import json
import os
import sys


SEARCH_ROOT = os.environ.get(
    "OPENCLAW_STATE_DIR", "/opt/vps-agent/data/openclaw"
)
PATTERN = os.path.join(SEARCH_ROOT, "agents", "*", "sessions", "*.jsonl")


def main() -> int:
    latest = None

    for path in glob.glob(PATTERN):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = entry.get("message") or {}
                    details = message.get("details") or {}
                    if details.get("status") != "approval-pending":
                        continue

                    approval_id = details.get("approvalId") or ""
                    approval_slug = details.get("approvalSlug") or approval_id[:8]
                    timestamp = (
                        entry.get("timestamp")
                        or message.get("timestamp")
                        or ""
                    )
                    command = details.get("command") or ""
                    candidate = {
                        "timestamp": timestamp,
                        "slug": approval_slug,
                        "approval_id": approval_id,
                        "command": command,
                        "path": path,
                    }
                    if latest is None or candidate["timestamp"] >= latest["timestamp"]:
                        latest = candidate
        except OSError:
            continue

    if latest is None:
        print("No recent exec approval request found.")
        return 0

    print(f"Latest pending-looking approval: {latest['slug']}")
    if latest["approval_id"]:
        print(f"Full approval id: {latest['approval_id']}")
    if latest["timestamp"]:
        print(f"Timestamp: {latest['timestamp']}")
    if latest["command"]:
        print(f"Command: {latest['command']}")
    print(f"Source: {latest['path']}")
    print("")
    print(f"/approve {latest['slug']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
