---
title: Evaluator (default-fail + citation verification)
type: module
tags: [evaluator, llm, safety]
language: python
entry_point: app/evaluator.py
updated: 2026-05-20
---

# Evaluator

Default-fail judge. Returns pass / fail / needs_human verdict on each worker artifact. Runs in **fresh context** (no conversation history pollution).

## Responsibility

Owns: correctness gating. Two layers:

1. **Schema validation** — required fields per summary present (`method`, `dataset`, `results`, `limitations`, `implementation_notes`).
2. **Citation verification** — every quoted line in `summary.citations[]` must exist in the source PDF text (fuzzy-normalized). Fabricated quotes → fail.

If either fails, returns `fail` with reason. Worker retries (max 3 attempts before escalation).

## Public Interface

```python
from app.evaluator import judge
verdict = judge(task: Task, artifact: Artifact) -> Verdict
```

Verdict: `{status: "pass" | "fail" | "needs_human", reason: str}`.

## LLM

- **Evaluator model:** Opus via OpenRouter (override via `EVALUATOR_MODEL` env). Stronger model for the gate.
- **Fresh context** — no conversation history; only artifact + source PDF text passed in. Prevents prompt-injection from artifacts.

## Default-fail design

Per README §"Evaluator rigor": evaluator defaults to fail. Worker must produce verifiable output for verdict to flip to pass.

## Related

- [[modules/worker]] — produces artifacts judged here
- [[modules/main-harness]] — invokes evaluator
- [[decisions/adr-2-default-fail-evaluator]]
- [[decisions/adr-3-citation-verification]]
