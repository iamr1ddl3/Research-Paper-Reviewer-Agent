---
title: T6 approval is stdin-only — blocks unattended runs
type: debt
severity: medium
status: open
filed: 2026-05-20
sources: [app/approval.py]
updated: 2026-05-20
---

# Stdin-only approval blocks unattended long-running

[[modules/approval]] prompts via stdin. Means: when T6 finishes, the process waits for a y/n keystroke. Long arXiv-fetching runs that take 30+ minutes can finish T1-T5 fine and then sit idle waiting for approval at T6.

## Impact

- Not truly long-running unattended.
- Lose the value of resume + checkpoint when blocked on synchronous input.

## Fix sketch

Async approval channel:
- Slack DM: post `FINAL_REPORT.md` excerpt + thumbs-up/thumbs-down reactor.
- Email: link to GitHub issue / form.
- Web hook: hosted approval URL.

Worker writes "awaiting approval" to memory; resume continues T7 once external system marks approved.

## Related

- [[modules/approval]]
- [[decisions/adr-5-human-gate-on-final-report]]
