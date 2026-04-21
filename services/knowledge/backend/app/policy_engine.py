import os
import re
from pathlib import Path

RULES_PATH = Path(os.environ.get("POLICY_RULES_PATH", "/policies/rules.txt"))


def load_rules():
    if not RULES_PATH.exists():
        return []
    return parse_rules(RULES_PATH.read_text(encoding="utf-8"))


def parse_rules(text):
    rules = []

    for block in re.split(r"^\s*---\s*$", text, flags=re.MULTILINE):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or not lines[0].startswith("RULE:"):
            continue

        rule = {"name": lines[0].removeprefix("RULE:").strip(), "conditions": [], "actions": []}
        section = None

        for line in lines[1:]:
            if line == "WHEN:":
                section = "conditions"
                continue
            if line == "THEN:":
                section = "actions"
                continue
            if section and line.startswith("- "):
                rule[section].append(line[2:].strip())

        rules.append(rule)

    return rules


def match_rule(item, rule):
    return all(_match_condition(item, condition) for condition in rule["conditions"])


def apply_actions(item, rule):
    for action in rule["actions"]:
        if action.startswith("set category ="):
            item.category = action.split("=", 1)[1].strip()
        elif action.startswith("add tags ="):
            new_tags = [tag.strip() for tag in action.split("=", 1)[1].split(",") if tag.strip()]
            existing_tags = item.tags or []
            item.tags = list(dict.fromkeys(existing_tags + new_tags))


def _match_condition(item, condition):
    if condition.startswith("content_type is "):
        expected = condition.removeprefix("content_type is ").strip()
        return item.content_type == expected

    if condition.startswith("text contains "):
        text = (item.extracted_text or item.raw_content or "").lower()
        values = _parse_or_values(condition.removeprefix("text contains "))
        return any(value.lower() in text for value in values)

    return False


def _parse_or_values(text):
    return [part.strip().strip('"') for part in re.split(r"\s+or\s+", text) if part.strip()]
