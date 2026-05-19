---
title: Full Review Run (end-to-end flow)
type: flow
trigger: python -m app.main --goal "..." --count N
updated: 2026-05-20
---

# Full Review Run

End-to-end pipeline from user goal to final PDF report.

## Trigger

```bash
python -m app.main --goal "Review papers on LLM agent architectures" --count 3
```

## Sequence

```
USER goal + count
  ↓
[main.py] init_or_load_task_graph(goal, count)
  ↓
[planner.py] LLM call (Sonnet) → constructs T1, T2, T3.1, T3.2, T3.3, T4, T5, T6, T7
  ↓
[memory.py] persists graph to SQLite
  ↓
HARNESS LOOP:
  ┌─ pick_next_task()
  │    ↓
  │  task = T1 collect
  │    ↓ worker.run(task)
  │    ↓ if workspace/papers/ underfull: arxiv_client.fetch_papers()
  │    ↓
  │  evaluator.judge() → pass
  │  memory.mark_done(T1), checkpoint
  │    ↓
  │  task = T2 extract
  │    ↓ worker.run() → pdf_tools.extract_text + meta
  │  evaluator → pass; checkpoint
  │    ↓
  │  task = T3.1 summarize
  │    ↓ worker.run() → LLM(paper.txt → summary.json)
  │    ↓ summary.json validated against Pydantic schema
  │  evaluator → schema-validate + verify citations exist in paper.txt
  │    ├─ pass: mark done
  │    └─ fail: retry (max 3)
  │    ↓
  │  task = T3.2 summarize, T3.3 summarize ...
  │    ↓
  │  task = T4 compare → comparison.md
  │  task = T5 patterns → patterns.md
  │  task = T6 final report → FINAL_REPORT.md
  │    ↓ approval.prompt(user)
  │    ├─ approved: continue
  │    └─ rejected: escalate
  │    ↓
  │  task = T7 export → FINAL_REPORT.pdf
  │    ↓
  └─ all done → exit
```

## Output artifacts

| Path | Producer |
|---|---|
| `workspace/papers/*.pdf` | T1 |
| `workspace/project/papers/<id>/raw.txt` + `meta.json` | T2 |
| `workspace/project/papers/<id>/summary.json` | T3.N |
| `workspace/project/comparison.md` | T4 |
| `workspace/project/patterns.md` | T5 |
| `workspace/project/FINAL_REPORT.md` | T6 (after human approval) |
| `workspace/project/FINAL_REPORT.pdf` | T7 |
| `workspace/artifacts/T*.md` | per-task handoff notes |

## Failure modes

| Stage | Failure | Behavior |
|---|---|---|
| Planner | LLM returns malformed graph | Pydantic validation throws |
| Worker T1 | arXiv rate limit / network | T1 fails, retried up to 3× |
| Worker T2 | PDF extraction error | Task fails, escalate after 3 attempts |
| Worker T3.N | LLM hallucinates citation | Evaluator catches (citation not in source) → fail → retry |
| Worker T3.N | Required field missing | Evaluator schema-fail → retry |
| Worker T6 | Human rejects approval | Task escalated |
| Evaluator | Opus API error | Verdict fails → worker retries |

## Resume

Crash anywhere → next `python -m app.main` reloads SQLite graph → resumes from `pick_next_task()`.

## Related

- [[modules/main-harness]]
- [[modules/planner]], [[modules/worker]], [[modules/evaluator]]
- [[modules/sandbox]], [[modules/approval]]
