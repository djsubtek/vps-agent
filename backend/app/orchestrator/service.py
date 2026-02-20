from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "orchestrator.db"
MIGRATION_PATH = BASE_DIR / "migrations" / "001_orchestrator.sql"
AUTONOMY_PATH = BASE_DIR / "autonomy.yml"


def _db_path() -> Path:
    return Path(os.getenv("ORCHESTRATOR_DB_PATH", str(DEFAULT_DB_PATH)))


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    if not MIGRATION_PATH.exists():
        raise FileNotFoundError(f"Missing migration: {MIGRATION_PATH}")
    with MIGRATION_PATH.open("r", encoding="utf-8") as handle:
        conn.executescript(handle.read())
    conn.commit()


def create_idea(conn: sqlite3.Connection, title: str, detail: Optional[str]) -> int:
    cursor = conn.execute(
        "INSERT INTO ideas (title, detail) VALUES (?, ?)",
        (title, detail),
    )
    conn.commit()
    return int(cursor.lastrowid)


def create_spec(conn: sqlite3.Connection, idea_id: int, content: str) -> int:
    cursor = conn.execute(
        "INSERT INTO specs (idea_id, content) VALUES (?, ?)",
        (idea_id, content),
    )
    conn.commit()
    return int(cursor.lastrowid)


def create_tickets(conn: sqlite3.Connection, spec_id: int, tickets: Iterable[tuple[str, str]]) -> list[int]:
    ids: list[int] = []
    for title, detail in tickets:
        cursor = conn.execute(
            "INSERT INTO tickets (spec_id, title, detail) VALUES (?, ?, ?)",
            (spec_id, title, detail),
        )
        ids.append(int(cursor.lastrowid))
    conn.commit()
    return ids


def select_one_ticket(conn: sqlite3.Connection, spec_id: int) -> Optional[int]:
    cursor = conn.execute(
        "SELECT id FROM tickets WHERE spec_id = ? ORDER BY id ASC LIMIT 1",
        (spec_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return int(row[0])


def record_iteration(
    conn: sqlite3.Connection,
    idea_id: int,
    spec_id: int,
    ticket_id: int,
    change_plan: str,
) -> int:
    cursor = conn.execute(
        "INSERT INTO iterations (idea_id, spec_id, ticket_id, change_plan) VALUES (?, ?, ?, ?)",
        (idea_id, spec_id, ticket_id, change_plan),
    )
    conn.commit()
    return int(cursor.lastrowid)


def record_deployment_stub(conn: sqlite3.Connection, iteration_id: int, env: str) -> int:
    cursor = conn.execute(
        "INSERT INTO deployments (iteration_id, env) VALUES (?, ?)",
        (iteration_id, env),
    )
    conn.commit()
    return int(cursor.lastrowid)


def healthcheck() -> dict:
    readiness = AUTONOMY_PATH.exists() and MIGRATION_PATH.exists()
    try:
        conn = get_db()
        ensure_schema(conn)
        conn.execute("SELECT 1")
        conn.close()
        return {"db": True, "readiness": readiness}
    except Exception:
        return {"db": False, "readiness": readiness}
