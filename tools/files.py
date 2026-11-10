from pathlib import Path


def _target(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        raise ValueError("Path escapes the project workspace")
    return target


def read_file(root: Path, relative: str) -> str:
    return _target(root, relative).read_text(encoding="utf-8")


def write_file(root: Path, relative: str, content: str, allowed_roots: tuple[str, ...]) -> None:
    if not allowed_roots or not any(relative == item or relative.startswith(item + "/") for item in allowed_roots):
        raise ValueError(f"Agent is not allowed to write {relative!r}; allowed roots: {allowed_roots}")
    target = _target(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def list_files(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)
