# Research-Paper-Reviewer-Agent — Wiki Index

Master table of contents. Mapped 2026-05-20.

## Entry points

- [[overview]] — what + why + open questions + cross-project lore candidates
- [[architecture/system-map]] — Planner/Worker/Evaluator components + harness loop
- [[flows/full-review-run]] — end-to-end task graph T1..T7
- [[log]] — activity log
- [[MILESTONES]] — milestone tags

## Modules (12)

**Orchestration:**
- [[modules/main-harness]] — the pick → worker → evaluator → checkpoint loop
- [[modules/memory]] — SQLite state + resume
- [[modules/sandbox]] — path-restricted file ops

**Three agent roles:**
- [[modules/planner]] — goal → T1..T7 task graph (Sonnet)
- [[modules/worker]] — task-type dispatcher (Sonnet)
- [[modules/evaluator]] — default-fail + citation verification (Opus, fresh context)
- [[modules/approval]] — interactive human gate for T6

**Shared infra:**
- [[modules/llm-wrapper]] — OpenRouter (OpenAI-compatible) wrapper
- [[modules/schemas]] — Pydantic models
- [[modules/config]] — env + paths

**Task-specific tools:**
- [[modules/arxiv-client]] — T1: paper fetch from arXiv
- [[modules/pdf-tools]] — T2 text extract + T7 PDF export

## Flows (1)

- [[flows/full-review-run]] — `python -m app.main --goal "..." --count N` end-to-end

## Decisions / ADRs (5)

- [[decisions/adr-1-planner-worker-evaluator-pattern]] — core architectural pattern
- [[decisions/adr-2-default-fail-evaluator]] — evaluator defaults to fail
- [[decisions/adr-3-citation-verification]] — fuzzy substring match against PDF text
- [[decisions/adr-4-sandbox-write-restriction]] — worker writes confined to workspace/project/
- [[decisions/adr-5-human-gate-on-final-report]] — T6 needs approval before T7

## Debt (3)

- [[debt/no-async-approval]] — MEDIUM — stdin-only approval blocks unattended runs
- [[debt/llm-wrapper-comment-stale]] — LOW — README comment for llm.py says Anthropic; uses OpenRouter
- [[debt/3-attempt-cap-may-be-low]] — LOW — 3 retries may be too tight for hard summaries

## APIs / Data Models / Scaling / Concepts / Analyses

Not enumerated. Pydantic models in [[modules/schemas]] cover data shapes.

## Page types summary

- `modules/` (12) · `apis/` (0) · `data-models/` (0) · `flows/` (1)
- `decisions/` (5) · `debt/` (3) · `scaling/` (0) · `concepts/` (0)
- `analyses/` (0) · `architecture/system-map.md` (1) · `overview.md` (1)

**Total maintained pages: 23** plus scaffolding (index, log, MILESTONES, SCHEMAS, WORKSHOP-GUIDE).
