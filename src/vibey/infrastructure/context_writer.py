"""Filesystem adapter for accepted DESIGN artifacts."""

from collections.abc import Mapping
from pathlib import Path


def write_context_artifacts(repo_path: Path, artifacts: Mapping[str, str]) -> tuple[Path, ...]:
    context_dir = repo_path / ".vibey" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, content in artifacts.items():
        if Path(name).name != name:
            raise ValueError(f"artifact name must be a filename, got {name!r}")
        path = context_dir / name
        if path.exists() and path.read_text() == content:
            continue
        path.write_text(content)
        written.append(path)
    return tuple(written)
