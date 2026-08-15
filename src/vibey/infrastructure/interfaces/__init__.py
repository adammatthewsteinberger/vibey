"""Infrastructure-internal seams.

These are not application ports -- nothing outside infrastructure/ implements
them. They live here so the `every class has an interface in interfaces/`
rule holds at every layer, not just the application boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from vibey.application.dto import RunSpec

if TYPE_CHECKING:  # concrete result types live beside their adapter
    from vibey.infrastructure.engines.claudeloop_process import (
        ClaudeLoopResult,
        CommandResult,
    )


@runtime_checkable
class BoundedClaudeLoop(Protocol):
    async def run(self, spec: RunSpec, *, web_search: bool = False) -> ClaudeLoopResult: ...


@runtime_checkable
class CommandExecutor(Protocol):
    async def execute(self, argv: tuple[str, ...]) -> CommandResult: ...


__all__ = [
    "BoundedClaudeLoop",
    "CommandExecutor",
]
