---
title: Memory (SQLite state store)
type: module
tags: [memory, sqlite, persistence]
language: python
entry_point: app/memory.py
updated: 2026-05-20
---

# Memory

SQLite-backed state. Tracks task graph, attempts, status, checkpoints. Source-of-truth for resume.

## Responsibility

Owns: persistent state across runs. Without it, no resume.

## What's persisted

- Task graph (nodes + edges, dependencies)
- Per-task: status (`pending` / `in_progress` / `done` / `fail` / `needs_human`), attempt count, artifact path, last error
- Run metadata (goal, count, timestamp)
- Checkpoints

## Public Interface

```python
from app.memory import (
    init_or_load, pick_next_task, mark_done,
    retry, escalate, checkpoint
)
```

## Resume mechanics

`python -m app.main` (no `--goal`) → `init_or_load` returns existing graph from SQLite. `pick_next_task()` returns any task with status in {`pending`, `fail` with attempts<3, retry-queued}.

## Storage

Location set by [[modules/config]]. Likely under `workspace/checkpoints/` per directory structure.

## Related

- [[modules/main-harness]] — primary consumer
- [[modules/schemas]] — Pydantic models for tasks
