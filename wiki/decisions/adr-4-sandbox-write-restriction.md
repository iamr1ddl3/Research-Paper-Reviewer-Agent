---
title: ADR-4 — Sandbox writes to workspace/project/ only
type: decision
status: accepted
date: 2026-05-20
sources: [README.md, app/sandbox.py]
updated: 2026-05-20
---

# ADR-4 — Sandbox restricts worker writes

## Status

Accepted.

## Context

LLM agents can be prompt-injected or hallucinate dangerous file paths. Without structural restriction, a poisoned PDF could trick the worker into writing to `~/.ssh/authorized_keys` or `.bashrc`.

## Decision

All worker file writes go through [[modules/sandbox]]. Writes outside `workspace/project/` are rejected at the sandbox boundary.

## Consequences

**Positive:**
- Structural guarantee — not policy.
- Quality issues caught by evaluator; safety issues caught here.

**Negative:**
- Inflexible — if a future task legitimately needs to write outside workspace, sandbox must be extended.

## References

- README §"Safety"
- `app/sandbox.py`

## Related

- [[modules/sandbox]]
- [[modules/worker]]
