---
title: Config (env + paths)
type: module
tags: [config]
language: python
entry_point: app/config.py
updated: 2026-05-20
---

# Config

Env var loading + path setup. Centralizes the constants the rest of the app reads.

## Env vars (from README)

| Var | Required | Used by |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | [[modules/llm-wrapper]] |
| `WORKER_MODEL` | optional (default Sonnet) | [[modules/worker]] |
| `PLANNER_MODEL` | optional (default Sonnet) | [[modules/planner]] |
| `EVALUATOR_MODEL` | optional (default Opus) | [[modules/evaluator]] |
| `ARXIV_QUERY` | optional | [[modules/arxiv-client]] |

## Paths

Likely defined here:
- `workspace_root = ./workspace/`
- `papers_dir = workspace/papers/`
- `project_dir = workspace/project/`
- `artifacts_dir = workspace/artifacts/`
- `checkpoints_dir = workspace/checkpoints/`
- `logs_dir = workspace/logs/`

[[modules/sandbox]] uses `project_dir` as its write-allowed root.

## Related

- All other modules consume this.
