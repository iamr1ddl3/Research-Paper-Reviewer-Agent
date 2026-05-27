---
title: arXiv Client (T1 paper fetcher)
type: module
tags: [arxiv, fetch]
language: python
entry_point: app/arxiv_client.py
updated: 2026-05-27
---

# arXiv Client

Thin wrapper over the `arxiv` PyPI package. Single function. Called by worker `_collect_papers` when local PDFs < PAPER_COUNT and `ARXIV_QUERY` is non-empty.

## Public Interface

```python
from app.arxiv_client import fetch_papers
paths = fetch_papers(query: str, count: int, dest_dir: Path) -> list[Path]
```

## Behavior

- `arxiv.Search(query=, max_results=count, sort_by=Relevance)`.
- `arxiv.Client(page_size=count, delay_seconds=3, num_retries=3)`.
- For each result: slug = `entry_id.rsplit('/', 1)[-1].replace('.', '_')`, filename = `<slug>.pdf`.
- Skips existing files (idempotent).
- Calls `result.download_pdf(dirpath=, filename=)` — writes to `workspace/papers/` directly.

## Sandbox bypass note

This module writes to `PAPERS_DIR` (i.e. `workspace/papers/`) via the upstream `arxiv` library's `download_pdf`, **not** through [[modules/sandbox]]. Sandbox is workspace-write-only by design; paper downloads are paper-write. Trust boundary: arxiv-client is trusted infrastructure code, not LLM-emitted code.

## Related

- [[modules/worker]] — T1 caller (`_collect_papers`)
- [[modules/pdf-tools]] — T2 successor (extracts text from these PDFs)
