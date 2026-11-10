import re
from pathlib import Path
from .runner import run


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def secret_scan(root: Path) -> list[str]:
    findings = []
    for file in root.rglob("*"):
        if not file.is_file() or ".git" in file.parts:
            continue
        content = file.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            findings.append(str(file.relative_to(root)))
    return findings


def git_commit(root: Path, message: str) -> dict:
    findings = secret_scan(root)
    if findings:
        raise RuntimeError(f"Secret scan blocked commit: {findings}")
    run(["git", "add", "."], root, 30)
    return run(["git", "commit", "-m", message], root, 30)
