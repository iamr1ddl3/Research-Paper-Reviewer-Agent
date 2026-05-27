---
title: LLM Wrapper (OpenAI SDK against OpenRouter)
type: module
tags: [llm, wrapper, openrouter]
language: python
entry_point: app/llm.py
updated: 2026-05-27
---

# LLM Wrapper

Thin wrapper over the **OpenAI Python SDK** pointed at OpenRouter's OpenAI-compatible endpoint. Singleton lazy client. Two call modes: plain text + JSON-coerced.

## Confirmed: OpenAI SDK, not Anthropic

`llm.py:5` — `from openai import OpenAI`. README's "Anthropic SDK wrapper" comment is stale ([[debt/llm-wrapper-comment-stale]]).

OpenRouter exposes an OpenAI-compatible API. Models are routed by string id (e.g. `anthropic/claude-sonnet-4.5`) — provider-agnostic at the wire level.

## Responsibility

Owns: client construction, header injection, `chat.completions` call, JSON-coercion of model output (strip code fences, recover from leading/trailing prose).

Does NOT own: prompt assembly, model selection (callers pass model id directly).

## Public Interface

```python
from app.llm import call_llm, call_llm_json
text = call_llm(system_prompt, user_prompt, model, max_tokens=DEFAULT_MAX_TOKENS) -> str
data = call_llm_json(system_prompt, user_prompt, model, max_tokens=DEFAULT_MAX_TOKENS) -> dict
```

## Error handling

- `finish_reason == "length"` → `RuntimeError` (truncation guard, llm.py:53).
- Empty content → `RuntimeError` with `finish_reason` reported.
- `call_llm_json`: strips ```` ```json ```` fences first; on parse fail, falls back to `{...}` substring extraction.

## Env-tunable model split (via [[modules/config]])

| Env | Default |
|---|---|
| `PLANNER_MODEL` | unused — planner.py is deterministic, no LLM call |
| `WORKER_MODEL` | `anthropic/claude-sonnet-4.5` |
| `EVALUATOR_MODEL` | `anthropic/claude-opus-4.1` |
| `OPENROUTER_API_KEY` | required |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENROUTER_REFERER` / `OPENROUTER_TITLE` | optional OpenRouter ranking headers |

PLANNER_MODEL appears in config.py:14 but is **never read by planner.py**. Dead config. Possible future use.

## Related

- [[modules/worker]] — primary caller
- [[modules/evaluator]] — uses for LLM judge path
- [[modules/config]]
- [[debt/llm-wrapper-comment-stale]]
