"""Faked-mode rotation: forced-rotation scenario where an engine wind-down
triggers selection of a different engine, exercising the full rotation
stack without subprocesses.
"""

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
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId, JobRequirement
from vibey.infrastructure.engines.descriptors import BY_ENGINE_ID


class _FakeEngineHealthRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[object, str], EngineHealthRecord] = {}

    async def get(self, project_id: object, engine_id: str) -> EngineHealthRecord | None:
        return self._records.get((project_id, engine_id))

    async def upsert(self, record: EngineHealthRecord) -> EngineHealthRecord:
        self._records[(record.project_id, record.engine_id.value)] = record
        return record

    async def list_for_project(self, project_id: object) -> tuple[EngineHealthRecord, ...]:
        return tuple(r for (pid, _), r in self._records.items() if pid == project_id)


class _FakeRotationCursorRepository:
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


async def _build_stack(
    engines: list[EngineId],
) -> tuple[RotationHandoffService, EngineSelector, object]:
    repo = _FakeEngineHealthRepository()
    cursor_repo = _FakeRotationCursorRepository()
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
    return handoff, selector, project_id


@pytest.mark.live
async def test_forced_rotation_selects_different_engine() -> None:
    """When an engine winds down, rotation must select a DIFFERENT engine."""
    handoff, _, project_id = await _build_stack(
        [EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.AGYLOOP]
    )

    decision = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-rotate-1",
        current_engine=EngineId.CLAUDELOOP,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=0,
        ledger_snapshot={"remaining_work": ["finish tests"]},
    )

    assert isinstance(decision, HandoffDecision)
    assert decision.next_engine != EngineId.CLAUDELOOP
    assert decision.wind_down_count == 1


@pytest.mark.live
async def test_consecutive_wind_downs_rotate_through_engines() -> None:
    """Two consecutive wind-downs cycle through at least two different engines."""
    handoff, _, project_id = await _build_stack(
        [EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.AGYLOOP]
    )

    d1 = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-2",
        current_engine=EngineId.CLAUDELOOP,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=0,
        ledger_snapshot={},
    )

    d2 = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-2",
        current_engine=d1.next_engine,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=1,
        ledger_snapshot={},
    )

    assert d2.next_engine != d1.next_engine
    assert d2.wind_down_count == 2


@pytest.mark.live
async def test_max_wind_downs_raises_too_many() -> None:
    """After max rotations (3), further wind-down attempts raise."""
    handoff, _, project_id = await _build_stack(
        [EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.AGYLOOP]
    )

    with pytest.raises(TooManyWindDowns):
        await handoff.handle_wind_down(
            project_id=project_id,
            work_item_id="wi-3",
            current_engine=EngineId.CLAUDELOOP,
            requirement=JobRequirement(effort=Effort.STANDARD),
            wind_down_count=3,
            ledger_snapshot={},
        )


@pytest.mark.live
async def test_handoff_brief_captures_ledger_residue() -> None:
    """The handoff brief should preserve the ledger snapshot so the next
    engine can resume from where the previous one left off."""
    handoff, _, project_id = await _build_stack([EngineId.CLAUDELOOP, EngineId.CODEXLOOP])

    ledger = {"remaining_work": ["item-a", "item-b"], "completed": 3}
    decision = await handoff.handle_wind_down(
        project_id=project_id,
        work_item_id="wi-4",
        current_engine=EngineId.CLAUDELOOP,
        requirement=JobRequirement(effort=Effort.STANDARD),
        wind_down_count=0,
        ledger_snapshot=ledger,
    )

    assert decision.handoff_brief["remaining_work"] == ["item-a", "item-b"]
    assert decision.handoff_brief["from_engine"] == "claudeloop"
    assert decision.handoff_brief["reason"] == "wind_down"
