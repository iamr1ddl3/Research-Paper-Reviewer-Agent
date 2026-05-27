import os
import sys

APPROVAL_TASK_IDS = {"T6"}


def needs_approval(task_id: str) -> bool:
    return task_id in APPROVAL_TASK_IDS


def request_approval(task_id: str, title: str) -> bool:
    if os.getenv("AUTO_APPROVE") == "1":
        print(f"[AUTO_APPROVE=1] Auto-approving {task_id}: {title}", flush=True)
        return True
    if not sys.stdin.isatty():
        print(
            f"Task {task_id} ({title}) needs approval but stdin is not a TTY. "
            "Set AUTO_APPROVE=1 or run interactively.",
            flush=True,
        )
        return False
    answer = input(f"Approve task {task_id} '{title}'? [yes/no]: ").strip().lower()
    return answer in {"yes", "y"}
