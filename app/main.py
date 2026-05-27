import argparse
import json
from datetime import datetime, timezone

from rich import print

from app.config import ARTIFACT_DIR, PAPER_COUNT, max_attempts_for
from app.memory import (
    init_db,
    save_task_graph,
    load_task_graph,
    save_artifact,
    save_checkpoint,
    log_event,
)
from app.planner import create_task_graph, inject_summarize_subtasks
from app.worker import run_worker
from app.evaluator import evaluate_task
from app.approval import needs_approval, request_approval
from app.sandbox import read_workspace_file
from app.schemas import TaskGraph, Task, Artifact


def pick_next_task(graph: TaskGraph) -> Task | None:
    passed = {t.id for t in graph.tasks if t.status == "passed"}
    for t in graph.tasks:
        if t.status in {"pending", "failed"}:
            if all(dep in passed for dep in t.dependencies):
                return t
    return None


def write_artifact_file(artifact: Artifact, task: Task, eval_issues: list[str] | None = None) -> None:
    path = ARTIFACT_DIR / f"{task.id}.md"
    eval_block = ""
    if eval_issues:
        eval_block = "\n## Evaluator Issues\n" + "\n".join(f"- {i}" for i in eval_issues)
    body = f"""# Artifact — {task.id}

Task: {task.title}
Type: {task.task_type}
Attempt: {task.attempts}
Timestamp (UTC): {datetime.now(timezone.utc).isoformat()}

## What changed
{artifact.changed or "_(nothing)_"}

## What failed
{artifact.failed or "_(nothing)_"}

## What remains
{artifact.remaining or "_(nothing)_"}

## Evidence
{artifact.evidence or "_(none)_"}
{eval_block}
"""
    path.write_text(body, encoding="utf-8")


def _maybe_fanout(graph: TaskGraph) -> TaskGraph:
    """If T3 placeholder still pending/failed and T2 passed, inject T3.N subtasks."""
    t3 = next((t for t in graph.tasks if t.id == "T3"), None)
    if t3 is None:
        return graph
    t2 = next((t for t in graph.tasks if t.id == "T2"), None)
    if not t2 or t2.status != "passed":
        return graph
    index_raw = read_workspace_file("paper_index.json")
    if not index_raw:
        return graph
    paper_ids = [entry["id"] for entry in json.loads(index_raw)]
    if not paper_ids:
        return graph
    graph = inject_summarize_subtasks(graph, paper_ids)
    save_task_graph(graph)
    save_checkpoint(graph)
    log_event("fanout_injected", {"count": len(paper_ids), "ids": paper_ids})
    print(f"[bold cyan]Fan-out:[/bold cyan] injected {len(paper_ids)} T3.* subtasks")
    return graph


def _run_one(graph: TaskGraph, task: Task) -> tuple[TaskGraph, bool]:
    """Run one task. Returns (graph, should_continue)."""
    print(f"\n[bold blue]Running:[/bold blue] {task.id} — {task.title} (attempt {task.attempts + 1})")
    log_event("task_start", {"task_id": task.id, "attempt": task.attempts + 1}, task_id=task.id)

    if needs_approval(task.id):
        ok = request_approval(task.id, task.title)
        if not ok:
            task.status = "needs_human"
            task.last_error = "Approval denied"
            save_task_graph(graph)
            save_checkpoint(graph)
            log_event("approval_denied", {"task_id": task.id}, task_id=task.id)
            print(f"[bold yellow]Approval denied — stopping at {task.id}[/bold yellow]")
            return graph, False

    task.status = "running"
    task.attempts += 1
    save_task_graph(graph)

    artifact = run_worker(task)
    save_artifact(artifact)
    result = evaluate_task(task, artifact)
    log_event(
        "task_evaluated",
        {"task_id": task.id, "passed": result.passed, "issues": result.issues},
        task_id=task.id,
    )
    write_artifact_file(artifact, task, eval_issues=None if result.passed else result.issues)

    if result.passed:
        task.status = "passed"
        task.last_error = None
        print(f"[bold green]PASS[/bold green] {task.id} (score {result.score})")
    else:
        task.last_error = "; ".join(result.issues) or "Evaluation failed"
        cap = max_attempts_for(task.task_type)
        if task.attempts >= cap or result.next_action == "human_review":
            task.status = "needs_human"
            print(f"[bold yellow]NEEDS HUMAN[/bold yellow] {task.id}: {task.last_error} (cap={cap})")
        else:
            task.status = "failed"
            print(f"[bold red]FAIL[/bold red] {task.id} (will retry, {task.attempts}/{cap}): {task.last_error}")

    save_task_graph(graph)
    save_checkpoint(graph)
    return graph, task.status != "needs_human"


def run(goal: str | None = None, count: int | None = None) -> None:
    init_db()

    if count is not None:
        import app.config as cfg
        cfg.PAPER_COUNT = count
        import app.worker as worker_mod
        worker_mod.PAPER_COUNT = count

    graph = load_task_graph()
    if not graph:
        if not goal:
            raise SystemExit("No existing task graph. Provide --goal on first run.")
        print(f"[bold blue]Planning:[/bold blue] {goal}")
        print(f"[dim]Target paper count: {count or PAPER_COUNT}[/dim]")
        graph = create_task_graph(goal)
        save_task_graph(graph)
        save_checkpoint(graph)
        log_event("graph_created", {"goal": goal, "task_count": len(graph.tasks)})

    while True:
        graph = _maybe_fanout(graph)
        task = pick_next_task(graph)
        if task is None:
            remaining = [t.id for t in graph.tasks if t.status not in {"passed"}]
            if not remaining:
                print("\n[bold green]All tasks passed.[/bold green]")
                print("Output: workspace/project/FINAL_REPORT.md")
            else:
                blocked = [(t.id, t.status, t.last_error) for t in graph.tasks if t.status != "passed"]
                print("\n[bold yellow]Stopped — no runnable task.[/bold yellow]")
                for tid, st, err in blocked:
                    print(f"  {tid}: {st} ({err or 'no error'})")
            return
        graph, cont = _run_one(graph, task)
        if not cont:
            return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", type=str, default=None)
    parser.add_argument("--count", type=int, default=None, help="Override PAPER_COUNT")
    args = parser.parse_args()
    run(goal=args.goal, count=args.count)


if __name__ == "__main__":
    main()
