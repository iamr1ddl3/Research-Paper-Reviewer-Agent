---
title: LLM Wrapper
type: module
tags: [llm, wrapper]
language: python
entry_point: app/llm.py
updated: 2026-05-20
---

# LLM Wrapper

LLM access abstraction. README says "Anthropic SDK wrapper" but is consumed for OpenRouter (OpenAI-compatible endpoint) — check actual code for which SDK.

## Responsibility

Owns: model selection (planner / worker / evaluator), prompt assembly, error handling around the LLM call.

## Env-tunable model split

| Env | Default | Used by |
|---|---|---|
| `PLANNER_MODEL` | Sonnet (via OpenRouter) | [[modules/planner]] |
| `WORKER_MODEL` | Sonnet (via OpenRouter) | [[modules/worker]] |
| `EVALUATOR_MODEL` | Opus (via OpenRouter) | [[modules/evaluator]] |
| `OPENROUTER_API_KEY` | required | All three |

## Provider abstraction

OpenRouter exposes OpenAI-compatible API → can swap providers via env without code changes. Same pattern as [[../../Friday/wiki/modules/agent-core]] (which uses NVIDIA NIM the same way).

## Possible drift

README §"Files" comment says `llm.py — Anthropic SDK wrapper` but config example uses `OPENROUTER_API_KEY` not `ANTHROPIC_API_KEY`. File may have started Anthropic-direct and pivoted to OpenRouter — comment stale. Worth verifying. ([[debt/llm-wrapper-comment-stale]] candidate.)

## Related

- [[modules/planner]], [[modules/worker]], [[modules/evaluator]] — consumers
- [[modules/config]]
