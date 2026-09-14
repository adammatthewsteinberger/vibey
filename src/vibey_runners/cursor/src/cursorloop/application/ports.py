# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Backwards-compatible re-export of `application.interfaces`.

The Protocols moved into `application/interfaces/` so every seam lives in
one discoverable place, one module per collaborator family. This shim keeps
the old `from cursorloop.application.ports import X` path working; new code
should import from `cursorloop.application.interfaces`.
"""

from __future__ import annotations

from cursorloop.application.interfaces import (
    AgentCatalog,
    AgentGateway,
    AgentLock,
    ApiGateway,
    AuditLog,
    CapacityProbe,
    Clock,
    HookManager,
    Logger,
    ModelCatalog,
    Notifier,
    ProgressReporter,
    RunControl,
    RunEventSink,
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
    Sleeper,
    StateBus,
    StreamUi,
    UsageReader,
)

__all__ = [
    "AgentCatalog",
    "AgentGateway",
    "AgentLock",
    "ApiGateway",
    "AuditLog",
    "CapacityProbe",
    "Clock",
    "HookManager",
    "Logger",
    "ModelCatalog",
    "Notifier",
    "ProgressReporter",
    "RunControl",
    "RunEventSink",
    "RunSnapshotSink",
    "RunStateStore",
    "SavePointStore",
    "Sleeper",
    "StateBus",
    "StreamUi",
    "UsageReader",
]
