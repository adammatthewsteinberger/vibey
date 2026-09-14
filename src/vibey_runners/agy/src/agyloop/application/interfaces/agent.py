# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The vendor session seam: sending turns, probing capacity, enumerating
sessions, and the run-scoped resources attached to one."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agyloop.application.dto import TurnOutcome
from agyloop.domain.model_profile import ModelEffortProfile
from agyloop.domain.session import SessionRef


@runtime_checkable
class AgentGateway(Protocol):
    """Wraps a live google.antigravity Agent session. The port must not leak
    google.antigravity types: ``set_permission_mode`` takes an agyloop enum
    (autonomous | scoped | safe | yolo) that a later adapter compiles into a
    policy list. Deliberately not a one-shot query — the session survives a
    capacity rejection so the run can probe and resume.
    """

    async def send_turn(self, prompt_text: str) -> TurnOutcome: ...
    async def close(self) -> None: ...
    async def set_profile(self, profile: ModelEffortProfile) -> None: ...
    async def set_permission_mode(self, mode: str) -> None: ...
    async def set_cwd(self, cwd: str) -> None: ...
    async def set_session_resources(self, **kwargs: Any) -> None: ...
    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool: ...


@runtime_checkable
class RunResources(Protocol):
    """Run-scoped attachments / skills / folders / memories applied mid-run."""

    def apply_mutate(
        self, *, action: str, kind: str, value: str, name: str | None = None
    ) -> dict[str, Any]: ...
    def gateway_payload(self) -> dict[str, Any]: ...
    def set_permission_mode(self, mode: str) -> None: ...
    def set_cwd(self, path: str) -> None: ...


@runtime_checkable
class CapacityProbe(Protocol):
    async def probe(self) -> TurnOutcome: ...


@runtime_checkable
class SessionCatalog(Protocol):
    """Enumerates agyloop's run registry, not vendor conversations."""

    def most_recent(self, cwd: str) -> SessionRef | None: ...
    def list_all(self, cwd: str | None = None) -> list[SessionRef]: ...
