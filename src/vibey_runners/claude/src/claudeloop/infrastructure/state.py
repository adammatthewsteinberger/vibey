# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""RunStateStore — persists run state to disk so a killed run can be
resumed. One JSON file per run_id under a state directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileRunStateStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        return self._directory / f"{run_id}.json"

    def save(self, run_id: str, state: dict[str, Any]) -> None:
        self._path(run_id).write_text(json.dumps(state, default=str), encoding="utf-8")

    def load(self, run_id: str) -> dict[str, Any] | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
