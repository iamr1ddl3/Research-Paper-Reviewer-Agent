---
title: Backtest — initial-map (2026-05-27)
type: analysis
tags: [backtest, audit, accuracy]
sources: [app/*.py, README.md]
updated: 2026-05-27
---

# Backtest — initial-map

First post-MAP backtest. Validates pages written 2026-05-20 against current `app/*.py` source.

## Scorecard

| Pass | Score | Notes |
|---|---|---|
| Structural (lint) | 100% | No broken intra-wiki links. External `../../...` links + SCHEMAS.md template placeholders excluded. |
| Accuracy spot-check | 25% (5/20) | Wiki was README-derived, not source-derived. Many "probably" stubs turned out wrong. |
| Coverage | 60% | 12 modules mapped; data-models missing entirely; ADR-3 mechanism wrong; T7 undocumented as broken. |
| Q&A fidelity | 20% (1/5) | Reader can't get reliable answers about status enum, planner LLM, citation logic, unattended runs. |

## Critical errors found

1. **[[modules/llm-wrapper]]** — wiki hedges. Source: `from openai import OpenAI` (llm.py:5). Definitively OpenAI SDK + OpenRouter base_url.
2. **[[modules/planner]]** — wiki claims "LLM call (Sonnet) called once per goal". Source: planner.py has **zero LLM calls**. Fully static graph build.
3. **[[modules/evaluator]]** — wiki says "LLM-as-judge with default-fail + citations". Source: evaluator.py uses **deterministic checks** for collect_papers / extract_text / summarize_paper / export_pdf — LLM only for compare_methods / identify_patterns / write_report.
4. **[[decisions/adr-3-citation-verification]]** — claims fuzzy substring + Levenshtein. Source: 3-tier cascade (whitespace-norm substring → alphanumeric-fingerprint substring → 60-char sliding window). No Levenshtein. (pdf_tools.py:90)
5. **[[modules/memory]]** — claims public API `init_or_load, pick_next_task, mark_done, retry, escalate, checkpoint`. Source: exports are `init_db, save_task_graph, load_task_graph, save_artifact, save_checkpoint, log_event`. `pick_next_task` lives in main.py:24, not memory.
6. **Task status enum mismatch** — wiki uses `pending / in_progress / done / fail`. Source: `pending / running / passed / failed`. (schemas.py:5)
7. **EvaluationResult shape wrong** — wiki has `{status: pass|fail|needs_human}`. Source: `{passed: bool, score: int, issues: list[str], next_action: continue|retry|human_review}`. (schemas.py:34)
8. **T7 missing from planner.create_task_graph** — only T1..T6 emitted (planner.py:4). Worker has `_export_pdf` handler (worker.py:358) but dispatch table (worker.py:24) has no `export_pdf` key. **T7 is dead code as currently wired.** Possible bug.
9. **T3 fan-out is runtime, not planning** — planner emits T3 placeholder; `_maybe_fanout` in main.py:61 injects T3.N after T2 passes. Wiki implies planner constructs T3.N directly.
10. **AUTO_APPROVE=1 env undocumented** — approval.py:12 has env-bypass. [[debt/no-async-approval]] says "stdin-only" — partially wrong; env escape exists.
11. **Sandbox uses `str.startswith` not `is_relative_to`** — sandbox.py:9. Prefix-collision risk: `/tmp/foo` is not parent of `/tmp/foobar` semantically, but `startswith` accepts it. New debt.
12. **Column-aware PDF extraction** — pdf_tools.py:12 implements column-aware reading order for 2-column papers. Meaningful design decision, no ADR.
13. **Citations require ≥3 verbatim quotes** — evaluator.py:136, worker SUMMARIZE_SYSTEM. Hard rule undocumented in wiki.
14. **PAPER_COUNT env** — config.py:16 reads `PAPER_COUNT`. Missing from [[modules/config]] env var table.

## Method

Read every file in `app/`. Verified 20 specific factual claims. Probed 5 representative developer questions answered using only the wiki, then checked source.

## Conclusions

Wiki was bootstrapped from README + directory structure without reading source. Several stub pages (sandbox, pdf-tools, schemas) explicitly admitted "read the source for canonical" — those stubs are honest. But several pages **stated wrong facts confidently** (planner LLM call, evaluator default-fail-everywhere, memory public API).

Pattern-level claims (Planner/Worker/Evaluator harness, model split, SQLite checkpointing) are correct in shape. **Implementation-level claims are mostly wrong.**

## Fixes applied this session

See [[log]] entry 2026-05-27 — backtest. Specifically:

- Rewrote [[modules/planner]], [[modules/evaluator]], [[modules/memory]], [[modules/llm-wrapper]].
- Corrected [[decisions/adr-3-citation-verification]] to match 3-tier cascade.
- Fixed status enum + Verdict shape across all modules.
- Created data-model pages for Task, TaskGraph, PaperSummary, EvaluationResult, Artifact.
- Filed new debt: [[debt/t7-dispatch-missing]], [[debt/sandbox-startswith-prefix]], [[debt/evaluator-prompt-vs-adr-2-drift]].
- Filed new ADR: [[decisions/adr-6-column-aware-pdf-extract]], [[decisions/adr-7-three-tier-citation-verify]] (supersedes ADR-3).
- Updated [[modules/config]] PAPER_COUNT + AUTO_APPROVE.
- Updated [[modules/approval]] for AUTO_APPROVE escape hatch.

## Related

- [[log]]
- [[overview]]
