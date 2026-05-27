import json
import re
from pathlib import Path

from app.config import (
    PAPER_COUNT,
    ARXIV_QUERY,
    PAPERS_DIR,
    WORKER_MODEL,
    REPORT_MAX_TOKENS,
)
from app.llm import call_llm, call_llm_json
from app.sandbox import (
    list_papers,
    safe_workspace_path,
    write_file,
    read_workspace_file,
)
from app.schemas import Task, Artifact, PaperSummary
from app import pdf_tools, arxiv_client


def run_worker(task: Task) -> Artifact:
    dispatch = {
        "collect_papers": _collect_papers,
        "extract_text": _extract_text,
        "summarize_fanout": _fanout_placeholder,
        "summarize_paper": _summarize_paper,
        "compare_methods": _compare_methods,
        "identify_patterns": _identify_patterns,
        "write_report": _write_report,
        "export_pdf": _export_pdf,
    }
    handler = dispatch.get(task.task_type)
    if handler is None:
        return Artifact(
            task_id=task.id,
            changed="",
            failed=f"Unknown task_type: {task.task_type}",
            remaining="Add a handler in worker.py dispatch table",
            evidence="",
        )
    return handler(task)


def _paper_id_from_path(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", path.stem)


def _collect_papers(task: Task) -> Artifact:
    existing = list_papers()
    needed = max(0, PAPER_COUNT - len(existing))
    fetched: list[Path] = []
    failed_msg = ""

    if needed > 0:
        if not ARXIV_QUERY:
            return Artifact(
                task_id=task.id,
                changed="",
                failed=(
                    f"Need {needed} more papers but ARXIV_QUERY is empty. "
                    f"Either drop {needed} PDFs into workspace/papers/ or set ARXIV_QUERY in .env."
                ),
                remaining=f"Acquire {needed} more papers",
                evidence=f"Found {len(existing)} local PDFs; PAPER_COUNT={PAPER_COUNT}",
            )
        try:
            fetched = arxiv_client.fetch_papers(ARXIV_QUERY, needed, PAPERS_DIR)
        except Exception as e:
            failed_msg = f"arXiv fetch failed: {e}"

    final = list_papers()[:PAPER_COUNT]
    index = [
        {
            "id": _paper_id_from_path(p),
            "filename": p.name,
            "source": "local" if p in existing else "arxiv",
        }
        for p in final
    ]
    write_file("paper_index.json", json.dumps(index, indent=2))

    if len(final) < PAPER_COUNT:
        return Artifact(
            task_id=task.id,
            changed=f"Wrote paper_index.json with {len(final)} papers",
            failed=failed_msg or f"Only {len(final)}/{PAPER_COUNT} papers collected",
            remaining=f"Acquire {PAPER_COUNT - len(final)} more papers",
            evidence=f"workspace/papers/ count={len(final)}",
        )

    return Artifact(
        task_id=task.id,
        changed=(
            f"Collected {len(final)} papers ({len(fetched)} from arXiv, "
            f"{len(final) - len(fetched)} local). Wrote paper_index.json."
        ),
        failed=failed_msg,
        remaining="",
        evidence=f"workspace/papers/ has {len(final)} PDFs; paper_index.json lists them",
    )


def _extract_text(task: Task) -> Artifact:
    index_raw = read_workspace_file("paper_index.json")
    if not index_raw:
        return Artifact(
            task_id=task.id,
            changed="",
            failed="paper_index.json missing — T1 must run first",
            remaining="Run T1",
            evidence="",
        )
    index = json.loads(index_raw)
    processed: list[str] = []
    failures: list[str] = []
    for entry in index:
        pid = entry["id"]
        pdf_path = PAPERS_DIR / entry["filename"]
        try:
            text = pdf_tools.extract_text(pdf_path)
            meta = pdf_tools.extract_metadata(pdf_path)
            write_file(f"papers/{pid}/raw.txt", text)
            write_file(f"papers/{pid}/meta.json", json.dumps(meta, indent=2))
            processed.append(pid)
        except Exception as e:
            failures.append(f"{pid}: {e}")
    return Artifact(
        task_id=task.id,
        changed=f"Extracted text + metadata for {len(processed)} papers",
        failed="; ".join(failures),
        remaining="",
        evidence=f"papers/<id>/raw.txt + meta.json for: {', '.join(processed)}",
    )


def _fanout_placeholder(task: Task) -> Artifact:
    return Artifact(
        task_id=task.id,
        changed="Fan-out subtasks will be created by the harness after T2 passes",
        failed="",
        remaining="",
        evidence="Placeholder task; harness handles T3.N injection",
    )


SUMMARIZE_SYSTEM = """You are the worker in a long running AI agent harness.

Your job: produce a structured summary of one research paper.

Rules:
1. Read the provided raw text carefully.
2. Fill every required field with concrete, paper-specific content. Never leave a field empty or write "N/A".
3. citations[] must contain at least 3 EXACT VERBATIM quotes (30-200 chars each) copied character-for-character from the raw text. Do not paraphrase. Do not summarize. Do not combine sentences. Pick uninterrupted spans of text that appear literally in the raw text. Quotes are programmatically verified — any deviation (rewording, punctuation change, line-break collapse) WILL fail evaluation.
4. Return ONLY valid JSON matching this exact shape:
{
  "paper_id": "string",
  "title": "string",
  "authors": ["string"],
  "method": "string (>= 2 sentences describing the technical approach)",
  "dataset": "string (datasets, benchmarks, or experimental setup)",
  "results": "string (key quantitative + qualitative results)",
  "limitations": "string (limitations stated by authors or evident from the work)",
  "implementation_notes": "string (architecture details, libraries, hyperparameters, reproducibility notes)",
  "citations": ["exact verbatim quote 1", "exact verbatim quote 2", "exact verbatim quote 3"]
}
"""


def _summarize_paper(task: Task) -> Artifact:
    pid = task.paper_id
    if not pid:
        return Artifact(
            task_id=task.id, changed="", failed="task.paper_id missing",
            remaining="", evidence=""
        )
    raw = read_workspace_file(f"papers/{pid}/raw.txt")
    meta_raw = read_workspace_file(f"papers/{pid}/meta.json")
    if not raw:
        return Artifact(
            task_id=task.id, changed="",
            failed=f"raw.txt missing for {pid} — T2 must run first",
            remaining="Run T2", evidence=""
        )
    meta = json.loads(meta_raw) if meta_raw else {}
    truncated = raw[:60000]
    prompt = (
        f"Paper id: {pid}\n"
        f"Metadata: {json.dumps(meta)}\n\n"
        f"Raw text (may be truncated):\n{truncated}\n\n"
        "Produce the summary JSON now."
    )
    try:
        data = call_llm_json(SUMMARIZE_SYSTEM, prompt, WORKER_MODEL)
        data["paper_id"] = pid
        summary = PaperSummary.model_validate(data)
    except Exception as e:
        return Artifact(
            task_id=task.id, changed="",
            failed=f"LLM/parse error: {e}",
            remaining="Retry summarization",
            evidence=""
        )
    write_file(
        f"papers/{pid}/summary.json",
        summary.model_dump_json(indent=2),
    )
    return Artifact(
        task_id=task.id,
        changed=f"Wrote papers/{pid}/summary.json",
        failed="",
        remaining="",
        evidence=(
            f"Fields filled: method({len(summary.method)} chars), "
            f"dataset({len(summary.dataset)}), results({len(summary.results)}), "
            f"limitations({len(summary.limitations)}), "
            f"implementation_notes({len(summary.implementation_notes)}), "
            f"citations={len(summary.citations)}"
        ),
    )


def _load_all_summaries() -> list[dict]:
    index_raw = read_workspace_file("paper_index.json")
    if not index_raw:
        return []
    index = json.loads(index_raw)
    out: list[dict] = []
    for entry in index:
        sj = read_workspace_file(f"papers/{entry['id']}/summary.json")
        if sj:
            out.append(json.loads(sj))
    return out


COMPARE_SYSTEM = """You are the worker in a long-running AI agent harness.

Produce comparison.md (markdown) comparing methods across the provided paper summaries.

Required sections (use these exact H2 headers):
## Method Comparison
## Dataset Overlap
## Notable Disagreements

Rules:
- Reference each paper by id (e.g. [P1234]).
- Cite specific claims from the summaries; do not invent.
- Return ONLY the markdown content (no JSON, no code fences around the whole doc).
"""


def _compare_methods(task: Task) -> Artifact:
    summaries = _load_all_summaries()
    if not summaries:
        return Artifact(
            task_id=task.id, changed="",
            failed="No summaries found", remaining="Run T3.N", evidence=""
        )
    prompt = "Paper summaries:\n\n" + json.dumps(summaries, indent=2)
    md = call_llm(COMPARE_SYSTEM, prompt, WORKER_MODEL)
    write_file("comparison.md", md)
    return Artifact(
        task_id=task.id,
        changed="Wrote comparison.md",
        failed="",
        remaining="",
        evidence=f"comparison.md length={len(md)} chars; covers {len(summaries)} papers",
    )


PATTERNS_SYSTEM = """You are the worker in a long-running AI agent harness.

Produce patterns.md identifying architectural patterns that recur across two or more papers.

Format:
## <Pattern Name>
- Papers: [P1234], [P5678]
- Description: ...
- Variations: ...

Rules:
- Every pattern must cite at least 2 paper ids.
- Only include patterns with concrete evidence in the summaries or comparison.
- Return ONLY markdown.
"""


def _identify_patterns(task: Task) -> Artifact:
    summaries = _load_all_summaries()
    comparison = read_workspace_file("comparison.md")
    if not summaries or not comparison:
        return Artifact(
            task_id=task.id, changed="",
            failed="Missing summaries or comparison.md",
            remaining="Run prior tasks", evidence=""
        )
    prompt = (
        "Summaries:\n" + json.dumps(summaries, indent=2) +
        "\n\nComparison:\n" + comparison
    )
    md = call_llm(PATTERNS_SYSTEM, prompt, WORKER_MODEL)
    write_file("patterns.md", md)
    return Artifact(
        task_id=task.id,
        changed="Wrote patterns.md",
        failed="",
        remaining="",
        evidence=f"patterns.md length={len(md)} chars",
    )


REPORT_SYSTEM = """You are the worker in a long-running AI agent harness.

Produce FINAL_REPORT.md — a synthesized technical report on the reviewed papers.

Required H1 title, then H2 sections in this order:
## Overview
## Per-paper Summaries
## Method Comparison
## Architecture Patterns
## Open Questions

Rules:
- Cite every paper id at least once.
- Per-paper Summaries: one subsection per paper with method/dataset/results/limitations.
- Method Comparison and Architecture Patterns: condense from comparison.md and patterns.md.
- Open Questions: 3-6 concrete unresolved questions the reviewed work raises.
- Return ONLY the markdown content.
"""


def _write_report(task: Task) -> Artifact:
    summaries = _load_all_summaries()
    comparison = read_workspace_file("comparison.md")
    patterns = read_workspace_file("patterns.md")
    if not summaries or not comparison or not patterns:
        return Artifact(
            task_id=task.id, changed="",
            failed="Missing inputs (summaries / comparison.md / patterns.md)",
            remaining="Run prior tasks", evidence=""
        )
    prompt = (
        "Summaries:\n" + json.dumps(summaries, indent=2) +
        "\n\nComparison:\n" + comparison +
        "\n\nPatterns:\n" + patterns
    )
    md = call_llm(REPORT_SYSTEM, prompt, WORKER_MODEL, max_tokens=REPORT_MAX_TOKENS)
    write_file("FINAL_REPORT.md", md)
    return Artifact(
        task_id=task.id,
        changed="Wrote FINAL_REPORT.md",
        failed="",
        remaining="",
        evidence=f"FINAL_REPORT.md length={len(md)} chars; covers {len(summaries)} papers",
    )


def _export_pdf(task: Task) -> Artifact:
    md_path = safe_workspace_path("FINAL_REPORT.md")
    pdf_path = safe_workspace_path("FINAL_REPORT.pdf")
    if not md_path.exists():
        return Artifact(
            task_id=task.id, changed="",
            failed="FINAL_REPORT.md missing", remaining="Run T6", evidence=""
        )
    try:
        pdf_tools.export_pdf(md_path, pdf_path)
    except Exception as e:
        return Artifact(
            task_id=task.id, changed="",
            failed=f"WeasyPrint failed: {e}",
            remaining="Install pango/cairo system deps (brew install pango cairo)",
            evidence=""
        )
    size = pdf_path.stat().st_size
    return Artifact(
        task_id=task.id,
        changed="Wrote FINAL_REPORT.pdf",
        failed="",
        remaining="",
        evidence=f"FINAL_REPORT.pdf size={size} bytes",
    )
