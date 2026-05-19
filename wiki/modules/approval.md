---
title: Approval (human gate for T6)
type: module
tags: [approval, human-in-loop]
language: python
entry_point: app/approval.py
updated: 2026-05-20
---

# Approval

Interactive human-approval gate. Required for T6 (final report).

## Responsibility

Owns: the explicit human-in-the-loop checkpoint. Without approval, T6 doesn't finalize → T7 doesn't run.

## Trigger

[[modules/main-harness]] calls `approval.prompt(task, artifact)` when:
- T6 produces `FINAL_REPORT.md` and needs sign-off.
- Or when [[modules/evaluator]] returns `needs_human` for any task.

## Public Interface

```python
from app.approval import prompt
approved: bool = prompt(task, artifact)
```

Behavior: prints artifact summary to stdout, waits on stdin for y/n.

## Related

- [[modules/main-harness]]
- [[modules/worker]] (T6)
- [[decisions/adr-5-human-gate-on-final-report]]
