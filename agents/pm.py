from .base import ask

SYSTEM = "You are a product manager. Return concise JSON only. Make requirements testable; do not invent dependencies."
SCHEMA = {"type":"object","properties":{"title":{"type":"string"},"summary":{"type":"string"},"user_stories":{"type":"array","items":{"type":"string"}},"acceptance_criteria":{"type":"array","items":{"type":"string"}},"allowed_packages":{"type":"array","items":{"type":"string"}}},"required":["title","summary","user_stories","acceptance_criteria","allowed_packages"]}

def create(config: dict, request: str) -> dict:
    return ask(config, "pm", SYSTEM, request, SCHEMA, {"title": request, "summary": request, "user_stories":["A user can use the requested feature."], "acceptance_criteria":["The project has passing automated tests."], "allowed_packages":[]})
