---
title: PDF Tools (column-aware extract + verify + export)
type: module
tags: [pdf, extract, export, citation]
language: python
entry_point: app/pdf_tools.py
updated: 2026-05-27
---

# PDF Tools

Three responsibilities:
1. **Extract** PDF text — column-aware reading order (PyMuPDF primary, pdfplumber fallback).
2. **Verify** citations — 3-tier fuzzy cascade.
3. **Export** FINAL_REPORT.md → FINAL_REPORT.pdf via WeasyPrint.

## Public Interface

```python
from app.pdf_tools import extract_text, extract_metadata, verify_citation, export_pdf
text = extract_text(pdf_path: Path) -> str
meta = extract_metadata(pdf_path: Path) -> dict  # title/author/subject/filename
ok = verify_citation(quote: str, full_text: str) -> bool
export_pdf(md_path: Path, pdf_path: Path) -> Path
```

## Column-aware extraction

PyMuPDF's default `sort=True` flattens by y-coordinate, which interleaves columns on 2-column papers. This module:

1. Calls `page.get_text("blocks")` for raw block coordinates.
2. Computes block-center x spread vs page width.
3. If spread > 35% of page width → 2-column mode: split blocks at midline, read left col top-to-bottom then right col top-to-bottom.
4. Else single-column mode: sort by (y, x).
5. Falls back to pdfplumber on PyMuPDF exception.

See [[decisions/adr-6-column-aware-pdf-extract]].

## Metadata

Reads via pdfplumber. Returns `{title (or pdf stem), author, subject, filename}`.

## Citation verification — 3-tier cascade

`verify_citation(quote, full_text)` returns True if **any** tier matches:

| Tier | Check | Min len |
|---|---|---|
| 1 | Whitespace-normalized substring (`_normalize_ws`: collapse \s+, strip, lower) | ≥ 8 chars |
| 2 | Alphanumeric-fingerprint substring (strip everything non-[a-z0-9]) | ≥ 30 chars fp |
| 3a | Head (first 40) + tail (last 40) of fingerprint both present in source fingerprint | ≥ 80 chars fp |
| 3b | Any 60-char contiguous fingerprint window (stride 10) appears in source fingerprint | ≥ 60 chars fp |

Catches: linebreak collapse, punctuation drift, hyphenation, light paraphrase of middle of quote. See [[decisions/adr-7-three-tier-citation-verify]].

## PDF export

`export_pdf`: markdown → HTML via `markdown` (extras: extra, tables, fenced_code, toc) → PDF via `weasyprint` with embedded CSS (A4, 2cm margins, system font).

Requires system libs pango + cairo (worker reports a hint on failure, worker.py:373).

## Related

- [[modules/worker]] — calls extract_text/extract_metadata (T2), export_pdf (T7 — currently unreachable, see [[debt/t7-dispatch-missing]])
- [[modules/evaluator]] — calls `verify_citation` for summarize_paper checks
- [[decisions/adr-6-column-aware-pdf-extract]]
- [[decisions/adr-7-three-tier-citation-verify]]
