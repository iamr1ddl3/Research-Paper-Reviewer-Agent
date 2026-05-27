---
title: EvaluationResult (judge verdict)
type: data-model
tags: [entity, pydantic]
storage: not persisted; consumed inline by main loop
sources: [app/schemas.py, app/evaluator.py]
updated: 2026-05-27
---

# EvaluationResult

Verdict from evaluator. Not persisted directly; its consequences live in mutated Task status + `task.last_error`.

## Schema

| Field | Type | Description |
|---|---|---|
| `task_id` | str | which task was judged |
| `passed` | bool | pass/fail boolean (NOT a 3-value status enum) |
| `score` | int | `100 - 20 * len(issues)`, floored at 0 |
| `issues` | list[str] | human-readable reasons for fail (empty on pass) |
| `next_action` | Literal | one of `continue` / `retry` / `human_review` |

## Default-fail score arithmetic

`_fail` (evaluator.py:39) sets `score = max(0, 100 - 20 * len(issues))`. Five issues → score 0. `_ok` returns score 100.

Score is informational — main-harness branches on `passed` + `next_action`, not score.

## Consequence mapping (main.py:113)

| Result | Task status outcome |
|---|---|
| `passed=True` | task.status = "passed" |
| `passed=False`, `attempts < MAX` AND `next_action != "human_review"` | task.status = "failed" (will retry) |
| `passed=False`, `attempts >= MAX` OR `next_action == "human_review"` | task.status = "needs_human" (loop stops) |

## Consumers

- [[modules/evaluator]] (producer)
- [[modules/main-harness]] (consumer)

## Related

- [[data-models/task]]
- [[data-models/artifact]]
