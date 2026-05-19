---
title: arXiv Client (T1 paper fetcher)
type: module
tags: [arxiv, fetch]
language: python
entry_point: app/arxiv_client.py
updated: 2026-05-20
---

# arXiv Client

T1 implementation. Fetches papers from arXiv when `workspace/papers/` is underfull relative to `--count`.

## Responsibility

Owns: arXiv API interaction + PDF download. Uses `ARXIV_QUERY` env to know what to fetch.

## Public Interface

Called by [[modules/worker]] when executing T1.

```python
from app.arxiv_client import fetch_papers
n_fetched = fetch_papers(query: str, count: int, dest: Path) -> int
```

## Behavior

- Reads `ARXIV_QUERY` if no explicit query passed.
- Skips if `workspace/papers/` already has `count` PDFs.
- Downloads to `workspace/papers/<id>.pdf`.

## Related

- [[modules/worker]] — T1 caller
- [[modules/pdf-tools]] — T2 successor (extracts text from these PDFs)
