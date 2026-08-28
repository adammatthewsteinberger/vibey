# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The vendor runner seam. Every *loop CLI shape lives behind this."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import (
    EngineEvent,
    EngineHealthRecord,
    PreflightResult,
    RotationCursor,
    RunHandle,
    RunSpec,
    SnapshotRef,
    StopSummary,
)
from vibey.domain.capacity import CapacityState
from vibey.domain.engine import EngineDescriptor, EngineId
from vibey.domain.job import FailureClass


@runtime_checkable
class EngineAdapter(Protocol):
    """infrastructure/engines/ -- the only place vendor CLI shapes exist."""

    @property
    def descriptor(self) -> EngineDescriptor: ...

    async def preflight(self) -> PreflightResult:
        """Runs `<engine> doctor`; classifies auth + availability."""
        ...

    async def start(self, spec: RunSpec) -> RunHandle:
        """Builds argv from descriptor.effort_projection + isolation flags,
        spawns the runner, returns a handle over its run directory."""
        ...

    def tail(self, handle: RunHandle) -> AsyncIterator[EngineEvent]:
        """Streams the runner's events.jsonl, translated into vibey's own
        event vocabulary."""
        ...

    async def send_prompt(self, handle: RunHandle, text: str, *, now: bool) -> None:
        """Writes the runner's control-plane inbox (prompt --now / --at-break)."""
        ...

    async def stop(self, handle: RunHandle) -> StopSummary:
        """Soft-stops the run; collects stop-summary.md and the final
        snapshot."""
        ...

    async def snapshot(self, handle: RunHandle) -> SnapshotRef | None: ...

    def classify(self, raw: Mapping[str, object]) -> CapacityState:
        """Vendor error shape -> vibey's capacity ADT."""
        ...

    def attribute(self, exit_code: int, tail: str) -> FailureClass: ...


@runtime_checkable
class EngineHealthRepository(Protocol):
    async def get(self, project_id: UUID, engine_id: str) -> EngineHealthRecord | None: ...

    async def upsert(self, record: EngineHealthRecord) -> EngineHealthRecord: ...

    async def list_for_project(self, project_id: UUID) -> tuple[EngineHealthRecord, ...]: ...


@runtime_checkable
class RotationCursorRepository(Protocol):
    async def get(self, project_id: UUID, engine_id: EngineId) -> RotationCursor | None: ...

    async def list_for_project(self, project_id: UUID) -> tuple[RotationCursor, ...]: ...

    async def upsert(self, cursor: RotationCursor) -> RotationCursor: ...

    async def update_many(
        self, project_id: UUID, cursors: tuple[RotationCursor, ...]
    ) -> tuple[RotationCursor, ...]: ...

    async def initialize_for_project(
        self, project_id: UUID, engines: tuple[EngineId, ...]
    ) -> tuple[RotationCursor, ...]: ...
