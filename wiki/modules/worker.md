---
title: Worker (task-type dispatcher)
type: module
tags: [worker, llm, dispatch]
language: python
entry_point: app/worker.py
updated: 2026-05-27
---

# Worker

Task-type dispatcher. Runs one task at a time. Returns an `Artifact` (changed/failed/remaining/evidence). Writes go through [[modules/sandbox]] (workspace-only).

## Dispatch table (worker.py:24)

```python
{
  "collect_papers":     _collect_papers,
  "extract_text":       _extract_text,
  "summarize_fanout":   _fanout_placeholder,
  "summarize_paper":    _summarize_paper,
  "compare_methods":    _compare_methods,
  "identify_patterns":  _identify_patterns,
  "write_report":       _write_report,
  "export_pdf":         _export_pdf,
}
```

T7 dispatch wired 2026-05-27. See [[decisions/adr-8-t7-wiring]].

## Per-handler summary

| Handler | Input | LLM | Output |
|---|---|---|---|
| `_collect_papers` | `workspace/papers/*.pdf` count + ARXIV_QUERY | — | `paper_index.json`, possibly arXiv downloads |
| `_extract_text` | `paper_index.json` | — | `papers/<id>/raw.txt`, `papers/<id>/meta.json` via [[modules/pdf-tools]] |
| `_fanout_placeholder` | — | — | empty artifact; harness handles fan-out |
| `_summarize_paper` | `papers/<pid>/raw.txt[:60000]` | Sonnet (`SUMMARIZE_SYSTEM`) | `papers/<pid>/summary.json` (PaperSummary-validated) |
| `_compare_methods` | all `papers/<id>/summary.json` | Sonnet (`COMPARE_SYSTEM`) | `comparison.md` w/ 3 required H2 sections |
| `_identify_patterns` | summaries + `comparison.md` | Sonnet (`PATTERNS_SYSTEM`) | `patterns.md` |
| `_write_report` | summaries + comparison + patterns | Sonnet (`REPORT_SYSTEM`, max_tokens=16000) | `FINAL_REPORT.md` w/ 5 H2 sections |
| `_export_pdf` | `FINAL_REPORT.md` | — | `FINAL_REPORT.pdf` via WeasyPrint |

## Citation discipline (SUMMARIZE_SYSTEM)

Worker is instructed to produce **≥ 3 exact verbatim quotes (30-200 chars each)** in `citations[]`. Evaluator enforces ≥ 3 + `verify_citation` pass.

## Truncation guard

Raw text truncated at 60000 chars before passing to Sonnet (worker.py:186). No chunked summarization for long papers.

## Public Interface

```python
from app.worker import run_worker
artifact: Artifact = run_worker(task)
```

## Related

- [[modules/main-harness]] — caller
- [[modules/evaluator]] — judges output
- [[modules/sandbox]] — file ops
- [[modules/llm-wrapper]] — `call_llm` / `call_llm_json`
- [[modules/pdf-tools]] — T2 + T7 backends
- [[modules/arxiv-client]] — T1 backend
- [[decisions/adr-8-t7-wiring]]
