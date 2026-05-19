---
title: Research-Paper-Reviewer-Agent — Overview
type: overview
updated: 2026-05-20
---

# Research-Paper-Reviewer-Agent — Overview

**Long-running AI agent** that takes a goal (e.g., "Review papers on LLM agent architectures, count=3"), pulls or accepts PDFs, and produces a synthesized technical report as Markdown + PDF.

**Pattern:** Planner → Worker → Evaluator harness with SQLite checkpointing. Resumes after crashes. Catches hallucinated citations structurally.

12-file Python app under `app/`. Pure backend — CLI-driven, no UI. Workspace already contains artifacts from real runs (T1.md..T6.md in `workspace/artifacts/`, FINAL_REPORT.md + comparison.md + patterns.md in `workspace/project/`, 2 sample papers under `workspace/project/papers/`).

## Domain

`ai-ml` — multi-agent orchestration, default-fail evaluator, citation verification, sandboxed execution.

## Status

`active` — functional. README documents pattern. Runs evidence in workspace/.

## Phases

| Phase | Status | Notes |
|---|---|---|
| 1. Planner / Worker / Evaluator harness | DONE | Core pattern shipped. |
| 2. SQLite checkpointing + resume | DONE | [[modules/memory]] |
| 3. Citation verification | DONE | [[decisions/adr-3-citation-verification]] |
| 4. Sandboxed worker writes | DONE | [[modules/sandbox]] |
| 5. Async approval channel | NOT STARTED | [[debt/no-async-approval]] |
| 6. Stale README comment fix | NOT STARTED | [[debt/llm-wrapper-comment-stale]] |
| 7. Per-task attempt-cap tuning | NOT STARTED | [[debt/3-attempt-cap-may-be-low]] |

## Key integrations

- **OpenRouter** — LLM access via OpenAI-compatible endpoint. Routes Planner + Worker (Sonnet) + Evaluator (Opus).
- **arXiv** — paper fetch for T1 when local PDFs are underfull.
- **SQLite** — state persistence.
- **PDF tooling** — text extract (T2) + final-report PDF export (T7).

## Pattern overlap (cross-project lore)

Strong overlap with **[[../../AI Agent Roadmap/wiki/modules/codeorch]]** — Planner + Coder + Tester + QualityGate pattern. Both projects independently arrived at:
- Externalized state (SQLite here; pgvector there)
- Default-fail evaluator
- Stateless agent roles
- Sonnet/Opus model split

**The Planner / Worker / Evaluator pattern belongs in [[../../wiki/ai-ml/concepts/]] — reusable lore across multi-agent projects.**

## Open questions

1. **Async approval channel.** Stdin-only blocks unattended runs at T6. ([[debt/no-async-approval]])
2. **Stale README comment** on `llm.py`. ([[debt/llm-wrapper-comment-stale]])
3. **3-attempt cap tuning.** May be too tight for hard summaries. ([[debt/3-attempt-cap-may-be-low]])
4. **Promote pattern to central hub.** Other projects ([[../../AI Agent Roadmap]]) use the same shape — codify as a concept.
5. **PDF text extraction quality** under unusual layouts (math, multi-column). Citation verification depends on this.

## Entry points

- [[architecture/system-map]] — components + harness loop
- [[flows/full-review-run]] — end-to-end
- [[modules/main-harness]] — the loop
- [[modules/planner]], [[modules/worker]], [[modules/evaluator]] — the three roles
- [[index]] — full ToC
