# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable run state: the state store, the run lock, git save points, and the
snapshot sink."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RunStateStore(Protocol):
    """Persisted run dicts keyed by run id. load returns None when absent."""

    def save(self, run_id: str, state: dict[str, Any]) -> None: ...
    def load(self, run_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class AgentLock(Protocol):
    """Advisory exclusive lock keyed by agent id."""

    def acquire(self, agent_id: str) -> bool: ...
    def release(self, agent_id: str) -> None: ...


@runtime_checkable
class SavePointStore(Protocol):
    """Worktree save points. Refs are opaque objects until domain savepoint types land."""

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
    ) -> object | None: ...
    def list_points(self, run_id: str) -> list[object]: ...
    def unwind(self, *, run_id: str, to: str, backup: bool) -> object: ...
    def changes_since(self, since_sha: str | None) -> str: ...


@runtime_checkable
class RunSnapshotSink(Protocol):
    """Write a handoff snapshot and publish its path and digest."""

    def emit(
        self,
        reason: str,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> object | None: ...
