---
title: PaperSummary (per-paper structured summary)
type: data-model
tags: [entity, pydantic]
storage: workspace/project/papers/<id>/summary.json
sources: [app/schemas.py, app/worker.py, app/evaluator.py]
updated: 2026-05-27
---

# PaperSummary

Structured per-paper summary. Output of T3.N (`summarize_paper`). Consumed by T4 (compare), T5 (patterns), T6 (report).

## Schema

| Field | Type | Required content |
|---|---|---|
| `paper_id` | str | filename-derived id (e.g. `2510_10460v1`) |
| `title` | str | paper title (from LLM, validated against extract metadata) |
| `authors` | list[str] | author list, default `[]` |
| `method` | str | ≥ 2 sentences; ≥ 20 chars; not placeholder; technical approach |
| `dataset` | str | datasets, benchmarks, experimental setup |
| `results` | str | quantitative + qualitative results |
| `limitations` | str | stated or evident limitations |
| `implementation_notes` | str | architecture, libs, hyperparams, reproducibility |
| `citations` | list[str] | ≥ 3 exact verbatim quotes, 30-200 chars each, programmatically verified against raw.txt |

## Required-field rules (evaluator.py:123)

For each of `(method, dataset, results, limitations, implementation_notes)`:
- Must be non-empty after `.strip()`.
- Not in `{"n/a", "none", "unknown", "tbd"}` (case-insensitive).
- ≥ 20 chars.

## Citation rules (evaluator.py:136)

- `len(citations) >= 3` (else fail).
- Every `quote` must pass `pdf_tools.verify_citation(quote, raw_text)` (3-tier cascade — see [[decisions/adr-7-three-tier-citation-verify]]).
- Reported failures list up to 3 unverified quote previews (first 80 chars).

## Lifecycle

1. Worker `_summarize_paper` (worker.py:170) prompts Sonnet with `raw_text[:60000]` + metadata.
2. LLM returns JSON, validated via `PaperSummary.model_validate(...)`.
3. Written to `papers/<pid>/summary.json` via [[modules/sandbox]] `write_file`.
4. Evaluator `_evaluate_summary` re-reads + validates + checks citations.
5. Read by T4/T5/T6 via `_load_all_summaries` (worker.py:223).

## Related

- [[modules/worker]] (producer)
- [[modules/evaluator]] (validator)
- [[modules/pdf-tools]] (citation verifier)
- [[decisions/adr-7-three-tier-citation-verify]]
