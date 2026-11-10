from .base import ask
SYSTEM = "You are a technical writer. Return JSON containing a concise README markdown string."
SCHEMA = {"type":"object","properties":{"readme":{"type":"string"}},"required":["readme"]}
def write(config: dict, spec: str) -> dict:
    return ask(config, "writer", SYSTEM, spec, SCHEMA, {"readme":"# Generated project\n\nSee SPEC.md for the approved requirements.\n"})
