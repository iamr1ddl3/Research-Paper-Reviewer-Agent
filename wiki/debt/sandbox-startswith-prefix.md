---
title: Sandbox path check uses str.startswith — prefix-collision risk
type: debt
severity: medium
status: resolved
filed: 2026-05-27
resolved: 2026-05-27
sources: [app/sandbox.py]
updated: 2026-05-27
---

# Sandbox `str.startswith` → `Path.relative_to` — RESOLVED

Surfaced + fixed during backtest 2026-05-27.

## Description (historical)

`sandbox._safe` previously used:

```python
if not str(target).startswith(str(base)):
    raise ValueError(f"Blocked unsafe path access: {relative_path}")
```

Prefix collision: `/foo/project-evil/x` `startswith` `/foo/project` returned True. Sandbox permitted writes outside the intended root.

Unexploitable in production (no `workspace/project-evil/` exists) but latent.

## Resolution

`sandbox.py:8` rewritten to use pathlib semantics:

```python
def _safe(base: Path, relative_path: str) -> Path:
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Blocked unsafe path access: {relative_path}")
    return target
```

`Path.relative_to` raises ValueError when target is not under base. The component-level check rejects sibling directories with shared string prefixes.

ValueError signature + message preserved — callers unaffected.

## Verification

```python
# Before: passed (bug)
# After:  ValueError("Blocked unsafe path access: ...")
safe_workspace_path("../project-evil/x")  # resolved path not under WORKSPACE → blocked
```

## Related

- [[modules/sandbox]]
- [[decisions/adr-4-sandbox-write-restriction]]
