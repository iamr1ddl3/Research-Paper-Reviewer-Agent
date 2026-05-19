---
title: Research-Paper-Reviewer-Agent — System Map
type: architecture
updated: 2026-05-20
---

# System Map

**Long-running AI agent** that reviews research papers (arxiv or local PDF) and produces a synthesized technical report (Markdown + JSON + PDF). Built on a **Planner → Worker → Evaluator** harness with SQLite checkpointing + resume.

## Components

| Component | Role | Path |
|---|---|---|
| [[modules/main-harness]] | The harness loop — pick task, run worker, evaluate, checkpoint | `app/main.py` |
| [[modules/planner]] | Goal → T1-T7 task graph (Sonnet via OpenRouter) | `app/planner.py` |
| [[modules/worker]] | Task-type dispatcher, runs one task at a time (Sonnet via OpenRouter) | `app/worker.py` |
| [[modules/evaluator]] | Default-fail judge with required-fields + citation verification (Opus via OpenRouter, fresh context) | `app/evaluator.py` |
| [[modules/approval]] | Interactive human-approval gate for T6/T7 | `app/approval.py` |
| [[modules/memory]] | SQLite state store (task graph, attempts, status) | `app/memory.py` |
| [[modules/sandbox]] | Path-restricted file ops (workspace/project/ only) | `app/sandbox.py` |
| [[modules/llm-wrapper]] | Anthropic SDK wrapper (despite OpenRouter usage per README) | `app/llm.py` |
| [[modules/schemas]] | Pydantic models for tasks, summaries, evaluator output | `app/schemas.py` |
| [[modules/arxiv-client]] | arXiv fetch — T1 task implementation | `app/arxiv_client.py` |
| [[modules/pdf-tools]] | PDF text extract + final-report PDF export | `app/pdf_tools.py` |
| [[modules/config]] | Env vars + path setup | `app/config.py` |

## Boundaries

**External systems consumed:**
- **OpenRouter** (`api.openrouter.ai`) — LLM access via OpenAI-compatible endpoint. Routes to Sonnet (planner/worker) + Opus (evaluator).
- **arXiv API** — paper fetch (`arxiv_client.py`).
- **Filesystem** — `workspace/papers/` (input PDFs), `workspace/project/` (worker output), `workspace/artifacts/T*.md` (handoff notes), `workspace/checkpoints/` (resume state), `workspace/logs/`.

**External systems produced:**
- `workspace/project/FINAL_REPORT.md` — final synthesized report
- `workspace/project/FINAL_REPORT.pdf` — PDF export
- `workspace/project/comparison.md`, `workspace/project/patterns.md` — intermediate artifacts
- Per-paper `workspace/project/papers/<id>/summary.json`

## Task graph (T1..T7)

| ID | Title | Output | Owner |
|---|---|---|---|
| T1 | Collect papers | `workspace/papers/*.pdf` (via arxiv_client or pre-supplied) | Worker |
| T2 | Extract text + metadata | `papers/<id>/raw.txt`, `papers/<id>/meta.json` | Worker (uses pdf_tools) |
| T3.N | Summarize paper N | `papers/<id>/summary.json` | Worker |
| T4 | Compare methods across papers | `comparison.md` | Worker |
| T5 | Identify repeated patterns | `patterns.md` | Worker |
| T6 | Write final report | `FINAL_REPORT.md` — **requires human approval** | Worker + Approval |
| T7 | Export PDF | `FINAL_REPORT.pdf` | Worker (pdf_tools) |

## Harness loop

```
pick_next_task() → returns next pending or retryable task from SQLite
  ↓
worker.run(task) → executes task-type dispatch
  ↓
evaluator.judge(task, artifact) → pass | fail (with reason) | needs_human
  ↓
if pass: mark task done, checkpoint
if fail: increment attempts (max 3), retry or escalate to needs_human
if needs_human: pause for approval
  ↓ loop until all tasks done OR escalation
```

## Safety + correctness primitives

- **Default-fail evaluator** — passes only when required fields present + citations verifiable.
- **Citation verification** — quotes in `summary.citations[]` must exist (fuzzy-normalized) in source PDF text. Fabricated quotes → fail.
- **Sandboxed file ops** — Worker can only write under `workspace/project/`.
- **Human gate on T6** — interactive approval before finalizing report.
- **Attempt cap** — max 3 per task before escalation.

## Resume behavior

`python -m app.main` (no `--goal`) reloads existing task graph from SQLite. All in-progress + failed tasks resume.

## Open questions

See [[overview]] §"Open questions".
