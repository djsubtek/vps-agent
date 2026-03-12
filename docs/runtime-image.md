# OpenClaw Runtime Image

This repository uses a custom builder runtime image that includes development and CI tooling required for OpenClaw operations.

Installed tools (examples):
- git
- gh (GitHub CLI)
- jq
- pytest
- python3-yaml (PyYAML)

Why the image exists:
The image provides a reproducible, auditable environment for repository automation, ensuring consistent behavior for guard hooks, PR tooling, and builder-mode operations.

How to rebuild:
- Update the Dockerfile under docker/openclaw-builder/Dockerfile
- Build the image with the repository build scripts or docker build
- Push the rebuilt image and update deployment manifests as needed
