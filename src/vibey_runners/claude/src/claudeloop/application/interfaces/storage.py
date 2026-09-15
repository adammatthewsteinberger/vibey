# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable run state seams specific to claudeloop's own design.

``RunStateStore`` and ``SessionLock`` moved to
``vibey_runners.common.application.interfaces.storage`` (they converge
verbatim across the runner family, modulo the domain-typed save-point and
snapshot result types below, which stay generic in the shared version).
``SavePointStore`` and ``RunSnapshotSink`` stay here, typed against this
runner's own domain save-point/snapshot vocabulary, because one of the
four runners in this family has a materially thinner save-point API (no
``changes_since``, plain string refs) and a differently shaped snapshot
sink -- a genuine design difference, not a naming one, so those two
protocols were not pulled into the shared package.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from claudeloop.domain.savepoint import SavePointRef, UnwindResult
from claudeloop.domain.snapshot import SnapshotReason, SnapshotRef


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
