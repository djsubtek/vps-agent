# Board Architecture

## Purpose

`/board` is a new orchestration dashboard surface that is intentionally separate from OpenClaw-owned UI routes.

Route ownership:
- `/` -> OpenClaw gateway UI
- `/control` -> OpenClaw-owned route
- `/board` -> new orchestration dashboard SPA
- `/board/api/*` -> new board backend/API

## Integration Point

The safest mount point is the existing internal FastAPI backend, routed through Caddy only for `/board*`.

Why:
- avoids touching OpenClaw route ownership
- avoids adding a public port
- keeps the board backend internal-only and path-routed
- gives future agent work a stable API/UI boundary

## Files

Backend:
- `/opt/vps-agent/backend/app/board/router.py`
- `/opt/vps-agent/backend/app/board/service.py`
- `/opt/vps-agent/backend/app/board/migrations/001_board.sql`

Frontend assets:
- `/opt/vps-agent/backend/app/board/templates/index.html`
- `/opt/vps-agent/backend/app/board/static/board.css`
- `/opt/vps-agent/backend/app/board/static/board.js`

Runtime wiring:
- `/opt/vps-agent/backend/Dockerfile`
- `/opt/vps-agent/backend/requirements.txt`
- `/opt/vps-agent/docker-compose.yml`
- `/opt/vps-agent/caddy/Caddyfile`

## API Contract

Read:
- `GET /board/api/tasks`
- `GET /board/api/agents`
- `GET /board/api/summaries`
- `GET /board/api/approvals`
- `GET /board/api/recurring`
- `GET /board/api/system`

Write:
- `POST /board/api/tasks`
- `PATCH /board/api/tasks/{task_id}`

## Persistence

SQLite database:
- host path: `/opt/vps-agent/data/board/board.db`
- container path: `/app/data/board.db`

Tables:
- `tasks`
- `task_runs`
- `agent_status`
- `summaries`
- `approvals`
- `recurring_tasks`
- `system_events`

Schema source:
- `/opt/vps-agent/backend/app/board/migrations/001_board.sql`

## Real vs Mocked

Real in MVP:
- board DB persistence
- board CRUD for tasks created through `/board`
- orchestrator/backend health in `/board/api/system`

Mocked in MVP:
- seeded task intelligence content
- agent activity details beyond health-ready signals
- approvals workflow payloads
- recurring task execution data
- research summaries and system event stream content

The mock data is stored with `source = 'mock'` or returned with `integration_mode = 'mock'/'mixed'` so future runtime adapters can replace it incrementally.

## Future Extension Path

Recommended next step for OpenClaw-driven development:
1. replace mocked approvals with runtime-backed approval records
2. add a runtime adapter for active sessions/tasks from OpenClaw
3. append board events from real orchestration actions
4. introduce optimistic drag-and-drop lane updates once task mutation contracts stabilize
