# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Agent reference and selection value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cursorloop.domain.errors import CursorloopError


class InvalidAgentSelectorError(CursorloopError):
    """Raised when an agent selector or reference is malformed."""


def runtime_from_id(agent_id: str) -> str:
    """Cloud agent ids are ``bc-`` prefixed; everything else is local."""
    if agent_id.startswith("bc-"):
        return "cloud"
    return "local"


@dataclass(frozen=True, slots=True)
class AgentRef:
    """A resolved reference to a Cursor agent (local or cloud)."""

    agent_id: str
    runtime: str
    cwd: str
    name: str | None = None
    summary: str | None = None
    last_modified: datetime | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise InvalidAgentSelectorError("agent_id must not be blank")
        if not self.cwd.strip():
            raise InvalidAgentSelectorError("cwd must not be blank")


@dataclass(frozen=True, slots=True)
class PlanFileSelector:
    """Start a brand-new agent seeded from the contents of a plan file."""

    plan_path: str

    def __post_init__(self) -> None:
        if not self.plan_path.strip():
            raise InvalidAgentSelectorError("plan_path must not be blank")


@dataclass(frozen=True, slots=True)
class ExplicitAgentSelector:
    """Resume a specific, caller-known agent id."""

    agent_id: str

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise InvalidAgentSelectorError("agent_id must not be blank")


@dataclass(frozen=True, slots=True)
class MostRecentAgentSelector:
    """Auto-select the most recently modified agent for a working directory."""

    cwd: str

    def __post_init__(self) -> None:
        if not self.cwd.strip():
            raise InvalidAgentSelectorError("cwd must not be blank")


AgentSelector = PlanFileSelector | ExplicitAgentSelector | MostRecentAgentSelector
