---
title: Main Harness (pick → worker → evaluator → checkpoint loop)
type: module
tags: [harness, orchestration]
language: python
entry_point: app/main.py
updated: 2026-05-20
---

# Main Harness

The orchestration loop. Wraps Planner + Worker + Evaluator + Approval + Memory into a long-running review pipeline that can resume after crashes.

## Responsibility

Owns: the harness loop. Picks next pending/retryable task, runs the worker, asks the evaluator to judge, persists checkpoint, escalates on hard-fail or human-required.

Does NOT own: task semantics. Workers know what each task does.

## Public Interface

```bash
# New run with goal
python -m app.main --goal "Review papers on LLM agent architectures" --count 3

# Resume existing graph
python -m app.main
```

## Loop logic

```
load_or_init_task_graph(goal, count) — Planner constructs T1..T7 if goal given
while True:
  task = memory.pick_next_task()
  if task is None: break  # all done or all escalated
  artifact = worker.run(task)
  verdict = evaluator.judge(task, artifact)
  if verdict.status == "pass":
    memory.mark_done(task)
  elif verdict.status == "fail":
    if task.attempts >= 3:
      memory.escalate(task, "needs_human")
    else:
      memory.retry(task, reason=verdict.reason)
  elif verdict.status == "needs_human":
    approval.prompt(task, artifact)
  memory.checkpoint()
```

## Dependencies

- [[modules/planner]], [[modules/worker]], [[modules/evaluator]], [[modules/approval]]
- [[modules/memory]] (SQLite state)
- [[modules/config]]

## Related

- [[flows/full-review-run]]
