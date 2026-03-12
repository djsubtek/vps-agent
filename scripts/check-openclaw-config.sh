#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$script_dir/validate_openclaw_config.sh" "${1:-/opt/vps-agent/data/openclaw/openclaw.json}"
