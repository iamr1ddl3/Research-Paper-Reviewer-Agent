---
title: Sandbox (path-restricted file ops)
type: module
tags: [safety, sandbox]
language: python
entry_point: app/sandbox.py
updated: 2026-05-20
---

# Sandbox

Path-restricted file operations. Worker writes go through this — restricted to `workspace/project/` subtree.

## Responsibility

Owns: file-op safety. Prevents the agent (even if hallucinating / prompt-injected) from writing outside the project workspace.

## Why this matters

Without sandbox: LLM could be tricked into writing to `~/.ssh/`, `~/.bash_profile`, etc. Default-fail evaluator catches *quality* issues but not all *destructive* issues. Sandbox is the structural guarantee.

## Public Interface

```python
from app.sandbox import write_file, read_file, list_dir
write_file("workspace/project/foo.md", content)  # OK
write_file("/etc/passwd", content)              # ERROR
write_file("../../../something", content)        # ERROR (resolves outside workspace)
```

## Path resolution

Probably: resolves to absolute path → checks `is_relative_to(workspace_root)` → reject if not. (Read source for exact mechanics.)

## Related

- [[modules/worker]] — sole consumer
- [[decisions/adr-4-sandbox-write-restriction]]
