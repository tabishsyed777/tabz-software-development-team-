# Tabz Software Development Team

An approval-gated, local-first software factory that coordinates focused Ollama roles to turn an idea into a tested project. It keeps the human in control at the specification and release stages, records each step in an inspectable log, and prevents model output from controlling workflow state.

## What it does

```text
Request → Product Manager → your spec approval → Architect → QA tests
        → Developer → pytest repair loop (max 5 attempts) → Reviewer
        → Documentation → your release approval
```

Each generated project lives in `workspace/<project-name>/` and includes its specification, architecture, task board, tests, and JSONL event log.

## Highlights

- Narrow, structured roles: PM, Architect, QA, Developer, Reviewer, Writer, and Release.
- Human approval gates before planning and release.
- Test-first workflow: an empty QA response blocks approval.
- Developer writes are limited to `src/`; QA writes are limited to `tests/`.
- Explicit model failures, bounded command timeouts, and a five-attempt repair cap.
- Release is blocked unless every task has verified pipeline completion.
- Local JSONL audit trail and a lightweight secret scan before commits.

## Requirements

- Python 3.11 or newer
- [Ollama](https://ollama.com/) running locally for autonomous agent runs
- A model installed for every role configured in `config.yaml`

## Quick start

```bash
git clone https://github.com/tabishsyed777/tabz-software-development-team-.git
cd tabz-software-development-team-
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ollama serve
```

In another terminal, create a project and inspect its proposed specification:

```bash
python3 orchestrator.py new expense-tracker "Build a CLI expense tracker with CSV export"
open workspace/expense-tracker/SPEC.md
```

If you approve the specification:

```bash
python3 orchestrator.py approve expense-tracker spec
python3 orchestrator.py run expense-tracker
python3 orchestrator.py status expense-tracker
```

Run `run` once for each task. When all tasks have passed, inspect `RELEASE.md`, then explicitly approve release preparation:

```bash
python3 orchestrator.py approve expense-tracker release
python3 orchestrator.py run expense-tracker
```

The factory never pushes code to GitHub on its own.

## Project layout

| Path | Purpose |
| --- | --- |
| `orchestrator.py` | Approval gates, task loop, and error handling |
| `agents/` | Role contracts and Ollama client |
| `tools/` | Constrained file, process, and Git helpers |
| `state.py` | Task board and append-only event log |
| `config.yaml` | Model names, limits, and endpoint configuration |
| `evals/prompts.json` | Starter prompts for measuring quality |
| `tests/` | Regression tests for workflow and safety boundaries |

## Safety model

LLM output is data, not authority. Agents return structured JSON; they do not execute shell commands directly. File writes are restricted by role, subprocesses use `shell=False` and timeouts, and a failed or interrupted task blocks release rather than being treated as complete.

This is a local developer tool, not a security boundary against the person who owns the filesystem. Review generated code, run it in a virtual environment or container, and never use administrator privileges.

## Configuration

`config.yaml` is JSON-compatible YAML. Set each role to an installed Ollama model. For a single-model setup, point every role to the same available model, for example `qwen2.5-coder:7b`.

If `pytest` is missing from the active environment, the factory stops before changing a task and tells you how to install it.

## Verification

```bash
python3 -m pytest -q
```

The suite covers model failures, write restrictions, timeout handling, approval rules, release blocking, false-positive secret scanning, and a mocked end-to-end pipeline.

## License

No license has been selected yet. Add one before distributing or accepting outside contributions.
