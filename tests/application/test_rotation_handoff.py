"""Tests for application/rotation_handoff.py — wind-down and capacity
rejection handling with bounded livelock."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from vibey.application.dto import EngineHealthRecord, RotationCursor
from vibey.application.engine_health_service import EngineHealthService
from vibey.application.engine_selector import EngineSelector
from vibey.application.rotation_handoff import (
    HandoffDecision,
    RotationHandoffService,
    TooManyWindDowns,
)
from vibey.domain.capacity import CreditsExhausted, WindowExhausted
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId, JobRequirement
from vibey.infrastructure.engines.descriptors import BY_ENGINE_ID


class FakeEngineHealthRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[object, str], EngineHealthRecord] = {}

    async def get(self, project_id: object, engine_id: str) -> EngineHealthRecord | None:
        return self._records.get((project_id, engine_id))

    async def upsert(self, record: EngineHealthRecord) -> EngineHealthRecord:
        self._records[(record.project_id, record.engine_id.value)] = record
        return record

    async def list_for_project(self, project_id: object) -> tuple[EngineHealthRecord, ...]:
        return tuple(r for (pid, _), r in self._records.items() if pid == project_id)


class FakeRotationCursorRepository:
    def __init__(self) -> None:
        self._cursors: dict[tuple[object, str], RotationCursor] = {}

    async def get(self, project_id: object, engine_id: EngineId) -> RotationCursor | None:
        return self._cursors.get((project_id, engine_id.value))

    async def list_for_project(self, project_id: object) -> tuple[RotationCursor, ...]:
        return tuple(c for (pid, _), c in self._cursors.items() if pid == project_id)

    async def upsert(self, cursor: RotationCursor) -> RotationCursor:
        self._cursors[(cursor.project_id, cursor.engine_id.value)] = cursor
        return cursor

    async def update_many(
        self, project_id: object, cursors: tuple[RotationCursor, ...]
    ) -> tuple[RotationCursor, ...]:
        for c in cursors:
            self._cursors[(c.project_id, c.engine_id.value)] = c
        return cursors

    async def initialize_for_project(
        self, project_id: object, engines: tuple[EngineId, ...]
    ) -> tuple[RotationCursor, ...]:
        for idx, eid in enumerate(engines):
            key = (project_id, eid.value)
            if key not in self._cursors:
                self._cursors[key] = RotationCursor(
                    project_id=project_id, engine_id=eid, current=0, order=idx
                )
        return tuple(
            c
            for (pid, _), c in sorted(self._cursors.items(), key=lambda x: x[1].order)
            if pid == project_id
        )


def _healthy_record(project_id: object, engine_id: EngineId) -> EngineHealthRecord:
    now = datetime.now(UTC)
    return EngineHealthRecord(
        project_id=project_id,
        engine_id=engine_id,
        installed=True,
        version="1.0.0",
        conformance_ok=True,
        conformance_at=now,
        auth_ok_at=now,
        circuit="closed",
        capacity_state=None,
        resets_at=None,
        probe_next_at=None,
        probe_attempt=0,
        consecutive_fail=0,
        ewma_failure=0.0,
        cost_usd_cycle=0.0,
        selected_count=0,
    )


async def _make_handoff_service(
    engines: list[EngineId] | None = None,
) -> tuple[RotationHandoffService, object]:
    engines = engines or [EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.AGYLOOP]
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    for eid in engines:
        await repo.upsert(_healthy_record(project_id, eid))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )
    handoff = RotationHandoffService(selector)
    return handoff, project_id


async def test_handle_wind_down_selects_different_engine() -> None:
    handoff, project_id = await _make_handoff_service()

    decision = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-1",
        current_engine=EngineId.CLAUDELOOP,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=0,
        ledger_snapshot={"remaining_work": ["task-a"]},
    )

    assert isinstance(decision, HandoffDecision)
    assert decision.next_engine != EngineId.CLAUDELOOP
    assert decision.wind_down_count == 1
    assert "wind_down" in decision.reason.lower() or "Wind-down" in decision.reason


async def test_handle_wind_down_increments_count() -> None:
    handoff, project_id = await _make_handoff_service()

    decision = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-1",
        current_engine=EngineId.CLAUDELOOP,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=1,
        ledger_snapshot={},
    )

    assert decision.wind_down_count == 2


async def test_handle_wind_down_raises_at_max() -> None:
    handoff, project_id = await _make_handoff_service()

    with pytest.raises(TooManyWindDowns):
        await handoff.handle_wind_down(
            project_id=project_id,
            work_item_id="wi-1",
            current_engine=EngineId.CLAUDELOOP,
            requirement=JobRequirement(effort=Effort.STANDARD),
            wind_down_count=3,
            ledger_snapshot={},
        )


async def test_handle_wind_down_brief_contains_required_fields() -> None:
    handoff, project_id = await _make_handoff_service()

    decision = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-1",
        current_engine=EngineId.CLAUDELOOP,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=0,
        ledger_snapshot={"remaining_work": ["task-a"]},
    )

    assert decision.handoff_brief["reason"] == "wind_down"
    assert decision.handoff_brief["from_engine"] == "claudeloop"
    assert decision.handoff_brief["work_item_id"] == "wi-1"
    assert decision.handoff_brief["remaining_work"] == ["task-a"]


async def test_handle_capacity_rejection_selects_different_engine() -> None:
    handoff, project_id = await _make_handoff_service()

    decision = await handoff.handle_capacity_rejection(
        project_id=project_id,
        current_engine=EngineId.CLAUDELOOP,
        capacity_state=CreditsExhausted(),
        requirement=JobRequirement(effort=Effort.STANDARD),
        ledger_snapshot={},
    )

    assert isinstance(decision, HandoffDecision)
    assert decision.next_engine != EngineId.CLAUDELOOP
    assert decision.wind_down_count == 0  # Capacity rejections don't count


async def test_handle_capacity_rejection_brief_contains_capacity_state() -> None:
    handoff, project_id = await _make_handoff_service()

    decision = await handoff.handle_capacity_rejection(
        project_id=project_id,
        current_engine=EngineId.CODEXLOOP,
        capacity_state=WindowExhausted(),
        requirement=JobRequirement(effort=Effort.STANDARD),
        ledger_snapshot={"remaining_work": ["task-b"]},
    )

    assert decision.handoff_brief["reason"] == "capacity_rejection"
    assert decision.handoff_brief["capacity_state"] == "WindowExhausted"
    assert decision.handoff_brief["from_engine"] == "codexloop"


async def test_too_many_wind_downs_is_a_vibey_error() -> None:
    from vibey.domain.errors import VibeyError

    assert issubclass(TooManyWindDowns, VibeyError)
