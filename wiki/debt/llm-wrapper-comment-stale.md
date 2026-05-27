---
title: llm.py comment says "Anthropic SDK", config uses OpenRouter
type: debt
severity: low
status: resolved
filed: 2026-05-20
resolved: 2026-05-27
sources: [README.md, app/llm.py]
updated: 2026-05-27
---

# README comment for `llm.py` is stale — RESOLVED

## Description (historical)

README §"Files" said:

```
  llm.py               # Anthropic SDK wrapper
```

Actual import (llm.py:5): `from openai import OpenAI`. README also called the LLM wrapper "Anthropic SDK" in the architecture description, and "PLANNER_MODEL" was listed as if used (planner is deterministic).

## Resolution

README rewritten 2026-05-27. Three lines touched:

- Architecture bullet now reads: "OpenAI SDK pointed at OpenRouter via OpenAI-compatible endpoint" + notes PLANNER_MODEL unused.
- Planner bullet now reads: "Planner (deterministic, no LLM)".
- Files block now reads: `llm.py # OpenAI SDK pointed at OpenRouter` plus accurate per-file descriptions matching source (sandbox containment, deterministic+LLM evaluator, etc).

While there, also updated:
- Output section now lists FINAL_REPORT.pdf (T7 wired via [[decisions/adr-8-t7-wiring]]).
- Task Graph table extended with T7.
- Evaluator rigor section documents 3-tier citation cascade + det+LLM two-track judging.
- Safety section documents `Path.relative_to` containment, AUTO_APPROVE escape hatch, env-tunable attempt caps.

## Related

- [[modules/llm-wrapper]]
- [[modules/config]]
