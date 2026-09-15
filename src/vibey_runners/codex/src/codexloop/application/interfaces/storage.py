# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable run state seams specific to codexloop's own design.

``RunStateStore`` and ``SessionLock`` moved to
``vibey_runners.common.application.interfaces.storage`` (they converge
verbatim across the runner family). ``SavePointStore`` and
``RunSnapshotSink`` stay here: this runner's save-point API is
deliberately thinner than the other runners' in this family (no
``changes_since``, plain ``str``/``Sequence[str]`` refs instead of typed
save-point/unwind results) and its snapshot sink is a single-argument
``write`` rather than an ``emit`` keyed by reason -- a different design,
not a naming difference.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class SavePointStore(Protocol):
    def create(self, run_id: str, label: str) -> str: ...
    def list(self, run_id: str) -> Sequence[str]: ...
    def unwind(self, run_id: str, to: str) -> None: ...


@runtime_checkable
class RunSnapshotSink(Protocol):
    def write(self, snapshot: Mapping[str, object]) -> None: ...
