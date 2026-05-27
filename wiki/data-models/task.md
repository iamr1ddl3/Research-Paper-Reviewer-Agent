---
title: Task (single node in TaskGraph)
type: data-model
tags: [entity, pydantic]
storage: sqlite (as JSON within task_graph row)
sources: [app/schemas.py]
updated: 2026-05-27
---

# Task

A single unit of work in the task graph. Pydantic `BaseModel`.

## Schema

| Field | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | str | no | — | e.g. `T1`, `T3.2` |
| `title` | str | no | — | human-readable label |
| `description` | str | no | — | detailed task description |
| `status` | TaskStatus | no | `"pending"` | one of `pending` / `running` / `passed` / `failed` / `needs_human` |
| `dependencies` | list[str] | no | `[]` | task ids that must be `passed` before this can run |
| `acceptance_criteria` | list[str] | no | `[]` | text criteria displayed to evaluator |
| `attempts` | int | no | `0` | incremented before each worker run |
| `last_error` | Optional[str] | yes | None | last evaluator issue summary |
| `task_type` | str | no | `"generic"` | dispatch key — see [[modules/worker]] table |
| `paper_id` | Optional[str] | yes | None | set on `T3.N` fan-out subtasks |

## TaskStatus literal

```python
TaskStatus = Literal["pending", "running", "passed", "failed", "needs_human"]
```

## Lifecycle

1. Created by [[modules/planner]] (`create_task_graph` or `inject_summarize_subtasks`).
2. Selected by `pick_next_task` in [[modules/main-harness]] (status ∈ {pending, failed} + deps passed).
3. Status `running`, `attempts += 1` (main.py:99).
4. Worker runs → evaluator judges.
5. Status → `passed` | `failed` | `needs_human`.
6. Persisted as part of `TaskGraph.tasks` JSON by [[modules/memory]] `save_task_graph`.

## Invariants

- `attempts` capped at `MAX_ATTEMPTS_PER_TASK` (=3) before `needs_human` escalation.
- `paper_id` only set on `summarize_paper` task_type.
- T3 placeholder (`task_type="summarize_fanout"`) is dropped and replaced by `T3.N` subtasks at runtime.

## Consumers

- [[modules/planner]] · [[modules/main-harness]] · [[modules/worker]] · [[modules/evaluator]] · [[modules/memory]]

## Related

- [[data-models/task-graph]]
- [[data-models/artifact]]
- [[data-models/evaluation-result]]
