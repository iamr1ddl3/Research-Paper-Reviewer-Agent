---
title: Config (env + paths + constants)
type: module
tags: [config]
language: python
entry_point: app/config.py
updated: 2026-05-27
---

# Config

Env-var loading via `python-dotenv`, path constants, hard limits. Auto-creates workspace subdirs on import.

## Env vars

| Var | Default | Used by |
|---|---|---|
| `OPENROUTER_API_KEY` | required | [[modules/llm-wrapper]] |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | [[modules/llm-wrapper]] |
| `OPENROUTER_REFERER` | `https://github.com/local/research-paper-reviewer-agent` | OpenRouter ranking header |
| `OPENROUTER_TITLE` | `Research Paper Reviewer Agent` | OpenRouter ranking header |
| `WORKER_MODEL` | `anthropic/claude-sonnet-4.5` | [[modules/worker]] |
| `EVALUATOR_MODEL` | `anthropic/claude-opus-4.1` | [[modules/evaluator]] |
| `PLANNER_MODEL` | `anthropic/claude-sonnet-4.5` | **declared but unused** — planner.py is deterministic |
| `PAPER_COUNT` | `5` | [[modules/worker]], [[modules/evaluator]] (target count) |
| `ARXIV_QUERY` | `""` (empty) | [[modules/arxiv-client]] |
| `AUTO_APPROVE` | unset | [[modules/approval]] — `=1` bypasses T6 prompt |
| `MAX_ATTEMPTS_PER_TASK` | `3` | default attempt cap; per-type overrides below |
| `MAX_ATTEMPTS_BY_TYPE` | unset | comma-list `task_type=N,...` (e.g. `summarize_paper=5,export_pdf=2`) |

## Paths (relative to repo root)

```
WORKSPACE_DIR     = workspace/project/
PAPERS_DIR        = workspace/papers/
ARTIFACT_DIR      = workspace/artifacts/
CHECKPOINT_DIR    = workspace/checkpoints/
LOG_DIR           = workspace/logs/
DB_PATH           = workspace/agent_state.db
```

Auto-created at import time. SQLite DB sits at the workspace root, not under checkpoints/.

## Hard constants

```python
DEFAULT_MAX_TOKENS = 8000
REPORT_MAX_TOKENS = 16000      # used for T6 write_report
```

## Per-task-type attempt caps

```python
MAX_ATTEMPTS_PER_TASK = int(os.getenv("MAX_ATTEMPTS_PER_TASK", "3"))

_DEFAULT_ATTEMPT_OVERRIDES = {
    "summarize_paper": 5,   # extraction artifacts often need slack
    "export_pdf": 2,        # mechanical, environmental failures only
}

MAX_ATTEMPTS_BY_TYPE = {
    **_DEFAULT_ATTEMPT_OVERRIDES,
    **_parse_attempt_overrides(os.getenv("MAX_ATTEMPTS_BY_TYPE", "")),
}

def max_attempts_for(task_type: str) -> int:
    return MAX_ATTEMPTS_BY_TYPE.get(task_type, MAX_ATTEMPTS_PER_TASK)
```

[[modules/main-harness]] reads `max_attempts_for(task.task_type)` per loop iteration. Resolution order: env override → built-in override → `MAX_ATTEMPTS_PER_TASK`. See [[debt/3-attempt-cap-may-be-low]] (resolved).

## Related

- All other modules import from here
