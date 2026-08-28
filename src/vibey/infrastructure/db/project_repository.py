# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Postgres persistence for project lifecycle and guarded phase updates."""

import json
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

import asyncpg

from vibey.application.dto import ProjectRecord
from vibey.domain.phase import Phase


def _row_to_project(row: asyncpg.Record) -> ProjectRecord:
    return ProjectRecord(
        project_id=row["id"],
        name=row["name"],
        repo_path=Path(row["repo_path"]),
        phase=Phase(row["phase"]),
        cycle=row["cycle"],
        max_cycles=row["max_cycles"],
        config=json.loads(row["config"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresProjectRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        name: str,
        repo_path: Path,
        *,
        max_cycles: int,
        config: Mapping[str, object],
    ) -> ProjectRecord:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO project (name, repo_path, max_cycles, config)
                VALUES ($1, $2, $3, $4::jsonb)
                RETURNING *
                """,
                name,
                str(repo_path.resolve()),
                max_cycles,
                json.dumps(dict(config)),
            )
            if row is None:
                raise LookupError("project insert returned no row")
            return _row_to_project(row)

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM project WHERE id = $1", project_id)
            return _row_to_project(row) if row is not None else None

    async def get_latest(self) -> ProjectRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM project ORDER BY created_at DESC LIMIT 1")
            return _row_to_project(row) if row is not None else None

    async def transition(
        self,
        project_id: UUID,
        *,
        expected: Phase,
        to: Phase,
        cycle: int | None = None,
    ) -> ProjectRecord:
        async with self._pool.acquire() as conn:
            if cycle is not None:
                row = await conn.fetchrow(
                    """
                    UPDATE project
                    SET phase = $3, cycle = $4, updated_at = now()
                    WHERE id = $1 AND phase = $2
                    RETURNING *
                    """,
                    project_id,
                    expected.value,
                    to.value,
                    cycle,
                )
            else:
                row = await conn.fetchrow(
                    """
                    UPDATE project
                    SET phase = $3, updated_at = now()
                    WHERE id = $1 AND phase = $2
                    RETURNING *
                    """,
                    project_id,
                    expected.value,
                    to.value,
                )
            if row is None:
                raise ValueError(
                    f"project {project_id} is not in expected phase {expected.value!r}"
                )
            return _row_to_project(row)
