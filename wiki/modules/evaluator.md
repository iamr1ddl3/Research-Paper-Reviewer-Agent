---
title: Evaluator (per-task-type judge — deterministic + LLM)
type: module
tags: [evaluator, llm, safety]
language: python
entry_point: app/evaluator.py
updated: 2026-05-27
---

# Evaluator

Per-task-type judge. **Deterministic checks** for file-producing tasks (T1, T2, T3.N, T7). **LLM judge** (Opus, fresh prompt) for content-quality tasks (T4 compare, T5 patterns, T6 report).

## Responsibility

Owns: pass/fail decision per task. Dispatch by `task.task_type`:

| task_type | Path | Checks |
|---|---|---|
| `collect_papers` | deterministic | ≥ PAPER_COUNT PDFs + paper_index.json valid + each entry has id/filename/source + file exists |
| `extract_text` | deterministic | raw.txt non-empty (≥500 chars), meta.json parses, has title or filename |
| `summarize_paper` | deterministic | PaperSummary validates + each required field non-empty + not placeholder ("N/A"/"none"/"unknown"/"tbd") + ≥ 20 chars + ≥ 3 citations + every citation `verify_citation()` passes |
| `summarize_fanout` | auto-pass | placeholder task |
| `export_pdf` | deterministic | FINAL_REPORT.pdf exists + size ≥ 1024 bytes |
| `compare_methods` | LLM | Opus reads workspace listing + comparison.md excerpt |
| `identify_patterns` | LLM | Opus reads workspace listing + patterns.md excerpt |
| `write_report` | LLM | Opus reads workspace listing + FINAL_REPORT.md excerpt (first 6000 chars) |

## Public Interface

```python
from app.evaluator import evaluate_task
result: EvaluationResult = evaluate_task(task: Task, artifact: Artifact)
```

Result shape ([[data-models/evaluation-result]]):

```
EvaluationResult {
  task_id: str
  passed: bool          # NOT status enum
  score: int            # 100 - 20*len(issues), floored at 0
  issues: list[str]
  next_action: "continue" | "retry" | "human_review"
}
```

## LLM judge — system prompt

evaluator.py:152 — `EVALUATOR_SYSTEM` prompt instructs: **"skeptical but fair. Only fail if a criterion is concretely unmet."**

This is the **Track 2** framing — see [[decisions/adr-2-default-fail-evaluator]] which now documents the two-track design: default-fail for deterministic file checks, skeptical-but-fair for LLM content judging.

## Model

`EVALUATOR_MODEL` env (default `anthropic/claude-opus-4.1`) via OpenRouter. Used only for `_evaluate_llm` path.

## Citation verification

Calls `pdf_tools.verify_citation(quote, raw_text)`. Three-tier cascade — see [[decisions/adr-7-three-tier-citation-verify]].

## Required summary fields

```python
REQUIRED_SUMMARY_FIELDS = ("method", "dataset", "results", "limitations", "implementation_notes")
```

Each must be non-empty, not placeholder ("N/A"/"none"/"unknown"/"tbd"), ≥ 20 chars (evaluator.py:129).

## Related

- [[modules/worker]] — produces artifacts judged here
- [[modules/main-harness]] — invokes evaluator
- [[modules/pdf-tools]] — provides `verify_citation`
- [[data-models/evaluation-result]]
- [[decisions/adr-2-default-fail-evaluator]]
- [[decisions/adr-7-three-tier-citation-verify]]
