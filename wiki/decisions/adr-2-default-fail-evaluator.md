---
title: ADR-2 — Two-track evaluator (default-fail det checks + skeptical-but-fair LLM judge)
type: decision
status: accepted
date: 2026-05-20
sources: [README.md, app/evaluator.py]
updated: 2026-05-27
---

# ADR-2 — Two-track evaluator

## Status

Accepted. Reframed 2026-05-27 to document the two-track design that was previously called uniformly "default-fail" (the LLM judge track is not strictly default-fail).

## Context

LLM-as-judge default behavior is to pass when in doubt → rubber-stamping. For paper review where summaries must be verifiable + structured, this is unacceptable.

But for **content-quality** tasks (comparison narratives, pattern identification, final report prose), a strict default-fail LLM rubric would over-reject on stylistic grounds → retry storm → cost spiral.

The natural split is between **what can be checked deterministically** (file existence, schema validity, citation provenance) and **what cannot** (narrative quality, synthesis correctness).

## Decision

Evaluator dispatches by `task.task_type` (evaluator.py:14) into two tracks.

### Track 1 — Deterministic, default-fail

Handles: `collect_papers`, `extract_text`, `summarize_paper`, `export_pdf`.

Pass only when **every** enumerated condition is concretely met:

- `collect_papers`: ≥ PAPER_COUNT PDFs + `paper_index.json` valid JSON list + each entry has id/filename/source + filename exists on disk.
- `extract_text`: every paper has `raw.txt` ≥ 500 chars + `meta.json` with `title` or `filename`.
- `summarize_paper`: PaperSummary validates + each required field non-empty + not placeholder ("N/A"/"none"/"unknown"/"tbd") + ≥ 20 chars + ≥ 3 citations + every citation `verify_citation()` passes (3-tier cascade, see [[decisions/adr-7-three-tier-citation-verify]]).
- `export_pdf`: `FINAL_REPORT.pdf` exists + size ≥ 1024 bytes.

`_fail(...)` scoring: `score = max(0, 100 - 20 * len(issues))`. `_ok` returns 100.

### Track 2 — LLM judge, skeptical-but-fair

Handles: `compare_methods`, `identify_patterns`, `write_report`.

Opus model via OpenRouter, fresh prompt every call (no conversation history). System prompt (`EVALUATOR_SYSTEM`) instructs:

> "Mode: skeptical but fair. ... Only fail if a criterion is concretely unmet (file missing, required section absent, citation invalid)."

Prompt includes: task spec + artifact JSON + workspace file listing with byte sizes + a truncated excerpt of the relevant output file. LLM returns the same `EvaluationResult` shape as Track 1.

## Consequences

**Positive:**
- Hallucinated citations + missing required fields caught structurally, not by review.
- Content tasks not over-rejected on style → retry budget preserved for genuine failures.
- Trust boundary explicit: det checks for files, LLM for prose.
- Fresh context per LLM eval prevents prompt-injection from artifacts.

**Negative:**
- Two-track design adds cognitive load — readers must know which track applies to a given task_type.
- Track 2 is genuinely permissive on style. A poor-quality but structurally-complete `comparison.md` will pass.
- Attempt-cap behavior is uniform across tracks — Track 2 retries cost more (Opus calls) but are no more likely to find a fixable defect than Track 1 retries.

## Pair with ADR-7

[[decisions/adr-7-three-tier-citation-verify]] is the specific check inside Track 1's `summarize_paper` path that makes default-fail meaningful — without verifiable citations, the schema check alone would let fabricated quotes pass.

## Alternatives Considered

- **Uniform default-fail across all tasks (original ADR-2 framing).** Rejected: too expensive on content tasks; rubber-stamp evaluator → no signal.
- **Uniform LLM judge across all tasks.** Rejected: LLM-judge on file-existence is wasteful + unreliable; deterministic check is faster + correct.
- **Hybrid (LLM judge with deterministic preconditions).** Considered. Adds latency; current two-track split is cleaner.

## References

- README §"Evaluator rigor"
- `app/evaluator.py`

## Related

- [[modules/evaluator]]
- [[decisions/adr-1-planner-worker-evaluator-pattern]]
- [[decisions/adr-7-three-tier-citation-verify]]
- [[debt/evaluator-prompt-vs-adr-2-drift]] (resolved)
