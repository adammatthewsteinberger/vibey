# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The vendor session seam: sending turns, probing capacity, and the
run-scoped resources attached to a session."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from claudeloop.application.dto import TurnOutcome
from claudeloop.domain.model_profile import ModelEffortProfile
from claudeloop.domain.session import SessionRef


@runtime_checkable
class AgentGateway(Protocol):
    """Wraps a live claude_agent_sdk.ClaudeSDKClient session. Deliberately NOT
    query() — see docs/architecture/decisions/0002-agent-sdk-over-subprocess.md
    for why query() cannot be used here (it raises after an error result and
    exits the process, where ClaudeSDKClient survives to be resumed)."""

    async def send_turn(self, prompt_text: str) -> TurnOutcome: ...
    async def close(self) -> None: ...
    async def set_profile(self, profile: ModelEffortProfile) -> None: ...
    async def set_permission_mode(self, mode: str) -> None: ...
    async def set_cwd(self, cwd: str) -> None: ...
    async def set_session_resources(self, **kwargs: Any) -> None: ...
    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool: ...


@runtime_checkable
class CapacityProbe(Protocol):
    async def probe(self) -> TurnOutcome: ...


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
class SessionCatalog(Protocol):
    def most_recent(self, cwd: str) -> SessionRef | None: ...
    def list_all(self, cwd: str | None = None) -> list[SessionRef]: ...
