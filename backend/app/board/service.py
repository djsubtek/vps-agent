from __future__ import annotations

import sqlite3
from pathlib import Path
import os
from datetime import datetime, timezone
from typing import Any

from backend.app.orchestrator import service as orchestrator_service

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "board.db"
MIGRATION_PATH = BASE_DIR / "migrations" / "001_board.sql"

KANBAN_COLUMNS = ["backlog", "todo", "running", "review", "done"]
BOARD_VERSION = "mvp"


def _db_path() -> Path:
    return Path(os.getenv("BOARD_DB_PATH", str(DEFAULT_DB_PATH)))


def get_db() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    with MIGRATION_PATH.open("r", encoding="utf-8") as handle:
        conn.executescript(handle.read())
    conn.commit()


def _table_empty(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return int(row["count"]) == 0


def seed_demo_data(conn: sqlite3.Connection) -> None:
    if not _table_empty(conn, "tasks"):
        return

    tasks = [
        (
            "Research routing gap",
            "Map the current ingress path and capture where /board should attach.",
            "Collect current reverse-proxy state, OpenClaw gateway paths, and board-safe mount points.",
            "Scout",
            "backlog",
            "medium",
            "Waiting for initial reconnaissance.",
        ),
        (
            "Draft board MVP shell",
            "Create the new /board desktop-first shell with kanban, sidebar, and intelligence panel.",
            "Use a modular SPA shell that OpenClaw can extend later without changing the route contract.",
            "Builder",
            "todo",
            "high",
            "UI frame ready for implementation.",
        ),
        (
            "Sync live orchestrator health",
            "Surface real readiness and DB health from the existing orchestrator backend.",
            "Expose only stable health primitives now; defer deeper runtime control until adapters are ready.",
            "Observer",
            "running",
            "high",
            "Polling orchestrator health gate.",
        ),
        (
            "Approval lane design",
            "Define MVP approval cards and action affordances.",
            "Keep approval data mocked for now, but preserve the API shape for later runtime wiring.",
            "Analyst",
            "review",
            "medium",
            "Awaiting owner review on approval data contract.",
        ),
        (
            "System event ledger",
            "Persist noteworthy board/system events for operator context.",
            "Seed with mock system events now, then replace with runtime-fed events later.",
            "Archivist",
            "done",
            "low",
            "Initial event schema approved.",
        ),
    ]

    for task in tasks:
        conn.execute(
            """
            INSERT INTO tasks
              (title, summary, detail, assigned_agent, status, priority, latest_activity, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'mock')
            """,
            task,
        )

    runs = [
        (3, "running", "2026-03-13T10:40:00Z", None, "Heartbeat OK. Waiting for next poll.", "real"),
        (4, "needs_review", "2026-03-13T09:20:00Z", "2026-03-13T09:46:00Z", "Contract draft prepared for review.", "mock"),
        (5, "completed", "2026-03-13T08:00:00Z", "2026-03-13T08:18:00Z", "Schema landed cleanly.", "mock"),
    ]
    for run in runs:
        conn.execute(
            """
            INSERT INTO task_runs
              (task_id, run_status, started_at, ended_at, latest_activity, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            run,
        )

    agents = [
        ("main", "online", "Sync live orchestrator health", "Watching staging readiness and board DB health.", "real"),
        ("researcher", "idle", "Collect reverse-proxy evidence", "Ready for the next routing spike.", "mock"),
        ("approver", "waiting", "Approval lane design", "Holding for a human decision point.", "mock"),
    ]
    for agent in agents:
        conn.execute(
            """
            INSERT INTO agent_status
              (agent_name, state, current_task, latest_activity, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            agent,
        )

    summaries = [
        (
            "ai_summary",
            "Board status",
            "OpenClaw remains authoritative for / and /control. The new board is isolated under /board with mocked operator-facing orchestration data and real backend health.",
            "mock",
        ),
        (
            "research",
            "Latest research output",
            "Routing audit confirms /board is the lowest-collision mount point because OpenClaw already owns /control and the gateway root.",
            "mock",
        ),
    ]
    for summary in summaries:
        conn.execute(
            """
            INSERT INTO summaries
              (summary_type, title, body, source)
            VALUES (?, ?, ?, ?)
            """,
            summary,
        )

    approvals = [
        ("Escalate runtime integration", "Promote board task state from mock adapters to live OpenClaw sessions.", "pending", "ops", "mock"),
        ("Approve recurring sync", "Enable recurring health snapshots every 15 minutes.", "pending", "scheduler", "mock"),
    ]
    for approval in approvals:
        conn.execute(
            """
            INSERT INTO approvals
              (title, summary, state, requested_by, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            approval,
        )

    recurring = [
        ("Health snapshot", "*/15 * * * *", "2026-03-13T10:45:00Z", "observer", "scheduled", "mock"),
        ("Approval digest", "0 * * * *", "2026-03-13T11:00:00Z", "approver", "scheduled", "mock"),
    ]
    for row in recurring:
        conn.execute(
            """
            INSERT INTO recurring_tasks
              (title, schedule, next_run_at, owner, state, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    events = [
        ("routing", "info", "Caddy now reserves /board for the orchestration dashboard.", "real"),
        ("adapters", "info", "Runtime-backed metrics limited to orchestrator health for MVP.", "mock"),
        ("tasks", "info", "Demo board dataset seeded for operator workflows.", "mock"),
    ]
    for event in events:
        conn.execute(
            """
            INSERT INTO system_events
              (event_type, level, message, source)
            VALUES (?, ?, ?, ?)
            """,
            event,
        )

    conn.commit()


def _dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def list_tasks(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT
          t.*,
          (
            SELECT json_object(
              'id', tr.id,
              'run_status', tr.run_status,
              'started_at', tr.started_at,
              'ended_at', tr.ended_at,
              'latest_activity', tr.latest_activity,
              'source', tr.source
            )
            FROM task_runs tr
            WHERE tr.task_id = t.id
            ORDER BY tr.id DESC
            LIMIT 1
          ) AS latest_run
        FROM tasks t
        ORDER BY
          CASE t.status
            WHEN 'running' THEN 1
            WHEN 'review' THEN 2
            WHEN 'todo' THEN 3
            WHEN 'backlog' THEN 4
            ELSE 5
          END,
          t.updated_at DESC,
          t.id DESC
        """
    ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["latest_run"] = _coerce_json(item["latest_run"])
        items.append(item)

    return {"items": items, "columns": KANBAN_COLUMNS, "integration_mode": "mixed"}


def create_task(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    cursor = conn.execute(
        """
        INSERT INTO tasks
          (title, summary, detail, assigned_agent, status, priority, latest_activity, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'real')
        """,
        (
            payload["title"],
            payload["summary"],
            payload.get("detail") or payload["summary"],
            payload.get("assigned_agent") or "unassigned",
            payload.get("status") or "backlog",
            payload.get("priority") or "medium",
            payload.get("latest_activity") or "Task created from /board.",
        ),
    )
    conn.commit()
    return get_task(conn, int(cursor.lastrowid))


def update_task(conn: sqlite3.Connection, task_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_task(conn, task_id)
    if not existing:
        return None

    updated = {
        "title": payload.get("title", existing["title"]),
        "summary": payload.get("summary", existing["summary"]),
        "detail": payload.get("detail", existing["detail"]),
        "assigned_agent": payload.get("assigned_agent", existing["assigned_agent"]),
        "status": payload.get("status", existing["status"]),
        "priority": payload.get("priority", existing["priority"]),
        "latest_activity": payload.get("latest_activity", existing["latest_activity"]),
    }

    conn.execute(
        """
        UPDATE tasks
        SET title = ?, summary = ?, detail = ?, assigned_agent = ?, status = ?, priority = ?,
            latest_activity = ?, source = 'real', updated_at = datetime('now')
        WHERE id = ?
        """,
        (
            updated["title"],
            updated["summary"],
            updated["detail"],
            updated["assigned_agent"],
            updated["status"],
            updated["priority"],
            updated["latest_activity"],
            task_id,
        ),
    )
    conn.commit()
    return get_task(conn, task_id)


def get_task(conn: sqlite3.Connection, task_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        return None
    return dict(row)


def list_agents(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM agent_status ORDER BY CASE state WHEN 'online' THEN 1 ELSE 2 END, agent_name ASC"
    ).fetchall()
    return {"items": _dicts(rows), "integration_mode": "mixed"}


def list_summaries(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM summaries ORDER BY updated_at DESC, id DESC").fetchall()
    return {"items": _dicts(rows), "integration_mode": "mock"}


def list_approvals(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM approvals ORDER BY updated_at DESC, id DESC").fetchall()
    return {"items": _dicts(rows), "integration_mode": "mock"}


def list_recurring(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM recurring_tasks ORDER BY next_run_at ASC, id ASC").fetchall()
    return {"items": _dicts(rows), "integration_mode": "mock"}


def list_system(conn: sqlite3.Connection) -> dict[str, Any]:
    events = conn.execute("SELECT * FROM system_events ORDER BY created_at DESC, id DESC LIMIT 8").fetchall()
    task_counts = conn.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM tasks
        GROUP BY status
        """
    ).fetchall()
    board_db_ok = True
    try:
        conn.execute("SELECT 1")
    except Exception:
        board_db_ok = False

    orchestrator = orchestrator_service.healthcheck()
    health = [
        {
            "name": "Board database",
            "status": "healthy" if board_db_ok else "degraded",
            "detail": str(_db_path()),
            "source": "real",
        },
        {
            "name": "Orchestrator backend",
            "status": "healthy" if orchestrator.get("db") else "degraded",
            "detail": "Existing orchestrator SQLite and readiness probe.",
            "source": "real",
        },
        {
            "name": "Runtime adapters",
            "status": "planned",
            "detail": "Task/approval/research adapters still mocked for MVP.",
            "source": "mock",
        },
    ]

    return {
        "health": health,
        "events": _dicts(events),
        "task_counts": _dicts(task_counts),
        "integration_mode": "mixed",
    }


def ensure_ready(conn: sqlite3.Connection) -> None:
    ensure_schema(conn)
    seed_demo_data(conn)


def health_snapshot() -> dict[str, str]:
    db_status = "ok"
    try:
        conn = get_db()
        try:
            ensure_ready(conn)
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except Exception:
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "service": "board",
        "status": status,
        "db": db_status,
        "timestamp": timestamp,
        "version": BOARD_VERSION,
    }


def _coerce_json(value: Any) -> Any:
    if value is None:
        return None
    try:
        import json

        return json.loads(value)
    except Exception:
        return value
