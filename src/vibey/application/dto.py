"""Data transfer objects crossing the application/infrastructure boundary.
Unlike domain/ types these may be mutated by callers and are not required to
be pure -- they are shapes, not behavior."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from vibey.domain.job import JobState
from vibey.domain.phase import Phase


@dataclass(frozen=True, slots=True)
class EnqueueRequest:
    project_id: UUID
    cycle: int
    phase: Phase
    kind: str
    idempotency_key: str
    payload: Mapping[str, object] = field(default_factory=dict)
    requirement: Mapping[str, object] = field(default_factory=dict)
    priority: int = 0
    work_item_id: str | None = None
    max_attempts: int = 7
    run_after: datetime | None = None
    depends_on: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class JobRecord:
    id: UUID
    project_id: UUID
    cycle: int
    phase: Phase
    kind: str
    state: JobState
    priority: int
    work_item_id: str | None
    payload: Mapping[str, object]
    requirement: Mapping[str, object]
    idempotency_key: str
    attempts: int
    max_attempts: int
    run_after: datetime
    lease_owner: str | None
    lease_expires_at: datetime | None
    assigned_engine: str | None
    last_error: Mapping[str, object] | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class HumanGateRequest:
    kind: str
    prompt: str
    options: tuple[str, ...] = ()
    default_answer: str | None = None
    timeout_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class HumanGateRecord:
    gate_id: UUID
    project_id: UUID
    job_id: UUID | None
    kind: str
    prompt: str
    options: tuple[str, ...]
    default_answer: str | None
    answer: Mapping[str, object] | None
    raised_at: datetime
    timeout_at: datetime | None
    answered_at: datetime | None
    answered_by: str | None
