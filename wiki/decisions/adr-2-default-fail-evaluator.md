---
title: ADR-2 — Default-fail evaluator
type: decision
status: accepted
date: 2026-05-20
sources: [README.md, app/evaluator.py]
updated: 2026-05-20
---

# ADR-2 — Default-fail evaluator

## Status

Accepted.

## Context

LLM-as-judge default behavior: when in doubt, pass. This makes evaluators useless — they rubber-stamp ambiguous output.

For paper-review where summaries must be verifiable + structured, this is unacceptable.

## Decision

Evaluator defaults to **fail**. Pass only when:
1. **Schema valid** — all required fields present (`method`, `dataset`, `results`, `limitations`, `implementation_notes`).
2. **Citations verifiable** — every quote in `summary.citations[]` substring-matches (fuzzy-normalized) the source PDF text.

Otherwise → fail with reason → worker retries (max 3 attempts).

## Consequences

**Positive:**
- Hallucinated citations caught structurally, not by review.
- Schema enforcement → downstream tasks (comparison, patterns) can trust summary shape.
- Honest failures preferred over confident hallucinations.

**Negative:**
- More retries → more cost.
- 3-attempt cap means hard papers may escalate to `needs_human` rather than complete.

## Pair with ADR-3

[[decisions/adr-3-citation-verification]] is the specific check that makes default-fail meaningful.

## References

- README §"Evaluator rigor"
- `app/evaluator.py`

## Related

- [[modules/evaluator]]
- [[decisions/adr-1-planner-worker-evaluator-pattern]]
