# Activity Log

Append-only. Newest entries at top. Never edit past entries.

---

## 2026-05-27 — update | Smoke run + WeasyPrint dyld fix

Ran first end-to-end smoke after the backtest + 4-debt-closure session. Result: T1..T6 all PASS on first attempt; T7 fails on macOS Apple Silicon because pango/cairo dylibs at `/opt/homebrew/lib/` are not on the default `DYLD` search path for Python processes.

### Smoke run

```
T1 PASS (score 100) | T2 PASS (score 100) | fanout T3.1, T3.2 injected
T3.1 PASS (score 100) | T3.2 PASS (score 100)
T4 PASS (score 100) | T5 PASS (score 100)
T6 [AUTO_APPROVE=1] PASS (score 100)
T7 FAIL (will retry, 1/2): FINAL_REPORT.pdf missing
T7 NEEDS HUMAN: FINAL_REPORT.pdf missing (cap=2)
```

Per-task-type cap behavior verified — T7 escalates at cap=2 not cap=3.

### Diagnosis

`brew list pango cairo` shows libs installed. `ls /opt/homebrew/lib/libpango*` confirms presence. But:

```
$ .venv/bin/python -c "from weasyprint import HTML"
# Fails — can't find libgobject etc

$ DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib .venv/bin/python -c "from weasyprint import HTML; print('OK')"
weasyprint OK
```

### Fix

- `run_agent.sh` + `reset_and_run.sh` now `export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}` before invoking `app.main`.
- README §Usage adds a macOS Apple Silicon note + the env var snippet for direct `python -m app.main` callers.

### New debt page

[[debt/weasyprint-dyld-macos]] — LOW, status `mitigated`. Captures the dylib path issue + records the shell-level fix + lists cleaner long-term options (import-time env set, macOS detection).

### Inventory after this update

| | Before | After |
|---|---|---|
| Total maintained pages | 36 | 37 |
| Debt open | 0 | 0 |
| Debt mitigated | 0 | 1 |
| Debt resolved/accepted | 6 | 6 |

Pages touched: log, index, README.md, run_agent.sh, reset_and_run.sh, debt/weasyprint-dyld-macos (new).

## 2026-05-27 — update | Close remaining 4 debt items

Closes the last 4 open debt items from the 2026-05-27 backtest. All 6 backtest-surfaced debt items now closed.

### Changes

**Code:**

1. `app/config.py:27` — `MAX_ATTEMPTS_PER_TASK` made env-tunable (`os.getenv("MAX_ATTEMPTS_PER_TASK", "3")`).
2. `app/config.py:32` — added `_DEFAULT_ATTEMPT_OVERRIDES` (`summarize_paper=5`, `export_pdf=2`).
3. `app/config.py:38` — added `_parse_attempt_overrides` parser for `MAX_ATTEMPTS_BY_TYPE` env (format: `task_type=N,task_type=N`).
4. `app/config.py:53` — composed `MAX_ATTEMPTS_BY_TYPE` dict + `max_attempts_for(task_type)` lookup.
5. `app/main.py:7` — replaced `MAX_ATTEMPTS_PER_TASK` import with `max_attempts_for`.
6. `app/main.py:119` — loop now reads per-task cap; PASS/FAIL log lines show `cap=N` and `attempts/cap`.
7. `.env.example` — documented `AUTO_APPROVE`, `MAX_ATTEMPTS_PER_TASK`, `MAX_ATTEMPTS_BY_TYPE`.

**README:**

8. Architecture section rewritten — planner now correctly described as deterministic; evaluator as two-track; LLM access as OpenAI SDK against OpenRouter.
9. Task Graph table extended with T7.
10. Evaluator rigor section rewritten with two-track + 3-tier citation cascade.
11. Safety section updated with `Path.relative_to`, `AUTO_APPROVE`, env-tunable caps.
12. Files block: every comment updated to match source (was: `llm.py # Anthropic SDK wrapper`; is: `llm.py # OpenAI SDK pointed at OpenRouter`).
13. Output section adds `FINAL_REPORT.pdf` + WeasyPrint system-dep note.

**Wiki:**

14. [[decisions/adr-2-default-fail-evaluator]] reframed as two-track (deterministic default-fail + skeptical-but-fair LLM judge). Explicit rationale: prose tasks have no objective ground truth, strict default-fail LLM rubric would over-reject on style.
15. [[modules/config]], [[modules/main-harness]], [[modules/evaluator]], [[modules/approval]] updated.
16. [[index]] now shows 0 open debt.
17. [[overview]] phases table updated; open questions narrowed to strategic-only (no debt items left).

### Debt closed

- [[debt/llm-wrapper-comment-stale]] — LOW, resolved (README rewrite).
- [[debt/3-attempt-cap-may-be-low]] — LOW, resolved (per-type caps + env override).
- [[debt/evaluator-prompt-vs-adr-2-drift]] — LOW, resolved (ADR-2 reframed; no code change).
- [[debt/no-async-approval]] — MEDIUM→LOW, **accepted**. AUTO_APPROVE is the unattended escape hatch. File-based async gate sketched as future option but not built.

### Smoke verification

```
$ python -c "from app.config import max_attempts_for, MAX_ATTEMPTS_BY_TYPE; ..."
default: 3
by_type: {'summarize_paper': 5, 'export_pdf': 2}
summarize_paper: 5
write_report: 3
export_pdf: 2
```

```
$ python -c "from app.main import _run_one; ..."
main import OK
sandbox escape blocked: Blocked unsafe path access: ../escape
```

### Wiki health after this update

| Metric | Value |
|---|---|
| Total maintained pages | 36 |
| Modules | 12 (1:1 with `app/*.py`) |
| ADRs | 8 (1 superseded) |
| Debt open | 0 |
| Debt resolved/accepted | 6 |

Pages touched: log, index, overview, README.md, app/config.py, app/main.py, .env.example, modules/config, modules/main-harness, modules/evaluator, modules/approval, decisions/adr-2-default-fail-evaluator (reframed), debt/llm-wrapper-comment-stale (resolved), debt/3-attempt-cap-may-be-low (resolved), debt/evaluator-prompt-vs-adr-2-drift (resolved), debt/no-async-approval (accepted).

## 2026-05-27 — update | Wire T7 + harden sandbox path check

Two debt items resolved in one pass.

### Changes (app/)

1. `app/planner.py:91` — appended T7 Task (`task_type="export_pdf"`, deps=["T6"], criteria: FINAL_REPORT.pdf exists + size ≥ 1 KB).
2. `app/worker.py:32` — added `"export_pdf": _export_pdf` to dispatch table.
3. `app/sandbox.py:8` — replaced `str(target).startswith(str(base))` with `target.relative_to(base)` (try/except ValueError). Fixes prefix-collision edge case.

### Debt closed

- [[debt/t7-dispatch-missing]] — HIGH — resolved. T7 now reachable end-to-end.
- [[debt/sandbox-startswith-prefix]] — MEDIUM — resolved. Path containment now pathlib-correct.

### New decisions

- [[decisions/adr-8-t7-wiring]] — recorded keep-vs-remove rationale for T7.

### Wiki updates

- [[modules/planner]], [[modules/worker]], [[modules/sandbox]] — corrected to reflect new code.
- [[architecture/system-map]], [[flows/full-review-run]], [[overview]] — T7 now in pipeline.
- [[data-models/task-graph]] — lifecycle updated (T1..T7).
- [[index]] — ADR count 7→8, debt 4 open + 2 resolved.

### Resume caveat

Existing `workspace/agent_state.db` rows hold the pre-T7 graph (T1..T6). Resume from those does not gain T7. Run `reset_and_run.sh` or `rm workspace/agent_state.db` then fresh `--goal` to pick up T7.

### Tests

No unit tests in repo. Recommended manual smoke:
- `python -m app.main --goal "..." --count 2` (needs OPENROUTER_API_KEY + ARXIV_QUERY + pango/cairo for T7).
- Sandbox containment: `python -c "from app.sandbox import safe_workspace_path; safe_workspace_path('../escape')"` should raise ValueError.

Pages touched: log, index, overview, architecture/system-map, flows/full-review-run, modules/planner, modules/worker, modules/sandbox, data-models/task-graph, decisions/adr-8-t7-wiring (new), debt/t7-dispatch-missing (status→resolved), debt/sandbox-startswith-prefix (status→resolved).

## 2026-05-27 — backtest | Full BACKTEST of initial map vs source

First post-MAP backtest. Read every `app/*.py` file and compared to wiki claims. **Initial map (2026-05-20) was README-derived, not source-derived** — many claims wrong.

### Scorecard

| Pass | Score |
|---|---|
| Structural (lint) | 100% (no broken intra-wiki links) |
| Accuracy spot-check | 25% (5/20 PASS) |
| Coverage | 60% (data-models missing entirely) |
| Q&A fidelity | 20% (1/5) |

### Critical errors corrected

1. [[modules/llm-wrapper]] now correctly states "OpenAI SDK against OpenRouter" (llm.py:5 `from openai import OpenAI`).
2. [[modules/planner]] rewritten — fully deterministic, no LLM call (previous wiki claimed Sonnet call per goal).
3. [[modules/evaluator]] rewritten — deterministic checks for T1/T2/T3.N/T7, LLM judge (Opus) only for T4/T5/T6 (previous wiki implied LLM-always).
4. [[modules/memory]] public interface corrected — exports are init_db/save_task_graph/load_task_graph/save_artifact/save_checkpoint/log_event. `pick_next_task` lives in main.py, not memory.
5. Task status enum corrected: `pending/running/passed/failed/needs_human` (was `pending/in_progress/done/fail/needs_human`).
6. EvaluationResult shape corrected: `{passed: bool, score: int, issues: list, next_action: continue|retry|human_review}` (wiki had `{status: ...}`).
7. [[decisions/adr-3-citation-verification]] superseded by [[decisions/adr-7-three-tier-citation-verify]] — actual mechanism is 3-tier cascade (whitespace-norm + alphanumeric fingerprint + head/tail anchor + 60-char sliding window), no Levenshtein.

### New pages

- **Data models (5):** [[data-models/task]], [[data-models/task-graph]], [[data-models/artifact]], [[data-models/evaluation-result]], [[data-models/paper-summary]]
- **ADRs (2):** [[decisions/adr-6-column-aware-pdf-extract]], [[decisions/adr-7-three-tier-citation-verify]]
- **Debt (3):** [[debt/t7-dispatch-missing]] (HIGH), [[debt/sandbox-startswith-prefix]] (MEDIUM), [[debt/evaluator-prompt-vs-adr-2-drift]] (LOW)
- **Analysis:** [[analyses/backtest-initial-map-2026-05-27]]

### Newly-discovered bug

**T7 (PDF export) is unreachable.** Planner doesn't emit T7 in its static graph. Worker's `_export_pdf` handler exists but isn't in the dispatch table. Evaluator's `_evaluate_pdf` exists but unreachable. README + system-map promised `FINAL_REPORT.pdf` — not produced. See [[debt/t7-dispatch-missing]].

### Sandbox latent bug

`sandbox._safe` uses `str.startswith(str(base))` instead of `target.is_relative_to(base)`. Permits `/foo/project-evil` to pass when base is `/foo/project`. Unexploitable in current single-process app but latent. See [[debt/sandbox-startswith-prefix]].

### Total wiki size

Was 23 pages. Now 35 maintained pages + scaffolding.

### Recommended next

Resolve [[debt/t7-dispatch-missing]] first (broken contract). Then [[debt/sandbox-startswith-prefix]] (one-line fix). Then revisit [[debt/evaluator-prompt-vs-adr-2-drift]].

Pages touched: log, index, overview, architecture/system-map, flows/full-review-run, all 12 modules/*, decisions/adr-3 (status flip), 2 new ADRs, 3 new debt, 5 data-models, analyses/backtest.

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
