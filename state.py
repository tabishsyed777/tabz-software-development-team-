"""Persistent, inspectable project state for the factory."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def project_dir(root: Path, name: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.lower()).strip("-")
    if not safe:
        raise ValueError("Project name must contain at least one letter or number")
    return root / "workspace" / safe


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_tasks(path: Path) -> list[dict]:
    return json.loads((path / "tasks.json").read_text())


def save_tasks(path: Path, tasks: list[dict]) -> None:
    (path / "tasks.json").write_text(json.dumps(tasks, indent=2) + "\n")


def log(path: Path, agent: str, event: str, payload: dict | None = None) -> None:
    entry = {"at": now(), "agent": agent, "event": event, "payload": payload or {}}
    with (path / "log.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry) + "\n")


def next_task(path: Path) -> dict | None:
    tasks = load_tasks(path)
    choices = [t for t in tasks if t["status"] == "todo"]
    return max(choices, key=lambda t: t.get("priority", 0), default=None)


def set_task_status(path: Path, task_id: str, status: str, **extra: object) -> None:
    tasks = load_tasks(path)
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = status
            task.update(extra)
            save_tasks(path, tasks)
            return
    raise KeyError(task_id)
