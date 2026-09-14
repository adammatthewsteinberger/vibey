# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""What `doctor` needs from the outside world.

Kept separate from the larger AgentGateway/SessionCatalog seams so `doctor`
stays cheap to run and never requires a live SDK connection.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DoctorEnvironment(Protocol):
    def find_claude_cli(self) -> str | None: ...
    def claude_cli_version(self, path: str) -> str | None: ...
    def is_authenticated(self) -> bool: ...
    def configured_mcp_servers(self) -> list[str]: ...
    def anthropic_sdk_version(self) -> str | None: ...
    def api_surface_method_count(self) -> int | None: ...
