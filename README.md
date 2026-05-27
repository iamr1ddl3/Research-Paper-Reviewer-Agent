# Research Paper Reviewer Agent

Long-running AI agent that reviews research papers and produces a final technical report (Markdown + PDF). Built on the Planner → Worker → Evaluator harness pattern with SQLite checkpointing and resume.

## Architecture

```
Goal ──> Planner ──> Task Graph (T1..T7) ──> SQLite
                            │
                            ▼
                  ┌─── Harness Loop ───┐
                  │  pick_next_task    │
                  │  worker.run(task)  │
                  │  evaluator.judge() │
                  │  checkpoint()      │
                  └────────────────────┘
```

- **Planner** (deterministic, no LLM): goal → T1–T7 task graph.
- **Worker** (Sonnet via OpenRouter): runs one task at a time, writes artifacts.
- **Evaluator** (deterministic checks for file-producing tasks; Opus via OpenRouter for content tasks): required-fields + 3-tier citation verification.
- **Harness**: loops until done, stuck, or needs human approval.

LLM access goes through OpenRouter using the OpenAI-compatible endpoint via the `openai` Python SDK. Swap models via `WORKER_MODEL` / `EVALUATOR_MODEL` in `.env`. (`PLANNER_MODEL` is read but unused — planner is deterministic.)

## Setup

```bash
cd Research-Paper-Reviewer-Agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then add OPENROUTER_API_KEY
```

## Usage

### Option A: Local PDFs
Drop PDFs into `workspace/papers/`, then:
```bash
python -m app.main --goal "Review papers on LLM agent architectures" --count 3
```

### Option B: arXiv fetch
Set `ARXIV_QUERY` in `.env`, then:
```bash
python -m app.main --goal "Review long-running AI agent papers" --count 5
```
If `workspace/papers/` has fewer than `--count` PDFs, T1 fetches the rest from arXiv.

### Resume
```bash
python -m app.main   # no --goal; reloads existing task graph
```

## Output

- `workspace/project/papers/<id>/summary.json` — structured summary per paper
- `workspace/project/comparison.md` — method comparison
- `workspace/project/patterns.md` — repeated architecture patterns
- `workspace/project/FINAL_REPORT.md` — synthesized report
- `workspace/project/FINAL_REPORT.pdf` — PDF export (requires `pango` + `cairo` system libs for WeasyPrint; on macOS: `brew install pango cairo`)
- `workspace/artifacts/T*.md` — per-task handoff artifacts

## Task Graph

| ID | Title | Output |
|---|---|---|
| T1 | Collect papers | `workspace/papers/*.pdf` + `paper_index.json` |
| T2 | Extract text + metadata | `workspace/project/papers/<id>/raw.txt`, `meta.json` |
| T3.N | Summarize paper N | `papers/<id>/summary.json` |
| T4 | Compare methods | `comparison.md` |
| T5 | Identify patterns | `patterns.md` |
| T6 | Write final report (needs approval) | `FINAL_REPORT.md` |
| T7 | Export PDF | `FINAL_REPORT.pdf` |

## Evaluator rigor

- **Deterministic checks** for file-producing tasks (T1, T2, T3.N, T7): file existence, schema validation, required-field non-empty checks.
- **Required fields per summary**: `method`, `dataset`, `results`, `limitations`, `implementation_notes` — each non-empty, not a placeholder ("N/A"/"none"/"unknown"/"tbd"), ≥ 20 chars.
- **Citation verification**: ≥ 3 quotes per summary, each verified via a 3-tier fuzzy cascade (whitespace-normalized substring → alphanumeric fingerprint → head/tail anchor + 60-char sliding window) against column-aware extracted PDF text. Fabricated quotes → fail.
- **LLM judge** (Opus) for content tasks (T4, T5, T6) with a "skeptical but fair" prompt.

## Safety

- Worker file ops restricted to `workspace/project/` via `Path.relative_to` containment.
- T6 requires interactive human approval (stdin TTY), with `AUTO_APPROVE=1` env override for unattended runs.
- Max attempts per task: `MAX_ATTEMPTS_BY_TYPE` env-tunable per task type (defaults: 5 for `summarize_paper`, 3 for everything else). After that → `needs_human`.

## Files

```
app/
  config.py            # env + paths + per-task attempt caps
  llm.py               # OpenAI SDK pointed at OpenRouter
  schemas.py           # Pydantic models
  memory.py            # SQLite state (task_graph, artifacts, checkpoints, events)
  sandbox.py           # path-restricted file ops (Path.relative_to containment)
  planner.py           # deterministic static T1..T7 task graph
  worker.py            # task-type dispatcher
  evaluator.py         # deterministic checks + LLM judge + 3-tier citation verify
  approval.py          # T6 gate (stdin + AUTO_APPROVE env)
  arxiv_client.py      # arXiv fetch
  pdf_tools.py         # column-aware PDF extract + WeasyPrint export
  main.py              # harness loop (pick → approve → run → evaluate → checkpoint)
```
