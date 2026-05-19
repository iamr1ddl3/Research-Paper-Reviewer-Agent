---
title: Schemas (Pydantic models)
type: module
tags: [schemas, pydantic]
language: python
entry_point: app/schemas.py
updated: 2026-05-20
---

# Schemas

Pydantic models. Type-safe contracts for tasks, summaries, evaluator verdicts, etc.

## Likely model set

Inferred from README + worker structure:

- `Task` — single task in graph (id, type, deps, status, attempts, artifact_path)
- `TaskGraph` — collection of Task nodes + edges
- `PaperSummary` — per-paper output (method, dataset, results, limitations, implementation_notes, citations[])
- `Citation` — quote + source location (page/section)
- `Verdict` — evaluator output (status, reason)
- `Artifact` — worker output reference (path + metadata)

## Public Interface

```python
from app.schemas import Task, TaskGraph, PaperSummary, Verdict
```

Used everywhere: by [[modules/planner]] (constructs graph), [[modules/worker]] (validates LLM JSON output), [[modules/evaluator]] (parses verdicts), [[modules/memory]] (persists state).

## Related

- [[modules/planner]], [[modules/worker]], [[modules/evaluator]], [[modules/memory]]
