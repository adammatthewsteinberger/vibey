# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable run state seams that converge across the runner family.

Only ``RunStateStore`` and the run/session/agent advisory lock converge
closely enough to share verbatim. ``SavePointStore`` and
``RunSnapshotSink`` do NOT live here: codexloop's versions use materially
different method names, arities, and return shapes (a thinner save-point
API with no ``changes_since``, and a single-argument ``write`` in place of
``emit``) that reflect a genuinely different design, not a typing or
naming difference -- forcing them into one shared protocol would either
misrepresent codexloop's real contract or require methods its concrete
adapter does not implement. They stay local to each runner that has them.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class RunStateStore(Protocol):
    """Persisted run dicts keyed by run id. ``load`` returns None when absent."""

    def save(self, run_id: str, state: Mapping[str, object]) -> None: ...
    def load(self, run_id: str) -> dict[str, object] | None: ...


@runtime_checkable
class SessionLock(Protocol):
    """Advisory exclusive lock keyed by a run/session/agent identifier.

    The identifier's vocabulary is the caller's (a session id, a thread id,
    an agent id) -- this seam only cares that it is a string key.
    """

    def acquire(self, key: str) -> bool: ...
    def release(self, key: str) -> None: ...
