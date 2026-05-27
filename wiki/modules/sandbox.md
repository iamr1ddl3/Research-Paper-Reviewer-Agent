---
title: Sandbox (path-restricted file ops)
type: module
tags: [safety, sandbox]
language: python
entry_point: app/sandbox.py
updated: 2026-05-27
---

# Sandbox

Path-restricted file ops. Two roots — `WORKSPACE` (= `workspace/project/`) for writes/reads, `PAPERS` (= `workspace/papers/`) for read-only paper bytes.

## Responsibility

Owns: file-op safety boundary. Resolves relative paths against the configured root, rejects anything that escapes.

## Path check mechanism

```python
def _safe(base: Path, relative_path: str) -> Path:
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Blocked unsafe path access: {relative_path}")
    return target
```

Uses `Path.relative_to` for component-level containment. Sibling directories with shared string prefixes (`/a/b/proj` vs `/a/b/project-evil`) are correctly rejected. Fixed 2026-05-27 — see [[debt/sandbox-startswith-prefix]].

## Public Interface

```python
from app.sandbox import (
    safe_workspace_path,   # → Path under WORKSPACE
    safe_paper_path,       # → Path under PAPERS
    write_file,            # writes under WORKSPACE only
    read_workspace_file,   # reads under WORKSPACE; returns "" if absent
    read_paper_file,       # reads under PAPERS as bytes
    list_papers,           # sorted list of PAPERS/*.pdf
    list_workspace,        # newline-joined relpaths under WORKSPACE
)
```

## Asymmetric write protection

`write_file` is workspace-only. **There is no write_paper_file.** Worker cannot write into `workspace/papers/` — only [[modules/arxiv-client]] writes there (via raw `result.download_pdf` to absolute path, bypassing sandbox).

## Related

- [[modules/worker]] — primary consumer
- [[modules/evaluator]] — uses `read_workspace_file` + `safe_workspace_path`
- [[decisions/adr-4-sandbox-write-restriction]]
