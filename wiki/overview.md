---
title: Research-Paper-Reviewer-Agent — Overview
type: overview
updated: 2026-05-27
---

# Research-Paper-Reviewer-Agent — Overview

**Long-running AI agent** that takes a goal (e.g., "Review papers on LLM agent architectures, count=3"), pulls or accepts PDFs, and produces a synthesized technical report as Markdown + PDF.

**Pattern:** Planner → Worker → Evaluator harness with SQLite checkpointing. Resumes after crashes. Catches hallucinated citations structurally via a 3-tier fuzzy verify cascade against column-aware PDF text.

12-file Python app under `app/`. Pure backend — CLI-driven, no UI. Workspace already contains artifacts from real runs (T1..T6 in `workspace/artifacts/`, FINAL_REPORT.md + comparison.md + patterns.md in `workspace/project/`, 2 sample papers under `workspace/project/papers/`).

## Domain

`ai-ml` — multi-agent orchestration, deterministic + LLM hybrid evaluator, fuzzy citation verification, sandboxed execution.

## Status

`active` — T1..T7 functional as of 2026-05-27.

## Phases

| Phase | Status | Notes |
|---|---|---|
| 1. Planner / Worker / Evaluator harness | DONE | Core pattern shipped. |
| 2. SQLite checkpointing + resume | DONE | Singleton task_graph row + events log. [[modules/memory]] |
| 3. Citation verification | DONE | 3-tier cascade. [[decisions/adr-7-three-tier-citation-verify]] |
| 4. Column-aware PDF extraction | DONE | [[decisions/adr-6-column-aware-pdf-extract]] |
| 5. Sandboxed worker writes | DONE | [[modules/sandbox]] — `Path.relative_to` containment |
| 6. AUTO_APPROVE env for unattended runs | DONE | [[modules/approval]] — async channel deferred, see [[debt/no-async-approval]] |
| 7. T7 PDF export wiring | DONE | [[decisions/adr-8-t7-wiring]] |
| 8. README accuracy refresh | DONE | [[debt/llm-wrapper-comment-stale]] resolved |
| 9. Per-task-type attempt caps | DONE | [[debt/3-attempt-cap-may-be-low]] resolved — `MAX_ATTEMPTS_BY_TYPE` env |
| 10. Two-track evaluator documented | DONE | [[decisions/adr-2-default-fail-evaluator]] reframed |

## Key integrations

- **OpenRouter** via OpenAI SDK — routes `WORKER_MODEL` (Sonnet) + `EVALUATOR_MODEL` (Opus). `PLANNER_MODEL` env declared but unused — planner is deterministic.
- **arXiv** — paper fetch via `arxiv` PyPI client. Bypasses sandbox (trusted infra code).
- **SQLite** — singleton task_graph + append-only artifacts/checkpoints/events.
- **PDF tooling** — PyMuPDF column-aware extract (primary), pdfplumber (fallback + metadata), WeasyPrint (export — currently unreachable).

## Pattern overlap (cross-project lore)

Strong overlap with **[[../../AI Agent Roadmap/wiki/modules/codeorch]]** — Planner + Coder + Tester + QualityGate. Both projects independently arrived at:
- Externalized state (SQLite here; pgvector there)
- Default-fail evaluator (this one is hybrid: det-fail for files, LLM-pass-with-grounds for content)
- Stateless agent roles
- Sonnet/Opus model split

**The Planner / Worker / Evaluator pattern belongs in [[../../wiki/ai-ml/concepts/]] — reusable lore across multi-agent projects.**

## Open questions

All 6 backtest-surfaced debt items are now closed (4 resolved by code, 1 resolved by doc-only, 1 accepted as bounded). Remaining strategic questions:

1. **Promote Planner/Worker/Evaluator pattern to central hub.** Other projects ([[../../AI Agent Roadmap]]) independently arrived at the same shape — codify as a concept under `~/Documents/Projects/wiki/ai-ml/concepts/`.
2. **File-based async approval gate.** If unattended-with-review is later needed, sketch in [[debt/no-async-approval]] is the cheapest path.
3. **PDF extraction quality on math-heavy + multi-column edge cases.** Column-aware extract handles 2-column well; 3-column or asymmetric layouts untested.
4. **WeasyPrint system dep friction.** T7 fails on bare macOS without `brew install pango cairo`. Now documented in README setup section.

## Entry points

- [[architecture/system-map]] — components + harness loop
- [[flows/full-review-run]] — end-to-end
- [[modules/main-harness]] — the loop
- [[modules/planner]], [[modules/worker]], [[modules/evaluator]] — the three roles
- [[index]] — full ToC
- [[analyses/backtest-initial-map-2026-05-27]] — what was wrong, what was fixed
