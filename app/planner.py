from app.schemas import Task, TaskGraph


def create_task_graph(goal: str) -> TaskGraph:
    tasks = [
        Task(
            id="T1",
            title="Collect papers",
            description=(
                "Scan workspace/papers/ for existing PDFs. If fewer than PAPER_COUNT, "
                "fetch the remainder from arXiv using ARXIV_QUERY. Return the final paper list."
            ),
            task_type="collect_papers",
            acceptance_criteria=[
                "workspace/papers/ contains at least PAPER_COUNT PDF files",
                "workspace/project/paper_index.json lists every paper with id, filename, source",
            ],
        ),
        Task(
            id="T2",
            title="Extract text and metadata",
            description=(
                "For each paper in paper_index.json, extract full text and metadata via pdfplumber. "
                "Write workspace/project/papers/<id>/raw.txt and meta.json."
            ),
            task_type="extract_text",
            dependencies=["T1"],
            acceptance_criteria=[
                "Every paper has papers/<id>/raw.txt non-empty",
                "Every paper has papers/<id>/meta.json with title and filename",
            ],
        ),
        Task(
            id="T3",
            title="Summarize papers (placeholder - fans out after T2)",
            description=(
                "Placeholder task. After T2 passes, the harness replaces this with one "
                "T3.N task per paper. Marked passed automatically once fan-out occurs."
            ),
            task_type="summarize_fanout",
            dependencies=["T2"],
            acceptance_criteria=[
                "Fan-out subtasks T3.1..T3.N created based on paper_index.json",
            ],
        ),
        Task(
            id="T4",
            title="Compare methods across papers",
            description=(
                "Read every papers/<id>/summary.json and produce comparison.md "
                "highlighting method similarities, differences, and dataset overlap."
            ),
            task_type="compare_methods",
            dependencies=["T3"],
            acceptance_criteria=[
                "workspace/project/comparison.md exists",
                "comparison.md references every paper by id",
                "comparison.md has a Method Comparison section",
            ],
        ),
        Task(
            id="T5",
            title="Identify repeated architecture patterns",
            description=(
                "From the summaries and comparison, identify architectural patterns that "
                "recur across two or more papers. Write workspace/project/patterns.md."
            ),
            task_type="identify_patterns",
            dependencies=["T4"],
            acceptance_criteria=[
                "workspace/project/patterns.md exists",
                "Each listed pattern cites at least two paper ids",
            ],
        ),
        Task(
            id="T6",
            title="Write final technical report",
            description=(
                "Synthesize summaries, comparison, and patterns into "
                "workspace/project/FINAL_REPORT.md. Include sections: Overview, "
                "Per-paper summaries, Method comparison, Architecture patterns, Open questions."
            ),
            task_type="write_report",
            dependencies=["T5"],
            acceptance_criteria=[
                "workspace/project/FINAL_REPORT.md exists",
                "Report has all five required sections",
                "Report cites every paper id",
            ],
        ),
        Task(
            id="T7",
            title="Export final report to PDF",
            description=(
                "Render workspace/project/FINAL_REPORT.md to "
                "workspace/project/FINAL_REPORT.pdf via WeasyPrint."
            ),
            task_type="export_pdf",
            dependencies=["T6"],
            acceptance_criteria=[
                "workspace/project/FINAL_REPORT.pdf exists",
                "FINAL_REPORT.pdf size >= 1 KB",
            ],
        ),
    ]
    return TaskGraph(goal=goal, tasks=tasks)


def inject_summarize_subtasks(graph: TaskGraph, paper_ids: list[str]) -> TaskGraph:
    """After T2 passes, fan out one T3.N summarize task per paper.

    Idempotent: if T3.N tasks already exist, do nothing.
    Inserts subtasks before T4 and makes T4 depend on all T3.N ids.
    """
    existing_ids = {t.id for t in graph.tasks}
    new_tasks: list[Task] = []
    sub_ids: list[str] = []
    for idx, pid in enumerate(paper_ids, start=1):
        tid = f"T3.{idx}"
        sub_ids.append(tid)
        if tid in existing_ids:
            continue
        new_tasks.append(
            Task(
                id=tid,
                title=f"Summarize paper {pid}",
                description=(
                    f"Read workspace/project/papers/{pid}/raw.txt and produce "
                    f"workspace/project/papers/{pid}/summary.json with required fields and citations."
                ),
                task_type="summarize_paper",
                paper_id=pid,
                dependencies=["T2"],
                acceptance_criteria=[
                    "summary.json has non-empty method, dataset, results, limitations, implementation_notes",
                    "Every citation in summary.citations[] is verifiable in raw.txt",
                    "summary.json title and authors populated",
                ],
            )
        )

    placeholder = next((t for t in graph.tasks if t.id == "T3"), None)
    if placeholder is not None:
        graph.tasks = [t for t in graph.tasks if t.id != "T3"]

    for t in graph.tasks:
        if t.id == "T4":
            t.dependencies = sorted(set(t.dependencies + sub_ids) - {"T3"})

    insert_at = next((i for i, t in enumerate(graph.tasks) if t.id == "T4"), len(graph.tasks))
    graph.tasks[insert_at:insert_at] = new_tasks
    return graph
