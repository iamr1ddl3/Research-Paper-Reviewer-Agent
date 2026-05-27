---
title: T6 approval is stdin-only — partial answer via AUTO_APPROVE env
type: debt
severity: low
status: accepted
filed: 2026-05-20
updated: 2026-05-27
sources: [app/approval.py]
---

# Stdin approval — accepted limitation, AUTO_APPROVE is the unattended escape hatch

Downgraded from MEDIUM to LOW and status `open` → `accepted` on 2026-05-27. No code change — the design is intentional.

## Current behavior

`approval.request_approval` (app/approval.py:11):

```python
if AUTO_APPROVE=1:        return True
elif not stdin.isatty():  return False
else:                     interactive y/n prompt on stdin
```

Three modes:
- **Interactive** (default): human types yes/no.
- **Unattended trusted** (`AUTO_APPROVE=1`): T6 auto-approved, full pipeline runs hands-off.
- **Unattended untrusted** (no TTY, no AUTO_APPROVE): denied, task escalates to `needs_human`, loop stops.

## Why this is fine for now

- **Coverage is binary by design.** Either a human supervises (interactive) or the run is trusted enough to skip review (AUTO_APPROVE). Adding a third "human will check later, but not in front of the terminal right now" mode requires real infrastructure (Slack / email / webhook) and isn't blocking any current use case.
- **AUTO_APPROVE is logged.** When set, approval.py prints `[AUTO_APPROVE=1] Auto-approving T6: ...` — auditable in stdout + workspace/logs.
- **Evaluator catches the failure modes that matter.** Required-fields + 3-tier citation verify catch the most-damaging T6 outputs (fabricated quotes, empty sections) before T6 even produces an artifact for approval.

## Future option: file-based async gate

If real async approval is later needed, the cheapest path is a file-based gate:

1. Harness writes `workspace/approvals/<task_id>.pending` and returns False from `request_approval` (instead of escalating to `needs_human`).
2. External system (cron, Slack bot, webhook handler) reads pending file, sends review somewhere, drops `<task_id>.approved` or `<task_id>.rejected` when human responds.
3. Resume loop polls for `.approved` file on next pick.

~30 lines. Not built today.

## Related

- [[modules/approval]]
- [[decisions/adr-5-human-gate-on-final-report]]
