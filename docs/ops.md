# Ops

## Smoke Test

```bash
bash scripts/smoke.sh
```

## CI Smoke Gate

The smoke test runs in CI on pull requests and on pushes to `main` via `.github/workflows/smoke.yml`.
`scripts/release.sh` will require a successful smoke CI run for the current HEAD SHA if `gh` is available
and the `origin` remote points to GitHub. If `gh` is missing, it prints a warning and continues.

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
