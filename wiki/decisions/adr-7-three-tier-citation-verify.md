---
title: "ADR-7 — Three-tier citation verification cascade"
type: decision
status: accepted
date: 2026-05-27
supersedes: adr-3-citation-verification
sources: [app/pdf_tools.py]
updated: 2026-05-27
---

# ADR-7 — Three-tier citation verification cascade

## Status

Accepted. Captured retroactively during backtest 2026-05-27. Supersedes [[decisions/adr-3-citation-verification]] which described the intended mechanism incorrectly.

## Context

Worker is instructed to produce ≥ 3 exact verbatim quotes per summary. Evaluator must verify each appears in the source PDF text. Tradeoff space:

- **Too strict (exact match)** → false negatives from PDF whitespace + hyphenation + ligature drift.
- **Too loose (semantic match)** → cannot catch hallucinated citations that don't appear at all.

Need: tolerate extraction-artifact drift, reject true hallucinations.

## Decision

Cascade of 4 increasingly-forgiving checks. `verify_citation(quote, full_text)` returns True on first hit.

| # | Check | Pre-process | Min length |
|---|---|---|---|
| 1 | Substring match | `_normalize_ws` (collapse `\s+`, strip, lower) | quote_norm ≥ 8 chars |
| 2 | Substring match on alphanumeric fingerprint | `_fingerprint` (drop everything non-`[a-z0-9]`) | fp ≥ 30 chars |
| 3a | Head(40)+Tail(40) of fp both present in source fp | fp | fp ≥ 80 chars |
| 3b | Any 60-char contiguous fp window (stride 10) present in source fp | fp | fp ≥ 60 chars |

A quote is **verified** if any tier passes. A quote is **rejected** if all tiers fail OR the normalized form is < 8 chars.

## Rationale per tier

- Tier 1 handles cosmetic whitespace + case drift.
- Tier 2 handles punctuation + hyphenation + ligature drift (`ﬁ` → `fi`, em-dash → minus, etc).
- Tier 3a handles cases where the LLM lightly rephrased the middle but quoted boundaries verbatim.
- Tier 3b handles cases where one or two interior words were swapped but a long verbatim run remains.

## Consequences

**Positive:**
- Real hallucinations (no overlap with source) caught.
- PDF extraction artifacts don't false-negative.
- No external dependency (rapidfuzz, etc).

**Negative:**
- Tier 3b is somewhat permissive — a 60-char window in a 200-char quote is ~30% verbatim. Heavily reworded quotes whose first or last 60 chars happen to appear in source will pass.
- Heuristic thresholds (40/40/60/30/10) are empirical, not tuned.
- No reporting of which tier fired — debugging false positives is harder.

## Alternatives Considered

- **Levenshtein/rapidfuzz**: slower, dependency, threshold tuning nightmare. Rejected.
- **Single normalized substring (tier 1 only)**: too strict for real PDFs. Rejected.
- **Embedding cosine**: defeats the purpose — must be syntactic, not semantic. Rejected.

## Related

- [[modules/pdf-tools]] (`verify_citation`)
- [[modules/evaluator]] (caller)
- [[decisions/adr-3-citation-verification]] (superseded)
- [[decisions/adr-6-column-aware-pdf-extract]] (extract quality dependency)
- [[decisions/adr-2-default-fail-evaluator]]
