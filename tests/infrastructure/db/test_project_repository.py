from pathlib import Path
from uuid import UUID

import asyncpg

from vibey.domain.phase import Phase
from vibey.infrastructure.db.project_repository import PostgresProjectRepository


async def test_create_get_and_transition_project(
    migrated_pool: asyncpg.Pool, tmp_path: Path
) -> None:
    repo = PostgresProjectRepository(migrated_pool)
    created = await repo.create(
        "demo", tmp_path, max_cycles=7, config={"project": {"name": "demo"}}
    )
    assert isinstance(created.project_id, UUID)
    assert created.phase is Phase.INTAKE
    assert created.cycle == 1
    assert created.max_cycles == 7

    same = await repo.get(created.project_id)
    assert same == created

    transitioned = await repo.transition(created.project_id, expected=Phase.INTAKE, to=Phase.DESIGN)
    assert transitioned.phase is Phase.DESIGN
    assert transitioned.cycle == 1

    # Transition with cycle increment
    transitioned_loop = await repo.transition(
        created.project_id, expected=Phase.DESIGN, to=Phase.BUILD, cycle=2
    )
    assert transitioned_loop.phase is Phase.BUILD
    assert transitioned_loop.cycle == 2


async def test_transition_rejects_stale_expected_phase(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresProjectRepository(migrated_pool)
    try:
        await repo.transition(project_id, expected=Phase.DESIGN, to=Phase.BUILD)
    except ValueError as exc:
        assert "expected phase" in str(exc)
    else:
        raise AssertionError("expected stale transition rejection")


async def test_get_missing_project_returns_none(migrated_pool: asyncpg.Pool) -> None:
    repo = PostgresProjectRepository(migrated_pool)
    assert await repo.get(UUID(int=0)) is None
