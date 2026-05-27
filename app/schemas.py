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
    task_type: str = "generic"
    paper_id: Optional[str] = None


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
    issues: List[str] = Field(default_factory=list)
    next_action: Literal["continue", "retry", "human_review"] = "retry"


class PaperSummary(BaseModel):
    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    method: str
    dataset: str
    results: str
    limitations: str
    implementation_notes: str
    citations: List[str] = Field(default_factory=list)
