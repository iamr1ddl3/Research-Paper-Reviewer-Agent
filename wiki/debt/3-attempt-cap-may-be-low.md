---
title: Max 3 attempts per task — may be tight for hard summaries
type: debt
severity: low
status: resolved
filed: 2026-05-20
resolved: 2026-05-27
sources: [README.md, app/main.py, app/config.py]
updated: 2026-05-27
---

# 3-attempt cap may escalate too easily — RESOLVED

## Description (historical)

`MAX_ATTEMPTS_PER_TASK = 3` was hardcoded. Math-heavy / multi-column / OCR-quality papers often needed > 3 retries for the citation verifier to pass — the run would escalate to `needs_human` even when a 4th retry would succeed.

## Resolution

Per-task-type cap with env override (config.py:27 + main.py:119), 2026-05-27.

### Config (config.py)

```python
MAX_ATTEMPTS_PER_TASK = int(os.getenv("MAX_ATTEMPTS_PER_TASK", "3"))

_DEFAULT_ATTEMPT_OVERRIDES = {
    "summarize_paper": 5,   # extraction artifacts need slack
    "export_pdf": 2,        # mechanical; failure is environmental
}

MAX_ATTEMPTS_BY_TYPE = {
    **_DEFAULT_ATTEMPT_OVERRIDES,
    **_parse_attempt_overrides(os.getenv("MAX_ATTEMPTS_BY_TYPE", "")),
}

def max_attempts_for(task_type: str) -> int:
    return MAX_ATTEMPTS_BY_TYPE.get(task_type, MAX_ATTEMPTS_PER_TASK)
```

### Loop (main.py)

```python
cap = max_attempts_for(task.task_type)
if task.attempts >= cap or result.next_action == "human_review":
    task.status = "needs_human"
    print(f"... (cap={cap})")
else:
    task.status = "failed"
    print(f"FAIL (will retry, {task.attempts}/{cap})")
```

### Env override format

```
MAX_ATTEMPTS_PER_TASK=3
MAX_ATTEMPTS_BY_TYPE=summarize_paper=5,export_pdf=2,write_report=4
```

### Defaults shipped

| task_type | cap |
|---|---|
| `summarize_paper` | 5 |
| `export_pdf` | 2 |
| (everything else) | 3 (`MAX_ATTEMPTS_PER_TASK`) |

## Related

- [[modules/main-harness]]
- [[modules/config]]
- [[modules/evaluator]]
