# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Tests for infrastructure/db/rotation_cursor_repository.py against real Postgres.

Requires VIBEY_TEST_DATABASE_URL (or defaults to localhost vibey_test).
"""

from uuid import UUID

import asyncpg

from vibey.application.dto import RotationCursor
from vibey.domain.engine import EngineId
from vibey.infrastructure.db.rotation_cursor_repository import PostgresRotationCursorRepository


async def test_get_returns_none_when_not_initialized(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    result = await repo.get(project_id, EngineId.CLAUDELOOP)
    assert result is None


async def test_upsert_then_get_round_trips(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    cursor = RotationCursor(
        project_id=project_id,
        engine_id=EngineId.CLAUDELOOP,
        current=5,
        order=0,
    )

    written = await repo.upsert(cursor)
    fetched = await repo.get(project_id, EngineId.CLAUDELOOP)

    assert fetched is not None
    assert fetched.project_id == project_id
    assert fetched.engine_id == EngineId.CLAUDELOOP
    assert fetched.current == 5
    assert fetched.order == 0
    assert written == fetched


async def test_upsert_overwrites_existing(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    c1 = RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=0, order=0)
    c2 = RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=10, order=1)

    await repo.upsert(c1)
    await repo.upsert(c2)

    fetched = await repo.get(project_id, EngineId.CLAUDELOOP)
    assert fetched is not None
    assert fetched.current == 10
    assert fetched.order == 1

    async with migrated_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM rotation_cursor WHERE project_id = $1 AND engine_id = $2",
            project_id,
            EngineId.CLAUDELOOP.value,
        )
    assert count == 1


async def test_list_for_project_returns_ordered(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.CODEXLOOP, current=0, order=2)
    )
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=0, order=0)
    )
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.AGYLOOP, current=0, order=1)
    )

    cursors = await repo.list_for_project(project_id)

    assert len(cursors) == 3
    assert [c.order for c in cursors] == [0, 1, 2]
    assert cursors[0].engine_id == EngineId.CLAUDELOOP
    assert cursors[1].engine_id == EngineId.AGYLOOP
    assert cursors[2].engine_id == EngineId.CODEXLOOP


async def test_list_for_project_returns_empty_when_no_cursors(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    cursors = await repo.list_for_project(project_id)
    assert cursors == ()


async def test_update_many_updates_all_atomically(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=0, order=0)
    )
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.CODEXLOOP, current=0, order=1)
    )

    updated = await repo.update_many(
        project_id,
        (
            RotationCursor(
                project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=3, order=0
            ),
            RotationCursor(
                project_id=project_id, engine_id=EngineId.CODEXLOOP, current=-2, order=1
            ),
        ),
    )

    assert len(updated) == 2
    fetched = await repo.list_for_project(project_id)
    by_id = {c.engine_id: c for c in fetched}
    assert by_id[EngineId.CLAUDELOOP].current == 3
    assert by_id[EngineId.CODEXLOOP].current == -2


async def test_initialize_for_project_creates_cursors(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    engines = (EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.AGYLOOP)

    cursors = await repo.initialize_for_project(project_id, engines)

    assert len(cursors) == 3
    for i, cursor in enumerate(cursors):
        assert cursor.project_id == project_id
        assert cursor.current == 0
        assert cursor.order == i


async def test_initialize_for_project_is_idempotent(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    engines = (EngineId.CLAUDELOOP, EngineId.CODEXLOOP)

    await repo.initialize_for_project(project_id, engines)
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=99, order=0)
    )
    second = await repo.initialize_for_project(project_id, engines)

    assert len(second) == 2
    by_id = {c.engine_id: c for c in second}
    assert by_id[EngineId.CLAUDELOOP].current == 99


async def test_initialize_adds_new_engines_without_resetting_existing(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresRotationCursorRepository(migrated_pool)
    await repo.initialize_for_project(project_id, (EngineId.CLAUDELOOP,))
    await repo.upsert(
        RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=42, order=0)
    )

    cursors = await repo.initialize_for_project(
        project_id, (EngineId.CLAUDELOOP, EngineId.CODEXLOOP)
    )

    by_id = {c.engine_id: c for c in cursors}
    assert by_id[EngineId.CLAUDELOOP].current == 42
    assert by_id[EngineId.CODEXLOOP].current == 0


async def test_fk_constraint_with_cascade_exists(
    migrated_pool: asyncpg.Pool,
) -> None:
    async with migrated_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT confdeltype
            FROM pg_constraint
            WHERE conname = 'rotation_cursor_project_id_fkey'
            """,
        )
    assert row is not None
    assert row["confdeltype"] == b"c"  # 'c' = CASCADE (asyncpg returns bytes for char)
