import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import orchestrator
from agents.base import AgentError, ask
from state import project_dir, save_tasks
from tools.files import write_file
from tools.git_tools import secret_scan
from tools.runner import run


class FactorySafetyTests(unittest.TestCase):
    def test_model_failure_is_explicit(self):
        config = {"ollama_url": "http://127.0.0.1:1", "models": {"qa": "missing"}}
        with self.assertRaises(AgentError):
            ask(config, "qa", "system", "user", {"type": "object"})

    def test_agent_cannot_change_control_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_file(Path(tmp), ".approved-release", "approved", ("src",))
            with self.assertRaises(ValueError):
                write_file(Path(tmp), "tests/test_fake.py", "assert True", ("src",))

    def test_timeout_becomes_result_not_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(["python3", "-c", "import time; time.sleep(1)"], Path(tmp), 0.01)
            self.assertEqual(result["returncode"], 124)

    def test_failed_task_cannot_prepare_release(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "ROOT", Path(tmp)), patch.object(orchestrator, "config", return_value={}):
            path = project_dir(Path(tmp), "demo")
            path.mkdir(parents=True)
            (path / ".approved-spec").write_text("approved")
            save_tasks(path, [{"id": "broken", "priority": 1, "status": "failed"}])
            self.assertIn("blocked", orchestrator.run("demo"))
            self.assertFalse((path / "RELEASE.md").exists())

    def test_missing_pytest_stops_before_task_execution(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "ROOT", Path(tmp)), patch.object(orchestrator, "config", return_value={}):
            path = project_dir(Path(tmp), "demo")
            path.mkdir(parents=True)
            (path / ".approved-spec").write_text("approved")
            save_tasks(path, [{"id": "task", "priority": 1, "status": "todo"}])
            with patch.object(orchestrator, "pytest_available", return_value=False):
                self.assertIn("pytest is unavailable", orchestrator.run("demo"))
            self.assertEqual(orchestrator.load_tasks(path)[0]["status"], "todo")

    def test_release_cannot_be_approved_early(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "ROOT", Path(tmp)):
            path = project_dir(Path(tmp), "demo")
            path.mkdir(parents=True)
            save_tasks(path, [{"id": "unfinished", "priority": 1, "status": "todo"}])
            with self.assertRaises(RuntimeError):
                orchestrator.approve("demo", "release")

    def test_second_spec_approval_does_not_reset_plan(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "ROOT", Path(tmp)):
            path = project_dir(Path(tmp), "demo")
            path.mkdir(parents=True)
            (path / ".approved-spec").write_text("approved")
            save_tasks(path, [{"id": "finished", "priority": 1, "status": "done"}])
            with self.assertRaises(RuntimeError):
                orchestrator.approve("demo", "spec")

    def test_empty_qa_output_blocks_spec_approval(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "ROOT", Path(tmp)), patch.object(orchestrator, "config", return_value={}):
            path = project_dir(Path(tmp), "demo")
            path.mkdir(parents=True)
            (path / "SPEC.md").write_text("# Demo")
            save_tasks(path, [])
            with patch.object(orchestrator.architect, "create", return_value={"architecture": "x", "tasks": [{"id": "a", "priority": 1}]}), \
                 patch.object(orchestrator.qa, "tests", return_value={"files": []}):
                with self.assertRaises(RuntimeError):
                    orchestrator.approve("demo", "spec")
            self.assertFalse((path / ".approved-spec").exists())

    def test_mocked_pipeline_completes_only_after_tests_and_review(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "ROOT", Path(tmp)), patch.object(orchestrator, "config", return_value={"max_fix_attempts": 1, "command_timeout_seconds": 10}):
            path = project_dir(Path(tmp), "demo")
            path.mkdir(parents=True)
            (path / "SPEC.md").write_text("# Demo")
            save_tasks(path, [])
            plan = {"architecture": "Python source in src/", "tasks": [{"id": "a", "priority": 1}]}
            qa_output = {"files": [{"path": "tests/test_app.py", "content": "from pathlib import Path\ndef test_source_exists():\n    assert (Path(__file__).parents[1] / 'src' / 'app.py').exists()\n"}]}
            dev_output = {"files": [{"path": "src/app.py", "content": "VALUE = 1\n"}]}
            with patch.object(orchestrator.architect, "create", return_value=plan), \
                 patch.object(orchestrator.qa, "tests", return_value=qa_output), \
                 patch.object(orchestrator.developer, "implement", return_value=dev_output), \
                 patch.object(orchestrator.reviewer, "review", return_value={"approved": True, "findings": []}), \
                 patch.object(orchestrator, "pytest_available", return_value=True), \
                 patch.object(orchestrator, "run_tests", return_value={"returncode": 0, "stdout": "1 passed", "stderr": ""}), \
                 patch.object(orchestrator, "run_linter", return_value={"returncode": 0, "stdout": "", "stderr": ""}):
                orchestrator.approve("demo", "spec")
                self.assertIn("Completed", orchestrator.run("demo"))
            task = orchestrator.load_tasks(path)[0]
            self.assertEqual(task["completed_by"], "pipeline")
            self.assertTrue(orchestrator.all_tasks_verified([task]))

    def test_secret_scan_does_not_flag_normal_hyphenated_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "notes.txt").write_text("A task-list is ordinary text.")
            self.assertEqual(secret_scan(root), [])
