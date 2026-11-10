"""Ollama client with strict JSON contracts. Failures are explicit, never stubbed."""
from __future__ import annotations
import json
import urllib.request


class AgentError(RuntimeError):
    pass


def ask(config: dict, role: str, system: str, user: str, schema: dict, fallback: dict | None = None) -> dict:
    body = {"model": config["models"][role], "stream": False, "format": schema,
            "options": {"temperature": config.get("temperature", 0.2)},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    try:
        request = urllib.request.Request(config["ollama_url"] + "/api/chat", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(json.loads(response.read())["message"]["content"])
    except Exception as error:
        raise AgentError(f"{role} model request failed: {type(error).__name__}: {error}") from error
