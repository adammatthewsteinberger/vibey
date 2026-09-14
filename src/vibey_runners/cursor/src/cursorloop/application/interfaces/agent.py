# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The vendor session seam: sending turns, probing capacity, enumerating
sessions, and the run-scoped resources attached to one."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cursorloop.application.dto import TurnOutcome
from cursorloop.domain.model_profile import ModelProfile
from cursorloop.domain.session import AgentRef


@runtime_checkable
class AgentGateway(Protocol):
    """Wraps a durable cursor_sdk Agent. Each send_turn() maps to one
    agent.send() → Run. An errored Run does NOT invalidate the agent, so the
    outer loop is repeated sends on one handle, never respawn-and-reattach."""

    async def send_turn(self, prompt_text: str, *, force: bool = False) -> TurnOutcome: ...
    async def close(self) -> None: ...
    async def set_profile(self, profile: ModelProfile) -> None: ...
    async def set_cwd(self, cwd: str) -> None: ...
    async def cancel_active_run(self) -> bool: ...
    def agent_id(self) -> str: ...


@runtime_checkable
class CapacityProbe(Protocol):
    """Cheap throwaway capacity check. Returns turn signals, not a live-session turn."""

    async def probe(self) -> TurnOutcome: ...


@runtime_checkable
class AgentCatalog(Protocol):
    """Resolved agent handles for a working directory. Never a filesystem glob."""

    def most_recent(self, cwd: str) -> AgentRef | None: ...
    def list_all(self, cwd: str | None = None) -> list[AgentRef]: ...


@runtime_checkable
class ModelCatalog(Protocol):
    """Vendor-published model identifiers. Implementations return ids, never SDK types."""

    def list_all(self) -> list[str]: ...


@runtime_checkable
class HookManager(Protocol):
    """Autonomy policy lives in .cursor/hooks.json because Cursor hooks are
    file-based only — there is no programmatic permission callback."""

    def install(self) -> None: ...
    def restore(self) -> bool: ...
    def is_installed(self) -> bool: ...
