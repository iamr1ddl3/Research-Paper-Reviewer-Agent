# Activity Log

Append-only. Newest entries at top. Never edit past entries.

---

## 2026-05-19 — wiki initialized

- Bootstrapped via `init-wiki-skeleton`.
- Project: Research-Paper-Reviewer-Agent.
- Next: run "map this codebase" in Claude Code.

## 2026-05-20 — map | Initial wiki-map of Research-Paper-Reviewer-Agent

Long-running AI agent project. README + source structure made this a clean full-depth map.

Identified 12 modules + 1 flow + 5 ADRs + 3 debt.

KEY FINDING: Strong overlap with [[../../AI Agent Roadmap/wiki/modules/codeorch]] — both projects independently arrived at the Planner / Worker / Evaluator pattern with externalized state + default-fail evaluator + Sonnet/Opus split. Pattern belongs in [[../../wiki/ai-ml/concepts/]] as reusable lore.

Pages touched (created):
- architecture/system-map
- overview
- index (full ToC)
- modules/{main-harness, planner, worker, evaluator, approval, memory, sandbox, llm-wrapper, schemas, arxiv-client, pdf-tools, config}
- flows/full-review-run
- decisions/{adr-1-planner-worker-evaluator-pattern, adr-2-default-fail-evaluator, adr-3-citation-verification, adr-4-sandbox-write-restriction, adr-5-human-gate-on-final-report}
- debt/{no-async-approval, llm-wrapper-comment-stale, 3-attempt-cap-may-be-low}

Workspace already contains evidence of real runs (T1-T6 artifacts, comparison.md, patterns.md, FINAL_REPORT.md, 2 sample papers).

5 important questions:
1. Async approval channel (Slack/email) to unblock unattended runs?
2. Update README comment for llm.py (says Anthropic; actually OpenRouter)?
3. Tune 3-attempt cap per task type?
4. Promote Planner/Worker/Evaluator pattern to ai-ml central hub concept?
5. PDF extraction quality under math/multi-column papers (citation verify dep)?

Recommended next: invoke `wiki-maintain` backtest.

Pages touched: log
