---
title: "ADR-3 — Citation verification (fuzzy substring match)"
type: decision
status: superseded
date: 2026-05-20
superseded_by: adr-7-three-tier-citation-verify
sources: [README.md]
updated: 2026-05-27
---

# ADR-3 — Citation verification

## Status

**Superseded by [[decisions/adr-7-three-tier-citation-verify]] (2026-05-27).**

Original framing assumed fuzzy substring + possible Levenshtein. Actual implementation is a 3-tier cascade with no Levenshtein. ADR-7 captures the real mechanism. Keep this page as historical context.

## Context (historical)

LLMs hallucinate quotes routinely. Default-fail evaluator needs a structural check on `summary.citations[]`.

## Decision (original framing — wrong)

- "Normalize whitespace + punctuation + case. Fuzzy substring match. Maybe Levenshtein distance threshold."

## Why superseded

Source (`pdf_tools.py:90`) implements:
1. Whitespace-normalized substring (≥ 8 chars).
2. Alphanumeric-fingerprint substring (≥ 30 chars).
3a. Head(40) + tail(40) fingerprint anchors (≥ 80 fp chars).
3b. 60-char sliding fingerprint window (stride 10, ≥ 60 fp chars).

No edit-distance check anywhere. Mechanism is anchor-and-window based, not distance-based.

## Related

- [[decisions/adr-7-three-tier-citation-verify]] (current)
- [[modules/pdf-tools]]
- [[decisions/adr-2-default-fail-evaluator]]
