---
title: TaskGraph (goal + ordered task list)
type: data-model
tags: [entity, pydantic]
storage: sqlite (singleton row in task_graph table)
sources: [app/schemas.py]
updated: 2026-05-27
---

# TaskGraph

Top-level container. One per run. Persisted as a singleton row in `task_graph` table.

## Schema

| Field | Type | Description |
|---|---|---|
| `goal` | str | original user goal string |
| `tasks` | list[[[data-models/task]]] | nodes in dependency order |

Edges are implicit: `Task.dependencies` lists ids of prerequisites.

## Lifecycle

1. **Create**: `planner.create_task_graph(goal)` builds T1..T7 (T7 added 2026-05-27, see [[decisions/adr-8-t7-wiring]]).
2. **Persist**: `memory.save_task_graph` upserts row 1 of `task_graph` table.
3. **Mutate**: `_maybe_fanout` in [[modules/main-harness]] calls `planner.inject_summarize_subtasks` after T2 passes, mutating the in-memory graph and re-persisting.
4. **Resume**: `memory.load_task_graph()` returns the singleton TaskGraph.

## Singleton constraint

`save_task_graph` (memory.py:65) does `SELECT id FROM task_graph LIMIT 1` → upserts row 1. Only one TaskGraph per DB. To start a new run, drop the row (or delete `agent_state.db`).

## Consumers

- [[modules/main-harness]] — primary driver
- [[modules/memory]] — persistence
- [[modules/planner]] — constructor + mutator

## Related

- [[data-models/task]]
