# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application interfaces -- every seam implemented by infrastructure/ and
never imported from it.

One module per collaborator family so a reader finds a seam by what it does
rather than by scrolling one long file. `application/ports.py` re-exports
this package unchanged, so existing imports keep working.
"""

from __future__ import annotations

from codexloop.application.interfaces.agent import (
    AgentGateway,
    CapacityProbe,
    RunResources,
    ThreadCatalog,
)
from codexloop.application.interfaces.api import (
    ApiGateway,
)
from codexloop.application.interfaces.control import (
    ControlInbox,
    RunControl,
)
from codexloop.application.interfaces.doctor import (
    DoctorCheck,
    DoctorEnvironment,
    DoctorReport,
)
from codexloop.application.interfaces.observability import (
    AuditLog,
    Logger,
    Notifier,
    ProgressReporter,
    RunEventSink,
    StateBus,
)
from codexloop.application.interfaces.permissions import (
    PermissionMode,
)
from codexloop.application.interfaces.storage import (
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
    SessionLock,
)
from codexloop.application.interfaces.system import (
    Clock,
    Sleeper,
)

__all__ = [
    "AgentGateway",
    "ApiGateway",
    "AuditLog",
    "CapacityProbe",
    "Clock",
    "ControlInbox",
    "DoctorCheck",
    "DoctorEnvironment",
    "DoctorReport",
    "Logger",
    "Notifier",
    "PermissionMode",
    "ProgressReporter",
    "RunControl",
    "RunEventSink",
    "RunResources",
    "RunSnapshotSink",
    "RunStateStore",
    "SavePointStore",
    "SessionLock",
    "Sleeper",
    "StateBus",
    "ThreadCatalog",
]
