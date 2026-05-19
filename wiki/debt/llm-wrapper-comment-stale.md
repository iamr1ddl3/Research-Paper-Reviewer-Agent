---
title: llm.py comment says "Anthropic SDK", config uses OpenRouter
type: debt
severity: low
status: open
filed: 2026-05-20
sources: [README.md, app/llm.py]
updated: 2026-05-20
---

# README comment for `llm.py` is stale

README §"Files" lists:

```
  llm.py               # Anthropic SDK wrapper
```

But setup section + env vars use `OPENROUTER_API_KEY` (not `ANTHROPIC_API_KEY`). All three model env vars (`PLANNER_MODEL`, `WORKER_MODEL`, `EVALUATOR_MODEL`) document OpenRouter routing.

## Impact

- New contributors expect `import anthropic`. Actual code may use `openai` (OpenAI-compatible OpenRouter endpoint).
- Minor — fixable with a one-line README edit.

## Fix

Update README comment to: `llm.py  # OpenRouter (OpenAI-compatible) wrapper`.

Verify against actual `app/llm.py` imports — if it really uses `anthropic` SDK pointed at OpenRouter, document that nuance.

## Related

- [[modules/llm-wrapper]]
