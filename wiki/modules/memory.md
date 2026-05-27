---
title: Memory (SQLite state store)
type: module
tags: [memory, sqlite, persistence]
language: python
entry_point: app/memory.py
updated: 2026-05-27
---

# Memory

SQLite-backed persistence. Stores task graph, artifacts, checkpoints, events. Source-of-truth for resume across runs.

## Responsibility

Owns: row-level persistence. Does NOT own: pick_next_task logic (lives in [[modules/main-harness]] `main.py:24`).

## Schema (4 tables)

| Table | Columns | Cardinality |
|---|---|---|
| `task_graph` | id PK, goal, graph_json, created_at, updated_at | **Singleton** — upsert always overwrites row 1 |
| `artifacts` | id AI, task_id, artifact_json, created_at | one row per worker run |
| `checkpoints` | id AI, checkpoint_json, created_at | one row per `save_checkpoint` call |
| `events` | id AI, task_id, event_type, event_json, created_at | append-only event log |

DB file at `workspace/agent_state.db` (config.py:25 `DB_PATH`).

## Public Interface

```python
from app.memory import (
    init_db,            # create tables if absent
    save_task_graph,    # upserts singleton row
    load_task_graph,    # → Optional[TaskGraph]
    save_artifact,      # appends Artifact row
    save_checkpoint,    # appends snapshot row
    log_event,          # append (event_type, payload, task_id?)
)
```

No `pick_next_task` / `mark_done` / `retry` / `escalate` / `checkpoint` exports. Those operations are done by [[modules/main-harness]] mutating the in-memory `TaskGraph` and calling `save_task_graph` + `save_checkpoint`.

## Resume mechanics

`python -m app.main` (no `--goal`) →
1. `init_db()` ensures schema.
2. `load_task_graph()` returns the singleton TaskGraph (or None).
3. Harness loop picks next runnable task (`status in {pending, failed}` with deps satisfied).

## Event types observed

Strings passed to `log_event`: `task_start`, `task_evaluated`, `approval_denied`, `graph_created`, `fanout_injected`.

## Related

- [[modules/main-harness]] — primary consumer
- [[modules/schemas]] — Pydantic models persisted as JSON
- [[data-models/task]] · [[data-models/task-graph]] · [[data-models/artifact]] · [[data-models/evaluation-result]]
