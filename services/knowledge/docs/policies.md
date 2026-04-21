# Policies

Policies are human-readable rules stored in `policies/rules.txt`. They are mounted into the backend container at `/policies/rules.txt` and loaded during ingestion, so behavior can be changed without editing Python code.

## Rule Format

```text
RULE: Restaurant Idea

WHEN:
- text contains "Restaurant" or "Essen"

THEN:
- set category = restaurant
- add tags = food
```

Separate multiple rules with:

```text
---
```

## Supported Conditions

- `content_type is <value>`
- `text contains <word>`
- `text contains "A" or "B"`

The text source is `extracted_text` when available, otherwise `raw_content`.

## Supported Actions

- `set category = X`
- `add tags = a, b`

Tags are stored as a JSON array and merged with existing tags.

## Limitations

Rules are applied in file order. Only the first matching rule is applied. If no rule matches, the item is left unchanged for later AI processing.

## Priority

Rules have priority over AI. AI classification runs after rules and must not overwrite a category set by a rule or remove rule-provided tags. AI may only add missing category values, merge additional tags, and set an empty summary.
