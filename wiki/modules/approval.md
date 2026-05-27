---
title: Approval (human gate for T6 + env override)
type: module
tags: [approval, human-in-loop]
language: python
entry_point: app/approval.py
updated: 2026-05-27
---

# Approval

Interactive human-approval gate. Triggered before T6 (`write_report`) executes. Hardcoded set: `APPROVAL_TASK_IDS = {"T6"}`.

## Trigger

[[modules/main-harness]] calls `needs_approval(task_id)` before running each task. If True, calls `request_approval(task_id, title)`. Denial sets task `status = "needs_human"` and stops the loop.

## Public Interface

```python
from app.approval import needs_approval, request_approval
gated: bool = needs_approval(task_id)
ok: bool = request_approval(task_id, title)
```

## Decision logic (approval.py)

```python
if AUTO_APPROVE=1:        return True   # env override
elif not stdin.isatty():  return False  # non-TTY → deny
else:                     prompt y/no on stdin → return answer in {"yes","y"}
```

## AUTO_APPROVE escape hatch

`AUTO_APPROVE=1` env auto-approves. Lets unattended runs proceed past T6 without a human. **Trades safety for unattended throughput** — use with awareness that no human checks `FINAL_REPORT.md` before T7.

Three operating modes total:
- **Interactive** (default, TTY): human types yes/no.
- **Unattended trusted** (`AUTO_APPROVE=1`): auto-approve, run hands-off.
- **Unattended untrusted** (no TTY, no AUTO_APPROVE): deny + escalate to `needs_human`.

This is considered the complete answer for now. See [[debt/no-async-approval]] (accepted) — file-based async gate is sketched as a future option if the binary trusted/untrusted split becomes insufficient.

## Related

- [[modules/main-harness]] (invokes per task, not just T6 by code-path — but only T6 is gated by the set)
- [[modules/worker]] (T6)
- [[decisions/adr-5-human-gate-on-final-report]]
- [[debt/no-async-approval]]
