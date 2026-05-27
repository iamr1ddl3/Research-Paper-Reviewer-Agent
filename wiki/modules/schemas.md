---
title: Schemas (Pydantic models)
type: module
tags: [schemas, pydantic]
language: python
entry_point: app/schemas.py
updated: 2026-05-27
---

# Schemas

Pydantic v2 models. Five models + one Literal type. All persistence + LLM JSON validation routes through these.

## Models

| Model | Purpose | Page |
|---|---|---|
| `Task` | single task node (id, status, attempts, deps, task_type, paper_id) | [[data-models/task]] |
| `TaskGraph` | `{goal, tasks: list[Task]}` | [[data-models/task-graph]] |
| `Artifact` | worker output reference (changed/failed/remaining/evidence) | [[data-models/artifact]] |
| `EvaluationResult` | judge verdict (passed, score, issues, next_action) | [[data-models/evaluation-result]] |
| `PaperSummary` | per-paper summary (method/dataset/results/limitations/implementation_notes/citations) | [[data-models/paper-summary]] |

## TaskStatus literal

```python
TaskStatus = Literal["pending", "running", "passed", "failed", "needs_human"]
```

(Not `in_progress` / `done` / `fail` — those names were in the previous wiki and were wrong.)

## Public Interface

```python
from app.schemas import Task, TaskGraph, Artifact, EvaluationResult, PaperSummary, TaskStatus
```

## Consumers

- [[modules/planner]] — builds TaskGraph
- [[modules/worker]] — constructs Artifact, validates PaperSummary from LLM JSON
- [[modules/evaluator]] — emits EvaluationResult
- [[modules/memory]] — persists Task/TaskGraph/Artifact as JSON

## Related

- [[modules/planner]] · [[modules/worker]] · [[modules/evaluator]] · [[modules/memory]]
