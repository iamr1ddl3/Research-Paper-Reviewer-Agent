---
title: Research-Paper-Reviewer-Agent — System Map
type: architecture
updated: 2026-05-27
---

# System Map

**Long-running AI agent** that reviews research papers (arXiv or local PDFs) and produces a synthesized technical report (Markdown + PDF). Built on a **Planner → Worker → Evaluator** harness with SQLite checkpointing + resume.

## Components

| Component | Role | Path |
|---|---|---|
| [[modules/main-harness]] | CLI + the harness loop. Also owns `pick_next_task` + fan-out trigger. | `app/main.py` |
| [[modules/planner]] | **Deterministic** static T1..T6 task graph builder (no LLM) | `app/planner.py` |
| [[modules/worker]] | Task-type dispatcher. Calls Sonnet for content tasks. | `app/worker.py` |
| [[modules/evaluator]] | Deterministic checks for file-producing tasks; Opus LLM judge for content tasks. | `app/evaluator.py` |
| [[modules/approval]] | Human gate on T6 + `AUTO_APPROVE=1` env override | `app/approval.py` |
| [[modules/memory]] | SQLite tables: task_graph (singleton), artifacts, checkpoints, events | `app/memory.py` |
| [[modules/sandbox]] | Path-restricted file ops (workspace-write, paper-read) | `app/sandbox.py` |
| [[modules/llm-wrapper]] | OpenAI SDK pointed at OpenRouter. JSON-coerced + text-mode calls. | `app/llm.py` |
| [[modules/schemas]] | Pydantic models (Task, TaskGraph, Artifact, EvaluationResult, PaperSummary) | `app/schemas.py` |
| [[modules/arxiv-client]] | arXiv fetch (T1 backend, bypasses sandbox by design) | `app/arxiv_client.py` |
| [[modules/pdf-tools]] | Column-aware PDF text extract + 3-tier citation verify + WeasyPrint export | `app/pdf_tools.py` |
| [[modules/config]] | Env vars + path constants + hard caps | `app/config.py` |

## Data models

- [[data-models/task]] · [[data-models/task-graph]] · [[data-models/artifact]] · [[data-models/evaluation-result]] · [[data-models/paper-summary]]

## Boundaries

**External systems consumed:**
- **OpenRouter** (`api.openrouter.ai`) via OpenAI SDK — `anthropic/claude-sonnet-4.5` (worker), `anthropic/claude-opus-4.1` (evaluator LLM-judge path). `PLANNER_MODEL` env exists but planner is deterministic — dead config.
- **arXiv API** — paper fetch via `arxiv` PyPI package.
- **Filesystem** — `workspace/papers/` (input PDFs), `workspace/project/` (worker output), `workspace/artifacts/T*.md` (handoff notes), `workspace/checkpoints/` (DB-backed), `workspace/agent_state.db` (SQLite).

**External systems produced:**
- `workspace/project/FINAL_REPORT.md` (T6)
- `workspace/project/comparison.md` (T4), `workspace/project/patterns.md` (T5)
- Per-paper: `workspace/project/papers/<id>/raw.txt` + `meta.json` (T2), `summary.json` (T3.N)
- `workspace/project/paper_index.json` (T1)
- `workspace/artifacts/<task_id>.md` per task — human-readable run log
- `workspace/project/FINAL_REPORT.pdf` (T7) — wired 2026-05-27, see [[decisions/adr-8-t7-wiring]]

## Task graph (planner output: T1..T7; T3 fans out at runtime)

| ID | task_type | Owner | Output |
|---|---|---|---|
| T1 | `collect_papers` | Worker → [[modules/arxiv-client]] | `paper_index.json` + `workspace/papers/*.pdf` |
| T2 | `extract_text` | Worker → [[modules/pdf-tools]] | `papers/<id>/raw.txt` + `meta.json` |
| T3 (placeholder) | `summarize_fanout` | Harness | replaced at runtime |
| T3.1..T3.N | `summarize_paper` | Worker (Sonnet) → [[modules/pdf-tools]] verify | `papers/<id>/summary.json` |
| T4 | `compare_methods` | Worker (Sonnet) | `comparison.md` with 3 required H2 sections |
| T5 | `identify_patterns` | Worker (Sonnet) | `patterns.md` |
| T6 | `write_report` | Worker (Sonnet, REPORT_MAX_TOKENS=16000) + **[[modules/approval]] gate** | `FINAL_REPORT.md` with 5 required H2 sections |
| T7 | `export_pdf` | Worker → [[modules/pdf-tools]] WeasyPrint | `FINAL_REPORT.pdf` (size ≥ 1 KB) |

## Harness loop

```
init_db()
graph = load_task_graph() or planner.create_task_graph(goal)
while True:
  graph = _maybe_fanout(graph)            # inject T3.1..T3.N if T2 passed
  task  = pick_next_task(graph)            # status ∈ {pending, failed} + deps passed
  if task is None: break
  if needs_approval(task.id):              # T6 only
    if not request_approval(): status=needs_human; stop
  task.status = "running"; task.attempts += 1
  artifact = worker.run_worker(task)
  evaluator.evaluate_task(task, artifact)
  if passed: status = "passed"
  elif attempts >= 3 or next_action == "human_review": status = "needs_human"; stop
  else: status = "failed"                  # retried next pick
  save_task_graph + save_checkpoint
```

## Safety + correctness primitives

- **Deterministic checks** for collect/extract/summarize/export — required files + non-empty + non-placeholder + ≥3 verified citations.
- **3-tier citation verification** — whitespace-norm + alphanumeric fingerprint + head/tail anchors + 60-char sliding window. See [[decisions/adr-7-three-tier-citation-verify]].
- **Column-aware PDF extraction** — preserves verbatim quote spans for 2-column papers. See [[decisions/adr-6-column-aware-pdf-extract]].
- **Sandboxed worker writes** — workspace/project/ only, via `Path.relative_to` containment check.
- **Human gate on T6** — interactive stdin, with `AUTO_APPROVE=1` env override.
- **Attempt cap** — MAX_ATTEMPTS_PER_TASK = 3 (hardcoded), escalates to `needs_human`.

## Resume behavior

`python -m app.main` (no `--goal`) reloads the singleton TaskGraph from SQLite. All `pending` and `failed` tasks resume. T3 fan-out idempotent across restarts.

## Open questions

See [[overview]] §"Open questions".
