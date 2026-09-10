# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The wind-down marker a supervisor reads: ``runs/<id>/handoff.json``.

Why a separate file rather than reusing ``snapshots/latest.json``: latest.json
is rewritten on every ``status`` snapshot, which happens on every turn, so its
existence proves nothing. handoff.json is written once per run and only after
every artifact it names is on disk, so its existence *is* the assertion.

That ordering gives the invariant a supervisor depends on:

    If handoff.json exists, every artifact it names exists.

A process killed mid-wind-down leaves no marker, and the supervisor falls back
to the reactive path it used before. Degradation, never a half-written handoff.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

HANDOFF_MARKER_FILENAME = "handoff.json"
HANDOFF_SCHEMA_VERSION = 1

# EX_TEMPFAIL. 0/1/2 and 130 (operator stop) are already taken, and a
# supervisor needs to tell "handed off, resume me elsewhere" from "failed".
EXIT_WIND_DOWN = 75


@dataclass(frozen=True, slots=True)
class HandoffMarker:
    run_id: str
    reason: str
    produced_at: datetime
    headroom: float | None = None
    headroom_source: str = ""
    resets_at: datetime | None = None
    snapshot_path: str | None = None
    bundle_path: str | None = None
    stop_summary_path: str | None = None
    savepoint_ref: str | None = None
    savepoint_sha: str | None = None
    session_id: str | None = None
    turns_spent: int = 0
    dollars_spent: float = 0.0
    remaining_work: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": HANDOFF_SCHEMA_VERSION,
            "run_id": self.run_id,
            "reason": self.reason,
            "produced_at": self.produced_at.isoformat(),
            "forecast": {
                "headroom": self.headroom,
                "source": self.headroom_source,
                "resets_at": self.resets_at.isoformat() if self.resets_at else None,
            },
            "snapshot_path": self.snapshot_path,
            "bundle_path": self.bundle_path,
            "stop_summary_path": self.stop_summary_path,
            "savepoint": {"ref": self.savepoint_ref, "sha": self.savepoint_sha},
            "session_id": self.session_id,
            "turns_spent": self.turns_spent,
            "dollars_spent": self.dollars_spent,
            "remaining_work": list(self.remaining_work),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def named_artifacts(self) -> tuple[str, ...]:
        """Paths this marker claims exist -- what a reader is entitled to open."""
        return tuple(
            path for path in (self.snapshot_path, self.bundle_path, self.stop_summary_path) if path
        )


def parse_marker(payload: str) -> HandoffMarker:
    data = json.loads(payload)
    version = data.get("schema_version")
    if version != HANDOFF_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported handoff schema {version!r}; this build understands "
            f"{HANDOFF_SCHEMA_VERSION}"
        )
    forecast = data.get("forecast") or {}
    savepoint = data.get("savepoint") or {}
    resets_at = forecast.get("resets_at")
    return HandoffMarker(
        run_id=str(data["run_id"]),
        reason=str(data["reason"]),
        produced_at=datetime.fromisoformat(data["produced_at"]),
        headroom=forecast.get("headroom"),
        headroom_source=str(forecast.get("source") or ""),
        resets_at=datetime.fromisoformat(resets_at) if resets_at else None,
        snapshot_path=data.get("snapshot_path"),
        bundle_path=data.get("bundle_path"),
        stop_summary_path=data.get("stop_summary_path"),
        savepoint_ref=savepoint.get("ref"),
        savepoint_sha=savepoint.get("sha"),
        session_id=data.get("session_id"),
        turns_spent=int(data.get("turns_spent", 0)),
        dollars_spent=float(data.get("dollars_spent", 0.0)),
        remaining_work=tuple(data.get("remaining_work") or ()),
    )
