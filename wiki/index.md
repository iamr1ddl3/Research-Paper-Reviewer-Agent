# Research-Paper-Reviewer-Agent — Wiki Index

Master table of contents. Mapped 2026-05-20. Backtested + corrected 2026-05-27. T7 + sandbox fixes 2026-05-27.

## Entry points

- [[overview]] — what + why + open questions + cross-project lore candidates
- [[architecture/system-map]] — Planner/Worker/Evaluator components + harness loop
- [[flows/full-review-run]] — end-to-end task graph T1..T7
- [[log]] — activity log
- [[MILESTONES]] — milestone tags

## Modules (12)

**Orchestration:**
- [[modules/main-harness]] — CLI + pick → approve → run → evaluate loop (also owns `pick_next_task`)
- [[modules/memory]] — SQLite tables (task_graph singleton, artifacts, checkpoints, events)
- [[modules/sandbox]] — workspace-write / paper-read path restriction

**Three agent roles:**
- [[modules/planner]] — **deterministic** static T1..T7 graph (no LLM)
- [[modules/worker]] — task-type dispatcher (Sonnet for content tasks)
- [[modules/evaluator]] — deterministic checks for files, Opus LLM judge for content
- [[modules/approval]] — interactive human gate for T6 + `AUTO_APPROVE=1` env override

**Shared infra:**
- [[modules/llm-wrapper]] — OpenAI SDK pointed at OpenRouter
- [[modules/schemas]] — Pydantic models
- [[modules/config]] — env + paths + hard caps

**Task-specific tools:**
- [[modules/arxiv-client]] — T1: paper fetch from arXiv
- [[modules/pdf-tools]] — column-aware extract + 3-tier citation verify + WeasyPrint export

## Data models (5)

- [[data-models/task]] — single node (Pydantic Task)
- [[data-models/task-graph]] — singleton container
- [[data-models/artifact]] — worker output report
- [[data-models/evaluation-result]] — judge verdict
- [[data-models/paper-summary]] — per-paper summary (method/dataset/results/limitations/implementation_notes/citations)

## Flows (1)

- [[flows/full-review-run]] — `python -m app.main --goal "..." --count N` end-to-end

## Decisions / ADRs (8, one superseded)

- [[decisions/adr-1-planner-worker-evaluator-pattern]] — core architectural pattern
- [[decisions/adr-2-default-fail-evaluator]] — evaluator default-fail discipline (see drift debt)
- [[decisions/adr-3-citation-verification]] — **superseded by ADR-7**
- [[decisions/adr-4-sandbox-write-restriction]] — worker writes confined to workspace/project/
- [[decisions/adr-5-human-gate-on-final-report]] — T6 needs approval before T7
- [[decisions/adr-6-column-aware-pdf-extract]] — column-aware reading order for 2-column PDFs
- [[decisions/adr-7-three-tier-citation-verify]] — current citation verify cascade
- [[decisions/adr-8-t7-wiring]] — wire T7 (PDF export) into task graph + dispatch

## Debt (6, 5 resolved/accepted, 0 open)

- [[debt/no-async-approval]] — LOW, **ACCEPTED 2026-05-27** — AUTO_APPROVE is the unattended escape hatch; async gate sketched as future option
- [[debt/llm-wrapper-comment-stale]] — LOW, **RESOLVED 2026-05-27** — README rewritten
- [[debt/3-attempt-cap-may-be-low]] — LOW, **RESOLVED 2026-05-27** — per-task-type caps via `MAX_ATTEMPTS_BY_TYPE` env
- [[debt/t7-dispatch-missing]] — HIGH, **RESOLVED 2026-05-27** — wired via ADR-8
- [[debt/sandbox-startswith-prefix]] — MEDIUM, **RESOLVED 2026-05-27** — fixed via `Path.relative_to`
- [[debt/evaluator-prompt-vs-adr-2-drift]] — LOW, **RESOLVED 2026-05-27** — ADR-2 reframed as two-track

## Analyses (1)

- [[analyses/backtest-initial-map-2026-05-27]] — first backtest of the 2026-05-20 map; scorecard + corrections

## APIs / Scaling / Concepts

Not yet enumerated.

## Page types summary

- `modules/` (12) · `apis/` (0) · `data-models/` (5) · `flows/` (1)
- `decisions/` (8, 1 superseded) · `debt/` (6, 0 open) · `scaling/` (0) · `concepts/` (0)
- `analyses/` (1) · `architecture/system-map.md` (1) · `overview.md` (1)

**Total maintained pages: 36** plus scaffolding (index, log, MILESTONES, SCHEMAS, WORKSHOP-GUIDE).
