# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application interfaces -- every seam implemented by infrastructure/ and
never imported from it.

One module per collaborator family so a reader finds a seam by what it does
rather than by scrolling one long file. `application/ports.py` re-exports
this package unchanged, so existing imports keep working.
"""

from __future__ import annotations

from cursorloop.application.interfaces.agent import (
    AgentCatalog,
    AgentGateway,
    CapacityProbe,
    HookManager,
    ModelCatalog,
)
from cursorloop.application.interfaces.api import (
    ApiGateway,
)
from cursorloop.application.interfaces.control import (
    RunControl,
)
from cursorloop.application.interfaces.observability import (
    AuditLog,
    Logger,
    Notifier,
    ProgressReporter,
    RunEventSink,
    StateBus,
    UsageReader,
)
from cursorloop.application.interfaces.storage import (
    AgentLock,
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
)
from cursorloop.application.interfaces.system import (
    Clock,
    Sleeper,
)
from cursorloop.application.interfaces.ui import (
    StreamUi,
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
