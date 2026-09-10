# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-run control directory layout under ``.codexloop/runs/<run_id>/``."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from codexloop.domain.handoff_marker import HANDOFF_MARKER_FILENAME, HandoffMarker

RUN_ID_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def validate_run_id(run_id: str) -> str:
    """Reject run ids that would escape or hide inside ``runs/``.

    A caller-supplied run id becomes a path segment, so ``../..`` or an
    absolute path would write outside the runs root. Leading dots are refused
    too, so a run can never be created hidden.
    """
    candidate = run_id.strip()
    if not RUN_ID_PATTERN.match(candidate):
        raise ValueError(
            f"invalid run id {run_id!r}: must be 1-128 characters of "
            "letters, digits, '.', '_' or '-', and start with a letter or digit"
        )
    return candidate


class RunDirectory:
    """Filesystem layout for one autonomous run's control plane."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.run_id = root.name
        self.meta_path = root / "meta.json"
        self.state_path = root / "state.json"
        self.events_path = root / "events.jsonl"
        self.inbox = root / "inbox"
        self.archive = root / "archive"
        self.savepoints_path = root / "savepoints.jsonl"
        self.snapshots = root / "snapshots"

    @classmethod
    def create(cls, runs_root: Path, *, run_id: str | None = None) -> RunDirectory:
        """Create -- or reopen -- a run directory.

        Unlike the sibling runners, this is deliberately idempotent: a
        supplied ``run_id`` that already exists is reopened with its contents
        intact (see ``test_create_is_idempotent``). Callers that need
        "must be fresh" have to check first.
        """
        run_id = str(uuid.uuid4()) if run_id is None else validate_run_id(run_id)
        directory = cls(runs_root / run_id)
        directory.ensure_layout()
        return directory

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(exist_ok=True)
        self.archive.mkdir(exist_ok=True)
        (self.inbox / "archive").mkdir(exist_ok=True)
        (self.inbox / "quarantine").mkdir(exist_ok=True)
        self.snapshots.mkdir(exist_ok=True)
        if not self.savepoints_path.is_file():
            self.savepoints_path.touch()
        if not self.meta_path.is_file():
            meta = {
                "run_id": self.run_id,
                "pid": os.getpid(),
                "started_at": datetime.now(UTC).isoformat(),
            }
            self.meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        if not self.state_path.is_file():
            self.state_path.write_text("{}\n", encoding="utf-8")
        if not self.events_path.is_file():
            self.events_path.touch()

    def update_meta(self, values: dict[str, object]) -> None:
        """Merge non-secret effective settings into the run metadata."""
        data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
        data.update(values)
        self.meta_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def runs_root_for(cwd: Path) -> Path:
    return cwd / ".codexloop" / "runs"


def write_handoff_marker(run_root: Path, marker: HandoffMarker) -> None:
    """Write handoff marker to runs/<run_id>/handoff.json.

    Uses temp-file + os.replace for crash-safety: if the write fails mid-way,
    any existing marker is left intact. The final marker file only appears
    after the entire payload is written to disk.
    """
    marker_path = run_root / HANDOFF_MARKER_FILENAME
    temp_path = run_root / f".{HANDOFF_MARKER_FILENAME}.{time.time_ns()}.tmp"

    # Write to temp file first
    temp_path.write_text(marker.to_json(), encoding="utf-8")

    # Atomic rename to final destination
    os.replace(temp_path, marker_path)
