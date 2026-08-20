"""Tests for application/engine_selector.py — the first production caller
of domain/rotation.select()."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from vibey.application.dto import EngineHealthRecord, RotationCursor
from vibey.application.engine_health_service import EngineHealthService
from vibey.application.engine_selector import EngineSelector
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId, JobRequirement
from vibey.domain.errors import NoEligibleEngine
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
        results = []
        for idx, eid in enumerate(engines):
            key = (project_id, eid.value)
            if key not in self._cursors:
                c = RotationCursor(project_id=project_id, engine_id=eid, current=0, order=idx)
                self._cursors[key] = c
                results.append(c)
        return tuple(
            c
            for (pid, _), c in sorted(self._cursors.items(), key=lambda x: x[1].order)
            if pid == project_id
        )


def _healthy_record(
    project_id: object, engine_id: EngineId, **overrides: object
) -> EngineHealthRecord:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "project_id": project_id,
        "engine_id": engine_id,
        "installed": True,
        "version": "1.0.0",
        "conformance_ok": True,
        "conformance_at": now,
        "auth_ok_at": now,
        "circuit": "closed",
        "capacity_state": None,
        "resets_at": None,
        "probe_next_at": None,
        "probe_attempt": 0,
        "consecutive_fail": 0,
        "ewma_failure": 0.0,
        "cost_usd_cycle": 0.0,
        "selected_count": 0,
    }
    defaults.update(overrides)
    return EngineHealthRecord(**defaults)  # type: ignore[arg-type]


async def _setup(
    engines: list[EngineId] | None = None,
    **health_overrides: object,
) -> tuple[EngineSelector, object]:
    engines = engines or [EngineId.CLAUDELOOP, EngineId.CODEXLOOP]
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    for eid in engines:
        await repo.upsert(_healthy_record(project_id, eid, **health_overrides))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )
    return selector, project_id


async def test_select_engine_returns_an_engine() -> None:
    selector, project_id = await _setup()

    engine_id, selection = await selector.select_engine(
        project_id, JobRequirement(effort=Effort.STANDARD)
    )

    assert engine_id in {EngineId.CLAUDELOOP, EngineId.CODEXLOOP}
    assert selection.engine_id == engine_id


async def test_select_engine_rotates_between_engines() -> None:
    selector, project_id = await _setup()
    req = JobRequirement(effort=Effort.STANDARD)

    selected = set()
    for _ in range(10):
        eid, _ = await selector.select_engine(project_id, req)
        selected.add(eid)

    assert len(selected) == 2


async def test_select_engine_raises_when_no_eligible() -> None:
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    # Only create a record with circuit open
    await repo.upsert(_healthy_record(project_id, EngineId.CLAUDELOOP, circuit="open"))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )

    with pytest.raises(NoEligibleEngine):
        await selector.select_engine(project_id, JobRequirement(effort=Effort.STANDARD))


async def test_select_engine_respects_excluded() -> None:
    selector, project_id = await _setup()

    engine_id, _ = await selector.select_engine(
        project_id,
        JobRequirement(effort=Effort.STANDARD, excluded=frozenset({EngineId.CLAUDELOOP})),
    )

    assert engine_id == EngineId.CODEXLOOP


async def test_select_engine_respects_allow_list() -> None:
    selector, project_id = await _setup(
        engines=[EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.AGYLOOP]
    )

    engine_id, _ = await selector.select_engine(
        project_id,
        JobRequirement(effort=Effort.STANDARD),
        allow_list=frozenset({EngineId.AGYLOOP}),
    )

    assert engine_id == EngineId.AGYLOOP


async def test_select_engine_affinity_boosts_preferred_engine() -> None:
    selector, project_id = await _setup()

    # With affinity for codexloop, it should win more often
    codex_wins = 0
    for _ in range(20):
        eid, _ = await selector.select_engine(
            project_id,
            JobRequirement(effort=Effort.STANDARD),
            affinity_engine=EngineId.CODEXLOOP,
        )
        if eid == EngineId.CODEXLOOP:
            codex_wins += 1

    assert codex_wins > 10


async def test_select_engine_updates_cursors() -> None:
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    for eid in [EngineId.CLAUDELOOP, EngineId.CODEXLOOP]:
        await repo.upsert(_healthy_record(project_id, eid))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )

    await selector.select_engine(project_id, JobRequirement(effort=Effort.STANDARD))

    # Cursors should now exist
    cursors = await cursor_repo.list_for_project(project_id)
    assert len(cursors) >= 2


async def test_select_engine_with_no_health_records_raises() -> None:
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )

    with pytest.raises(NoEligibleEngine):
        await selector.select_engine(uuid4(), JobRequirement(effort=Effort.STANDARD))


async def test_select_engine_skips_uninstalled_engines() -> None:
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    await repo.upsert(_healthy_record(project_id, EngineId.CLAUDELOOP, installed=False))
    await repo.upsert(_healthy_record(project_id, EngineId.CODEXLOOP))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )

    eid, _ = await selector.select_engine(project_id, JobRequirement(effort=Effort.STANDARD))
    assert eid == EngineId.CODEXLOOP


async def test_select_engine_skips_unknown_descriptors() -> None:
    """Health records for engines not in descriptors dict should be skipped."""
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    await repo.upsert(_healthy_record(project_id, EngineId.CLAUDELOOP))
    await repo.upsert(_healthy_record(project_id, EngineId.CODEXLOOP))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors={EngineId.CODEXLOOP: BY_ENGINE_ID[EngineId.CODEXLOOP]},
    )

    eid, _ = await selector.select_engine(project_id, JobRequirement(effort=Effort.STANDARD))
    assert eid == EngineId.CODEXLOOP


async def test_select_engine_handles_missing_cursor_gracefully() -> None:
    """When cursor_map is empty after init (edge case), fallback creates cursor."""
    repo = FakeEngineHealthRepository()
    project_id = uuid4()

    await repo.upsert(_healthy_record(project_id, EngineId.CLAUDELOOP))

    class _BrokenCursorRepo(FakeRotationCursorRepository):
        async def initialize_for_project(
            self, project_id: object, engines: tuple[EngineId, ...]
        ) -> tuple[RotationCursor, ...]:
            return ()

        async def list_for_project(self, project_id: object) -> tuple[RotationCursor, ...]:
            return ()

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=_BrokenCursorRepo(),
        descriptors=BY_ENGINE_ID,
    )

    eid, _ = await selector.select_engine(project_id, JobRequirement(effort=Effort.STANDARD))
    assert eid == EngineId.CLAUDELOOP


async def test_select_engine_skips_auth_expired_engines() -> None:
    repo = FakeEngineHealthRepository()
    cursor_repo = FakeRotationCursorRepository()
    project_id = uuid4()

    # Auth expired (auth_ok_at is None)
    await repo.upsert(_healthy_record(project_id, EngineId.CLAUDELOOP, auth_ok_at=None))
    await repo.upsert(_healthy_record(project_id, EngineId.CODEXLOOP))

    svc = EngineHealthService(repo)
    selector = EngineSelector(
        health_service=svc,
        cursor_repository=cursor_repo,
        descriptors=BY_ENGINE_ID,
    )

    eid, _ = await selector.select_engine(project_id, JobRequirement(effort=Effort.STANDARD))
    assert eid == EngineId.CODEXLOOP


async def test_an_expired_open_circuit_half_opens_and_probes() -> None:
    """The probe deadline must actually fire at selection: without it an
    opened circuit could only be closed by a success that could never
    happen, because open circuits are never selected -- one capacity
    rejection removed an engine from the project permanently, live."""
    from dataclasses import replace as _replace
    from datetime import UTC, datetime, timedelta

    repo = FakeEngineHealthRepository()
    project_id = uuid4()
    past = datetime.now(UTC) - timedelta(minutes=30)
    stuck_open = _replace(
        _healthy_record(project_id, EngineId.CLAUDELOOP),
        circuit="open",
        resets_at=past,
    )
    await repo.upsert(stuck_open)
    selector = EngineSelector(
        health_service=EngineHealthService(repo),
        cursor_repository=FakeRotationCursorRepository(),
        descriptors=BY_ENGINE_ID,
    )

    engine_id, _ = await selector.select_engine(project_id, JobRequirement(effort=Effort.LOW))

    assert engine_id is EngineId.CLAUDELOOP


async def test_an_open_circuit_before_its_deadline_stays_excluded() -> None:
    from dataclasses import replace as _replace
    from datetime import UTC, datetime, timedelta

    import pytest as _pytest

    from vibey.domain.errors import NoEligibleEngine

    repo = FakeEngineHealthRepository()
    project_id = uuid4()
    future = datetime.now(UTC) + timedelta(minutes=30)
    for resets_at in (future, None):
        stuck_open = _replace(
            _healthy_record(project_id, EngineId.CLAUDELOOP),
            circuit="open",
            resets_at=resets_at,
        )
        await repo.upsert(stuck_open)
        selector = EngineSelector(
            health_service=EngineHealthService(repo),
            cursor_repository=FakeRotationCursorRepository(),
            descriptors=BY_ENGINE_ID,
        )
        with _pytest.raises(NoEligibleEngine):
            await selector.select_engine(project_id, JobRequirement(effort=Effort.LOW))
