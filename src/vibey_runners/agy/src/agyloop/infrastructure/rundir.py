# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-run control directory layout under `.agyloop/runs/<run_id>/`."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
    conversation_id: str | None = None
    plan_path: str | None = None
    status: str = "active"
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
        conversation_id = data.get("conversation_id")
        if conversation_id is None:
            conversation_id = data.get("session_id")
        return cls(
            run_id=str(data["run_id"]),
            pid=int(data["pid"]),
            cwd=str(data["cwd"]),
            started_at=str(data["started_at"]),
            conversation_id=conversation_id,
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
        self.lock_path = root / "run.lock"
        self.snapshots_root = root / "snapshots"
        self.savepoints_path = root / "savepoints.jsonl"
        self.resources_root = root / "resources"
        self.status_path = root / "status.json"
        self.bus_path = root / "bus.jsonl"

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
            run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        else:
            run_id = validate_run_id(run_id)
        directory = cls(runs_root / run_id)
        directory.root.mkdir(parents=True, exist_ok=False)
        directory.inbox.mkdir()
        copied_plan: Path | None = None
        if plan_path is not None:
            copied_plan = directory.root / "plan.md"
            copied_plan.write_text(plan_path.read_text(encoding="utf-8"), encoding="utf-8")
        meta = RunMeta(
            run_id=run_id,
            pid=os.getpid(),
            cwd=str(cwd.resolve()),
            started_at=datetime.now(UTC).isoformat(),
            plan_path=str(copied_plan.resolve()) if copied_plan else None,
        )
        directory.write_meta(meta)
        directory.events_path.touch()
        return directory

    @classmethod
    def open_existing(cls, path: Path) -> RunDirectory:
        directory = cls(path)
        if not directory.meta_path.is_file():
            raise FileNotFoundError(f"not an agyloop run directory: {path}")
        return directory

    def write_meta(self, meta: RunMeta) -> None:
        payload = json.dumps(meta.to_dict(), indent=2) + "\n"
        tmp = self.meta_path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self.meta_path)

    def read_meta(self) -> RunMeta:
        data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return RunMeta.from_dict(data)

    def update_meta(self, **kwargs: Any) -> RunMeta:
        if "session_id" in kwargs and "conversation_id" not in kwargs:
            kwargs["conversation_id"] = kwargs.pop("session_id")
        meta = self.read_meta()
        # Preflight persist starts with session_id=None. Never erase a known
        # conversation_id until a successful turn supplies a replacement.
        if not kwargs.get("conversation_id") and meta.conversation_id:
            kwargs.pop("conversation_id", None)
        for key, value in kwargs.items():
            setattr(meta, key, value)
        self.write_meta(meta)
        return meta

    def read_plan_text(self) -> str | None:
        plan_copy = self.root / "plan.md"
        if plan_copy.is_file():
            return plan_copy.read_text(encoding="utf-8")
        meta = self.read_meta()
        if meta.plan_path and Path(meta.plan_path).is_file():
            return Path(meta.plan_path).read_text(encoding="utf-8")
        return None

    def is_active(self) -> bool:
        meta = self.read_meta()
        if meta.status not in {"active", "waiting"}:
            return False
        return pid_alive(meta.pid)


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def runs_root_for(cwd: Path) -> Path:
    return cwd / ".agyloop" / "runs"


def list_run_directories(cwd: Path) -> list[RunDirectory]:
    root = runs_root_for(cwd)
    if not root.is_dir():
        return []
    directories: list[RunDirectory] = []
    for path in root.iterdir():
        if not path.is_dir():
            continue
        try:
            directories.append(RunDirectory.open_existing(path))
        except FileNotFoundError:
            continue
    return sorted(directories, key=lambda item: item.read_meta().started_at)


def resolve_run_directory(cwd: Path, run_id: str | None = None) -> RunDirectory:
    """Resolve an active explicit run, else the most recent active run."""
    if run_id is not None:
        directory = RunDirectory.open_existing(runs_root_for(cwd) / run_id)
        if directory.is_active():
            return directory
        raise FileNotFoundError(f"agyloop run {run_id} is not active")
    candidates = list_run_directories(cwd)
    for directory in reversed(candidates):
        if directory.is_active():
            return directory
    if candidates:
        raise FileNotFoundError("no active agyloop runs found under .agyloop/runs/")
    raise FileNotFoundError("no agyloop runs found under .agyloop/runs/")


def resolve_run_directory_any(cwd: Path, run_id: str | None = None) -> RunDirectory:
    """Resolve an explicit run (active or not), else newest active, else newest."""
    if run_id is not None:
        return RunDirectory.open_existing(runs_root_for(cwd) / run_id)
    candidates = list_run_directories(cwd)
    for directory in reversed(candidates):
        if directory.is_active():
            return directory
    if candidates:
        return candidates[-1]
    raise FileNotFoundError("no agyloop runs found under .agyloop/runs/")
