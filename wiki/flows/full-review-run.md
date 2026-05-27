---
title: Full Review Run (end-to-end flow)
type: flow
trigger: python -m app.main --goal "..." --count N
updated: 2026-05-27
---

# Full Review Run

End-to-end pipeline from user goal to FINAL_REPORT.md + FINAL_REPORT.pdf. T7 wired 2026-05-27 — see [[decisions/adr-8-t7-wiring]].

## Trigger

```bash
python -m app.main --goal "Review papers on LLM agent architectures" --count 3
```

`--count` overrides `PAPER_COUNT` (default 5) at runtime.

## Sequence

```
USER goal + --count
  ↓
[main.py] init_db()
  ↓
[main.py] load_task_graph() OR planner.create_task_graph(goal)  ← deterministic, no LLM
  ↓
[memory.py] save_task_graph (singleton row), save_checkpoint
  ↓
HARNESS LOOP:
  ┌─ _maybe_fanout(graph)
  │    └─ if T2 passed + paper_index.json exists:
  │         planner.inject_summarize_subtasks(graph, paper_ids)
  │    ↓
  │  task = pick_next_task(graph)         ← main.py:24, NOT memory.py
  │    ↓
  │  if needs_approval(task.id):           ← currently only T6
  │     request_approval()                  ← stdin OR AUTO_APPROVE=1 env
  │       └─ denied: status=needs_human, stop
  │    ↓
  │  status = "running"; attempts += 1
  │    ↓
  │  artifact = worker.run_worker(task)    ← dispatch by task.task_type
  │    ↓
  │  memory.save_artifact(artifact)
  │    ↓
  │  result = evaluator.evaluate_task(task, artifact)
  │    ├─ collect_papers / extract_text / summarize_paper / export_pdf:
  │    │     deterministic checks (file existence + content + citations)
  │    └─ compare_methods / identify_patterns / write_report:
  │          LLM judge (Opus) — "skeptical but fair" prompt
  │    ↓
  │  main.write_artifact_file(artifact, task, eval_issues)
  │    ↓
  │  if result.passed:
  │     status = "passed"
  │  elif attempts >= MAX (3) OR next_action == "human_review":
  │     status = "needs_human"; STOP
  │  else:
  │     status = "failed"                  ← retried on next pick
  │    ↓
  │  save_task_graph + save_checkpoint
  └─ loop until pick_next_task returns None
```

## Per-task progression (happy path)

| ID | task_type | What happens |
|---|---|---|
| T1 | `collect_papers` | If local count < PAPER_COUNT: arxiv_client.fetch_papers(ARXIV_QUERY). Write `paper_index.json`. Det eval: ≥ count PDFs + index valid. |
| T2 | `extract_text` | For each paper: pdf_tools.extract_text + extract_metadata. Write `papers/<id>/raw.txt` + `meta.json`. Det eval: raw.txt ≥ 500 chars + meta has title/filename. |
| (fanout) | — | Harness `_maybe_fanout` injects T3.1..T3.N. |
| T3.N | `summarize_paper` | Read raw.txt[:60000] → Sonnet → PaperSummary JSON → write `papers/<id>/summary.json`. Det eval: all required fields populated + non-placeholder + ≥20 chars + ≥3 citations + every citation `verify_citation()` passes. |
| T4 | `compare_methods` | Read all summaries → Sonnet → `comparison.md` with 3 required H2 sections. Opus LLM judge. |
| T5 | `identify_patterns` | Summaries + comparison → Sonnet → `patterns.md`. Opus LLM judge. |
| T6 | `write_report` | All inputs → Sonnet (max_tokens=16000) → `FINAL_REPORT.md`. **Approval gate fires first.** Opus LLM judge. |
| T7 | `export_pdf` | pdf_tools.export_pdf renders FINAL_REPORT.md → FINAL_REPORT.pdf via WeasyPrint. Det eval: pdf exists + size ≥ 1 KB. Requires system libs pango + cairo. |

## Output artifacts

| Path | Producer |
|---|---|
| `workspace/papers/*.pdf` | T1 (local or arxiv) |
| `workspace/project/paper_index.json` | T1 |
| `workspace/project/papers/<id>/raw.txt` + `meta.json` | T2 |
| `workspace/project/papers/<id>/summary.json` | T3.N |
| `workspace/project/comparison.md` | T4 |
| `workspace/project/patterns.md` | T5 |
| `workspace/project/FINAL_REPORT.md` | T6 (post-approval) |
| `workspace/project/FINAL_REPORT.pdf` | T7 |
| `workspace/artifacts/<task_id>.md` | every task (handoff log) |
| `workspace/agent_state.db` | every task (SQLite) |

## Failure modes

| Stage | Failure | Behavior |
|---|---|---|
| Planner | n/a — deterministic | — |
| T1 | ARXIV_QUERY empty + local underfull | Det eval fails; user instructed to set env or drop PDFs |
| T1 | arXiv rate limit / network | Caught; failed_msg in artifact; eval re-checks count |
| T2 | PDF extract exception | Per-paper failure logged; column-aware PyMuPDF falls back to pdfplumber |
| T3.N | LLM hallucinates citation | `verify_citation` fails → eval fail → retry (max 3) |
| T3.N | LLM omits required field | Det eval fails on `< 20 chars` or placeholder → retry |
| T3.N | < 3 citations in summary | Det eval fails → retry |
| T4/T5/T6 | LLM produces missing section | LLM judge (Opus) fails → retry |
| T6 | Human rejects approval | `status=needs_human`, loop stops, "Approval denied" logged |
| Any | `attempts >= 3` | `status=needs_human`, loop stops |
| Evaluator | LLM/parse error | Returns `passed=False, next_action=retry` |

## Resume

Crash mid-loop → next `python -m app.main` (no `--goal`) → `load_task_graph()` returns singleton row → loop continues from `pick_next_task`. All `pending` + `failed` tasks (within attempt cap) are eligible.

## Unattended mode

Set `AUTO_APPROVE=1` to skip T6 stdin prompt. With ARXIV_QUERY + AUTO_APPROVE both set, the full T1..T7 chain runs unattended (assuming pango + cairo installed for T7).

## Resume caveat after 2026-05-27

Existing `workspace/agent_state.db` rows hold pre-T7 graphs (T1..T6 only). Resume from those does not add T7. Fresh `--goal` run (after DB delete or `reset_and_run.sh`) emits T7.

## Related

- [[modules/main-harness]]
- [[modules/planner]], [[modules/worker]], [[modules/evaluator]]
- [[modules/sandbox]], [[modules/approval]]
- [[decisions/adr-8-t7-wiring]]
