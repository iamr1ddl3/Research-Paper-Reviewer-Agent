---
title: ADR-5 — Human approval gate on T6 (final report)
type: decision
status: accepted
date: 2026-05-20
sources: [README.md, app/approval.py]
updated: 2026-05-20
---

# ADR-5 — Human gate on T6

## Status

Accepted.

## Context

T6 writes the final synthesized report. Most expensive task to redo (long context, lots of LLM output). Also the artifact a user will share.

If the report is wrong, redoing it is costly. Catching errors before T7 (PDF export) costs nothing.

## Decision

After T6 produces `FINAL_REPORT.md`, [[modules/approval]] prompts the human (interactive stdin). y → continue to T7. n → escalate.

## Consequences

**Positive:**
- Worst-case errors caught.
- Long-running run gains a meaningful checkpoint.
- Human stays in the loop on the artifact that matters most.

**Negative:**
- Not fully unattended — long runs need someone at the keyboard at the end.
- No async / web approval — stdin-only.

## Possible extension

A future async approval channel (e.g., Slack DM, email link) would unblock truly unattended runs. Currently stdin-only.

## References

- README §"Safety"
- `app/approval.py`

## Related

- [[modules/approval]]
- [[modules/worker]] (T6)
