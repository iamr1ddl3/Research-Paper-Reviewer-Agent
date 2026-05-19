---
title: Max 3 attempts per task — may be tight for hard summaries
type: debt
severity: low
status: open
filed: 2026-05-20
sources: [README.md, app/main.py]
updated: 2026-05-20
---

# 3-attempt cap may escalate too easily

README §"Safety" — "Max 3 attempts per task; after that → `needs_human`."

For some papers (math-heavy, unusual structure, OCR-quality issues), 3 retries may not be enough for evaluator to pass. Escalates to human even when an additional retry would have worked.

## Impact

- More human gate triggers than necessary.
- Loses the unattended-run thesis on edge-case papers.

## Fix sketch

- Increase cap to 5 for low-stakes tasks (T3.N summarize).
- Keep at 3 for T6 (high-stakes, expensive).
- Add backoff jitter — retry with slight temperature increase or prompt variation.

## Related

- [[modules/main-harness]]
- [[modules/evaluator]]
