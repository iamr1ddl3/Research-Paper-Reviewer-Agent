---
title: Worker (task-type dispatcher)
type: module
tags: [worker, llm, dispatch]
language: python
entry_point: app/worker.py
updated: 2026-05-20
---

# Worker

Task-type dispatcher. Runs ONE task at a time. Each task type has a different execution path; all share sandboxed file ops + LLM access.

## Responsibility

Owns: per-task execution. For each task type:

| Task type | What worker does | Tools used |
|---|---|---|
| T1 collect | Fetches papers from arXiv if `workspace/papers/` underfull | [[modules/arxiv-client]] |
| T2 extract | PDF → text + metadata | [[modules/pdf-tools]] |
| T3.N summarize | LLM call: paper text → `summary.json` (Pydantic-validated) | [[modules/llm-wrapper]] + [[modules/schemas]] |
| T4 compare | LLM call: N summaries → `comparison.md` | LLM |
| T5 patterns | LLM call: comparison → `patterns.md` | LLM |
| T6 final report | LLM call: all artifacts → `FINAL_REPORT.md` (HUMAN APPROVAL GATE) | LLM + [[modules/approval]] |
| T7 export | Render `FINAL_REPORT.md` → `FINAL_REPORT.pdf` | [[modules/pdf-tools]] |

## Public Interface

```python
from app.worker import run
artifact = run(task: Task) -> Artifact
```

## Constraints

- File ops MUST go through [[modules/sandbox]] (writes restricted to `workspace/project/`).
- LLM access via [[modules/llm-wrapper]] (Sonnet by default).

## LLM

- **Worker model:** Sonnet via OpenRouter (override via `WORKER_MODEL` env).

## Related

- [[modules/main-harness]] — caller
- [[modules/evaluator]] — judges worker output
- [[modules/sandbox]] — file op safety
