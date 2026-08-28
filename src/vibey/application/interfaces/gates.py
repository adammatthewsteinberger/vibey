# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Human gates: the parked-job seam a person answers (ADR-0009)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import (
    HumanGateRecord,
    HumanGateRequest,
)


@runtime_checkable
class HumanGateRepository(Protocol):
    async def raise_gate(
        self, project_id: UUID, job_id: UUID | None, request: HumanGateRequest
    ) -> HumanGateRecord: ...

    async def answer(
        self, gate_id: UUID, *, answer: Mapping[str, object], answered_by: str
    ) -> HumanGateRecord: ...

    async def latest_for_job(self, job_id: UUID) -> HumanGateRecord | None: ...

    async def open_for_project(self, project_id: UUID) -> tuple[HumanGateRecord, ...]:
        """Gates raised for this project and not yet answered, oldest first.

        The operator needs the whole set, not the latest: a project can be
        parked on several gates at once, and reporting only one would make
        answering it look like progress when nothing moved.
        """
        ...
