---
title: Planner (goal → task graph)
type: module
tags: [planner, llm]
language: python
entry_point: app/planner.py
updated: 2026-05-20
---

# Planner

Converts a user goal (e.g., "review papers on LLM agent architectures, count=3") into the T1..T7 task graph.

## Responsibility

Owns: task graph construction. Decides which T3.N (per-paper summarize) tasks need to exist based on `--count`.

## Public Interface

```python
from app.planner import plan
graph = plan(goal: str, count: int) -> TaskGraph
```

## LLM

- **Planner model:** Sonnet via OpenRouter (override via `PLANNER_MODEL` env).
- Called once per goal. Constructed graph is then persisted in SQLite by [[modules/memory]].

## Output

Returns Pydantic TaskGraph ([[modules/schemas]]) containing T1, T2, T3.1, T3.2, ..., T3.N, T4, T5, T6, T7 — each with type, dependencies, expected artifact path.

## Related

- [[modules/schemas]] — TaskGraph definition
- [[modules/main-harness]] — caller
- [[decisions/adr-1-planner-worker-evaluator-pattern]]
