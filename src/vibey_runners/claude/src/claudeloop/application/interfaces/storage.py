# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable run state: the state store, the session lock, git save points, and
the snapshot sink."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from claudeloop.domain.savepoint import SavePointRef, UnwindResult
from claudeloop.domain.snapshot import SnapshotReason, SnapshotRef


@runtime_checkable
class RunStateStore(Protocol):
    def save(self, run_id: str, state: dict[str, Any]) -> None: ...
    def load(self, run_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class SessionLock(Protocol):
    def acquire(self, session_id: str) -> bool: ...
    def release(self, session_id: str) -> None: ...


@runtime_checkable
class SavePointStore(Protocol):
    def create(
        self,
        *,
        run_id: str,
        label: str,
        message: str = "",
        attempt: int | None = None,
        verdict_name: str = "Continue",
        summary: str = "",
        remaining_work: tuple[str, ...] = (),
    ) -> SavePointRef | None: ...
    def list_points(self, run_id: str) -> list[SavePointRef]: ...
    def unwind(self, *, run_id: str, to: str, backup: bool) -> UnwindResult: ...
    def changes_since(self, since_sha: str | None) -> str: ...


@runtime_checkable
class RunSnapshotSink(Protocol):
    """Write handoff snapshots and publish path+digest on the state bus."""

    def emit(
        self,
        reason: SnapshotReason,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> SnapshotRef | None: ...
