from .base import ask

SYSTEM = "You are a software architect. Return JSON with small independently testable tasks."
SCHEMA = {"type":"object","properties":{"architecture":{"type":"string"},"tasks":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"title":{"type":"string"},"description":{"type":"string"},"priority":{"type":"integer"}},"required":["id","title","description","priority"]}}},"required":["architecture","tasks"]}

def create(config: dict, spec: str) -> dict:
    return ask(config, "architect", SYSTEM, spec, SCHEMA, {"architecture":"Implement a small Python package with tests before production code.", "tasks":[{"id":"implement-core","title":"Implement core feature","description":"Use the approved spec and make the QA tests pass.","priority":100}]})
