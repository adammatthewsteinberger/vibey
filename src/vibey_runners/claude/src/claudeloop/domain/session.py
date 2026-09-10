# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Session reference and selection value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from claudeloop.domain.errors import InvalidSessionSelectorError


@dataclass(frozen=True, slots=True)
class SessionRef:
    """A resolved reference to a Claude Code session."""

    session_id: str
    cwd: str
    last_modified: datetime | None = None
    git_branch: str | None = None
    first_prompt_preview: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise InvalidSessionSelectorError("session_id must not be blank")
        if not self.cwd.strip():
            raise InvalidSessionSelectorError("cwd must not be blank")


@dataclass(frozen=True, slots=True)
class PlanFileSelector:
    """Start a brand-new session seeded from the contents of a plan file."""

    plan_path: str

    def __post_init__(self) -> None:
        if not self.plan_path.strip():
            raise InvalidSessionSelectorError("plan_path must not be blank")


@dataclass(frozen=True, slots=True)
class ExplicitSessionSelector:
    """Resume a specific, caller-known session id."""

    session_id: str

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise InvalidSessionSelectorError("session_id must not be blank")


@dataclass(frozen=True, slots=True)
class MostRecentSessionSelector:
    """Auto-select the most recently modified session for a working directory."""

    cwd: str

    def __post_init__(self) -> None:
        if not self.cwd.strip():
            raise InvalidSessionSelectorError("cwd must not be blank")


SessionSelector = PlanFileSelector | ExplicitSessionSelector | MostRecentSessionSelector
