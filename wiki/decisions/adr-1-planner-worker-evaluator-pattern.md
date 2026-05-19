---
title: ADR-1 — Planner / Worker / Evaluator harness pattern
type: decision
status: accepted
date: 2026-05-20
sources: [README.md]
updated: 2026-05-20
---

# ADR-1 — Planner / Worker / Evaluator harness

## Status

Accepted. Core architectural pattern.

## Context

Long-running multi-step agent tasks fail without:
1. **Plan up-front** — without a stable plan, every task decision is ad-hoc and the run drifts.
2. **Quality gate** — without a separate evaluator, a bad summary slips through to comparison + final report.
3. **Resume** — without checkpoints, a 30-min run that crashes at minute 27 is unrecoverable.

## Decision

Three-role separation with a harness loop:

| Role | Model | Job |
|---|---|---|
| Planner | Sonnet | Goal → T1..T7 task graph |
| Worker | Sonnet | Execute one task at a time |
| Evaluator | Opus, fresh context | Default-fail judge |
| Harness | (no LLM) | Loop, dispatch, checkpoint |

Each role is a separate module: [[modules/planner]], [[modules/worker]], [[modules/evaluator]], [[modules/main-harness]].

## Consequences

**Positive:**
- Plan stability — task graph fixed up-front, only execution branches.
- Independent evaluator catches worker errors (citation hallucination, missing fields).
- SQLite checkpoint → full resume.
- Model split (Sonnet for cheap execution, Opus for stricter judgment) balances cost + correctness.

**Negative:**
- More moving parts.
- 3 separate LLM calls per task minimum (worker + evaluator + retry).
- Cost can rack up on hard tasks (worker retries × Opus evaluator).

## Pattern overlap with other projects

Strongly resembles [[../../AI Agent Roadmap/wiki/modules/codeorch]] (Planner + Coder + Tester + Quality Gate). Both use:
- Externalized state (this: SQLite; codeorch: pgvector)
- Default-fail evaluator
- Stateless agent roles
- Model split (small/cheap for execution, bigger/slow for judgment)

**Promote pattern to [[../../wiki/ai-ml/concepts/]] — generalizable lore.**

## References

- README §"Architecture"
- arxiv 2510.10460 (multi-agent code gen, similar pattern)

## Related

- [[modules/main-harness]]
- [[modules/planner]], [[modules/worker]], [[modules/evaluator]]
- [[decisions/adr-2-default-fail-evaluator]]
