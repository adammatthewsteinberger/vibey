# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import UTC, datetime, timedelta
from uuid import UUID

import asyncpg
import pytest

from vibey.application.dto import EngineHealthRecord, RotationCursor
from vibey.domain.capacity import CreditsExhausted, WindowExhausted
from vibey.domain.circuit import BackoffProbe, DeadlineProbe, schedule_probe
from vibey.domain.engine import EngineId
from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository
from vibey.infrastructure.db.rotation_cursor_repository import PostgresRotationCursorRepository

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _record(
    project_id: UUID, engine_id: str = "claudeloop", **overrides: object
) -> EngineHealthRecord:
    defaults: dict[str, object] = {
        "project_id": project_id,
        "engine_id": engine_id,
        "installed": True,
        "version": "1.2.3",
        "conformance_ok": True,
        "conformance_at": NOW,
        "auth_ok_at": NOW,
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


async def test_upsert_then_get_round_trips(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresEngineHealthRepository(migrated_pool)

    written = await repo.upsert(_record(project_id))
    fetched = await repo.get(project_id, "claudeloop")

    assert fetched is not None
    assert fetched.engine_id == "claudeloop"
    assert fetched.circuit == "closed"
    assert written.project_id == project_id


async def test_upsert_is_idempotent_on_project_and_engine(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresEngineHealthRepository(migrated_pool)

    await repo.upsert(_record(project_id, selected_count=1))
    await repo.upsert(_record(project_id, selected_count=2))

    async with migrated_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM engine_health WHERE project_id = $1 AND engine_id = 'claudeloop'",
            project_id,
        )
    assert count == 1

    fetched = await repo.get(project_id, "claudeloop")
    assert fetched is not None
    assert fetched.selected_count == 2


async def test_list_for_project_returns_all_engines_ordered(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresEngineHealthRepository(migrated_pool)
    await repo.upsert(_record(project_id, engine_id="codexloop"))
    await repo.upsert(_record(project_id, engine_id="claudeloop"))

    records = await repo.list_for_project(project_id)

    assert [r.engine_id for r in records] == ["claudeloop", "codexloop"]


async def test_get_returns_none_for_unknown_engine(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresEngineHealthRepository(migrated_pool)
    assert await repo.get(project_id, "nonexistent") is None


async def test_window_exhausted_with_resets_at_is_allowed(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresEngineHealthRepository(migrated_pool)
    resets_at = NOW + timedelta(minutes=5)

    written = await repo.upsert(
        _record(
            project_id,
            circuit="open",
            capacity_state="WindowExhausted",
            resets_at=resets_at,
        )
    )

    assert written.resets_at == resets_at


async def test_credits_exhausted_with_a_resets_at_violates_the_db_check_constraint(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    """The schema-level expression of the *loop family's hardest-won rule
    (data-model.md §3.8): a credits balance has no clock, and the database
    itself refuses to represent one."""
    repo = PostgresEngineHealthRepository(migrated_pool)

    with pytest.raises(asyncpg.exceptions.CheckViolationError):
        await repo.upsert(
            _record(
                project_id,
                circuit="open",
                capacity_state="CreditsExhausted",
                resets_at=NOW + timedelta(minutes=5),
            )
        )


async def test_credits_exhausted_without_a_resets_at_is_allowed(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresEngineHealthRepository(migrated_pool)

    written = await repo.upsert(
        _record(project_id, circuit="open", capacity_state="CreditsExhausted", resets_at=None)
    )

    assert written.capacity_state == "CreditsExhausted"
    assert written.resets_at is None


async def test_probe_scheduling_round_trip_for_window_exhausted(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    """Integration of domain/circuit.py::schedule_probe with real
    persistence: a WindowExhausted probe is a DeadlineProbe, and it
    persists with its resets_at intact."""
    repo = PostgresEngineHealthRepository(migrated_pool)
    resets_at = NOW + timedelta(minutes=10)
    capacity = WindowExhausted(resets_at=resets_at, rate_limit_type="rpm")

    probe = schedule_probe(capacity, now=NOW, attempt=0)
    assert isinstance(probe, DeadlineProbe)

    written = await repo.upsert(
        _record(
            project_id,
            circuit="open",
            capacity_state="WindowExhausted",
            resets_at=resets_at,
            probe_next_at=probe.at,
            probe_attempt=0,
        )
    )

    assert written.probe_next_at == probe.at
    assert written.resets_at == resets_at


async def test_upsert_raises_lookup_error_when_fetchrow_returns_none() -> None:
    class _NullConn:
        async def fetchrow(self, *a: object, **kw: object) -> None:
            return None

    class _NullPool:
        def acquire(self) -> "_NullPool":
            return self

        async def __aenter__(self) -> _NullConn:
            return _NullConn()

        async def __aexit__(self, *a: object) -> None:
            pass

    repo = PostgresEngineHealthRepository(_NullPool())  # type: ignore[arg-type]
    with pytest.raises(LookupError, match="upsert"):
        await repo.upsert(_record(UUID(int=0)))


async def test_probe_scheduling_round_trip_for_credits_exhausted_never_persists_a_deadline(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    """The other half of the same property: a CreditsExhausted probe is a
    BackoffProbe with no deadline, and persisting it faithfully (resets_at
    left NULL) is exactly what the CHECK constraint requires."""
    repo = PostgresEngineHealthRepository(migrated_pool)
    capacity = CreditsExhausted(can_purchase=True)

    probe = schedule_probe(capacity, now=NOW, attempt=2)
    assert isinstance(probe, BackoffProbe)

    written = await repo.upsert(
        _record(
            project_id,
            circuit="open",
            capacity_state="CreditsExhausted",
            resets_at=None,
            probe_next_at=probe.next_at,
            probe_attempt=probe.attempt,
        )
    )

    assert written.probe_next_at == probe.next_at
    assert written.resets_at is None
    assert written.probe_attempt == 2


async def test_row_engine_id_is_a_real_engine_id_enum(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    """Regression: the engine_id column is text; leaving the raw str on the
    record propagated into RotationCursor and crashed update_many's `.value`
    access the first time EngineSelector ran against real Postgres."""
    repo = PostgresEngineHealthRepository(migrated_pool)
    await repo.upsert(_record(project_id))

    fetched = await repo.get(project_id, "claudeloop")
    assert fetched is not None
    assert isinstance(fetched.engine_id, EngineId)
    listed = await repo.list_for_project(project_id)
    assert all(isinstance(r.engine_id, EngineId) for r in listed)


async def test_health_engine_id_survives_rotation_cursor_round_trip(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    """The exact production crash path: EngineSelector builds RotationCursors
    from health-record engine ids and calls update_many, which needs
    `.value`. A raw str here raised AttributeError before the fix."""
    health = PostgresEngineHealthRepository(migrated_pool)
    await health.upsert(_record(project_id))
    record = (await health.list_for_project(project_id))[0]

    cursors = PostgresRotationCursorRepository(migrated_pool)
    await cursors.update_many(
        project_id,
        (RotationCursor(project_id=project_id, engine_id=record.engine_id, current=7, order=0),),
    )

    fetched = await cursors.get(project_id, EngineId.CLAUDELOOP)
    assert fetched is not None
    assert fetched.current == 7
