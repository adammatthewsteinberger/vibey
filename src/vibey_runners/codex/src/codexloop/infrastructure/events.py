# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""RunEventSink — append-only JSONL under a run directory."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from codexloop.infrastructure.redact import redact


class JsonlRunEventSink:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    def emit(self, event: Mapping[str, object]) -> None:
        safe = redact(dict(event))
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe, default=str) + "\n")
            handle.flush()
