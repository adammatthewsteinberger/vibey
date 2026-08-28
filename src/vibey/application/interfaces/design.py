# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Phase 1 collaborators: interviewing, researching, and synthesising a spec."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.design import (
    DesignEvent,
    DesignStage,
    QuestionBatch,
    ResearchResult,
)
from vibey.domain.spec import DesignSpec


@runtime_checkable
class DesignProvider(Protocol):
    async def batch(
        self, stage: DesignStage, prior_events: Sequence[DesignEvent]
    ) -> QuestionBatch: ...

    async def research(self, topic: str) -> ResearchResult: ...

    async def synthesize(self, events: Sequence[DesignEvent]) -> DesignSpec: ...


@runtime_checkable
class DesignQuestionProvider(Protocol):
    async def batch(
        self, stage: DesignStage, prior_events: Sequence[DesignEvent]
    ) -> QuestionBatch: ...


@runtime_checkable
class DesignSpecReader(Protocol):
    """Read-only access to an accepted spec, shared by decompose and review."""

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None: ...


@runtime_checkable
class DesignSpecRepository(Protocol):
    async def save(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None: ...

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None: ...

    async def publish(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None: ...


@runtime_checkable
class ResearchProvider(Protocol):
    async def research(self, topic: str) -> ResearchResult: ...


@runtime_checkable
class SpecSynthesizer(Protocol):
    async def synthesize(self, events: Sequence[DesignEvent]) -> DesignSpec: ...
