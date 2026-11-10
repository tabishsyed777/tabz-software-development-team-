"""Approval-gated local software factory. Generated agents cannot control workflow state."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from agents import pm, architect, qa, developer, reviewer, writer, release
from agents.base import AgentError
from state import project_dir, log, next_task, set_task_status, load_tasks, save_tasks
from tools.files import write_file, list_files, read_file
from tools.runner import run_tests, run_linter, pytest_available

ROOT = Path(__file__).parent
CONTROL_FILES = {"SPEC.md", "ARCHITECTURE.md", "tasks.json", "log.jsonl", "RELEASE.md", "request.txt"}


def config() -> dict:
    return json.loads((ROOT / "config.yaml").read_text())


def project_context(path: Path, task: dict | None = None, feedback: str = "") -> str:
    """Bound context: the approved plan, tests, and implementation—not hidden state."""
    files = [name for name in list_files(path) if name not in CONTROL_FILES and not name.startswith(".")]
    contents = []
    for name in files:
        try:
            contents.append(f"\n--- {name} ---\n{read_file(path, name)[:12000]}")
        except (OSError, UnicodeDecodeError):
            continue
    return (f"APPROVED SPEC:\n{(path / 'SPEC.md').read_text()[:16000]}\n"
            f"ARCHITECTURE:\n{(path / 'ARCHITECTURE.md').read_text()[:16000]}\n"
            f"CURRENT TASK: {json.dumps(task or {}, indent=2)}\n"
            f"TEST/REVIEW FEEDBACK:\n{feedback[-12000:]}\n"
            f"PROJECT FILES:{''.join(contents)[:60000]}")


def initialise(name: str, request: str) -> Path:
    path = project_dir(ROOT, name)
    path.mkdir(parents=True, exist_ok=False)
    try:
        result = pm.create(config(), request)
    except AgentError as error:
        log(path, "pm", "model_error", {"error": str(error)})
        raise RuntimeError(f"Could not create a spec. See {path / 'log.jsonl'}") from error
    (path / "SPEC.md").write_text("# " + result["title"] + "\n\n" + result["summary"] + "\n\n## User stories\n" + "\n".join("- " + x for x in result["user_stories"]) + "\n\n## Acceptance criteria\n" + "\n".join("- " + x for x in result["acceptance_criteria"]) + "\n")
    (path / "request.txt").write_text(request + "\n")
    save_tasks(path, [])
    log(path, "pm", "spec_created", result)
    log(path, "system", "approval_required", {"gate": "spec"})
    return path


def approve(name: str, gate: str) -> None:
    path = project_dir(ROOT, name)
    if gate == "spec":
        if (path / ".approved-spec").exists() or load_tasks(path):
            raise RuntimeError("Spec was already approved; refusing to replace its task plan.")
        try:
            plan = architect.create(config(), (path / "SPEC.md").read_text())
            if not plan["tasks"]:
                raise RuntimeError("Architect produced no tasks; refusing to approve an empty plan.")
            (path / "ARCHITECTURE.md").write_text("# Architecture\n\n" + plan["architecture"] + "\n")
            qa_result = qa.tests(config(), project_context(path))
            if not qa_result["files"]:
                raise RuntimeError("QA produced no tests; refusing to approve a plan without a test target.")
            for item in qa_result["files"]:
                write_file(path, item["path"], item["content"], ("tests",))
            save_tasks(path, [{**task, "status": "todo"} for task in plan["tasks"]])
        except (AgentError, ValueError, OSError, RuntimeError) as error:
            log(path, "system", "approval_setup_failed", {"gate": gate, "error": str(error)})
            raise RuntimeError(f"Spec approval setup failed safely: {error}") from error
        (path / ".approved-spec").write_text("approved\n")
        log(path, "architect", "plan_created", plan)
        log(path, "qa", "tests_written", {"count": len(qa_result["files"])})
        log(path, "human", "approved", {"gate": gate})
        return
    release_file = path / "RELEASE.md"
    if not release_file.exists() or not all_tasks_verified(load_tasks(path)):
        raise RuntimeError("Release approval requires a prepared RELEASE.md and every task completed by the verified pipeline.")
    release_data = json.loads(release_file.read_text())
    if not release_data.get("ready"):
        raise RuntimeError("Release is blocked; resolve the findings in RELEASE.md first.")
    (path / ".approved-release").write_text("approved\n")
    log(path, "human", "approved", {"gate": gate})


def retry(name: str, task_id: str) -> None:
    path = project_dir(ROOT, name)
    task = next((item for item in load_tasks(path) if item["id"] == task_id), None)
    if not task or task["status"] != "failed":
        raise RuntimeError("Only an explicitly failed task can be retried.")
    set_task_status(path, task_id, "todo")
    log(path, "human", "task_retried", {"task": task_id})


def fail_task(path: Path, task: dict, error: Exception | str) -> str:
    message = str(error)
    set_task_status(path, task["id"], "failed", error=message[-4000:])
    log(path, "system", "task_failed", {"task": task["id"], "error": message})
    return f"{task['id']} failed safely; inspect log.jsonl and use retry after correction."


def all_tasks_verified(tasks: list[dict]) -> bool:
    """Do not mistake manually edited task JSON for an executed test result."""
    return bool(tasks) and all(task.get("status") == "done" and task.get("completed_by") == "pipeline"
                               and isinstance(task.get("verification"), dict) for task in tasks)


def run(name: str) -> str:
    path, cfg = project_dir(ROOT, name), config()
    if not (path / ".approved-spec").exists():
        return "Waiting for your SPEC approval. Run: approve NAME spec"
    tasks = load_tasks(path)
    if any(task.get("status") == "done" and task.get("completed_by") != "pipeline" for task in tasks):
        return "Work is blocked: a task claims completion without pipeline verification. Reset it to todo and rerun it."
    non_done = [task for task in tasks if task["status"] != "done"]
    failed = [task for task in non_done if task["status"] == "failed"]
    stranded = [task for task in non_done if task["status"] == "doing"]
    if failed or stranded:
        return "Work is blocked by failed/in-progress tasks; inspect status and explicitly retry a failed task."
    task = next_task(path)
    if not task:
        generated_readme = path / "README.md"
        try:
            if not generated_readme.exists():
                generated_readme.write_text(writer.write(cfg, project_context(path))["readme"])
                log(path, "writer", "documentation_written", {"path": "README.md"})
            if not (path / ".approved-release").exists():
                release_result = release.prepare(path)
                (path / "RELEASE.md").write_text(json.dumps(release_result, indent=2) + "\n")
                log(path, "release", "approval_required", release_result)
                return "All tasks complete. RELEASE.md is ready for your release approval."
        except (AgentError, OSError) as error:
            log(path, "system", "release_preparation_failed", {"error": str(error)})
            return "Release preparation failed safely; inspect log.jsonl."
        return "Released locally (no push is performed by this tool)."
    if not pytest_available():
        log(path, "system", "environment_error", {"error": "pytest is not installed for the active Python interpreter"})
        return "pytest is unavailable. Activate the project virtual environment, then run: pip install -r requirements-dev.txt"
    set_task_status(path, task["id"], "doing")
    feedback = ""
    try:
        for attempt in range(1, cfg["max_fix_attempts"] + 1):
            output = developer.implement(cfg, project_context(path, task, feedback))
            for item in output["files"]:
                write_file(path, item["path"], item["content"], ("src",))
            tests = run_tests(path, cfg["command_timeout_seconds"])
            log(path, "developer", "test_attempt", {"task": task["id"], "attempt": attempt, "result": tests})
            if tests["returncode"] == 0:
                lint = run_linter(path, cfg["command_timeout_seconds"])
                review = reviewer.review(cfg, project_context(path, task, json.dumps({"lint": lint})))
                log(path, "reviewer", "reviewed", review)
                if lint["returncode"] == 0 and review["approved"]:
                    set_task_status(path, task["id"], "done", completed_by="pipeline",
                                    verification={"tests": "passed", "lint": "passed", "review": "approved"})
                    return f"Completed {task['id']}. Run again for the next task."
                feedback = json.dumps({"lint": lint, "review": review})
            else:
                feedback = tests["stdout"] + "\n" + tests["stderr"]
    except (AgentError, ValueError, OSError) as error:
        return fail_task(path, task, error)
    return fail_task(path, task, f"Max fix attempts reached. Last feedback: {feedback[-4000:]}")


def status(name: str) -> None:
    path = project_dir(ROOT, name)
    print(json.dumps({"path": str(path), "tasks": load_tasks(path), "spec_approved": (path / ".approved-spec").exists(), "release_approved": (path / ".approved-release").exists()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Tabz local software-development factory")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new"); new.add_argument("name"); new.add_argument("request")
    app = sub.add_parser("approve"); app.add_argument("name"); app.add_argument("gate", choices=["spec", "release"])
    run_p = sub.add_parser("run"); run_p.add_argument("name")
    retry_p = sub.add_parser("retry"); retry_p.add_argument("name"); retry_p.add_argument("task_id")
    show = sub.add_parser("status"); show.add_argument("name")
    args = parser.parse_args()
    if args.command == "new": print(initialise(args.name, args.request))
    elif args.command == "approve": approve(args.name, args.gate)
    elif args.command == "run": print(run(args.name))
    elif args.command == "retry": retry(args.name, args.task_id)
    else: status(args.name)


if __name__ == "__main__": main()
