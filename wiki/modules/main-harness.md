---
title: Main Harness (CLI + harness loop)
type: module
tags: [harness, orchestration, cli]
language: python
entry_point: app/main.py
updated: 2026-05-27
---

# Main Harness

CLI entry + the pick → approve → run → evaluate → checkpoint loop. Includes the **T3 fan-out trigger** and **pick_next_task** (despite the name implying memory-only orchestration).

## Responsibility

Owns: the loop, task selection, fan-out injection, status transitions, escalation, artifact-file writeout.

## Public Interface

```bash
python -m app.main --goal "Review papers on LLM agent architectures" --count 3
python -m app.main                  # resume existing graph
```

`--count` overrides `PAPER_COUNT` env at runtime (mutates `app.config.PAPER_COUNT` + `app.worker.PAPER_COUNT` via runtime monkeypatch, main.py:135).

## Loop logic (main.py)

```
init_db()
graph = load_task_graph() or (planner.create_task_graph(goal) if --goal else SystemExit)
loop:
  graph = _maybe_fanout(graph)             # inject T3.1..T3.N if T2 passed + paper_index.json present
  task  = pick_next_task(graph)            # first pending|failed task w/ deps satisfied
  if task is None: break
  if needs_approval(task.id):              # currently only T6
    if not request_approval(): status="needs_human"; stop
  task.status = "running"; task.attempts += 1
  artifact = run_worker(task)
  save_artifact(artifact)
  result = evaluate_task(task, artifact)
  if result.passed:
    task.status = "passed"
  elif task.attempts >= max_attempts_for(task.task_type) or result.next_action == "human_review":
    task.status = "needs_human"; stop
  else:
    task.status = "failed"                  # will be retried next pick
  save_task_graph(graph); save_checkpoint(graph)
```

## pick_next_task

Implemented in main.py:24 (NOT in [[modules/memory]]):

```python
passed = {t.id for t in graph.tasks if t.status == "passed"}
for t in graph.tasks:
    if t.status in {"pending", "failed"} and all(dep in passed for dep in t.dependencies):
        return t
return None
```

## Fan-out trigger

`_maybe_fanout(graph)` (main.py:61):
- Checks T3 placeholder still present + T2 passed + `paper_index.json` exists.
- Reads paper ids from `paper_index.json`.
- Calls `planner.inject_summarize_subtasks(graph, paper_ids)`.
- Persists + logs `fanout_injected` event.

## Artifact file writeout

`write_artifact_file` (main.py:33) writes `workspace/artifacts/<task_id>.md` for every task. Includes "What changed / failed / remaining / Evidence" + evaluator issues block when failed.

## Escalation conditions

Stops the loop (returns) when:
- Approval denied.
- A task reaches `needs_human` (via per-task-type cap from [[modules/config]] `max_attempts_for` OR `next_action="human_review"` from evaluator).
- `pick_next_task` returns None (all done OR all remaining are blocked).

Per-task-type caps default: `summarize_paper=5`, `export_pdf=2`, all-other=`MAX_ATTEMPTS_PER_TASK` (=3 unless env-overridden).

## Dependencies

- [[modules/planner]] · [[modules/worker]] · [[modules/evaluator]] · [[modules/approval]] · [[modules/memory]] · [[modules/sandbox]] (`read_workspace_file` for paper_index.json) · [[modules/config]]

## Related

- [[flows/full-review-run]]
