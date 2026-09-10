# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run handoff snapshot ADTs — pure, no I/O."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

SNAPSHOT_SCHEMA_VERSION = 1

SnapshotReason = Literal[
    "started",
    "stopped",
    "finished",
    "failed",
    "waiting",
    "status",
    "manual",
    "handoff",
]

IMMUTABLE_REASONS: frozenset[SnapshotReason] = frozenset(
    {"started", "stopped", "finished", "failed", "waiting", "manual", "handoff"}
)

# A handoff snapshot is the one that must be complete: it is the only record
# the successor has of what happened, so it bundles like a terminal reason
# even though the work is not finished.
BUNDLE_REASONS: frozenset[SnapshotReason] = frozenset(
    {"stopped", "finished", "failed", "manual", "handoff"}
)


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    """Pointer to a written snapshot for callers / bus subscribers."""

    path: str
    digest: str
    reason: SnapshotReason
    immutable: bool
    bundle_path: str | None = None


def canonical_json_bytes(payload: dict[str, object]) -> bytes:
    """Stable UTF-8 JSON for digests (sorted keys, no whitespace noise)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def digest_payload(payload: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def parse_snapshot_reason(value: str) -> SnapshotReason:
    key = value.strip().lower()
    mapping: dict[str, SnapshotReason] = {
        "started": "started",
        "stopped": "stopped",
        "finished": "finished",
        "failed": "failed",
        "waiting": "waiting",
        "status": "status",
        "manual": "manual",
        "handoff": "handoff",
    }
    if key not in mapping:
        raise ValueError(f"invalid snapshot reason {value!r}; expected one of {sorted(mapping)}")
    return mapping[key]
