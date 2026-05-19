---
name: wiki-write
description: Use this skill to record any change, implementation, or decision into the wiki. Triggers on phrases like "save this to the wiki", "record what we just did", "wiki this change", "log this decision", "ingest this PR", "ingest this module", "ingest this doc", or whenever the user wants to persist new knowledge so it's not lost.
---

# wiki-write

Record a change/implementation/decision into the right wiki page(s) so future sessions don't waste tokens re-explaining context.

## When to use

- Just finished a code change — capture what changed and why
- Ingesting an external source: a PR (`raw/prs/`), design doc (`raw/docs/`), or new code file (`raw/code/`)
- A meaningful decision was made — file an ADR
- New debt was discovered or existing debt was resolved
- A new module/API/data-model/flow now exists

## Steps

1. **Decide page type.** Pick from: module / API / data-model / ADR / debt / flow / scaling / concept. Ask the user if unclear. The triangle: **debt** for problems, **ADR** for decisions, **module/api/data-model/flow** for facts.

2. **Read `wiki/SCHEMAS.md`** for the right template before writing. Never invent a schema.

3. **Write or update the page** at the correct path:
   - `wiki/modules/<name>.md`
   - `wiki/apis/<name>.md`
   - `wiki/data-models/<name>.md`
   - `wiki/decisions/adr-<N>-<slug>.md` (use next ADR number — check `wiki/index.md`)
   - `wiki/debt/<slug>.md`
   - `wiki/flows/<name>.md`
   - `wiki/scaling/<slug>.md`
   - `wiki/concepts/<name>.md`

4. **Update cross-links.**
   - If you wrote a module page, add it to the `Dependents` of any modules it depends on.
   - If you wrote an ADR, link to it from every module it affects.
   - If you wrote a debt page, link from the owning module page.
   - Use `[[wikilinks]]` for every mention of an entity that has its own page.

5. **Update `wiki/index.md`** if you created a new page. Update the per-section count and add a one-line entry.

6. **Append to `wiki/log.md`** (NEVER edit past entries — append only). Format:
   ```
   ## [YYYY-MM-DD] <operation> | <title>

   <1-3 sentence summary>
   Pages touched: page1, page2, ...
   ```
   Valid operations: `ingest-module`, `ingest-pr`, `ingest-doc`, `update`, `analysis`, `map`, `audit`, `lint`, `backtest`, `trace`.

7. **Flag contradictions.** If the new info conflicts with an existing wiki claim, note the tension in both pages explicitly. Do not silently overwrite.

## What good looks like

- Every page follows the schema in `wiki/SCHEMAS.md` exactly.
- Every entity mention is a `[[wikilink]]`, not bare text.
- The debt/ADR/module triangle is fully cross-linked.
- A reader six months from now can reconstruct what happened from the page + the log entry alone.
- The log entry is concise (1-3 sentences). It is NOT a full re-statement of the page.

## What to avoid

- Burying decisions inside a module page instead of filing an ADR.
- Burying known issues inside a module page instead of a debt page.
- Editing past `wiki/log.md` entries (append-only — protected by hook).
- Modifying anything under `raw/` (immutable — protected by hook).
- Over-stuffing pages with prose. Stubs with TL;DR + key sections beat long-but-vague pages.
