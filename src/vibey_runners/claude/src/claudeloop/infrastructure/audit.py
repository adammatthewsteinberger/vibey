# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-run JSONL audit log — the AuditLog port's real implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claudeloop.infrastructure.redact import redact


class JsonlAuditLog:
    def __init__(self, path: Path, *, run_id: str | None = None) -> None:
        self._path = path
        self._run_id = run_id
        self._session_id: str | None = None
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def bind(self, *, run_id: str | None = None, session_id: str | None = None) -> None:
        if run_id is not None:
            self._run_id = run_id
        if session_id is not None:
            self._session_id = session_id

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
        }
        if self._run_id is not None:
            entry["run_id"] = self._run_id
        if self._session_id is not None:
            entry["session_id"] = self._session_id
        entry.update(payload)
        safe = redact(entry)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe, default=str) + "\n")
