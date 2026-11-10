import tempfile
import unittest
from pathlib import Path
from state import project_dir, save_tasks, next_task, set_task_status
from tools.files import write_file

class StateTests(unittest.TestCase):
    def test_highest_priority_todo_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_tasks(root, [{"id":"low","priority":1,"status":"todo"}, {"id":"high","priority":9,"status":"todo"}])
            self.assertEqual(next_task(root)["id"], "high")
            set_task_status(root, "high", "done")
            self.assertEqual(next_task(root)["id"], "low")

    def test_write_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): write_file(Path(tmp), "../outside.txt", "no", ("src",))

    def test_project_names_are_safe(self):
        self.assertEqual(project_dir(Path("/tmp"), "Hello World!").name, "hello-world")
