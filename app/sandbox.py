from pathlib import Path
from app.config import WORKSPACE_DIR, PAPERS_DIR

WORKSPACE = WORKSPACE_DIR.resolve()
PAPERS = PAPERS_DIR.resolve()


def _safe(base: Path, relative_path: str) -> Path:
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Blocked unsafe path access: {relative_path}")
    return target


def safe_workspace_path(relative_path: str) -> Path:
    return _safe(WORKSPACE, relative_path)


def safe_paper_path(relative_path: str) -> Path:
    return _safe(PAPERS, relative_path)


def write_file(relative_path: str, content: str) -> Path:
    target = safe_workspace_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def read_workspace_file(relative_path: str) -> str:
    target = safe_workspace_path(relative_path)
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8")


def read_paper_file(relative_path: str) -> bytes:
    target = safe_paper_path(relative_path)
    if not target.exists():
        raise FileNotFoundError(f"Paper not found: {relative_path}")
    return target.read_bytes()


def list_papers() -> list[Path]:
    return sorted(p for p in PAPERS.glob("*.pdf") if p.is_file())


def list_workspace() -> str:
    files: list[str] = []
    for path in WORKSPACE.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(WORKSPACE)))
    return "\n".join(sorted(files))
