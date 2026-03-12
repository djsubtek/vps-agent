# Builder Mode

Purpose:
Builder Mode documents the safe, auditable automation surface used by OpenClaw to perform repository maintenance and CI-related tasks.

Allowed capabilities:
- git commit
- git push
- create pull requests
- make filesystem changes within the repository (non-privileged)

Restricted/forbidden operations:
- docker manipulation (docker run/exec/inspect)
- sudo or other privileged system changes
- systemctl or service restarts
- destructive or interactive shell commands that modify host state without explicit authorization
