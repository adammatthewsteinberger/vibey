# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""RunStateStore — persists per-run JSON with atomic write-then-rename."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileRunStateStore:
    """One JSON file per ``run_id`` under a state directory."""

    def __init__(self, directory: Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        return self._directory / f"{run_id}.json"

    def save(self, run_id: str, state: dict[str, Any]) -> None:
        path = self._path(run_id)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(state, default=str, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def load(self, run_id: str) -> dict[str, Any] | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
