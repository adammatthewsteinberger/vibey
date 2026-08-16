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
