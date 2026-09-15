# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Realtime per-run event sink — append-only JSONL with recursive redaction."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claudeloop.infrastructure.redact import redact


class JsonlRunEventSink:
    def __init__(
        self,
        path: Path,
        *,
        run_id: str,
        trace_id: str | None = None,
    ) -> None:
        self._path = path
        self._run_id = run_id
        self._trace_id = trace_id
        self._session_id: str | None = None
        self._attempt: int = 0
        self._phase: str | None = None
        self._turn_id: str | None = None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    def bind(
        self,
        *,
        session_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None:
        if session_id is not None:
            self._session_id = session_id
        if attempt is not None:
            self._attempt = attempt
        if phase is not None:
            self._phase = phase
        if trace_id is not None:
            self._trace_id = trace_id
        if turn_id is not None:
            self._turn_id = turn_id

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self._run_id,
            "event_type": event_type,
            "attempt": self._attempt,
            "phase": self._phase,
        }
        if self._trace_id is not None:
            entry["trace_id"] = self._trace_id
        if self._turn_id is not None:
            entry["turn_id"] = self._turn_id
        if self._session_id is not None:
            entry["session_id"] = self._session_id
        if payload:
            entry["payload"] = payload
        safe = redact(entry)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe, default=str) + "\n")
            f.flush()
