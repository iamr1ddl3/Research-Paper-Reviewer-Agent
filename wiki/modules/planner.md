---
title: Planner (deterministic task graph builder)
type: module
tags: [planner, static]
language: python
entry_point: app/planner.py
updated: 2026-05-27
---

# Planner

Builds the T1..T7 task graph for a goal. **Fully deterministic — no LLM call.** Static Pydantic graph constructor.

## Responsibility

Owns: task graph shape. Emits a fixed T1..T7 skeleton plus runtime fan-out logic for T3.N subtasks (one per paper).

Does NOT own: paper count (read from `PAPER_COUNT` env via [[modules/config]]). Does NOT own: graph persistence (handled by [[modules/memory]]).

## Public Interface

```python
from app.planner import create_task_graph, inject_summarize_subtasks
graph = create_task_graph(goal: str) -> TaskGraph          # static T1..T6
graph = inject_summarize_subtasks(graph, paper_ids: list[str])  # called by harness after T2
```

`create_task_graph` returns a TaskGraph containing:

| ID | task_type | dependencies | acceptance_criteria highlight |
|---|---|---|---|
| T1 | `collect_papers` | — | paper_index.json + ≥ PAPER_COUNT PDFs |
| T2 | `extract_text` | T1 | raw.txt + meta.json per paper |
| T3 | `summarize_fanout` (placeholder) | T2 | Replaced at runtime |
| T4 | `compare_methods` | T3 | comparison.md w/ Method Comparison section |
| T5 | `identify_patterns` | T4 | patterns.md, each pattern ≥ 2 paper ids |
| T6 | `write_report` | T5 | FINAL_REPORT.md w/ 5 H2 sections |
| T7 | `export_pdf` | T6 | FINAL_REPORT.pdf exists + size ≥ 1 KB |

T7 wired 2026-05-27 — see [[decisions/adr-8-t7-wiring]].

## Fan-out mechanics

`inject_summarize_subtasks(graph, paper_ids)`:
1. Drops T3 placeholder.
2. Inserts `T3.1..T3.N` (`task_type=summarize_paper`, deps=[T2], `paper_id` set).
3. Rewrites T4 dependencies to include all `T3.N` ids (and drops T3 from deps).

Called by harness in [[modules/main-harness]] `_maybe_fanout` (main.py:61) once T2 has passed and `workspace/project/paper_index.json` exists.

## Related

- [[modules/schemas]] — Task, TaskGraph definitions
- [[modules/main-harness]] — caller of both `create_task_graph` + `inject_summarize_subtasks`
- [[decisions/adr-1-planner-worker-evaluator-pattern]]
- [[decisions/adr-8-t7-wiring]]
