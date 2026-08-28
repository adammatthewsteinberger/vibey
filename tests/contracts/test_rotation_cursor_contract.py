# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Contract test: FakeRotationCursorRepository behaves like
PostgresRotationCursorRepository for the same inputs.

Parametrized over [fake, postgres] so a broken fake that silently
diverges from the real implementation breaks this test instead of
letting a false-green propagate through every faked-mode test.
"""

from uuid import UUID

import asyncpg
import pytest

from tests.fakes import FakeRotationCursorRepository
from vibey.application.dto import RotationCursor
from vibey.domain.engine import EngineId
from vibey.infrastructure.db.rotation_cursor_repository import PostgresRotationCursorRepository


@pytest.fixture()
def fake_repo() -> FakeRotationCursorRepository:
    return FakeRotationCursorRepository()


@pytest.fixture()
def pg_repo(migrated_pool: asyncpg.Pool) -> PostgresRotationCursorRepository:
    return PostgresRotationCursorRepository(migrated_pool)


@pytest.fixture(params=["fake", "postgres"])
def repo(
    request: pytest.FixtureRequest,
    fake_repo: FakeRotationCursorRepository,
    pg_repo: PostgresRotationCursorRepository,
) -> object:
    return fake_repo if request.param == "fake" else pg_repo


async def test_get_returns_none_initially(repo: object, project_id: UUID) -> None:
    result = await repo.get(project_id, EngineId.CLAUDELOOP)  # type: ignore[union-attr]
    assert result is None


async def test_upsert_then_get_round_trips(repo: object, project_id: UUID) -> None:
    cursor = RotationCursor(
        project_id=project_id,
        engine_id=EngineId.CLAUDELOOP,
        current=5,
        order=0,
    )
    await repo.upsert(cursor)  # type: ignore[union-attr]
    fetched = await repo.get(project_id, EngineId.CLAUDELOOP)  # type: ignore[union-attr]

    assert fetched is not None
    assert fetched.project_id == project_id
    assert fetched.engine_id == EngineId.CLAUDELOOP
    assert fetched.current == 5
    assert fetched.order == 0


async def test_upsert_overwrites(repo: object, project_id: UUID) -> None:
    c1 = RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=0, order=0)
    c2 = RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=10, order=1)
    await repo.upsert(c1)  # type: ignore[union-attr]
    await repo.upsert(c2)  # type: ignore[union-attr]

    fetched = await repo.get(project_id, EngineId.CLAUDELOOP)  # type: ignore[union-attr]
    assert fetched is not None
    assert fetched.current == 10
    assert fetched.order == 1


async def test_list_for_project_returns_ordered(repo: object, project_id: UUID) -> None:
    await repo.upsert(  # type: ignore[union-attr]
        RotationCursor(project_id=project_id, engine_id=EngineId.CODEXLOOP, current=0, order=2)
    )
    await repo.upsert(  # type: ignore[union-attr]
        RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=0, order=0)
    )

    cursors = await repo.list_for_project(project_id)  # type: ignore[union-attr]
    assert len(cursors) >= 2
    orders = [c.order for c in cursors]
    assert orders == sorted(orders)


async def test_initialize_is_idempotent(repo: object, project_id: UUID) -> None:
    engines = (EngineId.CLAUDELOOP, EngineId.CODEXLOOP)
    await repo.initialize_for_project(project_id, engines)  # type: ignore[union-attr]
    await repo.upsert(  # type: ignore[union-attr]
        RotationCursor(project_id=project_id, engine_id=EngineId.CLAUDELOOP, current=99, order=0)
    )
    second = await repo.initialize_for_project(project_id, engines)  # type: ignore[union-attr]

    by_id = {c.engine_id: c for c in second}
    assert by_id[EngineId.CLAUDELOOP].current == 99
