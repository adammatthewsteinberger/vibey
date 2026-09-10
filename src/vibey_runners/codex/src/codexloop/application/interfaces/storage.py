# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable run state: the state store, the run lock, git save points, and the
snapshot sink."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class RunStateStore(Protocol):
    def load(self, run_id: str) -> dict[str, object] | None: ...
    def save(self, run_id: str, state: Mapping[str, object]) -> None: ...


@runtime_checkable
class SessionLock(Protocol):
    def acquire(self, thread_id: str) -> bool: ...
    def release(self, thread_id: str) -> None: ...


@runtime_checkable
class SavePointStore(Protocol):
    def create(self, run_id: str, label: str) -> str: ...
    def list(self, run_id: str) -> Sequence[str]: ...
    def unwind(self, run_id: str, to: str) -> None: ...


@runtime_checkable
class RunSnapshotSink(Protocol):
    def write(self, snapshot: Mapping[str, object]) -> None: ...
