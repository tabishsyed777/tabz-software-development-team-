from .base import ask

SYSTEM = "You are QA. Propose tests first as JSON. Every path must be under tests/. Do not modify specs, task state, approvals, source, or documentation."
SCHEMA = {"type":"object","properties":{"files":{"type":"array","items":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},"required":["files"]}

def tests(config: dict, context: str) -> dict:
    return ask(config, "qa", SYSTEM, context, SCHEMA)
