"""Reading a project and moving it between phases."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import (
    ProjectRecord,
)
from vibey.domain.phase import (
    Phase,
)


@runtime_checkable
class ProjectStore(Protocol):
    async def get(self, project_id: UUID) -> ProjectRecord | None: ...

    async def transition(
        self, project_id: UUID, *, expected: Phase, to: Phase
    ) -> ProjectRecord: ...


@runtime_checkable
class ProjectTransitioner(Protocol):
    async def transition(
        self,
        project_id: UUID,
        *,
        expected: Phase,
        to: Phase,
        cycle: int | None = None,
    ) -> Any: ...
