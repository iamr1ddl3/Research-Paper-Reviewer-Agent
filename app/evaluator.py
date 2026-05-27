import json
from pathlib import Path

from app.config import EVALUATOR_MODEL, WORKSPACE_DIR, PAPERS_DIR, PAPER_COUNT
from app.llm import call_llm_json
from app.schemas import Task, Artifact, EvaluationResult, PaperSummary
from app.sandbox import read_workspace_file, safe_workspace_path
from app import pdf_tools


REQUIRED_SUMMARY_FIELDS = ("method", "dataset", "results", "limitations", "implementation_notes")


def evaluate_task(task: Task, artifact: Artifact) -> EvaluationResult:
    """Evaluate one task.

    Deterministic checks for file-producing tasks (T1, T2, T3.N, T7).
    LLM evaluator for content-quality tasks (T4, T5, T6).
    """
    if task.task_type == "summarize_paper":
        return _evaluate_summary(task, artifact)
    if task.task_type == "summarize_fanout":
        return _ok(task.id)
    if task.task_type == "collect_papers":
        return _evaluate_collect(task, artifact)
    if task.task_type == "extract_text":
        return _evaluate_extract(task, artifact)
    if task.task_type == "export_pdf":
        return _evaluate_pdf(task, artifact)
    return _evaluate_llm(task, artifact)


def _ok(task_id: str) -> EvaluationResult:
    return EvaluationResult(
        task_id=task_id, passed=True, score=100, issues=[], next_action="continue"
    )


def _fail(task_id: str, issues: list[str]) -> EvaluationResult:
    return EvaluationResult(
        task_id=task_id,
        passed=False,
        score=max(0, 100 - 20 * len(issues)),
        issues=issues,
        next_action="retry",
    )


def _evaluate_collect(task: Task, artifact: Artifact) -> EvaluationResult:
    issues: list[str] = []
    pdfs = sorted(p for p in PAPERS_DIR.glob("*.pdf") if p.is_file())
    if len(pdfs) < PAPER_COUNT:
        issues.append(f"Need {PAPER_COUNT} PDFs in workspace/papers/, found {len(pdfs)}")

    index_raw = read_workspace_file("paper_index.json")
    if not index_raw:
        issues.append("workspace/project/paper_index.json missing")
        return _fail(task.id, issues)
    try:
        index = json.loads(index_raw)
    except Exception as e:
        issues.append(f"paper_index.json invalid JSON: {e}")
        return _fail(task.id, issues)
    if not isinstance(index, list) or len(index) < PAPER_COUNT:
        issues.append(f"paper_index.json should list >= {PAPER_COUNT} papers, got {len(index) if isinstance(index, list) else 'non-list'}")
    for i, entry in enumerate(index if isinstance(index, list) else []):
        for k in ("id", "filename", "source"):
            if k not in entry:
                issues.append(f"paper_index.json[{i}] missing field '{k}'")
        if "filename" in entry and not (PAPERS_DIR / entry["filename"]).exists():
            issues.append(f"paper_index.json[{i}] filename {entry['filename']} not found in workspace/papers/")
    return _ok(task.id) if not issues else _fail(task.id, issues)


def _evaluate_extract(task: Task, artifact: Artifact) -> EvaluationResult:
    issues: list[str] = []
    index_raw = read_workspace_file("paper_index.json")
    if not index_raw:
        return _fail(task.id, ["paper_index.json missing"])
    index = json.loads(index_raw)
    for entry in index:
        pid = entry["id"]
        raw = read_workspace_file(f"papers/{pid}/raw.txt")
        meta = read_workspace_file(f"papers/{pid}/meta.json")
        if not raw.strip():
            issues.append(f"papers/{pid}/raw.txt missing or empty")
        elif len(raw) < 500:
            issues.append(f"papers/{pid}/raw.txt very short ({len(raw)} chars) — extraction likely failed")
        if not meta.strip():
            issues.append(f"papers/{pid}/meta.json missing")
        else:
            try:
                m = json.loads(meta)
                if not m.get("title") and not m.get("filename"):
                    issues.append(f"papers/{pid}/meta.json missing title and filename")
            except Exception as e:
                issues.append(f"papers/{pid}/meta.json invalid: {e}")
    return _ok(task.id) if not issues else _fail(task.id, issues)


def _evaluate_pdf(task: Task, artifact: Artifact) -> EvaluationResult:
    pdf = safe_workspace_path("FINAL_REPORT.pdf")
    if not pdf.exists():
        return _fail(task.id, ["FINAL_REPORT.pdf missing"])
    size = pdf.stat().st_size
    if size < 1024:
        return _fail(task.id, [f"FINAL_REPORT.pdf too small ({size} bytes < 1KB)"])
    return _ok(task.id)


def _evaluate_summary(task: Task, artifact: Artifact) -> EvaluationResult:
    pid = task.paper_id or ""
    issues: list[str] = []

    summary_raw = read_workspace_file(f"papers/{pid}/summary.json")
    if not summary_raw:
        return _fail(task.id, [f"summary.json missing for {pid}"])
    try:
        summary = PaperSummary.model_validate_json(summary_raw)
    except Exception as e:
        return _fail(task.id, [f"summary.json invalid: {e}"])

    for field in REQUIRED_SUMMARY_FIELDS:
        value = getattr(summary, field, "") or ""
        if not value.strip():
            issues.append(f"Required field empty: {field}")
        elif value.strip().lower() in {"n/a", "none", "unknown", "tbd"}:
            issues.append(f"Required field is placeholder ({field}={value!r})")
        elif len(value.strip()) < 20:
            issues.append(f"Required field too short ({field}, {len(value.strip())} chars)")

    raw_text = read_workspace_file(f"papers/{pid}/raw.txt")
    if not raw_text:
        issues.append("raw.txt missing — cannot verify citations")
    else:
        if len(summary.citations) < 3:
            issues.append(f"Need >= 3 citations; got {len(summary.citations)}")
        unverified: list[str] = []
        for quote in summary.citations:
            if not pdf_tools.verify_citation(quote, raw_text):
                preview = quote[:80].replace("\n", " ")
                unverified.append(preview)
        if unverified:
            issues.append(
                f"{len(unverified)}/{len(summary.citations)} citations not found in raw.txt: "
                + " | ".join(unverified[:3])
            )

    return _ok(task.id) if not issues else _fail(task.id, issues)


EVALUATOR_SYSTEM = """You are the evaluator in a long-running AI agent harness.

You judge ONE task. Mode: skeptical but fair.

Rules:
1. The artifact's "evidence" field, plus the workspace file listing and content excerpts provided below, are your ONLY sources of truth.
2. If acceptance criteria reference a file and that file appears in the workspace listing with non-trivial size, the file exists — do not demand to "see its contents" beyond what is shown.
3. Only fail if a criterion is concretely unmet (file missing, required section absent, citation invalid).
4. Return ONLY valid JSON in this exact shape:
{
  "task_id": "string",
  "passed": false,
  "score": 0,
  "issues": ["issue 1"],
  "next_action": "retry"
}
next_action ∈ {continue, retry, human_review}.
"""


def _list_workspace_with_sizes() -> str:
    base = Path(WORKSPACE_DIR)
    lines: list[str] = []
    for p in sorted(base.rglob("*")):
        if p.is_file():
            lines.append(f"workspace/project/{p.relative_to(base)} ({p.stat().st_size} bytes)")
    return "\n".join(lines)


def _list_papers_dir() -> str:
    base = Path(PAPERS_DIR)
    lines: list[str] = []
    for p in sorted(base.rglob("*")):
        if p.is_file():
            lines.append(f"workspace/papers/{p.relative_to(base)} ({p.stat().st_size} bytes)")
    return "\n".join(lines)


def _content_excerpts(task: Task) -> str:
    """For content-judging tasks, include relevant file content (truncated)."""
    blocks: list[str] = []
    targets: list[str] = []
    if task.task_type == "compare_methods":
        targets = ["comparison.md"]
    elif task.task_type == "identify_patterns":
        targets = ["patterns.md"]
    elif task.task_type == "write_report":
        targets = ["FINAL_REPORT.md"]
    for rel in targets:
        content = read_workspace_file(rel)
        if content:
            excerpt = content[:6000]
            tail = "" if len(content) <= 6000 else f"\n... (truncated, total {len(content)} chars)"
            blocks.append(f"--- {rel} ---\n{excerpt}{tail}")
    return "\n\n".join(blocks)


def _evaluate_llm(task: Task, artifact: Artifact) -> EvaluationResult:
    workspace_snapshot = _list_workspace_with_sizes()
    papers_snapshot = _list_papers_dir()
    excerpts = _content_excerpts(task)
    prompt = f"""Task:
{task.model_dump_json(indent=2)}

Artifact from worker:
{artifact.model_dump_json(indent=2)}

workspace/project/ files:
{workspace_snapshot}

workspace/papers/ files:
{papers_snapshot}

Relevant file content:
{excerpts or "(none for this task type)"}

Evaluate whether the task passed.
"""
    try:
        data = call_llm_json(EVALUATOR_SYSTEM, prompt, EVALUATOR_MODEL)
        data.setdefault("task_id", task.id)
        return EvaluationResult.model_validate(data)
    except Exception as e:
        return EvaluationResult(
            task_id=task.id,
            passed=False,
            score=0,
            issues=[f"Evaluator LLM/parse error: {e}"],
            next_action="retry",
        )
