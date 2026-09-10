# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Write a handoff snapshot under the run directory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    path: Path
    digest: str
    reason: str


class FileRunSnapshotSink:
    def __init__(self, snapshots_root: Path, *, run_id: str) -> None:
        self._root = snapshots_root
        self._root.mkdir(parents=True, exist_ok=True)
        self._run_id = run_id

    def emit(
        self,
        reason: str,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> SnapshotRef | None:
        del bundle
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": self._run_id,
            "reason": reason,
            "context": context or {},
        }
        body = json.dumps(payload, indent=2, default=str) + "\n"
        digest = hashlib.sha256(body.encode()).hexdigest()[:16]
        path = self._root / f"{digest}-{reason.replace(' ', '_')}.json"
        path.write_text(body, encoding="utf-8")
        return SnapshotRef(path=path, digest=digest, reason=reason)
