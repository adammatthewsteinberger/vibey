# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""File-backed state bus — pub/sub for run state changes.

Subscribers can:
- poll ``status.json`` (latest snapshot), or
- follow ``bus.jsonl`` (append-only event stream of every publish).

No network daemon required; other processes use ``claudeloop status`` /
``claudeloop watch`` or read the files directly.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claudeloop.infrastructure.redact import redact


class FileStateBus:
    def __init__(self, *, status_path: Path, bus_path: Path, run_id: str) -> None:
        self._status_path = status_path
        self._bus_path = bus_path
        self._run_id = run_id
        self._status_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._bus_path.exists():
            self._bus_path.touch()

    def publish(self, event_type: str, state: dict[str, Any]) -> None:
        payload = redact(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "run_id": self._run_id,
                "event_type": event_type,
                **state,
            }
        )
        self._write_status_atomic(payload)
        with self._bus_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
            f.flush()

    def _write_status_atomic(self, payload: dict[str, Any]) -> None:
        parent = self._status_path.parent
        fd, tmp_name = tempfile.mkstemp(prefix=".status-", dir=parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json.dumps(payload, indent=2, default=str) + "\n")
            os.replace(tmp_name, self._status_path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise
