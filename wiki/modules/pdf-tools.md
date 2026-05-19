---
title: PDF Tools (extract + export)
type: module
tags: [pdf, extract, export]
language: python
entry_point: app/pdf_tools.py
updated: 2026-05-20
---

# PDF Tools

Two responsibilities:
1. **T2: Extract** PDF text + metadata for downstream summarization.
2. **T7: Export** `FINAL_REPORT.md` → `FINAL_REPORT.pdf`.

## Public Interface

```python
from app.pdf_tools import extract_text, extract_metadata, export_pdf
```

## Likely libraries

- Text extract: `pypdf` / `pdfplumber` / `pymupdf`.
- Markdown → PDF export: `weasyprint` / `markdown-pdf` / shell out to `pandoc`.

(Exact choice not verified — read app/pdf_tools.py for canonical.)

## Used in citation verification

The text extracted in T2 is what [[modules/evaluator]] uses to verify citations in summaries. Fuzzy-normalized substring match between citation quote and PDF text → fabricated quotes caught.

## Related

- [[modules/worker]] — T2 + T7 caller
- [[modules/evaluator]] — citation verification source
- [[modules/arxiv-client]] — T1 predecessor
