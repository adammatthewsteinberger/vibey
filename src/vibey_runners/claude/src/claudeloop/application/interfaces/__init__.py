# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application interfaces — every Protocol implemented by infrastructure/ and
never imported from it.

One module per collaborator family so a reader can find the seam by what it
does rather than by scrolling one long file. `application/ports.py` re-exports
this package unchanged, so existing imports keep working.

See docs/architecture/overview.md for the onion rule this enforces:
application/ knows the SHAPE of a collaborator, never its concrete type.
"""

from __future__ import annotations

from claudeloop.application.interfaces.agent import (
    AgentGateway,
    CapacityProbe,
    RunResources,
    SessionCatalog,
)
from claudeloop.application.interfaces.api import ApiGateway
from claudeloop.application.interfaces.control import ControlInbox, RunControl
from claudeloop.application.interfaces.doctor import DoctorEnvironment
from claudeloop.application.interfaces.observability import (
    AuditLog,
    Logger,
    Notifier,
    ProgressReporter,
    RunEventSink,
    StateBus,
)
from claudeloop.application.interfaces.storage import (
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
    SessionLock,
)
from claudeloop.application.interfaces.system import Clock, Sleeper
from claudeloop.application.interfaces.ui import StreamUi

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
