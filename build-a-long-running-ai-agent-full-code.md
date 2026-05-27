# Build a Long Running AI Agent + Full Code
*A chatbot answers. A long running agent executes. And execution needs architecture.*

**Author:** Sri Nithya Thimmaraju  
**Date:** 2026-05-16

---

A real long-running agent is a backend system around the model. The model thinks, but the system decides what work exists, what step runs next, where progress is saved, what tools are allowed, what counts as done, what happens when something fails, and how the work resumes later without guessing.

Hi 💜 Good to see you on AI & Reflection! Subscribe for free to receive new posts every week.

This is the important shift.

[

![](https://substackcdn.com/image/fetch/$s_!DsuZ!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fc3a2398c-5831-4b32-8113-85119d3d52c5_1280x720.png)



](https://substackcdn.com/image/fetch/$s_!DsuZ!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fc3a2398c-5831-4b32-8113-85119d3d52c5_1280x720.png)

Anthropic’s long-running agent work is interesting because the architecture is not just “give Claude a bigger prompt.” Their public harness primitives describe patterns like a **generator evaluator loop**, **default fail criteria**, **fresh context evaluation, and agent-maintained handoff artifacts**. Their long-running application harness also separates planning, generation, and evaluation so the same agent is not both doing the work and judging the work. ([GitHub](https://github.com/anthropics/cwc-long-running-agents))

Microsoft Agent Framework documentation says something similar from a workflow angle. Long-running workflows need explicit control over execution order, state, human gates, checkpoints, resuming, and orchestration patterns like sequential, concurrent, handoff, and group chat. ([Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/journey/workflows))

So let’s build the simplest version of that.  
A small, real, file-based, long-running agent harness.

The goal is simple. You give it a project goal.

*   It creates a task graph.
    
*   It stores state.
    
*   It runs one task at a time.
    
*   It writes artifacts after every step.
    
*   It evaluates the work.
    
*   It checkpoints progress.
    

Then it can stop and resume from the last known state and that is the minimum architecture.

Here is the backend pipeline.

*   User goal goes into the planner.
    
*   The planner turns the goal into a structured task graph.
    
*   The task graph is saved in a database or workspace file.
    
*   The worker picks one pending task.
    
*   The worker runs in a sandboxed workspace with limited tools.
    
*   The worker writes artifacts after every step.
    
*   The evaluator checks whether the task actually passed.
    
*   If it fails, the task goes back to pending or needs human review.
    
*   If it passes, the checkpoint is saved.
    
*   The next run resumes from the saved checkpoint.
    
*   This is the difference between “AI replied” and “AI worked.”
    

Now let’s build it.

Project structure:

```
long-running-agent/
  app/
    __init__.py
    main.py
    config.py
    llm.py
    planner.py
    worker.py
    evaluator.py
    memory.py
    sandbox.py
    schemas.py
  workspace/
    artifacts/
    logs/
    checkpoints/
    project/
  .env
  requirements.txt
  README.md
```

The important folders are not random.

1.  `app` contains the harness logic.
    
2.  `workspace/project` is where the agent is allowed to create or modify files.
    
3.  `workspace/artifacts` stores what changed, what failed, and what remains.
    
4.  `workspace/checkpoints` stores resumable state.
    
5.  `workspace/logs` stores execution traces.
    

That separation matters because a long running agent should never keep the whole project only inside a prompt. The prompt is temporary. The workspace is durable.

Create the environment.

```
mkdir long-running-agent
cd long-running-agent

mkdir -p app workspace/artifacts workspace/logs workspace/checkpoints workspace/project

touch app/__init__.py
touch app/main.py app/config.py app/llm.py app/planner.py app/worker.py app/evaluator.py app/memory.py app/sandbox.py app/schemas.py
touch .env requirements.txt README.md
```

Install dependencies.

```
openai
python-dotenv
pydantic
rich
```

Put this in `.env`.

```
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-5.5
```

Now create the shared schemas.

```
# app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


TaskStatus = Literal["pending", "running", "passed", "failed", "needs_human"]


class Task(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus = "pending"
    dependencies: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    attempts: int = 0
    last_error: Optional[str] = None


class TaskGraph(BaseModel):
    goal: str
    tasks: List[Task]


class Artifact(BaseModel):
    task_id: str
    changed: str
    failed: str
    remaining: str
    evidence: str


class EvaluationResult(BaseModel):
    task_id: str
    passed: bool
    score: int
    issues: List[str]
    next_action: Literal["continue", "retry", "human_review"]
```

Now create config.

```
# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.5")

WORKSPACE_DIR = "workspace/project"
ARTIFACT_DIR = "workspace/artifacts"
CHECKPOINT_DIR = "workspace/checkpoints"
LOG_DIR = "workspace/logs"
DB_PATH = "workspace/agent_state.db"

MAX_ATTEMPTS_PER_TASK = 3
```

Now create the LLM wrapper.

This is intentionally thin.

A long running agent should not hide everything inside one giant model call. The model call should be one component inside the harness.

```
# app/llm.py

from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.output_text
```

Now build memory.

This is where the agent becomes durable.

It stores the task graph, task status, artifacts, and checkpoints in SQLite. You can later replace this with Postgres, Supabase, DynamoDB, or a proper workflow engine.

```
# app/memory.py

import sqlite3
import json
from datetime import datetime
from app.config import DB_PATH
from app.schemas import TaskGraph, Artifact


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_graph (
        id INTEGER PRIMARY KEY,
        goal TEXT NOT NULL,
        graph_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        artifact_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkpoint_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def save_task_graph(graph: TaskGraph):
    now = datetime.utcnow().isoformat()
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT id FROM task_graph LIMIT 1")
    row = cur.fetchone()

    graph_json = graph.model_dump_json(indent=2)

    if row:
        cur.execute(
            "UPDATE task_graph SET goal = ?, graph_json = ?, updated_at = ? WHERE id = ?",
            (graph.goal, graph_json, now, row[0])
        )
    else:
        cur.execute(
            "INSERT INTO task_graph (goal, graph_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (graph.goal, graph_json, now, now)
        )

    conn.commit()
    conn.close()


def load_task_graph() -> TaskGraph | None:
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT graph_json FROM task_graph LIMIT 1")
    row = cur.fetchone()

    conn.close()

    if not row:
        return None

    return TaskGraph.model_validate_json(row[0])


def save_artifact(artifact: Artifact):
    now = datetime.utcnow().isoformat()
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO artifacts (task_id, artifact_json, created_at) VALUES (?, ?, ?)",
        (artifact.task_id, artifact.model_dump_json(indent=2), now)
    )

    conn.commit()
    conn.close()


def save_checkpoint(graph: TaskGraph):
    now = datetime.utcnow().isoformat()
    conn = connect()
    cur = conn.cursor()

    checkpoint = {
        "goal": graph.goal,
        "graph": graph.model_dump(),
        "created_at": now
    }

    cur.execute(
        "INSERT INTO checkpoints (checkpoint_json, created_at) VALUES (?, ?)",
        (json.dumps(checkpoint, indent=2), now)
    )

    conn.commit()
    conn.close()
```

**Now build the** **planner**.

The planner does not write code.  
The planner does not evaluate.  
The planner only turns the user goal into a task graph.

That is the first important boundary.

```
# app/planner.py

import json
from app.llm import call_llm
from app.schemas import TaskGraph


PLANNER_SYSTEM_PROMPT = """
You are the planner in a long running AI agent harness.

Your job is to convert a user goal into a structured task graph.

Rules:
1. Break the goal into small tasks.
2. Each task must have clear acceptance criteria.
3. Each task must be independently testable.
4. Do not write code.
5. Do not mark anything complete.
6. Return only valid JSON.

The JSON must follow this shape:
{
  "goal": "string",
  "tasks": [
    {
      "id": "T1",
      "title": "short title",
      "description": "what needs to be done",
      "status": "pending",
      "dependencies": [],
      "acceptance_criteria": ["criterion 1", "criterion 2"],
      "attempts": 0,
      "last_error": null
    }
  ]
}
"""


def create_task_graph(goal: str) -> TaskGraph:
    raw = call_llm(
        system_prompt=PLANNER_SYSTEM_PROMPT,
        user_prompt=f"Create a task graph for this goal:\n\n{goal}"
    )

    data = json.loads(raw)
    return TaskGraph.model_validate(data)
```

Now build the sandbox.

For the first version, the sandbox is simple.

The worker can only read and write inside `workspace/project`.

That is the core safety rule.

In production, this should become a Docker container, Firecracker microVM, or cloud sandbox. But for a first version, path restriction is enough to teach the architecture.

```
# app/sandbox.py

from pathlib import Path
from app.config import WORKSPACE_DIR


WORKSPACE = Path(WORKSPACE_DIR).resolve()


def safe_path(relative_path: str) -> Path:
    target = (WORKSPACE / relative_path).resolve()

    if not str(target).startswith(str(WORKSPACE)):
        raise ValueError("Blocked unsafe path access")

    return target


def write_file(relative_path: str, content: str):
    target = safe_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def read_file(relative_path: str) -> str:
    target = safe_path(relative_path)

    if not target.exists():
        return ""

    return target.read_text(encoding="utf-8")


def list_workspace() -> str:
    files = []

    for path in WORKSPACE.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(WORKSPACE)))

    return "\n".join(files)
```

**Now build the worker.**

The worker does the actual work.

But notice the constraint.

It only receives one task.  
It receives the workspace file list.  
It has to produce artifacts.  
It cannot quietly say “done.”

```
# app/worker.py

import json
from app.llm import call_llm
from app.schemas import Task, Artifact
from app.sandbox import list_workspace, write_file


WORKER_SYSTEM_PROMPT = """
You are the worker agent in a long running AI agent harness.

Your job is to complete exactly one task.

Rules:
1. Work only on the task you are given.
2. Do not claim the whole project is done.
3. If you create code, write the file path and full file content.
4. Always write an artifact explaining what changed, what failed, what remains, and what evidence exists.
5. Return only valid JSON.

JSON shape:
{
  "files": [
    {
      "path": "relative/path/from/workspace",
      "content": "full file content"
    }
  ],
  "artifact": {
    "task_id": "T1",
    "changed": "what changed",
    "failed": "what failed",
    "remaining": "what remains",
    "evidence": "how someone can verify this"
  }
}
"""


def run_worker(task: Task) -> Artifact:
    workspace_snapshot = list_workspace()

    prompt = f"""
Current workspace files:
{workspace_snapshot}

Current task:
{task.model_dump_json(indent=2)}

Complete this task only.
"""

    raw = call_llm(WORKER_SYSTEM_PROMPT, prompt)
    data = json.loads(raw)

    for file_item in data.get("files", []):
        write_file(file_item["path"], file_item["content"])

    return Artifact.model_validate(data["artifact"])
```

**Now build the evaluator.**

This is the second important boundary.

The evaluator should not be the same mental process as the worker.

The evaluator is skeptical.

The evaluator starts from default fail.

If there is no evidence, it fails.

This one design choice alone makes the agent much more reliable.

```
# app/evaluator.py

import json
from app.llm import call_llm
from app.schemas import Task, Artifact, EvaluationResult
from app.sandbox import list_workspace


EVALUATOR_SYSTEM_PROMPT = """
You are the evaluator in a long running AI agent harness.

Your job is to judge whether one task passed.

Rules:
1. Default to failed.
2. Passing requires concrete evidence.
3. Do not be polite.
4. Do not assume the task is complete.
5. If acceptance criteria are not met, fail it.
6. If evidence is weak, fail it.
7. Return only valid JSON.

JSON shape:
{
  "task_id": "T1",
  "passed": false,
  "score": 0,
  "issues": ["issue 1", "issue 2"],
  "next_action": "retry"
}

next_action must be one of:
continue
retry
human_review
"""


def evaluate_task(task: Task, artifact: Artifact) -> EvaluationResult:
    workspace_snapshot = list_workspace()

    prompt = f"""
Task:
{task.model_dump_json(indent=2)}

Artifact written by worker:
{artifact.model_dump_json(indent=2)}

Current workspace files:
{workspace_snapshot}

Evaluate whether the task passed.
"""

    raw = call_llm(EVALUATOR_SYSTEM_PROMPT, prompt)
    data = json.loads(raw)

    return EvaluationResult.model_validate(data)
```

**Now build the HARNESS.**

This is the real system.

The harness is the execution loop that decides what runs next, when to retry, when to checkpoint, and when to stop.

```
# app/main.py

from rich import print
from app.memory import init_db, save_task_graph, load_task_graph, save_artifact, save_checkpoint
from app.planner import create_task_graph
from app.worker import run_worker
from app.evaluator import evaluate_task
from app.config import MAX_ATTEMPTS_PER_TASK


def pick_next_task(graph):
    passed_ids = {task.id for task in graph.tasks if task.status == "passed"}

    for task in graph.tasks:
        if task.status in ["pending", "failed"]:
            dependencies_done = all(dep in passed_ids for dep in task.dependencies)
            if dependencies_done:
                return task

    return None


def run(goal: str | None = None):
    init_db()

    graph = load_task_graph()

    if not graph:
        if not goal:
            raise ValueError("No existing task graph found. Please provide a goal.")

        print("[bold blue]Planning project...[/bold blue]")
        graph = create_task_graph(goal)
        save_task_graph(graph)
        save_checkpoint(graph)

    task = pick_next_task(graph)

    if not task:
        print("[bold green]All tasks are complete.[/bold green]")
        return

    print(f"[bold blue]Running task:[/bold blue] {task.id} {task.title}")

    task.status = "running"
    task.attempts += 1
    save_task_graph(graph)

    artifact = run_worker(task)
    save_artifact(artifact)

    result = evaluate_task(task, artifact)

    if result.passed:
        task.status = "passed"
        task.last_error = None
        print(f"[bold green]Task passed:[/bold green] {task.id}")
    else:
        task.last_error = "; ".join(result.issues)

        if task.attempts >= MAX_ATTEMPTS_PER_TASK or result.next_action == "human_review":
            task.status = "needs_human"
            print(f"[bold yellow]Task needs human review:[/bold yellow] {task.id}")
        else:
            task.status = "failed"
            print(f"[bold red]Task failed and will retry later:[/bold red] {task.id}")

    save_task_graph(graph)
    save_checkpoint(graph)

    print("[bold blue]Checkpoint saved.[/bold blue]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", type=str, required=False)
    args = parser.parse_args()

    run(goal=args.goal)
```

Run it for the first time.

```
python -m app.main --goal "Build a tiny notes app with a README, simple backend design, and test plan"
```

Then run it again.

```
python -m app.main
```

That second run is the important part.

The agent does not start from scratch.

It loads the existing task graph.  
It checks what passed.  
It picks the next task.  
It continues from the saved state.

That is the first version of a long running agent.

Very small.  
Very simple.  
But architecturally correct.

Now let’s make it better.

The first improvement is stronger artifact writing.

After every worker step, force this file to exist:

```
workspace/artifacts/TASK_ID.md
```

It should always contain:

```
Task ID:
What changed:
Files touched:
What failed:
What remains:
Evidence:
Next recommended step:
```

Why does this matter?

> Because long running agents die when context is only inside the model.
> 
> _**The artifact is the handoff.**_

If the model loses context, the system can reload the artifact.

If the process crashes, the system can resume.

If a human reviews the run, the human can inspect what happened.

The second improvement is stronger evaluators.

Do not let the evaluator say “looks good.”

Make it run checks.

For a coding project, the evaluator should run:

```
python -m pytest
npm test
npm run lint
npm run build
```

For a UI project, add Playwright.

```
npm install -D @playwright/test
npx playwright install
```

Then the evaluator should not only read files. It should open the app, click buttons, take screenshots, and compare the result against the acceptance criteria.

That is where long running agents become much more real.

**The third improvement is human approval.**

Some tasks should not auto execute.

Examples:

Deleting files.  
Pushing code.  
Sending emails.  
Changing production data.  
Running expensive jobs.  
Calling external APIs with user data.

Add a simple approval gate.

```
# app/approval.py

SENSITIVE_KEYWORDS = [
    "delete",
    "remove",
    "send",
    "deploy",
    "payment",
    "production",
    "credential",
    "secret"
]


def needs_approval(task_title: str, task_description: str) -> bool:
    text = f"{task_title} {task_description}".lower()
    return any(keyword in text for keyword in SENSITIVE_KEYWORDS)


def request_approval(task_id: str) -> bool:
    answer = input(f"Task {task_id} needs approval. Continue? yes/no: ")
    return answer.strip().lower() == "yes"
```

Then call it before the worker runs.

```
from app.approval import needs_approval, request_approval

if needs_approval(task.title, task.description):
    approved = request_approval(task.id)
    if not approved:
        task.status = "needs_human"
        save_task_graph(graph)
        save_checkpoint(graph)
        return
```

Thiss teaches the real production pattern.

A long-running agent should not be fully autonomous everywhere. It should be autonomous where the risk is low and gated where the risk is high.

The fourth improvement is task locking.

If you ever run multiple workers at the same time, you need task locks.

Without locks, two workers can pick the same task and corrupt the workspace.

Add a `locked_by` and `locked_at` field later.

For the first version, keep it single worker.

The fifth improvement is better state.

SQLite is fine for learning.

For production, use Postgres.

A good production schema looks like this:

```
projects
  id
  goal
  status
  created_at
  updated_at

tasks
  id
  project_id
  title
  description
  status
  dependencies
  acceptance_criteria
  attempts
  locked_by
  locked_at
  last_error
  created_at
  updated_at

artifacts
  id
  project_id
  task_id
  type
  content
  file_path
  created_at

checkpoints
  id
  project_id
  state_json
  created_at

runs
  id
  project_id
  task_id
  agent_role
  model
  input_tokens
  output_tokens
  cost
  latency_ms
  status
  created_at

events
  id
  project_id
  task_id
  event_type
  event_json
  created_at
```

This is where observability comes in.

Every long running agent should have events.

Not just final output.

You need to know:

What did the planner create?  
Which task was selected?  
What files did the worker touch?  
What did the evaluator reject?  
How many retries happened?  
Where did the agent stop?  
What checkpoint was used to resume?  
Which step needed human approval?

Without this, you do not have an agent system.

**The sixth improvement is fresh context evaluation.**

This is one of the most important lessons from the Anthropic style architecture.

Do not let the same worker evaluate itself.

A worker wants to believe it is done.

An evaluator should start fresh, read the acceptance criteria, inspect the artifact, check the files, and fail anything that does not have evidence.

That fresh context makes the evaluator more useful because it is not emotionally attached to the work.

In system design terms, this is separation of duties.

Planner defines the job.  
Worker does the job.  
Evaluator judges the job.  
Harness controls the loop.

That is the architecture.

Here is the final mental model.

*   The model is not the long running agent.
    
*   The loop is the agent.
    
*   The memory is the continuity.
    
*   The artifacts are the handoff.
    
*   The evaluator is the quality gate.
    
*   The checkpoint is the recovery system.
    
*   The human approval gate is the safety layer.
    
*   The harness is what makes the whole thing durable.
    

If you want to build one serious project from this, build a “research paper reviewer agent.”

Goal:

```
Review 20 research papers, extract the core ideas, compare methods, identify implementation patterns, and produce a final technical report.
```

The planner creates tasks like:

```
T1 Collect papers
T2 Extract metadata
T3 Summarize each paper
T4 Compare methods
T5 Identify repeated architecture patterns
T6 Write final report
T7 Evaluate report quality
```

*   The worker processes one paper at a time.
    
*   The memory layer stores each summary.
    
*   The evaluator checks whether each summary has method, dataset, result, limitation, and implementation notes.
    
*   The final report is created only after all required artifacts exist.
    

That is a real long running agent use case.

Or build a coding agent.

Goal:

```
Build a small expense tracker app with auth, dashboard, charts, tests, and deployment notes.
```

*   The planner creates the product plan.
    
*   The worker builds one feature at a time.
    
*   The evaluator runs tests and UI checks.
    
*   The harness retries failed tasks.
    
*   The state is checkpointed after every step.
    
*   That is how you move from “AI generated some code” to “AI completed a controlled workflow.”
    

And that is the whole point :)

**Long running AI Agents are not built by asking the model to work longer.**

**They are built by giving the model a system that can** _**remember, verify, recover, and continue**_**.**