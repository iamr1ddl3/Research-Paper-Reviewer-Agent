---
title: T7 (export_pdf) is dead code — not in planner output, not in worker dispatch
type: debt
severity: high
status: resolved
filed: 2026-05-27
resolved: 2026-05-27
sources: [app/planner.py, app/worker.py]
updated: 2026-05-27
---

# T7 export_pdf is unreachable — RESOLVED

Surfaced during backtest 2026-05-27. Resolved same day.

## Description (historical)

The PDF export step (T7) was documented but unreachable:

1. **Planner did not emit T7.** `planner.create_task_graph` returned only T1..T6.
2. **Worker dispatch did not register `export_pdf`.** Dispatch had 7 task_types, no `export_pdf` key.
3. `_export_pdf` (worker.py) and `_evaluate_pdf` (evaluator.py) existed but unreachable.

## Resolution

Two-edit fix (2026-05-27):

1. `planner.py:91` — appended T7 Task: `id="T7"`, `task_type="export_pdf"`, `dependencies=["T6"]`, criteria: FINAL_REPORT.pdf exists + size ≥ 1 KB.
2. `worker.py:32` — added `"export_pdf": _export_pdf` to dispatch table.

Evaluator `_evaluate_pdf` was already wired via `task_type` dispatch (evaluator.py:28) and required no change.

See [[decisions/adr-8-t7-wiring]] for the keep-vs-remove rationale.

## Resume caveat

Existing `workspace/agent_state.db` rows hold the pre-fix T1..T6 graph. Fresh `--goal` runs (after DB reset) pick up T7. In-progress runs do not gain T7 retroactively.

## Related

- [[modules/planner]]
- [[modules/worker]]
- [[modules/evaluator]]
- [[modules/pdf-tools]]
- [[flows/full-review-run]]
- [[decisions/adr-8-t7-wiring]]
