# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""What `doctor` needs from the outside world, and the vocabulary it answers in.

Kept separate from the AgentGateway seam so `doctor` stays cheap to run and
never requires a live SDK session. The result types live here too: they are
part of the seam's vocabulary, not of the use case that consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

AuthLane = Literal["developer_api", "enterprise", "unresolved"]


@dataclass(frozen=True, slots=True)
class AuthResolution:
    """Effective auth lane plus the env/file source that selected it.

    ``lane`` is ``unresolved`` when doctor cannot positively identify
    Developer API vs Enterprise -- it never guesses.
    """

    lane: AuthLane
    source: str
    authenticated: bool
    detail: str


@dataclass(frozen=True, slots=True)
class HarnessStatus:
    """SDK harness availability and smoke-check result."""

    available: bool
    detail: str


@runtime_checkable
class DoctorEnvironment(Protocol):
    """What doctor needs from the outside world -- no live SDK session."""

    def resolve_auth(self) -> AuthResolution: ...
    def interactive_hooks_registered(self) -> bool: ...
    def find_agy_cli(self) -> str | None: ...
    def agy_cli_version(self, path: str) -> str | None: ...
    def configured_mcp_servers(self) -> list[str]: ...
    def check_sdk_harness(self) -> HarnessStatus: ...
