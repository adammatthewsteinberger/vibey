# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""RunStateStore — persist run state as ``state.json`` under a run directory."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from codexloop.infrastructure.redact import redact


class FileRunStateStore:
    def __init__(self, runs_root: Path) -> None:
        self._runs_root = runs_root

    def _path(self, run_id: str) -> Path:
        return self._runs_root / run_id / "state.json"

    def load(self, run_id: str) -> dict[str, object] | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data

    def save(self, run_id: str, state: Mapping[str, object]) -> None:
        path = self._path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        safe = redact(dict(state))
        path.write_text(json.dumps(safe, default=str) + "\n", encoding="utf-8")
