# Wiki Page Schemas

Reference for every page type in the wiki. Always consult this file before creating or restructuring a page. Skills (`wiki-write`, `wiki-map`, `wiki-trace`) point here rather than inlining the templates.

---

## Module Page (`wiki/modules/<name>.md`)

```markdown
---
title: <Module Name>
type: module
tags: [backend|frontend|shared|infra|test]
language: typescript|python|go|...
entry_point: src/path/to/entry.ts
sources: [pr-slug, doc-slug]
updated: YYYY-MM-DD
---

# <Module Name>

<2-3 sentence TL;DR: what this module does and why it exists.>

## Responsibility
What this module owns. What it does NOT own (explicit boundary).

## Public Interface
Key exported functions, classes, hooks, or APIs. Be specific about signatures.

## Dependencies
- [[modules/dep-a]] — why this module depends on it
- [[modules/dep-b]] — what it uses from it

## Dependents
- [[modules/consumer-a]] — what it gets from this module

## Data Flow
How data enters and exits this module. Reference [[data-models/]] pages.

## Key Decisions
- Why X was implemented this way (reference [[decisions/adr-N]] if applicable)

## Known Issues / Debt
- Reference [[debt/]] pages for tracked issues

## Related
- [[apis/endpoint]] — API this module exposes
- [[flows/flow-name]] — flow this module participates in
```

---

## API Page (`wiki/apis/<name>.md`)

```markdown
---
title: <API / Endpoint Name>
type: api
tags: [rest|graphql|grpc|websocket|internal|external]
base_path: /api/v1/...
owner: [[modules/owner-module]]
sources: []
updated: YYYY-MM-DD
---

# <API Name>

<TL;DR: what this API does, who calls it, authentication requirements.>

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET    | /resource/:id | ... |

## Request / Response Shape
Key request fields, response fields, error codes.

## Auth & Permissions
Who can call this. What tokens/roles are required.

## Rate Limits & SLAs
Known limits. Expected latency.

## Consumers
- [[modules/x]] — how it uses this API

## Related
- [[data-models/schema]] — data model returned
- [[flows/flow-name]] — flow this API participates in
```

---

## Data Model Page (`wiki/data-models/<name>.md`)

```markdown
---
title: <Entity / Schema Name>
type: data-model
tags: [entity|event|dto|schema|enum]
storage: postgres|redis|s3|in-memory|...
sources: []
updated: YYYY-MM-DD
---

# <Entity Name>

<TL;DR: what this entity represents in the domain.>

## Schema
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id    | uuid | no       | primary key |

## Relationships
- belongs to [[data-models/parent]]
- has many [[data-models/child]]

## Lifecycle
How instances are created, updated, and deleted. Who owns each transition.

## Consumers
Which modules read and write this model.

## Invariants
Business rules that must always hold on this entity.

## Related
```

---

## Architecture Decision Record (`wiki/decisions/adr-<N>-<slug>.md`)

```markdown
---
title: "ADR-N: <Short Title>"
type: decision
status: proposed | accepted | superseded | deprecated
date: YYYY-MM-DD
supersedes: adr-N-old (if applicable)
superseded_by: adr-N-new (if applicable)
sources: []
updated: YYYY-MM-DD
---

# ADR-N: <Short Title>

## Status
Accepted | Proposed | Superseded by [[decisions/adr-N-new]]

## Context
What situation or constraint forced this decision.

## Decision
What was decided. Be concrete.

## Consequences
- **Good:** what this enables
- **Bad:** what this costs or constrains
- **Neutral:** notable side effects

## Alternatives Considered
What else was on the table and why it was rejected.

## Related
```

---

## Flow Page (`wiki/flows/<name>.md`)

```markdown
---
title: <Flow Name>
type: flow
tags: [user-flow|data-flow|event-flow|auth|onboarding|...]
sources: []
updated: YYYY-MM-DD
---

# <Flow Name>

<TL;DR: what this flow accomplishes, who initiates it, what it produces.>

## Trigger
What starts this flow. User action, scheduled job, external event.

## Steps
1. [[modules/a]] receives X → does Y → emits Z
2. [[modules/b]] consumes Z → ...

## Data Involved
- [[data-models/entity]] — how it's read/written at each step

## Error Paths
What can fail. How failures are handled or surfaced.

## Performance Characteristics
Known latency, throughput constraints, caching behaviour.

## Related
```

---

## Technical Debt Page (`wiki/debt/<slug>.md`)

```markdown
---
title: <Debt Item>
type: debt
severity: critical | high | medium | low | resolved
area: [[modules/x]]
created: YYYY-MM-DD
sources: []
updated: YYYY-MM-DD
---

# <Debt Item>

<TL;DR: what the problem is and what it costs.>

## Description
Detailed description of the issue.

## Root Cause
Why this exists.

## Impact
What breaks, slows down, or is blocked because of this.

## Remediation
Proposed fix. Effort estimate. Dependencies.

## Related
```

---

## Scaling Page (`wiki/scaling/<slug>.md`)

```markdown
---
title: <Scaling Topic>
type: scaling
tags: [bottleneck|strategy|capacity|roadmap]
area: [[modules/x]]
sources: []
updated: YYYY-MM-DD
---

# <Scaling Topic>

<TL;DR: what the scaling concern is or what the strategy achieves.>

## Current State
Where the system stands today on this dimension.

## Bottleneck / Opportunity
What limits growth. What the ceiling is.

## Strategy
Proposed or implemented approach. Tradeoffs.

## Milestones
Key thresholds: when to act, what triggers each step.

## Related
```

---

## Concept Page (`wiki/concepts/<name>.md`)

```markdown
---
title: <Concept Name>
type: concept
tags: []
sources: []
updated: YYYY-MM-DD
---

# <Concept Name>

<TL;DR: what this concept is and why it matters for this project.>

## Definition
Clear definition, including what it is NOT.

## How It Works
The mechanism, step by step.

## Tradeoffs
What you gain. What you pay.

## Application in This Project
Where and how this concept appears in the codebase.

## Related
```

---

## Analysis Page (`wiki/analyses/<slug>.md`)

```markdown
---
title: <Analysis Title>
type: analysis
tags: []
sources: []
updated: YYYY-MM-DD
---

# <Analysis Title>

<TL;DR: what this analysis covers and what it found.>

## Context
Why this analysis was done.

## Method
How the analysis was conducted.

## Results
Findings. Tables, numbers, comparisons.

## Conclusions
What to do based on the results.

## Related
```

---

## Conventions (apply to every page)

- **Wikilinks everywhere.** Every mention of a module, API, data-model, flow, ADR, debt item, or concept that has its own page must be a `[[wikilink]]`.
- **Explicit boundaries.** Every module page must state what it does NOT own.
- **Stubs are fine.** A stub page with TL;DR + empty sections is better than no page. Mark stubs with `<!-- stub -->` near the frontmatter.
- **Flag contradictions, never silently overwrite.** If new info conflicts with an existing claim, note the tension explicitly.
- **Cross-link the debt-ADR-module triangle.** Every debt page references its module. Every ADR references the modules it affects. Every module page references its debt and relevant ADRs.
- **Update `wiki/index.md`** whenever a new page is created.
- **Append to `wiki/log.md`** for every wiki change (never edit past entries — append-only).
