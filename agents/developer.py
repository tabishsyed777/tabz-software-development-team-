from .base import ask

SYSTEM = "You are a developer. Return JSON with a small list of files under src/ only. Never modify tests, specs, task state, approvals, or documentation. Never include shell commands."
SCHEMA = {"type":"object","properties":{"files":{"type":"array","items":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},"required":["files"]}

def implement(config: dict, context: str) -> dict:
    return ask(config, "developer", SYSTEM, context, SCHEMA)
