# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The vendor session seam: sending turns, probing capacity, enumerating
sessions, and the run-scoped resources attached to one."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from codexloop.application.dto import ProbeResult, TurnOutcome
from codexloop.application.interfaces.permissions import PermissionMode
from codexloop.domain.model_profile import ModelEffortProfile
from codexloop.domain.session import ThreadRef


@runtime_checkable
class AgentGateway(Protocol):
    """Vendor-agnostic agent session (exec and app-server adapters implement this)."""

    async def send_turn(self, prompt: str) -> TurnOutcome: ...
    async def close(self) -> None: ...
    async def set_profile(self, profile: ModelEffortProfile) -> None: ...
    async def set_permission_mode(self, mode: PermissionMode) -> None: ...
    async def set_cwd(self, path: str) -> None: ...
    async def set_session_resources(self, resources: Mapping[str, object]) -> None: ...
    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool: ...


@runtime_checkable
class CapacityProbe(Protocol):
    async def probe(self) -> ProbeResult: ...


@runtime_checkable
class ThreadCatalog(Protocol):
    """Our run registry keyed by ``thread_id``, not vendor session discovery."""

    def list_threads(self) -> Sequence[ThreadRef]: ...
    def get(self, thread_id: str) -> ThreadRef | None: ...
    def record(self, ref: ThreadRef) -> None: ...


@runtime_checkable
class RunResources(Protocol):
    """Placeholder for run-scoped attachments applied mid-run."""

    def as_payload(self) -> Mapping[str, object]: ...
