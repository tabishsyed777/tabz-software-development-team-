from .base import ask

SYSTEM = "You are a security-minded code reviewer. Return JSON only."
SCHEMA = {"type":"object","properties":{"approved":{"type":"boolean"},"findings":{"type":"array","items":{"type":"string"}}},"required":["approved","findings"]}
def review(config: dict, context: str) -> dict:
    return ask(config, "reviewer", SYSTEM, context, SCHEMA)
