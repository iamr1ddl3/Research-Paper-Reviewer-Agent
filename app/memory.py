import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional
from app.config import DB_PATH
from app.schemas import TaskGraph, Artifact


def connect() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH))


def init_db() -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS task_graph (
            id INTEGER PRIMARY KEY,
            goal TEXT NOT NULL,
            graph_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            artifact_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkpoint_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            event_type TEXT NOT NULL,
            event_json TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_task_graph(graph: TaskGraph) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM task_graph LIMIT 1")
    row = cur.fetchone()
    graph_json = graph.model_dump_json(indent=2)
    now = _now()
    if row:
        cur.execute(
            "UPDATE task_graph SET goal = ?, graph_json = ?, updated_at = ? WHERE id = ?",
            (graph.goal, graph_json, now, row[0]),
        )
    else:
        cur.execute(
            "INSERT INTO task_graph (goal, graph_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (graph.goal, graph_json, now, now),
        )
    conn.commit()
    conn.close()


def load_task_graph() -> Optional[TaskGraph]:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT graph_json FROM task_graph LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return TaskGraph.model_validate_json(row[0])


def save_artifact(artifact: Artifact) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO artifacts (task_id, artifact_json, created_at) VALUES (?, ?, ?)",
        (artifact.task_id, artifact.model_dump_json(indent=2), _now()),
    )
    conn.commit()
    conn.close()


def save_checkpoint(graph: TaskGraph) -> None:
    conn = connect()
    cur = conn.cursor()
    checkpoint = {"goal": graph.goal, "graph": graph.model_dump(), "created_at": _now()}
    cur.execute(
        "INSERT INTO checkpoints (checkpoint_json, created_at) VALUES (?, ?)",
        (json.dumps(checkpoint, indent=2), _now()),
    )
    conn.commit()
    conn.close()


def log_event(event_type: str, payload: dict | None = None, task_id: str | None = None) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (task_id, event_type, event_json, created_at) VALUES (?, ?, ?, ?)",
        (task_id, event_type, json.dumps(payload or {}), _now()),
    )
    conn.commit()
    conn.close()
