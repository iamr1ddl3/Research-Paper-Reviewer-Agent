---
title: ADR-3 — Citation verification (fuzzy substring match)
type: decision
status: accepted
date: 2026-05-20
sources: [README.md]
updated: 2026-05-20
---

# ADR-3 — Citation verification

## Status

Accepted. Specific mechanism inside the default-fail evaluator.

## Context

LLMs hallucinate quotes routinely — especially on technical papers where exact wording matters. Without checking, a summary's `citations[]` is often fabricated.

## Decision

For every quote in `summary.citations[]`:
1. Normalize whitespace + punctuation + case in both the quote and the source PDF text.
2. Fuzzy substring match against normalized source text.
3. If no match → fail with reason `citation_not_found: "<quote excerpt>"`.

Worker retries up to 3 times.

## Consequences

**Positive:**
- Fabricated citations caught.
- Forces worker to quote real text (or omit citations).
- Trust in final report's evidence chain.

**Negative:**
- Fuzzy normalization isn't perfect — true positives may slip through with heavy edits.
- Whitespace + hyphenation in PDF text extract may cause false negatives (PDF "long-running" → text "longrunning" or "long running").
- Worker may produce summaries with no citations to avoid the check.

## Implementation notes

- Use `unicodedata.normalize` + collapse whitespace + strip punctuation.
- Substring match (don't require exact alignment).
- Maybe Levenshtein distance threshold for short citations.

## References

- README §"Evaluator rigor"

## Related

- [[modules/evaluator]]
- [[modules/pdf-tools]] — source text extractor
- [[decisions/adr-2-default-fail-evaluator]]
