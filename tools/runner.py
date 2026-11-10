"""Constrained subprocess runner: no shell, bounded time, project-local cwd."""
from __future__ import annotations
import subprocess
import sys
import importlib.util
from pathlib import Path


def run(command: list[str], cwd: Path, timeout: int) -> dict:
    if not command or any(not isinstance(arg, str) for arg in command):
        raise ValueError("Command must be a non-empty argv list")
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                timeout=timeout, shell=False)
    except subprocess.TimeoutExpired as error:
        return {"returncode": 124, "stdout": (error.stdout or "")[-12000:],
                "stderr": (error.stderr or "")[-12000:] + f"\nTimed out after {timeout}s."}
    return {"returncode": result.returncode, "stdout": result.stdout[-12000:], "stderr": result.stderr[-12000:]}


def run_tests(cwd: Path, timeout: int = 120) -> dict:
    return run([sys.executable, "-m", "pytest", "-q"], cwd, timeout)


def pytest_available() -> bool:
    return importlib.util.find_spec("pytest") is not None


def run_linter(cwd: Path, timeout: int = 120) -> dict:
    return run([sys.executable, "-m", "compileall", "-q", "."], cwd, timeout)
