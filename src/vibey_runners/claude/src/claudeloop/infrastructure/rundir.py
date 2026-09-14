# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-run control directory layout under `.claudeloop/runs/<run_id>/`."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claudeloop.domain.handoff_marker import (
    HANDOFF_MARKER_FILENAME,
    HandoffMarker,
)

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


@dataclass
class RunMeta:
    run_id: str
    pid: int
    cwd: str
    started_at: str
    session_id: str | None = None
    plan_path: str | None = None
    status: str = "active"  # active | stopped | finished | failed
    phase: str | None = None
    attempt: int = 0
    waiting_until: str | None = None
    model: str | None = None
    effort: str | None = None
    preset: str | None = None
    capacity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunMeta:
        return cls(
            run_id=str(data["run_id"]),
            pid=int(data["pid"]),
            cwd=str(data["cwd"]),
            started_at=str(data["started_at"]),
            session_id=data.get("session_id"),
            plan_path=data.get("plan_path"),
            status=str(data.get("status", "active")),
            phase=data.get("phase"),
            attempt=int(data.get("attempt", 0)),
            waiting_until=data.get("waiting_until"),
            model=data.get("model"),
            effort=data.get("effort"),
            preset=data.get("preset"),
            capacity=data.get("capacity"),
        )


class RunDirectory:
    """Filesystem layout for one autonomous run's control plane."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.inbox = root / "inbox"
        self.events_path = root / "events.jsonl"
        self.meta_path = root / "meta.json"
        self.savepoints_path = root / "savepoints.jsonl"
        self.stop_summary_path = root / "stop-summary.md"
        self.lock_path = root / "run.lock"

    @classmethod
    def create(
        cls,
        runs_root: Path,
        *,
        cwd: Path,
        plan_path: Path | None = None,
        run_id: str | None = None,
    ) -> RunDirectory:
        """Create a fresh run directory.

        ``run_id`` lets an orchestrator name the run up front instead of
        scraping it from stderr after the process exits. That matters when
        several runs are in flight at once: "the newest directory under
        runs/" is a race, and there is no other way to attach to a run while
        it is still going.
        """
        if run_id is None:
            run_id = (
                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
            )
        else:
            run_id = validate_run_id(run_id)
        directory = cls(runs_root / run_id)
        directory.root.mkdir(parents=True, exist_ok=False)
        directory.inbox.mkdir()
        (directory.root / "resources").mkdir()
        (directory.root / "memories").mkdir()
        (directory.root / "artifacts").mkdir()
        (directory.root / "snapshots").mkdir()
        meta = RunMeta(
            run_id=run_id,
            pid=os.getpid(),
            cwd=str(cwd.resolve()),
            started_at=datetime.now(timezone.utc).isoformat(),
            plan_path=str(plan_path.resolve()) if plan_path else None,
        )
        directory.write_meta(meta)
        directory.events_path.touch()
        directory.savepoints_path.touch()
        return directory

    @classmethod
    def open_existing(cls, path: Path) -> RunDirectory:
        directory = cls(path)
        if not directory.meta_path.is_file():
            raise FileNotFoundError(f"not a claudeloop run directory: {path}")
        return directory

    def write_meta(self, meta: RunMeta) -> None:
        self.meta_path.write_text(json.dumps(meta.to_dict(), indent=2) + "\n", encoding="utf-8")

    def read_meta(self) -> RunMeta:
        data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return RunMeta.from_dict(data)

    def update_meta(self, **kwargs: Any) -> RunMeta:
        meta = self.read_meta()
        for key, value in kwargs.items():
            setattr(meta, key, value)
        self.write_meta(meta)
        return meta

    def write_stop_summary(self, markdown: str) -> Path:
        self.stop_summary_path.write_text(markdown, encoding="utf-8")
        return self.stop_summary_path

    @property
    def handoff_marker_path(self) -> Path:
        return self.root / HANDOFF_MARKER_FILENAME

    def write_handoff_marker(self, marker: HandoffMarker) -> Path:
        """Write the marker atomically, as the last act of a wind-down.

        tmp-then-replace so a reader never sees a partial marker: its whole
        purpose is to assert that the artifacts it names are on disk, and a
        truncated one would assert that falsely.
        """
        target = self.handoff_marker_path
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(marker.to_json(), encoding="utf-8")
        os.replace(tmp, target)
        return target

    @property
    def resources_root(self) -> Path:
        return self.root / "resources"

    @property
    def snapshots_root(self) -> Path:
        return self.root / "snapshots"


def runs_root_for(cwd: Path) -> Path:
    return cwd / ".claudeloop" / "runs"


def list_run_directories(cwd: Path) -> list[RunDirectory]:
    root = runs_root_for(cwd)
    if not root.is_dir():
        return []
    dirs = [RunDirectory.open_existing(p) for p in sorted(root.iterdir()) if p.is_dir()]
    return dirs


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # pragma: no cover - process exists but not ours
        return True
    return True


def resolve_run_directory(cwd: Path, run_id: str | None = None) -> RunDirectory:
    """Resolve an explicit run id, else the most recent active (live pid) run."""
    if run_id is not None:
        path = runs_root_for(cwd) / run_id
        return RunDirectory.open_existing(path)

    candidates = list_run_directories(cwd)
    for directory in reversed(candidates):
        meta = directory.read_meta()
        if meta.status == "active" and _pid_alive(meta.pid):
            return directory
    if candidates:
        return candidates[-1]
    raise FileNotFoundError("no claudeloop runs found under .claudeloop/runs/")
