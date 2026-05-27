---
title: "ADR-8 — Wire T7 (PDF export) into the task graph"
type: decision
status: accepted
date: 2026-05-27
sources: [app/planner.py, app/worker.py, app/evaluator.py, app/pdf_tools.py]
updated: 2026-05-27
---

# ADR-8 — Wire T7 (PDF export) into the task graph

## Status

Accepted.

## Context

Backtest 2026-05-27 found T7 unreachable: planner emitted T1..T6, worker dispatch lacked `export_pdf`. Handler + evaluator existed in source but never ran.

Two options:

**A. Remove the dead code.** Strip `_export_pdf`, `_evaluate_pdf`, README mentions, system-map T7 row. Acknowledge that FINAL_REPORT.md is the deliverable.

**B. Wire T7 in.** Add T7 to planner output + worker dispatch. Honor the documented contract.

## Decision

**Option B — wire it in.**

Reasons:
1. README + system-map promise `FINAL_REPORT.pdf`. Honoring the contract beats trimming the README.
2. `_export_pdf` + `_evaluate_pdf` are real, tested-looking code (WeasyPrint setup, error hint for missing pango/cairo, size-floor evaluator check). Removing them discards working logic.
3. PDF deliverable is a normal-user expectation for a "research paper reviewer." Markdown alone is engineer-only.
4. Two-line diff to fix vs ~30 lines + docs to remove.

## Implementation

- `planner.py:91` — T7 Task: `task_type="export_pdf"`, `dependencies=["T6"]`, criteria mirror `_evaluate_pdf` (FINAL_REPORT.pdf exists + ≥ 1 KB).
- `worker.py:32` — `"export_pdf": _export_pdf` in dispatch.

## Consequences

**Positive:**
- README contract honored.
- Existing handler + evaluator now exercised.
- Two more debt items closed in one pass (see [[debt/t7-dispatch-missing]]).

**Negative:**
- WeasyPrint requires system libs (pango, cairo). Users on bare macOS will hit T7 failure with the existing helpful error message ("brew install pango cairo"). T7 retries 3× then escalates `needs_human`.
- T7 not gated by approval. Could add to `APPROVAL_TASK_IDS` if a human should sign off on the PDF artifact too — current design assumes T6 approval covers the content, T7 is mechanical.
- Existing `agent_state.db` rows hold pre-T7 graphs. Resume runs don't gain T7. Fresh `--goal` (or `reset_and_run.sh`) required.

## Alternatives Considered

- **Removal** (Option A) — rejected; honor existing contract.
- **Lazy T7 (only emit if WeasyPrint importable)** — over-engineering for the failure mode. T7 fails loudly with a useful hint; that's good enough.

## Related

- [[modules/planner]] · [[modules/worker]] · [[modules/evaluator]] · [[modules/pdf-tools]]
- [[debt/t7-dispatch-missing]] (resolved)
- [[flows/full-review-run]]
