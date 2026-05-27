---
title: Artifact (worker output report)
type: data-model
tags: [entity, pydantic]
storage: sqlite (artifacts table, append-only) + workspace/artifacts/<task_id>.md
sources: [app/schemas.py]
updated: 2026-05-27
---

# Artifact

What the worker reports after running a task. Four free-form text fields + task_id. Used by the evaluator (LLM judge path includes the artifact JSON in the prompt).

## Schema

| Field | Type | Description |
|---|---|---|
| `task_id` | str | which task produced this |
| `changed` | str | what the worker successfully changed (files written, etc.) |
| `failed` | str | what failed and why (or `""`) |
| `remaining` | str | what's still TODO (or `""`) |
| `evidence` | str | concrete pointers — sizes, counts, file names |

## Lifecycle

1. Worker returns an Artifact at end of `run_worker(task)`.
2. `memory.save_artifact` appends to `artifacts` table (one row per run).
3. `main.write_artifact_file` writes `workspace/artifacts/<task_id>.md` for human inspection.
4. Evaluator reads (for LLM-judged tasks) via `artifact.model_dump_json(indent=2)` embedded in prompt.

## Invariants

- Every worker dispatch handler returns an Artifact (no None / no exception escapes).
- Failure cases populate `failed` + minimal `changed`/`evidence`.

## Consumers

- [[modules/main-harness]] (writes artifact .md file)
- [[modules/memory]] (persists)
- [[modules/evaluator]] (reads for LLM judge)

## Related

- [[data-models/task]]
- [[data-models/evaluation-result]]
