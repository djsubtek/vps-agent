# Ops

## Smoke Test

```bash
bash scripts/smoke.sh
```

## Release

```bash
bash scripts/release.sh
```

## Rollback

Find a known good SHA:

```bash
git log --oneline -n 20
```

Rollback to a specific SHA:

```bash
bash scripts/rollback.sh <sha>
```
