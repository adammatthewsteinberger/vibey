# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Data transfer objects crossing the application/infrastructure boundary.
Unlike domain/ types these may be mutated by callers and are not required to
be pure -- they are shapes, not behavior."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import UUID

from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId, IsolationLevel
from vibey.domain.job import FailureClass, JobState
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
class ProjectRecord:
    project_id: UUID
    name: str
    repo_path: Path
    phase: Phase
    cycle: int
    max_cycles: int
    config: Mapping[str, object]
    created_at: datetime
    updated_at: datetime


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


@dataclass(frozen=True, slots=True)
class RunSpec:
    """What to run: the prompt/task plus the effort and isolation the
    adapter must translate into the engine's own flags."""

    run_id: UUID
    worktree_path: Path
    prompt: str
    effort: Effort
    isolation: IsolationLevel
    session_id: str | None = None  # set to resume a warm session


@dataclass(frozen=True, slots=True)
class RunHandle:
    run_id: UUID
    engine_id: EngineId
    run_dir: Path
    pid: int | None


@dataclass(frozen=True, slots=True)
class PreflightResult:
    installed: bool
    version: str | None
    auth_ok: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class StopSummary:
    run_id: UUID
    complete: bool
    summary: str
    remaining_work: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    path: Path
    schema_version: int
    session_id: str | None


@dataclass(frozen=True, slots=True)
class EngineEvent:
    """One line of a runner's events.jsonl, before translation into a
    vibey LedgerEvent -- the adapter's own vocabulary, not ours."""

    kind: str
    at: datetime
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ConformanceCheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    engine_id: EngineId
    checks: tuple[ConformanceCheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)


@dataclass(frozen=True, slots=True)
class EngineHealthRecord:
    project_id: UUID
    engine_id: EngineId
    installed: bool
    version: str | None
    conformance_ok: bool
    conformance_at: datetime | None
    auth_ok_at: datetime | None
    circuit: str
    capacity_state: str | None
    resets_at: datetime | None
    probe_next_at: datetime | None
    probe_attempt: int
    consecutive_fail: int
    ewma_failure: float
    cost_usd_cycle: float
    selected_count: int


@dataclass(frozen=True, slots=True)
class FailureAttribution:
    failure_class: FailureClass
    detail: str


@dataclass(frozen=True, slots=True)
class RotationCursor:
    """SWRR cursor state for one engine in one project."""

    project_id: UUID
    engine_id: EngineId
    current: int
    order: int
