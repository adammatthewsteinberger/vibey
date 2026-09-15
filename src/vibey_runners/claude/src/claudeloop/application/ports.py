# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Backwards-compatible re-export of `application.interfaces`.

The Protocols moved into `application/interfaces/` so every seam lives in one
discoverable place, one module per collaborator family. This shim keeps the
old `from claudeloop.application.ports import X` import path working; new code
should import from `claudeloop.application.interfaces`.
"""

from __future__ import annotations

from claudeloop.application.interfaces import (
    AgentGateway,
    ApiGateway,
    AuditLog,
    CapacityProbe,
    Clock,
    ControlInbox,
    DoctorEnvironment,
    Logger,
    Notifier,
    ProgressReporter,
    RunControl,
    RunEventSink,
    RunResources,
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
    SessionCatalog,
    SessionLock,
    Sleeper,
    StateBus,
    StreamUi,
)

__all__ = [
    "AgentGateway",
    "ApiGateway",
    "AuditLog",
    "CapacityProbe",
    "Clock",
    "ControlInbox",
    "DoctorEnvironment",
    "Logger",
    "Notifier",
    "ProgressReporter",
    "RunControl",
    "RunEventSink",
    "RunResources",
    "RunSnapshotSink",
    "RunStateStore",
    "SavePointStore",
    "SessionCatalog",
    "SessionLock",
    "Sleeper",
    "StateBus",
    "StreamUi",
]
