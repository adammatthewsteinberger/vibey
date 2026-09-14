# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSONL audit log — the AuditLog port's filesystem adapter."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from codexloop.infrastructure.redact import redact


class JsonlAuditLog:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: Mapping[str, object]) -> None:
        entry: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            **dict(payload),
        }
        safe = redact(entry)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe, default=str) + "\n")
