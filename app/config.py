import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "https://github.com/local/research-paper-reviewer-agent")
OPENROUTER_TITLE = os.getenv("OPENROUTER_TITLE", "Research Paper Reviewer Agent")

WORKER_MODEL = os.getenv("WORKER_MODEL", "anthropic/claude-sonnet-4.5")
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "anthropic/claude-opus-4.1")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "anthropic/claude-sonnet-4.5")

PAPER_COUNT = int(os.getenv("PAPER_COUNT", "5"))
ARXIV_QUERY = os.getenv("ARXIV_QUERY", "").strip()

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = ROOT / "workspace" / "project"
PAPERS_DIR = ROOT / "workspace" / "papers"
ARTIFACT_DIR = ROOT / "workspace" / "artifacts"
CHECKPOINT_DIR = ROOT / "workspace" / "checkpoints"
LOG_DIR = ROOT / "workspace" / "logs"
DB_PATH = ROOT / "workspace" / "agent_state.db"

MAX_ATTEMPTS_PER_TASK = int(os.getenv("MAX_ATTEMPTS_PER_TASK", "3"))

# Per-task-type overrides. Summarize is the most retry-friendly because PDF
# extraction artifacts (hyphenation, math, multi-column) often need 1-2 extra
# tries before citations all verify. Export_pdf is mechanical — 2 tries enough.
_DEFAULT_ATTEMPT_OVERRIDES = {
    "summarize_paper": 5,
    "export_pdf": 2,
}


def _parse_attempt_overrides(raw: str) -> dict[str, int]:
    """Parse MAX_ATTEMPTS_BY_TYPE env. Format: 'task_type=N,task_type=N,...'."""
    out: dict[str, int] = {}
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        key, val = chunk.split("=", 1)
        try:
            out[key.strip()] = int(val.strip())
        except ValueError:
            continue
    return out


MAX_ATTEMPTS_BY_TYPE: dict[str, int] = {
    **_DEFAULT_ATTEMPT_OVERRIDES,
    **_parse_attempt_overrides(os.getenv("MAX_ATTEMPTS_BY_TYPE", "")),
}


def max_attempts_for(task_type: str) -> int:
    return MAX_ATTEMPTS_BY_TYPE.get(task_type, MAX_ATTEMPTS_PER_TASK)


DEFAULT_MAX_TOKENS = 8000
REPORT_MAX_TOKENS = 16000

for d in (WORKSPACE_DIR, PAPERS_DIR, ARTIFACT_DIR, CHECKPOINT_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)
