---
title: "ADR-6 — Column-aware PDF text extraction"
type: decision
status: accepted
date: 2026-05-27
sources: [app/pdf_tools.py]
updated: 2026-05-27
---

# ADR-6 — Column-aware PDF text extraction

## Status

Accepted. Captured retroactively during backtest 2026-05-27.

## Context

Academic papers are routinely 2-column. PyMuPDF's default `sort=True` flattens text blocks by y-coordinate — this interleaves left + right columns into a single reading order. For citation verification, interleaved text means a verbatim quote in the PDF appears split or reordered in the extracted text, and the substring match in [[decisions/adr-7-three-tier-citation-verify]] fails.

Citation verify is upstream-dependent on extract quality.

## Decision

`pdf_tools._extract_page_columnar` (pdf_tools.py:12):

1. Pull raw blocks via `page.get_text("blocks")`.
2. Compute spread of block-center x-coords vs page width.
3. If spread > 35% of page width → 2-column mode: partition at page midline, read left column top-to-bottom then right column top-to-bottom.
4. Else single-column: sort by (y, x).

Falls back to pdfplumber-per-page extraction on PyMuPDF exception.

## Consequences

**Positive:**
- Verbatim quote spans survive extraction for 2-column papers.
- Citation verify rate goes up.

**Negative:**
- Heuristic threshold (35%) is empirical, not principled. Edge cases: full-width figures with text annotations on both sides could be miscategorized.
- 3-column layouts (rare in CS papers) are not handled.
- Block-center midline split fails on asymmetric column widths.

## Alternatives Considered

- **pdfplumber primary**: slower, weaker on math-heavy papers; kept as fallback.
- **PyMuPDF default sort**: documented to interleave columns — rejected.
- **Custom column detector via clustering on x-coords**: more accurate but adds dependency + complexity. Punted.

## Related

- [[modules/pdf-tools]]
- [[decisions/adr-7-three-tier-citation-verify]]
- [[modules/evaluator]] (downstream consumer of extract quality)
