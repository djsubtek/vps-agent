#!/usr/bin/env bash
set -euo pipefail

config_path="${1:-/opt/vps-agent/data/openclaw/openclaw.json}"

python3 - "$config_path" <<'PY'
import json
import sys
from pathlib import Path

allowed_root_keys = {
    "meta",
    "agents",
    "messages",
    "commands",
    "channels",
    "gateway",
}


def expect_mapping(value, label, errors):
    if value is not None and not isinstance(value, dict):
        errors.append(f"{label} must be an object")


def expect_string_list(value, label, errors):
    if value is None:
        return
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{label} must be a non-empty string array")


path = Path(sys.argv[1])
errors = []

if not path.exists():
    print(f"FAIL: config file not found: {path}", file=sys.stderr)
    sys.exit(1)

try:
    data = json.loads(path.read_text())
except json.JSONDecodeError as exc:
    print(f"FAIL: invalid JSON in {path}: {exc}", file=sys.stderr)
    sys.exit(1)

if not isinstance(data, dict):
    print(f"FAIL: root value in {path} must be an object", file=sys.stderr)
    sys.exit(1)

unsupported_keys = sorted(set(data) - allowed_root_keys)
if unsupported_keys:
    errors.append(
        "unsupported root keys: " + ", ".join(unsupported_keys)
    )

if "policies" in data:
    errors.append('runtime config must not contain root key "policies"')

meta = data.get("meta")
expect_mapping(meta, "meta", errors)

agents = data.get("agents")
expect_mapping(agents, "agents", errors)
if isinstance(agents, dict):
    defaults = agents.get("defaults")
    expect_mapping(defaults, "agents.defaults", errors)
    if isinstance(defaults, dict):
        model = defaults.get("model")
        expect_mapping(model, "agents.defaults.model", errors)
        if isinstance(model, dict):
            primary = model.get("primary")
            if primary is not None and (not isinstance(primary, str) or "/" not in primary):
                errors.append("agents.defaults.model.primary must be a provider/model string")
            expect_string_list(model.get("fallbacks"), "agents.defaults.model.fallbacks", errors)

        models = defaults.get("models")
        expect_mapping(models, "agents.defaults.models", errors)
        if isinstance(models, dict):
            for model_name, config in models.items():
                if not isinstance(model_name, str) or "/" not in model_name:
                    errors.append("agents.defaults.models keys must be provider/model strings")
                    break
                if not isinstance(config, dict):
                    errors.append(f"agents.defaults.models.{model_name} must be an object")
                    break

messages = data.get("messages")
expect_mapping(messages, "messages", errors)

commands = data.get("commands")
expect_mapping(commands, "commands", errors)

channels = data.get("channels")
expect_mapping(channels, "channels", errors)

gateway = data.get("gateway")
expect_mapping(gateway, "gateway", errors)
if isinstance(gateway, dict):
    control_ui = gateway.get("controlUi")
    expect_mapping(control_ui, "gateway.controlUi", errors)
    if isinstance(control_ui, dict):
        expect_string_list(control_ui.get("allowedOrigins"), "gateway.controlUi.allowedOrigins", errors)
        base_path = control_ui.get("basePath")
        if base_path is not None and not isinstance(base_path, str):
            errors.append("gateway.controlUi.basePath must be a string")

    expect_string_list(gateway.get("trustedProxies"), "gateway.trustedProxies", errors)

if errors:
    print(f"FAIL: {path}", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    sys.exit(1)

print(f"OK: {path}")
print("Allowed root keys: " + ", ".join(sorted(allowed_root_keys)))
PY
