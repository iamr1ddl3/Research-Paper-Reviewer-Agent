---
title: Evaluator LLM prompt says "skeptical but fair" — drifts from ADR-2 "default-fail"
type: debt
severity: low
status: resolved
filed: 2026-05-27
resolved: 2026-05-27
sources: [app/evaluator.py]
updated: 2026-05-27
---

# Evaluator system prompt vs ADR-2 framing — RESOLVED (documented)

## Description (historical)

[[decisions/adr-2-default-fail-evaluator]] framed evaluator as **default-fail** uniformly. But `EVALUATOR_SYSTEM` (evaluator.py:152) prompts the LLM judge as "**skeptical but fair**. Only fail if a criterion is concretely unmet." That's default-pass-with-grounds, not default-fail.

Inconsistency was between two real, intentional designs that hadn't been reconciled in the wiki.

## Resolution

[[decisions/adr-2-default-fail-evaluator]] updated 2026-05-27 to document the **two-track** design:

- **Track 1 — deterministic checks (`_evaluate_collect`, `_evaluate_extract`, `_evaluate_summary`, `_evaluate_pdf`)**: default-fail. Enumerate required conditions; pass only if every condition met.
- **Track 2 — LLM judge (`_evaluate_llm`, used for `compare_methods`, `identify_patterns`, `write_report`)**: skeptical-but-fair. Pass unless a criterion is concretely unmet by what the artifact + file listing show.

Rationale for the asymmetry:
- Files either exist with the right shape or they don't — deterministic checks are cheap + reliable for that.
- Content-quality tasks (comparison narratives, pattern identification, final report prose) have no objective ground truth. A strict default-fail LLM rubric would over-reject prose for stylistic reasons → more retries → cost spiral. The "skeptical but fair" frame catches the failure modes that matter (missing section, missing citation, missing paper id) without over-rejecting on style.

No code change. ADR-2 updated to make the design explicit.

## Related

- [[modules/evaluator]]
- [[decisions/adr-2-default-fail-evaluator]]
